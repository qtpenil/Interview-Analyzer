import pytest

from app.integration.transcription.utils import (
    compute_chunk_size_ms,
    deduplicate_overlapping_text,
    find_overlap_length,
    normalize_text,
    split_into_segments,
    split_audio_to_memory,
)


class TestNormalizeText:
    def test_normalize_curly_quotes(self):
        result = normalize_text("\u201cHello\u201d")
        assert result == '"Hello"'

    def test_normalize_dashes(self):
        result = normalize_text("test\u2014value")
        assert " - " in result

    def test_collapse_spaces(self):
        result = normalize_text("too   many    spaces")
        assert result == "too many spaces"

    def test_strip_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_empty_string(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestFindOverlapLength:
    def test_exact_overlap(self):
        prev = ["something", "about", "this", "is", "a", "test"]
        curr = ["this", "is", "a", "test", "of", "the"]
        assert find_overlap_length(prev, curr) >= 3

    def test_no_overlap(self):
        prev = ["hello", "world"]
        curr = ["completely", "different"]
        assert find_overlap_length(prev, curr) == 0

    def test_empty_lists(self):
        assert find_overlap_length([], ["a", "b"]) == 0
        assert find_overlap_length(["a", "b"], []) == 0

    def test_short_lists_below_minimum(self):
        assert find_overlap_length(["a"], ["a"]) == 0

    def test_fuzzy_overlap(self):
        prev = ["okay", "let's", "move", "on.", "to", "the"]
        curr = ["move", "on.", "to", "the", "next", "part"]
        assert find_overlap_length(prev, curr) >= 3


class TestDeduplicateOverlappingText:
    class MockChunk:
        def __init__(self, chunk_number, start_time, end_time, text):
            self.chunk_number = chunk_number
            self.start_time = start_time
            self.end_time = end_time
            self.text = text

    def test_no_overlap_between_chunks(self):
        chunks = [
            self.MockChunk(0, 0.0, 10.0, "Hello world"),
            self.MockChunk(1, 10.0, 20.0, "Next segment"),
        ]
        result = deduplicate_overlapping_text(chunks)
        assert len(result) == 2

    def test_overlap_removed(self):
        chunks = [
            self.MockChunk(0, 0.0, 15.0, "Hello world this is a test"),
            self.MockChunk(1, 10.0, 25.0, "this is a test second chunk"),
        ]
        result = deduplicate_overlapping_text(chunks)
        assert len(result) == 2
        assert "this is a test" not in result[1]["text"]

    def test_empty_chunks_handled(self):
        chunks = [
            self.MockChunk(0, 0.0, 10.0, "Hello"),
            self.MockChunk(1, 10.0, 20.0, ""),
            self.MockChunk(2, 20.0, 30.0, "World"),
        ]
        result = deduplicate_overlapping_text(chunks)
        assert len(result) == 3
        assert result[1]["text"] == ""

    def test_empty_results_list(self):
        assert deduplicate_overlapping_text([]) == []


class TestSplitIntoSegments:
    def test_short_text_single_segment(self):
        segments = split_into_segments("Hello world.", max_words=20)
        assert len(segments) == 1

    def test_split_by_sentence(self):
        text = "First sentence. Second sentence. Third sentence."
        segments = split_into_segments(text, max_words=20)
        assert len(segments) >= 2

    def test_respect_max_words(self):
        text = "word " * 50
        segments = split_into_segments(text.strip(), max_words=10)
        assert all(len(s.split()) <= 10 for s in segments)
        assert len(segments) >= 5

    def test_empty_text(self):
        assert split_into_segments("") == []
        assert split_into_segments("   ") == []


# ═══════════════════════════════════════════════════════════════
# compute_chunk_size_ms (extracted dynamic-sizing logic)
# ═══════════════════════════════════════════════════════════════


class TestComputeChunkSizeMs:
    def test_default_chunk_size_used_when_under_max(self):
        # 100000ms / 5min(300000ms) = 1 chunk <= 20 max
        result = compute_chunk_size_ms(100000, 5, 20)
        assert result == 300000

    def test_increases_when_over_max(self):
        # 1000000ms / 5min(300000ms) = 4 chunks > 20 max? No, 4 <= 20
        # Need a bigger duration
        result = compute_chunk_size_ms(10000000, 5, 20)
        # 10000000 / 300000 = 34 chunks > 20, so chunk_size = 10000000/20 = 500000
        assert result == 500000

    def test_target_changes_with_total_duration(self):
        # Shorter audio uses default; longer audio increases
        short = compute_chunk_size_ms(100000, 5, 20)
        long_ = compute_chunk_size_ms(20000000, 5, 20)
        assert short != long_
        assert short == 300000  # default
        assert long_ > 300000  # increased


# ═══════════════════════════════════════════════════════════════
# split_audio_to_memory with chunk_boundaries (silence_aware)
# ═══════════════════════════════════════════════════════════════


class TestSplitAudioToMemoryWithBoundaries:
    def test_uses_pre_computed_boundaries(self):
        """When chunk_boundaries is provided, split_audio_to_memory
        consumes them instead of doing its own fixed chunking."""
        from unittest.mock import MagicMock, patch
        from app.integration.transcription.utils import split_audio_to_memory

        audio_path = "/fake/audio.wav"
        boundaries = [
            {"offset_seconds": 0.0, "end_time": 60.0},
            {"offset_seconds": 60.0, "end_time": 120.0},
        ]

        # Create a minimal fake AudioSegment-like object
        fake_chunk = MagicMock()
        fake_buffer = MagicMock()
        fake_buffer.read = MagicMock(return_value=b"audio_bytes")
        fake_buffer.seek = MagicMock()
        fake_chunk.export = MagicMock(return_value=None)

        fake_audio = MagicMock()
        fake_audio.__len__ = MagicMock(return_value=240000)
        fake_audio.set_channels = MagicMock(return_value=fake_audio)
        fake_audio.set_frame_rate = MagicMock(return_value=fake_audio)
        fake_audio.__getitem__ = MagicMock(return_value=fake_chunk)

        with patch("app.integration.transcription.utils.AudioSegment.from_wav", return_value=fake_audio):
            with patch("app.integration.transcription.utils.logger"):
                with patch("app.integration.transcription.utils.BytesIO") as mock_bio:
                    mock_bio.return_value = fake_buffer

                    result = split_audio_to_memory(audio_path, chunk_boundaries=boundaries)

        assert len(result) == 2
        assert result[0]["chunk_index"] == 0
        assert result[0]["offset_seconds"] == 0.0
        assert result[0]["end_time"] == 60.0
        assert result[1]["chunk_index"] == 1
        assert result[1]["offset_seconds"] == 60.0
        assert result[1]["end_time"] == 120.0

    def test_empty_boundaries_yields_empty_chunks(self):
        from unittest.mock import MagicMock, patch

        audio_path = "/fake/audio.wav"
        mock_audio = MagicMock()
        mock_audio.set_channels.return_value = MagicMock()
        mock_audio.set_frame_rate.return_value = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=120000)

        with patch("app.integration.transcription.utils.AudioSegment.from_wav", return_value=mock_audio):
            result = split_audio_to_memory(audio_path, chunk_boundaries=[])
            assert result == []
