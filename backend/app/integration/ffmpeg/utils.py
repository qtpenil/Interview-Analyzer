import json
import os
import re
import subprocess
import tempfile

from app.integration.ffmpeg.commands import build_duration_command, build_extract_segment_command
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


def seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds into HH:MM:SS.mmm format.

    Example:
        3661.5 -> 01:01:01.500
    """

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return f"{hours:02}:{minutes:02}:{secs:06.3f}"


def parse_silence_output(ffmpeg_output: str) -> list[dict]:
    """
    Parse FFmpeg silencedetect output.

    Returns:
        List of detected silence intervals.
    """

    starts = re.findall(r"silence_start: ([0-9.]+)", ffmpeg_output)

    ends = re.findall(r"silence_end: ([0-9.]+)", ffmpeg_output)

    silences = []

    for start, end in zip(starts, ends):
        start_sec = float(start)
        end_sec = float(end)

        silences.append(
            {
                "start": seconds_to_timestamp(start_sec),
                "end": seconds_to_timestamp(end_sec),
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration": round(end_sec - start_sec, 2),
            }
        )

    return silences


def build_keep_intervals(
    silences: list[dict],
    total_duration: float,
) -> list[tuple[float, float]]:
    """
    Build intervals that should be kept after removing silences.

    Example:
        Total Duration: 100

        Silences:
            20–30
            60–70

        Returns:
            [
                (0, 20),
                (30, 60),
                (70, 100),
            ]
    """

    keep_intervals = []

    current_start = 0.0

    for silence in silences:
        silence_start = silence["start_sec"]

        # Only keep the interval if it has a positive duration.
        # If the audio starts with silence, silence_start == 0.0,
        # which would produce a (0.0, 0.0) segment that FFmpeg rejects.
        if silence_start > current_start:
            keep_intervals.append(
                (
                    current_start,
                    silence_start,
                )
            )

        current_start = silence["end_sec"]

    if current_start < total_duration:
        keep_intervals.append(
            (
                current_start,
                total_duration,
            )
        )

    return keep_intervals


def generate_audio_fingerprint(audio_path: str) -> str | None:

    logger = get_logger(__name__)

    try:
        # --- Check duration first ---
        duration_cmd = build_duration_command(audio_path)
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration_data = json.loads(duration_result.stdout)
        duration = float(duration_data["format"]["duration"])

        OFFSET = 300.0
        LENGTH = 120.0

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        if duration > OFFSET:
            # Long enough — sample from the 5-minute mark
            start = OFFSET
            end = min(OFFSET + LENGTH, duration)
        else:
            # Short audio — just fingerprint whatever we have
            logger.warning(f"Audio {audio_path} is only {duration:.1f}s, fingerprinting from start.")
            start = 0.0
            end = duration

        trim_cmd = build_extract_segment_command(
            audio_path=audio_path,
            start=start,
            end=end,
            output_path=tmp_path,
        )
        subprocess.run(trim_cmd, capture_output=True, check=True)

        result = subprocess.run(
            ["fpcalc", "-json", "-length", str(int(end - start)), tmp_path],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        fingerprint = data.get("fingerprint")

        if not fingerprint:
            logger.warning(f"fpcalc returned no fingerprint for {audio_path}")
            return None

        logger.info(f"Audio fingerprint generated for {audio_path} (sampled {start:.0f}s→{end:.0f}s)")
        return fingerprint

    except FileNotFoundError as exc:
        logger.error(f"Missing tool ({exc.filename}). Ensure ffmpeg and fpcalc are installed.")
        return None

    except subprocess.CalledProcessError as exc:
        logger.error(f"Subprocess failed for {audio_path}: {exc.stderr}")
        return None

    except Exception as exc:
        logger.error(f"Unexpected error generating audio fingerprint for {audio_path}: {exc}")
        return None

    finally:
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
