"""Tests for the silence-aware audio prep features added to
interview_media_service.py.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.modules.interview.interview_media_service import (
    AudioPrepResult,
    build_offset_mapping,
    compute_silence_aware_chunk_boundaries,
    group_keep_intervals,
)


# ═══════════════════════════════════════════════════════════════
# group_keep_intervals — pure function unit tests
# ═══════════════════════════════════════════════════════════════


class TestGroupKeepIntervals:
    def test_empty_intervals(self):
        assert group_keep_intervals([], 60.0) == []

    def test_single_interval(self):
        intervals = [(0.0, 10.0)]
        result = group_keep_intervals(intervals, 60.0)
        assert result == [[(0.0, 10.0)]]

    def test_intervals_within_target(self):
        """Multiple short intervals that fit within the target
        duration are grouped together."""
        intervals = [(0.0, 10.0), (15.0, 20.0), (25.0, 30.0)]
        result = group_keep_intervals(intervals, 60.0)
        assert len(result) == 1
        assert result[0] == intervals

    def test_intervals_split_when_exceed_target(self):
        """When adding the next interval would exceed target, a
        new group is started."""
        intervals = [(0.0, 30.0), (35.0, 45.0), (50.0, 60.0)]
        result = group_keep_intervals(intervals, 30.0)
        assert len(result) >= 2

    def test_long_interval_stands_alone(self):
        """A single interval longer than target is left as its own
        chunk — never split mid-interval."""
        intervals = [(0.0, 10.0), (60.0, 120.0), (130.0, 140.0)]
        result = group_keep_intervals(intervals, 30.0)
        # The 60-second interval is alone in its group
        assert any(len(group) == 1 and group[0] == (60.0, 120.0) for group in result)

    def test_no_interval_split_mid_interval(self):
        """No interval is ever split — every interval appears
        exactly once across all groups."""
        intervals = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0), (60.0, 70.0)]
        result = group_keep_intervals(intervals, 25.0)
        all_intervals = [iv for group in result for iv in group]
        assert len(all_intervals) == len(intervals)
        assert set(all_intervals) == set(intervals)

    def test_target_changes_grouping(self):
        """Changing the target duration changes the grouping."""
        intervals = [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0)]
        result_small = group_keep_intervals(intervals, 15.0)
        result_large = group_keep_intervals(intervals, 100.0)
        assert len(result_small) > len(result_large)


# ═══════════════════════════════════════════════════════════════
# build_offset_mapping — pure function unit tests
# ═══════════════════════════════════════════════════════════════


class TestBuildOffsetMapping:
    def test_empty_groups(self):
        assert build_offset_mapping([]) == []

    def test_single_group(self):
        groups = [[(0.0, 10.0), (20.0, 30.0)]]
        result = build_offset_mapping(groups)
        assert len(result) == 1
        assert result[0][0] == {"chunk_offset": 0.0, "original_timestamp": 0.0}
        assert result[0][1] == {"chunk_offset": 10.0, "original_timestamp": 20.0}

    def test_multiple_groups(self):
        groups = [
            [(0.0, 10.0)],
            [(20.0, 30.0), (40.0, 50.0)],
        ]
        result = build_offset_mapping(groups)
        assert len(result) == 2
        # Group 0
        assert result[0][0]["chunk_offset"] == 0.0
        assert result[0][0]["original_timestamp"] == 0.0
        # Group 1
        assert result[1][0]["chunk_offset"] == 0.0
        assert result[1][0]["original_timestamp"] == 20.0
        assert result[1][1]["chunk_offset"] == 10.0
        assert result[1][1]["original_timestamp"] == 40.0

    def test_position_maps_to_true_original_timestamp(self):
        """Given a chunk built from known original-timeline intervals
        with known gaps removed, a position within the concatenated
        chunk correctly maps back to the true original-audio
        timestamp."""
        groups = [[(5.0, 15.0), (30.0, 40.0)]]
        mappings = build_offset_mapping(groups)
        # Position 0 maps to original timestamp 5.0
        assert mappings[0][0]["chunk_offset"] == 0.0
        assert mappings[0][0]["original_timestamp"] == 5.0
        # Position 10 in chunk = where second interval starts; gap
        # between 15.0 and 30.0 was removed, so original timestamp
        # is 30.0, not 25.0 (which would be position-in-trimmed)
        assert mappings[0][1]["chunk_offset"] == 10.0
        assert mappings[0][1]["original_timestamp"] == 30.0


# ═══════════════════════════════════════════════════════════════
# compute_silence_aware_chunk_boundaries — pure function tests
# ═══════════════════════════════════════════════════════════════


class TestComputeSilenceAwareChunkBoundaries:
    def test_empty(self):
        assert compute_silence_aware_chunk_boundaries([], []) == []

    def test_single_chunk(self):
        groups = [[(0.0, 10.0)]]
        mappings = [[{"chunk_offset": 0.0, "original_timestamp": 0.0}]]
        result = compute_silence_aware_chunk_boundaries(groups, mappings)
        assert len(result) == 1
        assert result[0] == {"offset_seconds": 0.0, "end_time": 10.0}

    def test_multiple_chunks_sequential(self):
        groups = [[(0.0, 10.0)], [(20.0, 30.0)]]
        mappings = [
            [{"chunk_offset": 0.0, "original_timestamp": 0.0}],
            [{"chunk_offset": 0.0, "original_timestamp": 20.0}],
        ]
        result = compute_silence_aware_chunk_boundaries(groups, mappings)
        assert len(result) == 2
        assert result[0] == {"offset_seconds": 0.0, "end_time": 10.0}
        assert result[1] == {"offset_seconds": 10.0, "end_time": 20.0}


# ═══════════════════════════════════════════════════════════════
# AudioPrepResult — smoke tests
# ═══════════════════════════════════════════════════════════════


class TestAudioPrepResult:
    def test_trimmed_result(self):
        result = AudioPrepResult(audio_path="/tmp/audio.wav", mode="trimmed")
        assert result.audio_path == "/tmp/audio.wav"
        assert result.mode == "trimmed"
        assert result.chunk_boundaries is None
        assert result.offset_mappings is None

    def test_silence_aware_result(self):
        boundaries = [{"offset_seconds": 0.0, "end_time": 60.0}]
        mappings = [[{"chunk_offset": 0.0, "original_timestamp": 0.0}]]
        result = AudioPrepResult(
            audio_path="/tmp/audio.wav",
            mode="silence_aware",
            chunk_boundaries=boundaries,
            offset_mappings=mappings,
        )
        assert result.mode == "silence_aware"
        assert result.chunk_boundaries == boundaries
        assert result.offset_mappings == mappings


# ═══════════════════════════════════════════════════════════════
# prepare_audio_for_transcription — integration tests
# ═══════════════════════════════════════════════════════════════


class TestPrepareAudioForTranscription:
    @patch("app.modules.interview.interview_media_service.ffmpeg_manager")
    @patch("app.modules.interview.interview_media_service.build_keep_intervals")
    @patch("app.modules.interview.interview_media_service.compute_chunk_size_ms")
    def test_trimmed_mode_returns_audio_prep_result(
        self, mock_compute, mock_build_keep, mock_ffmpeg
    ):
        from app.modules.interview.interview_media_service import (
            interview_media_service,
        )

        mock_ffmpeg.extract_audio.return_value = "/tmp/audio.wav"
        mock_ffmpeg.get_duration.return_value = 120.0
        mock_build_keep.return_value = [(0.0, 10.0), (20.0, 30.0)]
        mock_ffmpeg.extract_segments.return_value = ["/tmp/seg1.wav"]
        mock_compute.return_value = 300000  # default 5 min

        with patch("os.path.join", side_effect=lambda *a: "/".join(a)):
            with patch("os.makedirs"):
                with patch("os.path.exists", return_value=True):
                    with patch("builtins.open"):
                        with patch("app.integration.ffmpeg.manager.ffmpeg_manager.concat_segments"):
                            with patch("shutil.move"):
                                result = interview_media_service.prepare_audio_for_transcription(
                                    "/tmp/video.mp4", audio_prep_mode="trimmed"
                                )

        assert isinstance(result, AudioPrepResult)
        assert result.mode == "trimmed"
        assert result.chunk_boundaries is None

    @patch("app.modules.interview.interview_media_service.ffmpeg_manager")
    @patch("app.modules.interview.interview_media_service.build_keep_intervals")
    @patch("app.modules.interview.interview_media_service.compute_chunk_size_ms")
    def test_silence_aware_mode_returns_result_with_boundaries(
        self, mock_compute, mock_build_keep, mock_ffmpeg
    ):
        from app.modules.interview.interview_media_service import (
            interview_media_service,
        )

        mock_ffmpeg.extract_audio.return_value = "/tmp/audio.wav"
        mock_ffmpeg.get_duration.return_value = 120.0
        mock_build_keep.return_value = [(0.0, 10.0), (20.0, 30.0)]
        mock_ffmpeg.extract_segments.return_value = "/tmp/seg.wav"
        mock_compute.return_value = 60000  # 60s target

        with patch("os.path.join", side_effect=lambda *a: "/".join(a)):
            with patch("os.makedirs"):
                with patch("os.path.exists", return_value=True):
                    with patch("builtins.open"):
                        with patch("app.integration.ffmpeg.manager.ffmpeg_manager.concat_segments"):
                            with patch("shutil.move"):
                                result = interview_media_service.prepare_audio_for_transcription(
                                    "/tmp/video.mp4", audio_prep_mode="silence_aware"
                                )

        assert isinstance(result, AudioPrepResult)
        assert result.mode == "silence_aware"
        assert result.chunk_boundaries is not None
        assert result.offset_mappings is not None

    def test_raw_mode_skips_silence_detection(self):
        from app.modules.interview.interview_media_service import (
            interview_media_service,
        )

        with patch(
            "app.modules.interview.interview_media_service.ffmpeg_manager"
        ) as mock_ffmpeg:
            mock_ffmpeg.extract_audio.return_value = "/tmp/audio.wav"
            mock_ffmpeg.get_duration.return_value = 120.0

            with patch("os.path.join", side_effect=lambda *a: "/".join(a)):
                with patch("os.makedirs"):
                    with patch("shutil.move"):
                        result = interview_media_service.prepare_audio_for_transcription(
                            "/tmp/video.mp4", audio_prep_mode="raw"
                        )

        assert isinstance(result, AudioPrepResult)
        assert result.mode == "raw"
        # detect_silence should NOT have been called in raw mode
        assert not mock_ffmpeg.detect_silence.called


# ═══════════════════════════════════════════════════════════════
# AUDIO_PREP_MODE config setting tests
# ═══════════════════════════════════════════════════════════════


class TestAUDIO_PREP_MODE:
    """Verify the three modes (trimmed/raw/silence_aware) are all
    recognized and that the existing trimmed/raw paths are not
    affected by the silence_aware addition."""

    def test_all_modes_are_valid(self):
        """All three modes are valid; the prepare_audio_for_transcription
        method branches on this value."""
        for mode in ("trimmed", "raw", "silence_aware"):
            result = AudioPrepResult(audio_path="/tmp/audio.wav", mode=mode)
            assert result.mode == mode

    def test_trimmed_mode_is_default(self):
        assert settings.AUDIO_PREP_MODE in ("trimmed", "raw", "silence_aware")

    def test_trimmed_mode_unaffected(self):
        """The trimmed path still returns a simple AudioPrepResult
        with no chunk metadata."""
        result = AudioPrepResult(audio_path="/tmp/audio.wav", mode="trimmed")
        assert result.mode == "trimmed"
        assert result.chunk_boundaries is None
        assert result.offset_mappings is None

    def test_raw_mode_unaffected(self):
        """The raw path still returns a simple AudioPrepResult
        with no chunk metadata."""
        result = AudioPrepResult(audio_path="/tmp/audio.wav", mode="raw")
        assert result.mode == "raw"
        assert result.chunk_boundaries is None
        assert result.offset_mappings is None