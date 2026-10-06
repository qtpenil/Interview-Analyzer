import re
from io import BytesIO
from math import ceil
from typing import Any

from pydub import AudioSegment

from app.core.config import settings
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)

# Configure pydub to use the project's ffmpeg paths
AudioSegment.converter = settings.FFMPEG_PATH
AudioSegment.ffprobe = settings.FFPROBE_PATH


# ═══════════════════════════════════════════════════════════════════════════
# Shared dynamic chunk-sizing logic
# ═══════════════════════════════════════════════════════════════════════════


def compute_chunk_size_ms(total_duration_ms: int, default_chunk_minutes: int, max_chunks: int) -> int:
    """
    Compute the chunk size in milliseconds so that the total number of
    chunks never exceeds `max_chunks`.

    If the default chunk size would create more than `max_chunks`,
    the chunk size is increased so that total chunks == max_chunks.

    This is the shared dynamic-sizing logic used by both
    `split_audio_to_memory` and the interval-grouping step in
    `group_keep_intervals` so they stay consistent.
    """

    default_chunk_size_ms = default_chunk_minutes * 60 * 1000
    estimated_chunks = ceil(total_duration_ms / default_chunk_size_ms)

    if estimated_chunks > max_chunks:
        chunk_size_ms = ceil(total_duration_ms / max_chunks)
        logger.info(
            f"Audio would create {estimated_chunks} chunks. "
            f"Increasing chunk size to {chunk_size_ms / 1000:.2f}s "
            f"to stay within {max_chunks} chunks."
        )
    else:
        chunk_size_ms = default_chunk_size_ms

    return chunk_size_ms


# ═══════════════════════════════════════════════════════════════════════════
# Audio Chunking (with overlap support)
# ═══════════════════════════════════════════════════════════════════════════


def split_audio_to_memory(
    file_path: str,
    default_chunk_minutes: int = 5,
    max_chunks: int = 20,
    overlap_seconds: int = 20,
    chunk_boundaries: list[dict] | None = None,
) -> list[dict]:
    """
    Split a WAV audio file into MP3 chunks stored in memory with overlap.

    When `chunk_boundaries` is provided (a list of dicts with
    `"offset_seconds"` and `"end_time"` keys, as produced by
    `group_keep_intervals`), the function consumes those pre-computed
    boundaries instead of doing its own fixed chunking.  This is the
    `silence_aware` path: each boundary corresponds to a gap-respecting
    group of keep_intervals that was already extracted and concatenated
    into a separate audio file.

    The standard fixed-chunking path (when `chunk_boundaries` is None)
    is unchanged.

    Rules:
    - Default chunk size is defined by default_chunk_minutes (e.g. 5 minutes).
    - If that would create more than max_chunks,
      automatically increase chunk size so total chunks <= max_chunks.
    - Each chunk (except the first) overlaps with the previous chunk by
      overlap_seconds to provide context for better transcription.

    Args:
        file_path: Path to the WAV audio file.
        default_chunk_minutes: Default chunk duration in minutes.
        max_chunks: Maximum number of chunks. If exceeded, chunk size increases.
        overlap_seconds: Overlap duration in seconds between consecutive chunks.
        chunk_boundaries: Optional pre-computed chunk boundaries
            [{"offset_seconds": float, "end_time": float}, ...].

    Returns:
        List of chunk dicts:
            {
                "chunk_index": int,
                "offset_seconds": float (start time in original audio),
                "end_time": float (end time in original audio),
                "audio_bytes": bytes (MP3 data),
            }
    """

    audio = AudioSegment.from_wav(file_path)

    # Normalize to mono, 16kHz
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    total_duration_ms = len(audio)

    # ═══════════════════════════════════════════════════════════════
    # Pre-computed boundary path (silence_aware)
    # ═══════════════════════════════════════════════════════════════
    if chunk_boundaries is not None:
        chunks = []
        for idx, boundary in enumerate(chunk_boundaries):
            start_ms = int(boundary["offset_seconds"] * 1000)
            end_ms = int(boundary["end_time"] * 1000)
            # Clamp to audio duration
            end_ms = min(end_ms, total_duration_ms)
            if start_ms >= total_duration_ms:
                continue

            chunk = audio[start_ms:end_ms]

            buffer = BytesIO()
            chunk.export(buffer, format="wav")
            buffer.seek(0)

            chunks.append(
                {
                    "chunk_index": idx,
                    "offset_seconds": boundary["offset_seconds"],
                    "end_time": boundary["end_time"],
                    "audio_bytes": buffer.read(),
                }
            )

        logger.info(
            f"Split audio into {len(chunks)} pre-computed chunks "
            f"from {file_path}"
        )
        return chunks

    # ═══════════════════════════════════════════════════════════════
    # Standard fixed-chunking path (default / trimmed / raw)
    # ═══════════════════════════════════════════════════════════════
    chunk_size_ms = compute_chunk_size_ms(total_duration_ms, default_chunk_minutes, max_chunks)

    overlap_ms = overlap_seconds * 1000

    chunks = []
    chunk_index = 0
    idx = 0

    while idx < total_duration_ms:
        # Calculate chunk boundaries
        chunk_start = idx
        chunk_end = min(idx + chunk_size_ms, total_duration_ms)

        # Extract chunk audio
        chunk = audio[chunk_start:chunk_end]

        # Export to wav in memory
        buffer = BytesIO()
        chunk.export(buffer, format="wav")
        buffer.seek(0)

        chunks.append(
            {
                "chunk_index": chunk_index,
                "offset_seconds": chunk_start / 1000.0,
                "end_time": chunk_end / 1000.0,
                "audio_bytes": buffer.read(),
            }
        )

        logger.debug(f"Created chunk {chunk_index}: {chunk_start / 1000:.2f}s - {chunk_end / 1000:.2f}s")

        # Move to next chunk, accounting for overlap
        # Overlap = rewind by overlap_ms so next chunk starts within current chunk
        idx = chunk_end - overlap_ms if chunk_end > overlap_ms and chunk_end < total_duration_ms else chunk_end
        chunk_index += 1

    logger.info(
        f"Split audio into {len(chunks)} chunks "
        f"(chunk size: {chunk_size_ms / 1000:.2f}s, overlap: {overlap_seconds}s) "
        f"from {file_path}"
    )

    return chunks


# ═══════════════════════════════════════════════════════════════════════════
# Segment Adjustment (legacy, kept for compatibility)
# ═══════════════════════════════════════════════════════════════════════════


def adjust_segments(segments: list, offset_seconds: float) -> list[dict]:
    """
    [LEGACY] Adjust segment timestamps by adding the chunk's offset.

    This function is kept for backward compatibility.
    New code should use deduplicate_overlapping_text() instead.

    Args:
        segments: Raw segments from Whisper API.
        offset_seconds: Time offset of the chunk in the original audio.

    Returns:
        List of adjusted segment dicts.
    """

    adjusted = []

    for seg in segments:
        adjusted.append(
            {"start": seg["start"] + offset_seconds, "end": seg["end"] + offset_seconds, "text": seg["text"]}
        )

    return adjusted


# ═══════════════════════════════════════════════════════════════════════════
# Text Normalization
# ═══════════════════════════════════════════════════════════════════════════


def normalize_text(text: str) -> str:
    """
    Normalize text by fixing curly quotes, dashes, and multiple spaces.

    Args:
        text: Input text to normalize.

    Returns:
        Normalized text.
    """

    if not text:
        return ""

    # Normalize curly quotes and apostrophes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    # Normalize dashes
    text = text.replace("—", " - ").replace("–", " - ")

    # Replace multiple spaces / newlines with single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ═══════════════════════════════════════════════════════════════════════════
# Overlap Detection (for deduplication)
# ═══════════════════════════════════════════════════════════════════════════


def find_overlap_length(prev_words: list[str], curr_words: list[str]) -> int:
    """
    Find the longest overlap between the end of prev_words and the start of curr_words.

    Uses fuzzy matching (lowercase + punctuation stripped) so minor transcription
    differences at chunk boundaries (e.g. "okay," vs "okay") are still detected.

    Example:
        prev_words = ["and", "the", "cat", "sat,"]
        curr_words = ["sat,", "on", "the", "mat"]
        → Returns 1 (overlap of "sat," ≈ "sat,")

    Note:
        Overlaps shorter than 3 words are ignored (min_match) to
        reduce false positives.

    Args:
        prev_words: Words from the previous chunk.
        curr_words: Words from the current chunk.

    Returns:
        Number of overlapping words to strip from the start of curr_words.
    """

    min_match = 3  # raised from 2 → reduces false positives
    max_search = 60  # only scan the tail/head to keep it O(n) not O(n²)

    if len(prev_words) < min_match or len(curr_words) < min_match:
        return 0

    def normalize(word: str) -> str:
        return re.sub(r"[^a-z0-9]", "", word.lower())

    norm_prev = [normalize(w) for w in prev_words[-max_search:]]
    norm_curr = [normalize(w) for w in curr_words[:max_search]]

    best_n = 0

    for n in range(min_match, min(len(norm_prev), len(norm_curr)) + 1):
        if norm_prev[-n:] == norm_curr[:n]:
            best_n = n

    return best_n


# ═══════════════════════════════════════════════════════════════════════════
# Deduplication of Overlapping Text
# ═══════════════════════════════════════════════════════════════════════════


def deduplicate_overlapping_text(results: list) -> list[dict[str, Any]]:
    """
    Remove duplicate text introduced by chunk overlap using fuzzy boundary matching.

    When chunks overlap (e.g., 20 seconds), the overlapping portion gets transcribed
    in both chunks, creating duplicates. This function detects and removes the
    duplicate text at chunk boundaries using word-level matching.

    Args:
        results: List of ChunkResult objects from transcription.

    Returns:
        List of deduplicated chunk dicts with cleaned text and adjusted timestamps.
    """

    if not results:
        return []

    deduplicated: list[dict[str, Any]] = []
    prev_words: list[str] = []

    for i, result in enumerate(results):
        text = result.text.strip()

        if not text:
            # Empty chunk: still add it with original timestamps
            deduplicated.append(
                {
                    "chunk_number": result.chunk_number,
                    "start_time": result.start_time,
                    "end_time": result.end_time,
                    "text": "",
                }
            )
            continue

        curr_words = text.split()
        adjusted_start = result.start_time

        # If not the first chunk and there's overlap, try to remove it
        if i > 0 and prev_words:
            overlap_n = find_overlap_length(prev_words, curr_words)

            if overlap_n > 0:
                # Calculate what fraction of this chunk is duplicate
                ratio = overlap_n / len(curr_words) if len(curr_words) > 0 else 0.0
                duration = result.end_time - result.start_time

                # Adjust start time forward to skip the duplicate portion
                adjusted_start = result.start_time + (ratio * duration)

                # Remove overlapping words from the current chunk
                curr_words = curr_words[overlap_n:]

                logger.info(
                    f"Chunk {result.chunk_number}: removed {overlap_n} overlapping words, "
                    f"adjusted start from {result.start_time:.2f}s to {adjusted_start:.2f}s"
                )

        # Clean the text (re-join overlap-stripped words + strip only).
        # NOTE: do NOT normalize here. TranscriptionManager._merge_results
        # performs the single per-chunk normalize_text() pass immediately
        # BEFORE computing character offsets. Normalizing here as well would
        # be a redundant second pass, and normalizing the JOINED text later
        # would invalidate those offsets (normalize_text() changes string
        # length, e.g. bare "—" -> " - "). See _merge_results.
        cleaned_text = " ".join(curr_words).strip()

        deduplicated.append(
            {
                "chunk_number": result.chunk_number,
                "start_time": adjusted_start,
                "end_time": result.end_time,
                "text": cleaned_text,
            }
        )

        # Keep original words for next overlap check
        prev_words = result.text.strip().split()

    return deduplicated


# ═══════════════════════════════════════════════════════════════════════════
# Segment Splitting (natural boundaries)
# ═══════════════════════════════════════════════════════════════════════════


def split_into_segments(text: str, max_words: int = 20) -> list[str]:
    """
    Split text into natural segments using sentence boundaries and word count limits.

    This creates segments that are suitable for timestamping and display:
    - Prefers to split at sentence boundaries (. ! ?)
    - Falls back to comma/semicolon boundaries if sentences are too long
    - Further chunks at word limits if still too long

    Args:
        text: Input text to split.
        max_words: Maximum words per segment.

    Returns:
        List of text segments.
    """

    # Split by sentence-ending punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)
    segments = []

    for s in sentences:
        s = s.strip()

        if not s:
            continue

        words = s.split()

        # Sentence fits within max_words: use as-is
        if len(words) <= max_words:
            segments.append(s)
        else:
            # Sentence too long: split by comma/semicolon first
            parts = re.split(r"(?<=[,;])\s+", s)
            curr_segment: list[str] = []

            for part in parts:
                part_words = part.split()

                if not part_words:
                    continue

                # Can add this part to current segment
                if len(curr_segment) + len(part_words) <= max_words:
                    curr_segment.extend(part_words)
                else:
                    # Current segment is full: save it and start new one
                    if curr_segment:
                        segments.append(" ".join(curr_segment))
                        curr_segment = []

                    # If this part is still too long, chunk it by max_words
                    if len(part_words) > max_words:
                        for j in range(0, len(part_words), max_words):
                            segments.append(" ".join(part_words[j : j + max_words]))
                    else:
                        curr_segment.extend(part_words)

            # Add any remaining words
            if curr_segment:
                segments.append(" ".join(curr_segment))

    return segments
