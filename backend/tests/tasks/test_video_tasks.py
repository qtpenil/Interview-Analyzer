import uuid
from unittest.mock import MagicMock, patch

import pytest


class TestProcessVideoToAudio:
    def test_process_video_success(self):
        from app.tasks.video_tasks import process_video_to_audio
        from app.modules.interview.interview_media_service import AudioPrepResult

        with patch("app.tasks.video_tasks.ffmpeg_manager.get_duration", return_value=300.0):
            with patch("app.tasks.video_tasks.update_interview_status") as mock_status:
                with patch(
                    "app.tasks.video_tasks.interview_media_service.prepare_audio_for_transcription",
                    return_value=AudioPrepResult(audio_path="/tmp/audio.wav", mode="trimmed"),
                ):
                    with patch("app.tasks.video_tasks.os.path.exists", return_value=True):
                        with patch("app.tasks.video_tasks.os.remove"):
                            with patch(
                                "app.tasks.video_tasks.generate_audio_fingerprint", return_value="test_fingerprint"
                            ):
                                with patch("app.tasks.video_tasks.update_interview_fields"):
                                    with patch("app.tasks.transcription_tasks.transcribe_audio.delay"):
                                        with patch("app.tasks.video_tasks.SessionLocal") as mock_session:
                                            mock_db = MagicMock()
                                            mock_session.return_value = mock_db
                                            mock_db.query.return_value.filter.return_value.first.return_value = None

                                            result = process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")
                                            assert result is not None
                                            assert result["status"] in ("audio_ready", "cancelled")
                                            assert result.get("audio_prep_mode") == "trimmed"

    def test_process_video_too_short(self):
        from app.tasks.video_tasks import process_video_to_audio

        with patch("app.tasks.video_tasks.ffmpeg_manager.get_duration", return_value=30.0):
            with patch("app.tasks.video_tasks.update_interview_status"):
                with patch("app.tasks.video_tasks.update_interview_fields"):
                    with patch("app.tasks.video_tasks.os.path.exists", return_value=True):
                        with patch("app.tasks.video_tasks.os.remove"):
                            result = process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")
                            assert result["status"] == "too_short"

    def test_process_video_too_long(self):
        from app.tasks.video_tasks import process_video_to_audio

        with patch("app.tasks.video_tasks.ffmpeg_manager.get_duration", return_value=7300.0):
            with patch("app.tasks.video_tasks.update_interview_status"):
                with patch("app.tasks.video_tasks.update_interview_fields"):
                    with patch("app.tasks.video_tasks.os.path.exists", return_value=True):
                        with patch("app.tasks.video_tasks.os.remove"):
                            result = process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")
                            assert result["status"] == "too_long"

    def test_process_video_cancelled(self):
        from app.tasks.video_tasks import process_video_to_audio

        with patch("app.tasks.video_tasks.is_interview_cancelled", return_value=True):
            with patch("app.tasks.video_tasks.os.path.exists", return_value=True):
                with patch("app.tasks.video_tasks.os.remove"):
                    result = process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")
                    assert result["status"] == "cancelled"

    def test_process_video_ffmpeg_failure(self):
        from app.tasks.video_tasks import process_video_to_audio

        with patch("app.tasks.video_tasks.update_interview_status"):
            with patch(
                "app.tasks.video_tasks.interview_media_service.prepare_audio_for_transcription",
                side_effect=Exception("FFmpeg failed"),
            ):
                with patch("app.tasks.video_tasks.update_interview_status") as mock_fail:
                    with pytest.raises(Exception):
                        process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")

    def test_process_video_video_cleanup_on_error(self):
        from app.tasks.video_tasks import process_video_to_audio

        with patch("app.tasks.video_tasks.update_interview_status"):
            with patch("app.tasks.video_tasks.is_interview_cancelled", return_value=True):
                with patch("app.tasks.video_tasks.os.path.exists", return_value=True):
                    with patch("app.tasks.video_tasks.os.remove") as mock_remove:
                        process_video_to_audio(str(uuid.uuid4()), "/tmp/video.mp4")
                        mock_remove.assert_called_once_with("/tmp/video.mp4")


class TestCopyInterviewResults:
    def test_copy_results(self):
        from app.tasks.video_tasks import copy_interview_results

        mock_db = MagicMock()
        src = MagicMock()
        src.id = "src-id"
        src.topics = []
        src.overall_score = 8.5
        src.hiring_decision = "HIRE"

        dest = MagicMock()
        dest.id = "dest-id"

        mock_db.query.return_value.filter.return_value.first.side_effect = [src, dest]

        copy_interview_results(src.id, dest.id, mock_db)
        mock_db.commit.assert_called_once()


class TestBuildStateDictForDuplicate:
    def test_build_from_db_fields(self):
        from app.tasks.video_tasks import build_state_dict_for_duplicate

        src = MagicMock()
        src.id = "src-id"
        src.title = "Test"
        src.overall_score = 8.0
        src.technical_score = 7.5
        src.communication_score = 8.0
        src.confidence_score = 9.0
        src.knowledge_depth = 7.0
        src.experience_alignment_score = 6.5
        hiring_mock = MagicMock()
        hiring_mock.value = "HIRE"
        src.hiring_decision = hiring_mock
        src.transcript = None
        src.topics = []
        src.claimed_experience_years = 5.0

        result = build_state_dict_for_duplicate(src, "dest-id")
        assert result["interview_id"] == "dest-id"
        assert result["hiring_decision"] == "HIRE"
