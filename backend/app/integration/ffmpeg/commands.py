from app.core.config import settings


def build_extract_audio_command(video_path: str, audio_path: str) -> list[str]:
    """
    Build FFmpeg command to extract audio suitable for Whisper.
    """

    return [
        settings.FFMPEG_PATH,
        "-i",
        video_path,  # Input video file.
        "-ar",
        "16000",  # Resample audio to 16 kHz (Whisper standard).
        "-ac",
        "1",  # Convert audio to a single (mono) channel.
        "-c:a",
        "pcm_s16le",  # Use 16-bit PCM WAV encoding.
        "-af",
        "highpass=f=80,lowpass=f=8000,afftdn,dynaudnorm",  # Apply audio filters.
        "-y",  # Overwrite output file without asking.
        audio_path,  # Output audio file path.
    ]


def build_duration_command(audio_path: str) -> list[str]:
    """
    Build FFprobe command to get media duration.
    """

    return [
        settings.FFPROBE_PATH,
        "-v",
        "quiet",  # Suppress unnecessary logs.
        "-print_format",
        "json",  # Force output format as JSON.
        "-show_format",  # Include container-level information such as total duration.
        audio_path,
    ]


def build_detect_silence_command(
    audio_path: str,
    noise_threshold: str,
    silence_duration: int,
) -> list[str]:
    """
    Build FFmpeg command to detect silence.
    """

    return [
        settings.FFMPEG_PATH,
        "-i",
        audio_path,  # Input audio file to analyze.
        "-af",  # Apply an audio filter to the input stream.
        f"silencedetect=noise={noise_threshold}:d={silence_duration}",
        # silencedetect:
        #   noise=<threshold> : Treat audio below this level as silence
        #                       (e.g., -35dB).
        #   d=<duration>      : Report silence only if it lasts for at least
        #                       this many seconds (e.g., 10 seconds).
        "-f",  # Specify output format.
        "null",  # Use FFmpeg's null muxer because we only need the silence detection logs, not an actual output file.
        "-",  # Redirect output to standard error (where filter logs are printed).
    ]


def build_extract_segment_command(
    audio_path: str,
    start: float,
    end: float,
    output_path: str,
) -> list[str]:
    """
    Build FFmpeg command to extract a segment.
    """

    return [
        settings.FFMPEG_PATH,
        "-y",  # Overwrite output file if it exists.
        "-i",
        audio_path,  # Input audio file.
        "-ss",
        str(start),  # Segment start time (seconds).
        "-to",
        str(end),  # Segment end time (seconds).
        "-c",
        "copy",  # Copy original audio stream without re-encoding.
        output_path,
    ]


def build_concat_command(
    concat_file_path: str,
    output_path: str,
) -> list[str]:
    """
    Build FFmpeg command to concatenate segments.
    """

    return [
        settings.FFMPEG_PATH,
        "-y",  # Overwrite output file if it exists.
        "-f",
        "concat",  # Use FFmpeg concat demuxer.
        "-safe",
        "0",  # Allow absolute paths in concat file.
        "-i",
        concat_file_path,  # Text file listing segment paths.
        "-c",
        "copy",  # Copy streams without re-encoding.
        output_path,
    ]
