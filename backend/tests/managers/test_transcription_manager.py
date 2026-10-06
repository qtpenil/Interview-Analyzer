from unittest.mock import MagicMock, patch

import pytest


class TestTranscriptionManager:
    def test_transcribe_success(self):
        with patch("app.integration.transcription.manager.split_audio_to_memory") as mock_split:
            mock_split.return_value = [
                {"chunk_index": 0, "offset_seconds": 0.0, "end_time": 300.0, "audio_bytes": b"audio1"},
            ]

            with patch("app.integration.transcription.manager.TranscriptionManager._transcribe_chunk") as mock_chunk:
                mock_chunk.return_value = _make_chunk_result(0, 0.0, 300.0, "Hello world")

                with patch("app.integration.transcription.manager.TranscriptionManager._merge_results") as mock_merge:
                    mock_merge.return_value = {
                        "source_file": "test.wav",
                        "audio_duration_seconds": 300.0,
                        "chunk_count": 1,
                        "full_text": "Hello world",
                        "segments": [{"start": 0.0, "end": 300.0, "text": "Hello world"}],
                    }

                    from app.integration.transcription.manager import transcription_manager

                    result = transcription_manager.transcribe("/audio/test.wav")
                    assert result["full_text"] == "Hello world"
                    assert result["chunk_count"] == 1

    def test_transcribe_multiple_chunks(self):
        with patch("app.integration.transcription.manager.split_audio_to_memory") as mock_split:
            mock_split.return_value = [
                {"chunk_index": i, "offset_seconds": i * 300.0, "end_time": (i + 1) * 300.0, "audio_bytes": b"audio"}
                for i in range(3)
            ]

            with patch("app.integration.transcription.manager.TranscriptionManager._transcribe_chunk") as mock_chunk:
                mock_chunk.side_effect = [
                    _make_chunk_result(i, i * 300.0, (i + 1) * 300.0, f"chunk {i}") for i in range(3)
                ]

                with patch("app.integration.transcription.manager.TranscriptionManager._merge_results") as mock_merge:
                    mock_merge.return_value = {
                        "source_file": "test.wav",
                        "audio_duration_seconds": 900.0,
                        "chunk_count": 3,
                        "full_text": "chunk 0 chunk 1 chunk 2",
                        "segments": [],
                    }

                    from app.integration.transcription.manager import transcription_manager

                    result = transcription_manager.transcribe("/audio/test.wav")
                    assert result["chunk_count"] == 3

    def test_transcribe_no_chunks_does_not_crash(self):
        with patch("app.integration.transcription.manager.split_audio_to_memory") as mock_split:
            mock_split.return_value = []

            from app.integration.transcription.manager import transcription_manager

            result = transcription_manager.transcribe("/audio/empty.wav")
            assert result["chunk_count"] == 0
            assert result["full_text"] == ""
            assert result["segments"] == []

    def test_parse_api_keys(self):
        with patch("app.core.config.settings.GEMINI_API_KEYS", "key1,key2,key3"):
            from app.integration.transcription.manager import TranscriptionManager

            tm = TranscriptionManager()
            keys = tm._parse_api_keys()
            assert len(keys) == 3
            assert keys == ["key1", "key2", "key3"]

    def test_parse_api_keys_empty(self):
        with patch("app.core.config.settings.GEMINI_API_KEYS", ""):
            from app.integration.transcription.manager import TranscriptionManager

            tm = TranscriptionManager()
            with pytest.raises(RuntimeError):
                tm._parse_api_keys()

    def test_interpolate_time_basic(self):
        from app.integration.transcription.manager import TranscriptionManager

        tm = TranscriptionManager()
        mappings = [
            {"start_char": 0, "end_char": 50, "start_time": 0.0, "end_time": 10.0},
        ]
        time = tm._interpolate_time(25, mappings)
        assert 4.0 <= time <= 6.0

    def test_interpolate_time_edge_cases(self):
        from app.integration.transcription.manager import TranscriptionManager

        tm = TranscriptionManager()
        assert tm._interpolate_time(0, []) == 0.0

        mappings = [
            {"start_char": 10, "end_char": 20, "start_time": 5.0, "end_time": 10.0},
        ]
        assert tm._interpolate_time(0, mappings) == 5.0
        assert tm._interpolate_time(30, mappings) == 10.0


class TestTranscribeChunk:
    def test_transcribe_chunk_success(self):
        with patch("app.integration.transcription.manager.genai") as mock_genai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Transcribed text"
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from app.integration.transcription.manager import TranscriptionManager

            tm = TranscriptionManager()
            chunk = {"chunk_index": 0, "offset_seconds": 0.0, "end_time": 300.0, "audio_bytes": b"audio"}
            result = tm._transcribe_chunk(chunk, ["fake-key"])
            assert result.text == "Transcribed text"
            assert result.chunk_number == 0

    def test_transcribe_chunk_sends_wav_with_configured_model(self):
        with patch("app.integration.transcription.manager.genai") as mock_genai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Transcribed text"
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            with patch("app.integration.transcription.manager.types.Part.from_bytes") as mock_from_bytes:
                mock_from_bytes.return_value = MagicMock()

                from app.core.config import settings
                from app.integration.transcription.manager import TranscriptionManager

                tm = TranscriptionManager()
                chunk = {"chunk_index": 0, "offset_seconds": 0.0, "end_time": 300.0, "audio_bytes": b"audio"}
                tm._transcribe_chunk(chunk, ["fake-key"])

                call_kwargs = mock_client.models.generate_content.call_args.kwargs
                assert call_kwargs["model"] == settings.GOOGLE_AI_MODEL

                _, from_bytes_kwargs = mock_from_bytes.call_args
                assert from_bytes_kwargs["mime_type"] == "audio/wav"

    def test_transcribe_chunk_failure_key_rotation(self):
        with patch("app.integration.transcription.manager.genai") as mock_genai:
            mock_client = MagicMock()
            mock_client.models.generate_content.side_effect = Exception("API Error")
            mock_genai.Client.return_value = mock_client

            from app.integration.transcription.manager import (
                TranscriptionChunkError,
                TranscriptionManager,
            )

            tm = TranscriptionManager()
            chunk = {"chunk_index": 0, "offset_seconds": 0.0, "end_time": 300.0, "audio_bytes": b"audio"}
            with pytest.raises(TranscriptionChunkError):
                tm._transcribe_chunk(chunk, ["key1", "key2"])


def _make_chunk_result(chunk_number, start_time, end_time, text):
    from app.integration.transcription.manager import ChunkResult

    return ChunkResult(
        chunk_number=chunk_number,
        start_time=start_time,
        end_time=end_time,
        text=text,
        verbose_json={},
    )


def _make_offset_drift_fixture():
    """Two raw chunks where chunk 0 contains BARE em-dashes (no surrounding
    spaces), so normalize_text() changes its length: each "—" (1 char)
    becomes " - " (3 chars), i.e. +2 chars per dash with nothing for the
    whitespace-collapser to absorb.

    Chunk texts are chosen so that (a) no 3-word fuzzy overlap is detected
    between them (dedup leaves both intact, timestamps unadjusted), and
    (b) the joined text splits into 3 sentence segments, the last two of
    which lie fully inside chunk 1's span.
    """
    raw0 = "first part\u2014with em dash\u2014right here and then some more words to finish."
    raw1 = "second chunk content here with several words. third sentence follows here."
    results = [
        _make_chunk_result(0, 0.0, 300.0, raw0),
        _make_chunk_result(1, 300.0, 600.0, raw1),
    ]
    expected_full = (
        "first part - with em dash - right here and then some more words to finish. "
        "second chunk content here with several words. third sentence follows here."
    )
    return results, raw0, raw1, expected_full


class TestMergeResultsCharOffsets:
    """Regression tests for the transcription char-offset drift bug.

    normalize_text() is length-changing (bare "—" is 1 char, " - " is 3),
    so offsets in `mappings` must be computed from the already-normalized
    per-chunk text. Computing offsets on raw text and normalizing the joined
    string afterwards shifts every later offset, which misplaces downstream
    _interpolate_time timestamps (and can yield end < start segments that
    security_hardening.preprocess_transcript then silently drops).
    """

    def test_later_chunk_offsets_unaffected_by_earlier_normalization(self):
        from app.integration.transcription.manager import TranscriptionManager

        results, _raw0, _raw1, expected_full = _make_offset_drift_fixture()
        tm = TranscriptionManager()
        merged = tm._merge_results(source_file="t.wav", duration=600.0, results=results)

        # The joined text must be exactly the normalized parts joined once —
        # no second full-string pass may have altered anything after offsets.
        assert merged["full_text"] == expected_full

        # Dedup must have left both chunks intact (no overlap stripping).
        assert "first part - with em dash - right here" in merged["full_text"]
        assert "second chunk content here" in merged["full_text"]

        segments = merged["segments"]
        assert len(segments) == 3

        # The segment starting chunk 1's content must start exactly at chunk
        # 1's start_time: its first char IS chunk 1's recorded start_char.
        # With stale (pre-normalization) offsets this drifts forward by the
        # +4 chars chunk 0 gained (~16s here) — the core of the bug.
        second = [s for s in segments if "second chunk content" in s["text"]]
        assert len(second) == 1
        assert second[0]["start"] == pytest.approx(300.0, abs=2.0)
        assert 300.0 <= second[0]["end"] <= 600.0

    def test_no_negative_duration_after_length_changing_substitution(self):
        """Original bug shape: a length-changing substitution in an early
        chunk, then _interpolate_time for a segment starting after it, must
        never produce end < start."""
        from app.integration.transcription.manager import TranscriptionManager

        results, _raw0, _raw1, _expected = _make_offset_drift_fixture()
        tm = TranscriptionManager()
        merged = tm._merge_results(source_file="t.wav", duration=600.0, results=results)

        assert merged["segments"], "expected segments"
        for seg in merged["segments"]:
            assert seg["end"] >= seg["start"], f"negative-duration segment: {seg}"

    def test_normalize_called_per_chunk_never_on_joined_string(self):
        """Pin the required operation order: exactly one normalize_text()
        call per non-empty chunk (before joining), and never a single pass
        over the already-joined full string."""
        from app.integration.transcription import manager as manager_module
        from app.integration.transcription.manager import TranscriptionManager
        from app.integration.transcription.utils import normalize_text as real_normalize

        results, raw0, raw1, _expected = _make_offset_drift_fixture()

        seen: list[str] = []

        def spy(text):
            seen.append(text)
            return real_normalize(text)

        with patch.object(manager_module, "normalize_text", side_effect=spy):
            tm = TranscriptionManager()
            tm._merge_results(source_file="t.wav", duration=600.0, results=results)

        # Exactly one call per chunk, each receiving that chunk's own raw
        # text — never the joined full string (old code called it once with
        # raw0 + " " + raw1, which fails this assertion).
        assert sorted(seen) == sorted([raw0, raw1])
