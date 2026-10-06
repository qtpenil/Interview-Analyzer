from app.core.config import settings
from app.integration.ffmpeg.commands import (
    build_concat_command,
    build_detect_silence_command,
    build_duration_command,
    build_extract_audio_command,
    build_extract_segment_command,
)


class TestBuildExtractAudioCommand:
    def test_basic_command_structure(self):
        cmd = build_extract_audio_command("/input/video.mp4", "/output/audio.wav")
        assert cmd[0] == settings.FFMPEG_PATH
        assert "-i" in cmd
        input_idx = cmd.index("-i") + 1
        assert cmd[input_idx] == "/input/video.mp4"
        assert cmd[-1] == "/output/audio.wav"

    def test_audio_settings(self):
        cmd = build_extract_audio_command("in.mp4", "out.wav")
        assert "-ar" in cmd
        assert cmd[cmd.index("-ar") + 1] == "16000"
        assert "-ac" in cmd
        assert cmd[cmd.index("-ac") + 1] == "1"
        assert "-af" in cmd

    def test_output_is_wav(self):
        cmd = build_extract_audio_command("in.mp4", "out.wav")
        assert cmd[-1].endswith(".wav")


class TestBuildDurationCommand:
    def test_uses_ffprobe(self):
        cmd = build_duration_command("/audio/file.wav")
        assert cmd[0] == settings.FFPROBE_PATH

    def test_json_output(self):
        cmd = build_duration_command("test.wav")
        assert "-print_format" in cmd
        assert cmd[cmd.index("-print_format") + 1] == "json"
        assert "-show_format" in cmd


class TestBuildDetectSilenceCommand:
    def test_includes_silencedetect_filter(self):
        cmd = build_detect_silence_command("test.wav", "-35dB", 10)
        filter_idx = cmd.index("-af") + 1
        assert "silencedetect" in cmd[filter_idx]
        assert "-35dB" in cmd[filter_idx]

    def test_output_to_null(self):
        cmd = build_detect_silence_command("test.wav", "-35dB", 10)
        assert "-f" in cmd
        assert cmd[cmd.index("-f") + 1] == "null"
        assert cmd[-1] == "-"

    def test_custom_threshold(self):
        cmd = build_detect_silence_command("test.wav", "-40dB", 15)
        filter_str = cmd[cmd.index("-af") + 1]
        assert "-40dB" in filter_str
        assert "d=15" in filter_str


class TestBuildExtractSegmentCommand:
    def test_basic_segment(self):
        cmd = build_extract_segment_command("test.wav", 10.0, 20.0, "/out/segment.wav")
        assert "-ss" in cmd
        assert cmd[cmd.index("-ss") + 1] == "10.0"
        assert "-to" in cmd
        assert cmd[cmd.index("-to") + 1] == "20.0"
        assert "-c" in cmd
        assert cmd[cmd.index("-c") + 1] == "copy"

    def test_segment_with_float_times(self):
        cmd = build_extract_segment_command("test.wav", 5.5, 15.75, "out.wav")
        assert cmd[cmd.index("-ss") + 1] == "5.5"
        assert cmd[cmd.index("-to") + 1] == "15.75"


class TestBuildConcatCommand:
    def test_concat_structure(self):
        cmd = build_concat_command("/tmp/concat.txt", "/out/final.wav")
        assert "-f" in cmd
        assert cmd[cmd.index("-f") + 1] == "concat"
        assert "-safe" in cmd
        assert cmd[cmd.index("-safe") + 1] == "0"
        concat_idx = cmd.index("-i") + 1
        assert cmd[concat_idx] == "/tmp/concat.txt"

    def test_concat_output(self):
        cmd = build_concat_command("concat.txt", "final.wav")
        assert cmd[-1] == "final.wav"
