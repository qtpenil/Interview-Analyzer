from unittest.mock import MagicMock, patch

import pytest


class TestFFmpegManager:
    def test_extract_audio_success(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            from app.integration.ffmpeg.manager import ffmpeg_manager

            with patch("os.path.join", return_value="/tmp/dir/uuid.wav"):
                result = ffmpeg_manager.extract_audio("/input/video.mp4", "/tmp/dir")
                assert result == "/tmp/dir/uuid.wav"

    def test_extract_audio_ffmpeg_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            from app.integration.ffmpeg.manager import ffmpeg_manager
            from app.shared.exceptions.custom_exceptions import FFmpegNotFoundException

            with pytest.raises(FFmpegNotFoundException):
                ffmpeg_manager.extract_audio("/input/video.mp4", "/tmp/dir")

    def test_extract_audio_execution_error(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error processing"
            mock_run.side_effect = __import__("subprocess").CalledProcessError(1, ["ffmpeg"])

            from app.integration.ffmpeg.manager import ffmpeg_manager
            from app.shared.exceptions.custom_exceptions import FFmpegExecutionException

            with pytest.raises(FFmpegExecutionException):
                ffmpeg_manager.extract_audio("/input/video.mp4", "/tmp/dir")

    def test_get_duration_success(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '{"format": {"duration": 120.5}}'
            mock_run.return_value = mock_result

            from app.integration.ffmpeg.manager import ffmpeg_manager

            duration = ffmpeg_manager.get_duration("/audio/test.wav")
            assert duration == 120.5

    def test_detect_silence_success(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = "silence_start: 10.0\nsilence_end: 15.0 | silence_duration: 5.0\n"
            mock_run.return_value = mock_result

            from app.integration.ffmpeg.manager import ffmpeg_manager

            silences = ffmpeg_manager.detect_silence("/audio/test.wav")
            assert len(silences) == 1
            assert silences[0]["start_sec"] == 10.0

    def test_extract_segments_success(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            from app.integration.ffmpeg.manager import ffmpeg_manager

            with patch("os.path.join", side_effect=lambda *a: "/".join(a)):
                segments = ffmpeg_manager.extract_segments(
                    "/audio/test.wav",
                    [(0.0, 10.0), (20.0, 30.0)],
                    "/tmp/dir",
                )
                assert len(segments) == 2

    def test_concat_segments_success(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            with patch("builtins.open", MagicMock()):
                from app.integration.ffmpeg.manager import ffmpeg_manager

                with patch("os.path.join", side_effect=lambda *a: "/".join(a)):
                    result = ffmpeg_manager.concat_segments(
                        ["/tmp/part_0.wav", "/tmp/part_1.wav"],
                        "/output/final.wav",
                        "/tmp/dir",
                    )
                    assert result == "/output/final.wav"
