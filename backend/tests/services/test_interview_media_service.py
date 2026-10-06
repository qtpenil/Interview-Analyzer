from unittest.mock import MagicMock, patch

import pytest


class TestPrepareAudioForTranscription:
    def test_prepare_audio_success(self, sample_video_path: str):
        from app.modules.interview.interview_media_service import interview_media_service

        with patch.object(
            interview_media_service, "prepare_audio_for_transcription", return_value="/tmp/test_audio.wav"
        ) as mock_method:
            result = interview_media_service.prepare_audio_for_transcription(sample_video_path)
            assert result == "/tmp/test_audio.wav"
            mock_method.assert_called_once_with(sample_video_path)

    def test_prepare_audio_returns_wav_path(self, sample_video_path: str):
        from app.modules.interview.interview_media_service import interview_media_service

        with patch.object(
            interview_media_service, "prepare_audio_for_transcription", return_value="/tmp/audio_123.wav"
        ):
            result = interview_media_service.prepare_audio_for_transcription(sample_video_path)
            assert result.endswith(".wav")

    def test_prepare_audio_invalid_video_path(self):
        from app.modules.interview.interview_media_service import interview_media_service

        with patch.object(interview_media_service, "prepare_audio_for_transcription", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                interview_media_service.prepare_audio_for_transcription("/nonexistent/video.mp4")

    def test_prepare_audio_empty_video(self):
        from app.modules.interview.interview_media_service import interview_media_service

        with patch.object(
            interview_media_service, "prepare_audio_for_transcription", side_effect=ValueError("Empty video")
        ):
            with pytest.raises(ValueError):
                interview_media_service.prepare_audio_for_transcription("/tmp/empty.mp4")
