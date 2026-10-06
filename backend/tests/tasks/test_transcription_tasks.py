from unittest.mock import MagicMock, patch

import pytest


class TestCleanupAudioFile:
    def test_cleanup_success(self):
        from app.tasks.transcription_tasks import cleanup_audio_file

        with patch("os.remove") as mock_remove:
            cleanup_audio_file("/tmp/audio.wav")
            mock_remove.assert_called_once_with("/tmp/audio.wav")

    def test_cleanup_file_not_found(self):
        from app.tasks.transcription_tasks import cleanup_audio_file

        with patch("os.remove", side_effect=FileNotFoundError):
            cleanup_audio_file("/tmp/nonexistent.wav")

    def test_cleanup_permission_error(self):
        from app.tasks.transcription_tasks import cleanup_audio_file

        with patch("os.remove", side_effect=PermissionError):
            cleanup_audio_file("/tmp/protected.wav")


class TestTranscribeAudio:
    def test_transcribe_success(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.transcription_tasks.update_interview_status"):
                with patch("app.tasks.transcription_tasks.transcription_manager.transcribe") as mock_transcribe:
                    mock_transcribe.return_value = {
                        "segments": [{"start": 0.0, "end": 5.0, "text": "Hello"}],
                        "full_text": "Hello, this is an interview conversation.",
                        "chunks_processed": 1,
                        "processing_time": 10.0,
                    }
                    with patch("app.tasks.transcription_tasks.update_interview_fields"):
                        with patch("app.tasks.transcription_tasks.cleanup_audio_file"):
                            with patch(
                                "app.tasks.transcription_tasks.classify_transcript_with_context",
                                return_value={"is_interview": True, "reason": "", "confidence": 1.0},
                            ):
                                 with patch("app.tasks.analysis_tasks.analyze_transcript.delay"):
                                    result = transcribe_audio("test-id", "/tmp/audio.wav", [], "trimmed")
                                    assert result["status"] == "transcription_complete"

    def test_transcribe_classifier_rejects(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.transcription_tasks.update_interview_status"):
                with patch("app.tasks.transcription_tasks.transcription_manager.transcribe") as mock_transcribe:
                    mock_transcribe.return_value = {
                        "segments": [{"start": 0.0, "end": 5.0, "text": "Music playing"}],
                        "full_text": "La la la musical notes",
                        "chunks_processed": 1,
                        "processing_time": 10.0,
                    }
                    with patch("app.tasks.transcription_tasks.update_interview_fields"):
                        with patch("app.tasks.transcription_tasks.cleanup_audio_file"):
                            with patch(
                                "app.tasks.transcription_tasks.classify_transcript_with_context",
                                return_value={
                                    "is_interview": False,
                                    "reason": "Not a conversation",
                                    "confidence": 0.95,
                                },
                            ):
                                result = transcribe_audio("test-id", "/tmp/audio.wav", [], "trimmed")
                                assert result["status"] == "not_an_interview"
                                assert "reason" in result

    def test_transcribe_cancelled(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=True):
            with patch("app.tasks.transcription_tasks.cleanup_audio_file") as mock_cleanup:
                result = transcribe_audio("test-id", "/tmp/audio.wav")
                assert result["status"] == "cancelled"
                mock_cleanup.assert_called_once_with("/tmp/audio.wav")

    def test_transcribe_empty_full_text_skips_classifier(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.transcription_tasks.update_interview_status"):
                with patch("app.tasks.transcription_tasks.transcription_manager.transcribe") as mock_transcribe:
                    mock_transcribe.return_value = {
                        "segments": [],
                        "full_text": "",
                        "chunks_processed": 0,
                        "processing_time": 5.0,
                    }
                    with patch("app.tasks.transcription_tasks.update_interview_fields"):
                        with patch("app.tasks.transcription_tasks.cleanup_audio_file"):
                            with patch("app.tasks.analysis_tasks.analyze_transcript.delay"):
                                result = transcribe_audio("test-id", "/tmp/audio.wav", [], "trimmed")
                                assert result["status"] == "transcription_complete"

    def test_transcribe_empty_segments(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.transcription_tasks.update_interview_status"):
                with patch("app.tasks.transcription_tasks.transcription_manager.transcribe") as mock_transcribe:
                    mock_transcribe.return_value = {
                        "segments": [],
                        "chunks_processed": 0,
                        "processing_time": 5.0,
                    }
                    with patch("app.tasks.transcription_tasks.update_interview_fields"):
                        with patch("app.tasks.transcription_tasks.cleanup_audio_file"):
                            with patch("app.tasks.analysis_tasks.analyze_transcript.delay"):
                                result = transcribe_audio("test-id", "/tmp/audio.wav", [], "trimmed")
                                assert result["status"] == "transcription_complete"

    def test_transcribe_failure_retries(self):
        from app.tasks.transcription_tasks import transcribe_audio

        with patch("app.tasks.transcription_tasks.is_interview_cancelled", return_value=False):
            with patch("app.tasks.transcription_tasks.update_interview_status"):
                with patch(
                    "app.tasks.transcription_tasks.transcription_manager.transcribe", side_effect=Exception("API Error")
                ):
                    with pytest.raises(Exception):
                        transcribe_audio("test-id", "/tmp/audio.wav", [], "trimmed")


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