from unittest.mock import MagicMock, patch

import pytest

from app.integration.ffmpeg.utils import (
    build_keep_intervals,
    generate_audio_fingerprint,
    parse_silence_output,
    seconds_to_timestamp,
)


class TestSecondsToTimestamp:
    def test_zero_seconds(self):
        assert seconds_to_timestamp(0) == "00:00:00.000"

    def test_basic_conversion(self):
        assert seconds_to_timestamp(3661.5) == "01:01:01.500"

    def test_exact_hour(self):
        assert seconds_to_timestamp(3600) == "01:00:00.000"

    def test_milliseconds(self):
        assert seconds_to_timestamp(1.001) == "00:00:01.001"
        assert seconds_to_timestamp(1.999) == "00:00:01.999"


class TestParseSilenceOutput:
    def test_empty_output(self):
        assert parse_silence_output("") == []

    def test_no_silence(self):
        output = "ffmpeg version ... no silence detected"
        assert parse_silence_output(output) == []

    def test_single_silence(self):
        output = (
            "[silencedetect @ 0x...] silence_start: 10.5\n"
            "[silencedetect @ 0x...] silence_end: 15.3 | silence_duration: 4.8\n"
        )
        result = parse_silence_output(output)
        assert len(result) == 1
        assert result[0]["start_sec"] == 10.5
        assert result[0]["end_sec"] == 15.3
        assert result[0]["duration"] == 4.8

    def test_multiple_silences(self):
        output = (
            "silence_start: 5.0\nsilence_end: 8.0 | silence_duration: 3.0\n"
            "silence_start: 20.0\nsilence_end: 25.0 | silence_duration: 5.0\n"
        )
        result = parse_silence_output(output)
        assert len(result) == 2
        assert result[0]["start_sec"] == 5.0
        assert result[1]["start_sec"] == 20.0

    def test_timestamp_format(self):
        output = "silence_start: 0.0\nsilence_end: 5.0 | silence_duration: 5.0\n"
        result = parse_silence_output(output)
        assert result[0]["start"] == "00:00:00.000"
        assert result[0]["end"] == "00:00:05.000"


class TestBuildKeepIntervals:
    def test_no_silences(self):
        intervals = build_keep_intervals([], 100.0)
        assert intervals == [(0.0, 100.0)]

    def test_single_silence_middle(self):
        silences = [{"start_sec": 20.0, "end_sec": 30.0}]
        intervals = build_keep_intervals(silences, 100.0)
        assert intervals == [(0.0, 20.0), (30.0, 100.0)]

    def test_silence_at_start(self):
        silences = [{"start_sec": 0.0, "end_sec": 10.0}]
        intervals = build_keep_intervals(silences, 100.0)
        assert intervals == [(10.0, 100.0)]

    def test_silence_at_end(self):
        silences = [{"start_sec": 90.0, "end_sec": 100.0}]
        intervals = build_keep_intervals(silences, 100.0)
        assert intervals == [(0.0, 90.0)]

    def test_overlapping_silences_ignored(self):
        silences = [
            {"start_sec": 20.0, "end_sec": 30.0},
            {"start_sec": 25.0, "end_sec": 35.0},
        ]
        intervals = build_keep_intervals(silences, 100.0)
        assert intervals == [(0.0, 20.0), (35.0, 100.0)]

    def test_full_silence(self):
        silences = [{"start_sec": 0.0, "end_sec": 100.0}]
        intervals = build_keep_intervals(silences, 100.0)
        assert intervals == []


class TestGenerateAudioFingerprint:
    def test_fingerprint_success(self):
        with patch("subprocess.run") as mock_run:
            duration_result = MagicMock()
            duration_result.returncode = 0
            duration_result.stdout = '{"format": {"duration": 600.0}}'

            trim_result = MagicMock()
            trim_result.returncode = 0
            trim_result.stdout = ""

            fpcalc_result = MagicMock()
            fpcalc_result.returncode = 0
            fpcalc_result.stdout = '{"fingerprint": "test_fingerprint_123"}'

            mock_run.side_effect = [duration_result, trim_result, fpcalc_result]

            with patch("tempfile.NamedTemporaryFile") as mock_tmp:
                mock_tmp.return_value.__enter__.return_value.name = "/tmp/fp.wav"
                mock_tmp.return_value.name = "/tmp/fp.wav"

                with patch("os.remove"):
                    result = generate_audio_fingerprint("/audio/test.wav")
                    assert result is not None

    def test_fingerprint_short_audio(self):
        with patch("subprocess.run") as mock_run:
            duration_result = MagicMock()
            duration_result.returncode = 0
            duration_result.stdout = '{"format": {"duration": 30.0}}'

            trim_result = MagicMock()
            trim_result.returncode = 0
            trim_result.stdout = ""

            fpcalc_result = MagicMock()
            fpcalc_result.returncode = 0
            fpcalc_result.stdout = '{"fingerprint": "short_fingerprint"}'

            mock_run.side_effect = [duration_result, trim_result, fpcalc_result]

            with patch("tempfile.NamedTemporaryFile") as mock_tmp:
                mock_tmp.return_value.name = "/tmp/fp.wav"

                with patch("os.remove"):
                    result = generate_audio_fingerprint("/audio/short.wav")
                    assert result is not None

    def test_fingerprint_missing_tool(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = generate_audio_fingerprint("/audio/test.wav")
            assert result is None

    def test_fingerprint_no_fingerprint_returned(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"format": {"duration": 100.0}}'
            mock_run.return_value = mock_result

            with patch("tempfile.NamedTemporaryFile") as mock_tmp:
                mock_tmp.return_value.name = "/tmp/fp.wav"
                mock_run.side_effect = [mock_result, mock_result]

                second_result = MagicMock()
                second_result.stdout = '{"fingerprint": null}'
                mock_run.side_effect = [mock_result, second_result]

                with patch("os.remove"):
                    result = generate_audio_fingerprint("/audio/test.wav")
                    assert result is None
