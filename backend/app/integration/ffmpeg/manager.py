import json
import os
import subprocess
import uuid

from app.core.config import settings
from app.integration.ffmpeg.commands import (
    build_concat_command,
    build_detect_silence_command,
    build_duration_command,
    build_extract_audio_command,
    build_extract_segment_command,
)
from app.integration.ffmpeg.utils import (
    parse_silence_output,
)
from app.shared.exceptions.custom_exceptions import (
    FFmpegExecutionException,
    FFmpegNotFoundException,
)
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


class FFmpegManager:
    def _execute_command(
        self,
        command: list[str],
        error_message: str,
    ) -> subprocess.CompletedProcess:
        """
        Execute FFmpeg/FFprobe commands safely.
        """

        try:
            return subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )

        except FileNotFoundError:
            logger.exception("FFmpeg/FFprobe executable not found.")
            raise FFmpegNotFoundException()

        except subprocess.CalledProcessError as exc:
            logger.exception(f"{error_message} FFmpeg output: {exc.stderr}")

            raise FFmpegExecutionException(message=error_message)

    def extract_audio(self, video_path: str, temp_dir: str) -> str:
        """
        Extract audio from a video file.

        Args:
            video_path: Input video path.
            temp_dir: Temporary directory.

        Returns:
            Extracted WAV audio path.
        """

        audio_path = os.path.join(temp_dir, f"{uuid.uuid4()}.wav")

        command = build_extract_audio_command(video_path=video_path, audio_path=audio_path)

        self._execute_command(
            command=command,
            error_message="Failed to extract audio from video.",
        )

        logger.info(f"Audio extracted successfully: {audio_path}")

        return audio_path

    def get_duration(
        self,
        audio_path: str,
    ) -> float:
        """
        Get the duration of the video in seconds.

        Args:
            video_path: Video file path.

        Returns:
            Video duration in seconds.
        """

        command = build_duration_command(audio_path)

        result = self._execute_command(
            command=command,
            error_message="Failed to get video duration.",
        )

        data = json.loads(result.stdout)

        duration = float(data["format"]["duration"])

        logger.info(f"Video duration: {duration} seconds")

        return duration

    def detect_silence(
        self,
        audio_path: str,
    ) -> list[dict]:

        noise = settings.SILENCE_NOISE_THRESHOLD
        duration = settings.SILENCE_MIN_DURATION
        """
        Detect long silence intervals in audio.

        Args:
            audio_path: Audio file path.
            noise: Silence threshold.
            duration: Minimum silence duration in seconds.

        Returns:
            List of detected silence intervals.
        """

        command = build_detect_silence_command(
            audio_path=audio_path,
            noise_threshold=noise,
            silence_duration=duration,
        )

        result = self._execute_command(
            command=command,
            error_message="Failed to detect silence.",
        )

        silences = parse_silence_output(result.stderr)

        logger.info(f"Detected {len(silences)} silence interval(s).")

        return silences

    def extract_segments(
        self,
        audio_path: str,
        keep_intervals: list[tuple[float, float]],
        temp_dir: str,
    ) -> list[str]:
        """
        Extract video segments that should be kept.
        """

        segment_paths = []

        for index, (start, end) in enumerate(keep_intervals):
            segment_path = os.path.join(
                temp_dir,
                f"part_{index}.wav",
            )

            command = build_extract_segment_command(
                # pyrefly: ignore [unexpected-keyword]
                audio_path=audio_path,
                output_path=segment_path,
                start=start,
                end=end,
            )

            self._execute_command(
                command=command,
                error_message=(f"Failed to extract segment {index}."),
            )

            segment_paths.append(segment_path)

        logger.info(f"Extracted {len(segment_paths)} segment(s).")

        return segment_paths

    def concat_segments(
        self,
        segment_paths: list[str],
        output_path: str,
        temp_dir: str,
    ) -> str:
        """
        Concatenate extracted segments into a final video.
        """

        concat_file_path = os.path.join(
            temp_dir,
            "concat.txt",
        )

        with open(
            concat_file_path,
            "w",
            encoding="utf-8",
        ) as file:
            for segment_path in segment_paths:
                normalized_path = segment_path.replace(
                    "\\",
                    "/",
                )

                file.write(f"file '{normalized_path}'\n")

        command = build_concat_command(
            concat_file_path=concat_file_path,
            output_path=output_path,
        )

        self._execute_command(
            command=command,
            error_message=("Failed to concatenate segments."),
        )

        logger.info(f"Concatenated video created: {output_path}")

        return output_path


ffmpeg_manager = FFmpegManager()
