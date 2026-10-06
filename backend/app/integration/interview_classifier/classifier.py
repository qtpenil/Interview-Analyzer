import json
import time
from collections import Counter

from google import genai

from app.core.config import settings
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)

# Fast heuristic thresholds — very lenient, only reject truly empty/garbage
MIN_TRANSCRIPT_WORDS = 30
MIN_TRANSCRIPT_SEGMENTS = 2
MIN_AUDIO_DURATION_SECONDS = 10


USER_FRIENDLY_REASONS = {
    "heuristic": "The recording appears too short or empty. Please upload a longer interview recording.",
    "not_interview": "We couldn't detect a clear interview structure in this recording. "
                     "Please ensure the audio contains a back-and-forth conversation "
                     "with questions and answers about work experience or technical topics.",
    "asr_error": "The audio quality may be too low for accurate transcription. "
                 "Please try a clearer recording with less background noise.",
    "default": "This doesn't appear to be a valid interview recording. "
               "Please upload a professional interview with clear Q&A content.",
}


def _quick_heuristic_check(
    full_text: str,
    segments: list[dict],
    duration_seconds: float,
    interview_id: str,
) -> dict | None:
    words = full_text.split()
    word_count = len(words)
    segment_count = len(segments)

    reasons = []

    if word_count < MIN_TRANSCRIPT_WORDS:
        reasons.append(f"Only {word_count} words (min {MIN_TRANSCRIPT_WORDS})")

    if segment_count < MIN_TRANSCRIPT_SEGMENTS:
        reasons.append(f"Only {segment_count} speech segments (min {MIN_TRANSCRIPT_SEGMENTS})")

    if duration_seconds < MIN_AUDIO_DURATION_SECONDS:
        reasons.append(f"Only {duration_seconds:.0f}s audio (min {MIN_AUDIO_DURATION_SECONDS}s)")

    if reasons:
        reason = " | ".join(reasons)
        logger.warning(f"[{interview_id}] Heuristic reject: {reason}")
        return {
            "is_interview": False,
            "reason": USER_FRIENDLY_REASONS["heuristic"],
            "raw_reason": f"Insufficient interview content: {reason}",
            "confidence": 0.9,
        }

    return None


def _detect_repetitive_transcript(full_text: str) -> bool:
    """
    Detect if transcript is likely an ASR hallucination (repetitive loop).
    Returns True if the text appears to be a repetitive artifact.
    """
    words = full_text.lower().split()
    if len(words) < 20:
        return False

    # Check for repeated n-grams (phrases)
    # Common Whisper hallucination: short phrase repeated many times
    for n in range(1, 6):  # 1-5 word phrases
        phrases = []
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n])
            phrases.append(phrase)

        if not phrases:
            continue

        # Count occurrences of each phrase
        phrase_counts = Counter(phrases)

        # If any phrase appears more than 30% of the time, it's repetitive
        most_common_phrase, count = phrase_counts.most_common(1)[0]
        if count / len(phrases) > 0.3 and len(most_common_phrase.split()) <= 5:
            logger.warning(f"Repetitive transcript detected: '{most_common_phrase}' appears {count}/{len(phrases)} times")
            return True

    return False


# EXTREMELY LENIENT PROMPT - defaults to interview unless CLEARLY not
CLASSIFIER_PROMPT = """You are an interview classifier. Given a transcript from an ASR system,
determine if this represents a professional or technical job interview.

CRITICAL: The transcript is RAW ASR OUTPUT — NO speaker labels, imperfect punctuation, 
transcription errors, filler words, and noise. This is EXPECTED and NORMAL.

IMPORTANT: ASR systems sometimes produce REPETITIVE HALLUCINATIONS (loops of a phrase).
If the transcript looks like a repeated phrase, it's likely an AUDIO QUALITY ISSUE, 
not "not an interview". In such cases, return is_interview: true with low confidence.

DEFAULT TO "is_interview: true" UNLESS THE CONTENT IS UNAMBIGUOUSLY NOT AN INTERVIEW.
False negatives (rejecting real interviews) are MUCH WORSE than false positives.

The following ARE interviews (even if messy):
- Any professional/technical discussion about work, projects, skills, experience
- Q&A about past roles, challenges, decisions, technologies, methodologies
- Mentions of: programming languages, frameworks, tools, companies, teams, projects
- Problem-solving discussions, architecture choices, debugging stories
- Career history, responsibilities, achievements, learning experiences
- Multiple topics discussed in a conversational manner
- Even a single speaker describing their work experience in detail
- Repetitive transcripts that may be ASR artifacts from poor audio

ONLY return "is_interview: false" for CLEARLY non-interview content:
- Pure music, silence, noise, or unintelligible audio
- Casual personal chat with ZERO professional/technical content
- Scripted entertainment (podcast intros, news, storytelling)
- Clearly automated/robotic speech (TTS, IVR systems)
- Single-word or extremely short fragments (< 30 words total)

When uncertain, ALWAYS return true.

Transcript (first ~8000 chars):
{transcript}

Respond with ONLY a JSON object:
{{"is_interview": true/false, "reason": "Brief explanation", "confidence": 0.0-1.0}}"""


def classify_transcript(transcript_text: str, interview_id: str) -> dict:
    text = transcript_text
    if len(text) > 8000:
        text = text[:8000]
        logger.info(f"[{interview_id}] Classifier input truncated to 8000 chars")

    api_keys = [k.strip() for k in settings.GEMINI_API_KEYS.split(",") if k.strip()]
    if not api_keys:
        logger.warning(f"[{interview_id}] No Gemini API keys configured, skipping classifier")
        return {"is_interview": True, "reason": "Classifier disabled (no API keys)", "confidence": 1.0}

    last_error = None
    for attempt in range(min(3, len(api_keys))):
        key = api_keys[attempt % len(api_keys)]
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=settings.GOOGLE_AI_MODEL,
                contents=CLASSIFIER_PROMPT.format(transcript=text),
                config={"response_mime_type": "application/json"},
            )
            result_text = response.text or "{}"
            result = json.loads(result_text)
            logger.info(
                f"[{interview_id}] Classifier result: is_interview={result.get('is_interview')}, "
                f"confidence={result.get('confidence')}, reason={result.get('reason')}"
            )
            return result
        except Exception as exc:
            last_error = exc
            logger.warning(f"[{interview_id}] Classifier attempt {attempt + 1} failed: {exc}")
            time.sleep(1)

    logger.error(f"[{interview_id}] All classifier attempts failed: {last_error}")
    return {"is_interview": True, "reason": "Classifier unavailable, allowing pipeline", "confidence": 0.5}


def classify_transcript_with_context(
    full_text: str,
    segments: list[dict],
    duration_seconds: float,
    interview_id: str,
) -> dict:
    # 1. Fast heuristic — reject only truly empty/garbage
    heuristic_result = _quick_heuristic_check(full_text, segments, duration_seconds, interview_id)
    if heuristic_result is not None:
        return heuristic_result

    # 2. Check for repetitive ASR hallucination BEFORE LLM
    is_repetitive = _detect_repetitive_transcript(full_text)
    if is_repetitive:
        logger.warning(f"[{interview_id}] Repetitive transcript detected — treating as likely ASR artifact, accepting as interview")
        return {
            "is_interview": True,
            "reason": "Accepted despite repetitive transcript (likely ASR artifact from audio quality)",
            "confidence": 0.6,
            "raw_reason": "Repetitive transcript pattern detected - probable ASR hallucination",
        }

    # 3. Build context for LLM
    word_count = len(full_text.split())
    segment_count = len(segments)
    avg_segment_words = word_count / max(segment_count, 1)

    context = (
        f"[Metadata: {word_count} words, {segment_count} segments, "
        f"{duration_seconds:.0f}s duration, ~{avg_segment_words:.0f} words/segment]\n"
        f"{full_text[:8000]}"
    )

    # 4. Call LLM with EXTREMELY LENIENT prompt
    api_keys = [k.strip() for k in settings.GEMINI_API_KEYS.split(",") if k.strip()]
    if not api_keys:
        logger.warning(f"[{interview_id}] No Gemini API keys, skipping classifier")
        return {"is_interview": True, "reason": "Classifier disabled (no API keys)", "confidence": 1.0}

    last_error = None
    for attempt in range(min(3, len(api_keys))):
        key = api_keys[attempt % len(api_keys)]
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=settings.GOOGLE_AI_MODEL,
                contents=CLASSIFIER_PROMPT.format(transcript=context),
                config={"response_mime_type": "application/json"},
            )
            result_text = response.text or "{}"
            result = json.loads(result_text)

            # Log the raw LLM response for debugging
            logger.info(
                f"[{interview_id}] LLM raw response: is_interview={result.get('is_interview')}, "
                f"confidence={result.get('confidence')}, reason={result.get('reason')}"
            )

            # ONLY reject if LLM is EXTREMELY confident (>= 0.95) it's not an interview
            # Otherwise default to interview
            is_interview = result.get("is_interview", True)
            confidence = result.get("confidence", 0.5)

            if not is_interview and confidence < 0.95:
                logger.warning(
                    f"[{interview_id}] LLM said not_interview but confidence "
                    f"({confidence}) < 0.95 — OVERRIDING to is_interview=true"
                )
                is_interview = True
                confidence = 1.0 - confidence  # flip confidence
                result["reason"] = "Auto-accepted: low confidence rejection"

            if is_interview:
                confidence = min(1.0, confidence + 0.1)

            result["is_interview"] = is_interview
            result["confidence"] = confidence

            # Map to user-friendly message ONLY for genuine high-confidence rejections
            if not is_interview:
                raw_reason = result.get("reason", "").lower()
                if "asr" in raw_reason or "transcription" in raw_reason or "artifact" in raw_reason:
                    result["reason"] = USER_FRIENDLY_REASONS["asr_error"]
                else:
                    result["reason"] = USER_FRIENDLY_REASONS["not_interview"]

            logger.info(
                f"[{interview_id}] Final classifier: is_interview={is_interview}, "
                f"confidence={confidence}, reason={result.get('reason')}"
            )
            return result
        except Exception as exc:
            last_error = exc
            logger.warning(f"[{interview_id}] Classifier attempt {attempt + 1} failed: {exc}")
            time.sleep(1)

    logger.error(f"[{interview_id}] All classifier attempts failed: {last_error}")
    return {"is_interview": True, "reason": "Classifier unavailable, allowing pipeline", "confidence": 0.5}
