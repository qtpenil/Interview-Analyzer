import os
import shutil
import tempfile
import uuid

from app.core.config import settings
from app.integration.ffmpeg.manager import ffmpeg_manager
from app.integration.ffmpeg.utils import build_keep_intervals
from app.integration.transcription.utils import compute_chunk_size_ms


def group_keep_intervals(
    intervals: list[tuple[float, float]],
    target_duration_seconds: float,
) -> list[list[tuple[float, float]]]:
    """
    Group a flat list of keep_intervals into chunk groups that never
    cross a real silence gap.

    A chunk boundary may only fall at a gap between two consecutive
    keep_intervals (i.e. a real silence cut point), never inside one.
    If a single interval is longer than the target duration, it is
    left as its own chunk rather than being split (splitting would
    re-introduce the original mid-speech-boundary problem).

    Every input interval appears exactly once across the output groups.

    Args:
        intervals: List of (start_sec, end_sec) tuples in original
            audio timeline, sorted ascending.
        target_duration_seconds: The desired chunk duration, typically
            computed by `compute_chunk_size_ms` from the rate-limit-
            driven sizing logic in utils.py.

    Returns:
        List of groups, where each group is a list of intervals
        belonging to that chunk.
    """

    if not intervals:
        return []

    groups: list[list[tuple[float, float]]] = []
    current_group: list[tuple[float, float]] = []
    current_duration = 0.0

    for interval in intervals:
        start, end = interval
        interval_duration = end - start

        # If this single interval already exceeds the target and we
        # already have a group, flush the current group and start a
        # new one with this interval alone.
        if current_group and interval_duration > target_duration_seconds:
            groups.append(current_group)
            current_group = [interval]
            current_duration = interval_duration
        elif current_group and current_duration + interval_duration > target_duration_seconds:
            # Adding this interval would exceed the target. Flush
            # the current group — but only if there is a real gap
            # between the last interval of the group and this one.
            # Since keep_intervals are already gap-separated (by
            # build_keep_intervals), any break between consecutive
            # intervals IS a real silence gap, so it's always safe
            # to break here.
            groups.append(current_group)
            current_group = [interval]
            current_duration = interval_duration
        else:
            current_group.append(interval)
            current_duration += interval_duration

    if current_group:
        groups.append(current_group)

    return groups


def build_offset_mapping(
    groups: list[list[tuple[float, float]]],
) -> list[list[dict]]:
    """
    Build offset mappings for each chunk group.

    For each group, produces a list of dicts mapping a position
    within the concatenated chunk to the true original-audio
    timestamp, accounting for the fact that gaps were removed
    during within-chunk concatenation.

    Returns:
        List of lists of dicts: one list per chunk group, where
        each dict is {"chunk_offset": float, "original_timestamp": float}.
    """

    all_mappings: list[list[dict]] = []

    for group in groups:
        chunk_mappings: list[dict] = []
        chunk_offset = 0.0

        for start, end in group:
            chunk_mappings.append(
                {
                    "chunk_offset": chunk_offset,
                    "original_timestamp": start,
                }
            )
            chunk_offset += end - start

        all_mappings.append(chunk_mappings)

    return all_mappings


def compute_silence_aware_chunk_boundaries(
    groups: list[list[tuple[float, float]]],
    offset_mappings: list[list[dict]],
) -> list[dict]:
    """
    Build chunk_boundary dicts for `split_audio_to_memory` from
    grouped intervals and their offset mappings.

    Each dict has `"offset_seconds"` and `"end_time"` keys representing
    the start and end of this chunk's audio in the concatenated file.
    """

    boundaries: list[dict] = []
    current_offset = 0.0

    for group, mappings in zip(groups, offset_mappings):
        group_duration = sum(end - start for start, end in group)
        boundaries.append(
            {
                "offset_seconds": current_offset,
                "end_time": current_offset + group_duration,
            }
        )
        current_offset += group_duration

    return boundaries


class AudioPrepResult:
    """
    Result of `prepare_audio_for_transcription` when called with
    `silence_aware` mode. Contains the audio file path plus the
    metadata needed for gap-respecting chunked transcription.
    """

    audio_path: str
    mode: str
    chunk_boundaries: list[dict] | None
    offset_mappings: list[list[dict]] | None

    def __init__(
        self,
        audio_path: str,
        mode: str,
        chunk_boundaries: list[dict] | None = None,
        offset_mappings: list[list[dict]] | None = None,
    ) -> None:
        self.audio_path = audio_path
        self.mode = mode
        self.chunk_boundaries = chunk_boundaries
        self.offset_mappings = offset_mappings


class InterviewMediaService:
    def prepare_audio_for_transcription(
        self,
        video_path: str,
        audio_prep_mode: str | None = None,
    ) -> AudioPrepResult:
        """
        Convert interview video into clean audio suitable for
        Whisper transcription.

        Args:
            video_path: Path to the video file.
            audio_prep_mode: One of "trimmed" (default), "raw", or
                "silence_aware".  Controlled by the AUDIO_PREP_MODE
                setting.

        Returns:
            AudioPrepResult containing the audio path and, for
            `silence_aware`, chunk boundaries and offset mappings.
        """

        mode = audio_prep_mode or settings.AUDIO_PREP_MODE

        with tempfile.TemporaryDirectory() as temp_dir:
            # Step 1: Extract audio from video
            audio_path = ffmpeg_manager.extract_audio(
                video_path=video_path,
                temp_dir=temp_dir,
            )

            # Step 2: Get audio duration
            duration = ffmpeg_manager.get_duration(
                audio_path=audio_path,
            )

            if mode == "raw":
                whisper_dir = os.path.join("storage", "whisper")
                os.makedirs(whisper_dir, exist_ok=True)
                return self._prepare_raw(
                    audio_path=audio_path,
                    duration=duration,
                    temp_dir=temp_dir,
                    whisper_dir=whisper_dir,
                )

            # Step 3 (trimmed / silence_aware): Detect silence
            silences = ffmpeg_manager.detect_silence(
                audio_path=audio_path,
            )

            # Step 4 (trimmed / silence_aware): Build intervals
            keep_intervals = build_keep_intervals(
                silences=silences,
                total_duration=duration,
            )

            # Step 5 (trimmed / silence_aware): Extract segments
            segment_paths = ffmpeg_manager.extract_segments(
                audio_path=audio_path,
                keep_intervals=keep_intervals,
                temp_dir=temp_dir,
            )

            # Permanent output path
            whisper_dir = os.path.join("storage", "whisper")
            os.makedirs(whisper_dir, exist_ok=True)

            if mode == "silence_aware":
                return self._prepare_silence_aware(
                    audio_path=audio_path,
                    keep_intervals=keep_intervals,
                    segment_paths=segment_paths,
                    temp_dir=temp_dir,
                    whisper_dir=whisper_dir,
                    duration=duration,
                )
            else:
                # Default / trimmed mode
                return self._prepare_trimmed(
                    audio_path=audio_path,
                    segment_paths=segment_paths,
                    temp_dir=temp_dir,
                    whisper_dir=whisper_dir,
                )

    def _prepare_trimmed(
        self,
        audio_path: str,
        segment_paths: list[str],
        temp_dir: str,
        whisper_dir: str,
    ) -> AudioPrepResult:
        """Default mode: extract segments and concatenate into a single file."""
        final_audio_path = os.path.join(whisper_dir, f"{uuid.uuid4()}.wav")
        temp_clean_audio = os.path.join(temp_dir, "clean_audio.wav")

        ffmpeg_manager.concat_segments(
            segment_paths=segment_paths,
            output_path=temp_clean_audio,
            temp_dir=temp_dir,
        )
        shutil.move(temp_clean_audio, final_audio_path)

        return AudioPrepResult(
            audio_path=final_audio_path,
            mode="trimmed",
        )

    def _prepare_raw(
        self,
        audio_path: str,
        duration: float,
        temp_dir: str,
        whisper_dir: str,
    ) -> AudioPrepResult:
        """
        Raw mode: skip silence trimming, use the full extracted
        audio as-is.  No silence detection or interval building
        is performed.
        """
        final_audio_path = os.path.join(whisper_dir, f"{uuid.uuid4()}.wav")
        shutil.move(audio_path, final_audio_path)

        return AudioPrepResult(
            audio_path=final_audio_path,
            mode="raw",
        )

    def _prepare_silence_aware(
        self,
        audio_path: str,
        keep_intervals: list[tuple[float, float]],
        segment_paths: list[str],
        temp_dir: str,
        whisper_dir: str,
        duration: float,
    ) -> AudioPrepResult:
        """
        Silence-aware mode: group keep_intervals into gap-respecting
        chunks, extract and concatenate within each chunk only, and
        build offset mappings for true-timeline timestamp recovery.
        """
        # Compute target chunk duration from the shared dynamic-sizing
        # logic in utils.py, so this path stays consistent with the
        # rate-limit-driven chunk count elsewhere in the codebase.
        total_duration_ms = int(duration * 1000)
        target_chunk_size_ms = compute_chunk_size_ms(
            total_duration_ms=total_duration_ms,
            default_chunk_minutes=5,
            max_chunks=20,
        )
        target_chunk_duration = target_chunk_size_ms / 1000.0

        # Group intervals into gap-respecting chunks
        groups = group_keep_intervals(keep_intervals, target_chunk_duration)

        # Build offset mappings for each chunk
        offset_mappings = build_offset_mapping(groups)

        # For each group: extract segments within the group, concatenate
        # only within the group, and save as a separate file.
        chunk_audio_paths: list[str] = []

        for group_idx, group in enumerate(groups):
            group_segment_paths = ffmpeg_manager.extract_segments(
                audio_path=audio_path,
                keep_intervals=group,
                temp_dir=temp_dir,
            )

            if not group_segment_paths:
                continue

            group_output_path = os.path.join(
                temp_dir, f"chunk_{group_idx}.wav"
            )
            temp_group_audio = os.path.join(
                temp_dir, f"chunk_{group_idx}_concat.wav"
            )

            ffmpeg_manager.concat_segments(
                segment_paths=group_segment_paths,
                output_path=temp_group_audio,
                temp_dir=temp_dir,
            )

            chunk_audio_paths.append(temp_group_audio)

        # Concatenate all chunk files into a single audio file for
        # split_audio_to_memory to consume. Each chunk preserves its
        # internal gap-respecting boundaries via the offset mapping.
        final_audio_path = os.path.join(
            whisper_dir, f"{uuid.uuid4()}.wav"
        )
        temp_clean_audio = os.path.join(
            temp_dir, "clean_audio.wav"
        )

        ffmpeg_manager.concat_segments(
            segment_paths=chunk_audio_paths,
            output_path=temp_clean_audio,
            temp_dir=temp_dir,
        )
        shutil.move(temp_clean_audio, final_audio_path)

        # Build chunk boundaries for split_audio_to_memory
        chunk_boundaries = compute_silence_aware_chunk_boundaries(
            groups, offset_mappings
        )

        return AudioPrepResult(
            audio_path=final_audio_path,
            mode="silence_aware",
            chunk_boundaries=chunk_boundaries,
            offset_mappings=offset_mappings,
        )


interview_media_service = InterviewMediaService()