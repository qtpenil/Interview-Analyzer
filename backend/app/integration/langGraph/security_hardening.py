import re
import unicodedata

from app.core.config import settings
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)

# Regular expressions for PII redaction
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"\+?\d{1,4}[-.\s]?\(?\d{1,3}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}")
SSN_REGEX = re.compile(r"\d{3}-\d{2}-\d{4}")

# How many malformed segments we tolerate before giving up on the whole transcript.
# A handful of bad segments is normal ASR noise; a huge number signals something
# is systemically wrong upstream and we should fail loudly instead of silently
# dropping most of the interview.
MAX_MALFORMED_SEGMENT_RATIO = 0.05  # 5%


def preprocess_transcript(segments: list[dict], interview_id: str) -> list[dict]:
    """
    Run safety checks and transformations on raw Whisper segments:
    1. Unicode normalization (NFC)
    2. Input structure validation (fields, times)
    3. Transcript size & duration constraints
    4. PII redaction (configurable)
    """
    if not isinstance(segments, list):
        raise ValueError("Transcript segments must be a list of dictionaries")

    processed = []
    total_chars = 0
    max_size = settings.MAX_TRANSCRIPT_SIZE
    max_duration = settings.MAX_TRANSCRIPT_DURATION
    limit_exceeded = False
    skipped_segments = 0

    for idx, s in enumerate(segments):
        # 1. Input Validation
        if not isinstance(s, dict):
            raise ValueError(f"Segment at index {idx} is not a dictionary")
        if "start" not in s or "end" not in s or "text" not in s:
            raise ValueError(f"Segment {idx} is missing required fields (start, end, text)")

        start, end, text = s["start"], s["end"], s["text"]

        # Non-numeric check
        try:
            start = float(start)
            end = float(end)
        except (ValueError, TypeError):
            raise ValueError(f"Segment {idx} has non-numeric timestamps: start={start}, end={end}")

        # Logical bounds check.
        # Malformed timing on an individual segment is common ASR noise (chunk-boundary
        # merges, VAD glitches) rather than a structural problem with the whole transcript.
        # Skip the offending segment instead of failing the entire interview, but keep
        # a count so we can still bail out if too much of the transcript is corrupt.
        #
        # NOTE: the primary KNOWN cause of negative-duration segments — character
        # offsets in TranscriptionManager._merge_results being computed on raw
        # text followed by a length-changing normalize_text() pass over the
        # joined string — has been fixed at the source (per-chunk normalization
        # before offset mapping). This skip stays as a safety net, but if the
        # skip rate stays non-trivial after that fix it likely indicates a
        # DIFFERENT bug, not the offset drift.
        if end < start:
            logger.warning(
                f"[{interview_id}] Segment {idx} has negative duration (start={start}, end={end}); skipping segment."
            )
            skipped_segments += 1
            continue
        if start < 0 or end > 86400:  # 24 hours max
            logger.warning(
                f"[{interview_id}] Segment {idx} timestamps out of reasonable bounds "
                f"(start={start}, end={end}); skipping segment."
            )
            skipped_segments += 1
            continue

        # 2. Unicode Normalization (NFC)
        normalized_text = unicodedata.normalize("NFC", str(text))

        # 3. PII Redaction (Phases 7 & 8)
        if settings.ENABLE_PII_REDACTION:
            normalized_text = EMAIL_REGEX.sub("[EMAIL]", normalized_text)
            normalized_text = SSN_REGEX.sub("[ID]", normalized_text)
            normalized_text = PHONE_REGEX.sub("[PHONE]", normalized_text)

        # 4. Transcript Size Constraints
        seg_len = len(normalized_text)
        if total_chars + seg_len > max_size:
            limit_exceeded = True
            if settings.ON_LIMIT_EXCEEDED == "reject":
                raise ValueError(
                    f"Transcript character count {total_chars + seg_len} exceeds MAX_TRANSCRIPT_SIZE limit of {max_size}."
                )
            elif settings.ON_LIMIT_EXCEEDED in ("split", "truncate"):
                # Truncate remaining segments
                logger.warning(f"[{interview_id}] Transcript character count exceeded {max_size}. Slicing transcript.")
                break

        # Duration Constraints
        if end > max_duration:
            limit_exceeded = True
            if settings.ON_LIMIT_EXCEEDED == "reject":
                raise ValueError(
                    f"Transcript duration {end}s exceeds MAX_TRANSCRIPT_DURATION limit of {max_duration}s."
                )
            elif settings.ON_LIMIT_EXCEEDED in ("split", "truncate"):
                # Truncate at this segment
                logger.warning(f"[{interview_id}] Transcript duration exceeded {max_duration}s. Slicing transcript.")
                break

        total_chars += seg_len
        processed.append({"start": start, "end": end, "text": normalized_text})

    # If a large fraction of segments were malformed, something is systemically wrong
    # upstream (bad ASR run, corrupted upload, etc.) -- fail loudly rather than silently
    # analyzing a mostly-empty transcript.
    if segments and (skipped_segments / len(segments)) > MAX_MALFORMED_SEGMENT_RATIO:
        raise ValueError(
            f"Too many malformed segments in transcript: {skipped_segments}/{len(segments)} "
            f"({skipped_segments / len(segments):.1%}) exceeded tolerance of "
            f"{MAX_MALFORMED_SEGMENT_RATIO:.0%}."
        )

    logger.info(
        f"[{interview_id}] Preprocessed transcript: {len(processed)} segments, {total_chars} characters. "
        f"Skipped malformed segments: {skipped_segments}. "
        f"PII Redaction: {settings.ENABLE_PII_REDACTION}, Size Limit Exceeded: {limit_exceeded}"
    )

    return processed
