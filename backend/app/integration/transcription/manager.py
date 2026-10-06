import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from google import genai
from google.genai import types

from app.core.config import settings
from app.integration.transcription.utils import (
    deduplicate_overlapping_text,
    normalize_text,
    split_audio_to_memory,
    split_into_segments,
)
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


class TranscriptionChunkError(RuntimeError):
    """Raised when a chunk cannot be transcribed after exhausting all API keys."""


# ═══════════════════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(slots=True)
class ChunkResult:
    """Result from transcribing a single chunk."""

    chunk_number: int
    start_time: float
    end_time: float
    text: str
    verbose_json: dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
# Improved Transcription Prompt for Gemini
# ═══════════════════════════════════════════════════════════════════════════

TRANSCRIPT_PROMPT = """You are an expert transcriber for technical interviews.

Your task is to transcribe the audio content accurately. Follow these rules:

CRITICAL - DO NOT INVENT, GUESS, OR COMPLETE:
* Transcribe ONLY words you actually hear.
* If you're uncertain, STOP. Do not guess or continue.
* Do not fill silence, noise, or unclear sections with invented text.
* Do not complete sentences or thoughts.
* Do not add words that might logically follow but were not spoken.

ACCURACY OVER FLUENCY:
* Preserve exact wording, including filler words (uh, um, like, you know).
* Keep technical terms, APIs, framework names, product names, company names exactly as spoken.
* Preserve numbers, dates, percentages, version numbers precisely.
* Do NOT correct grammar, pronunciation, or accent.
* Keep abbreviations and acronyms as spoken.

SILENCE AND NOISE:
* Omit unintelligible or unclear speech entirely—do not attempt to guess words.
* Ignore background noise, music, keyboard clicks, papers rustling.
* If only 1-2 words are clear in a section, include only those.

PUNCTUATION:
* Add minimal punctuation only when audio clearly indicates sentence/clause boundaries.
* Prefer fewer punctuation marks if unsure.

SAFETY:
* When in doubt, transcribe less rather than more.
* Short gaps? Leave them silent. Better to miss 5% than invent 5%.

Output the transcription as plain text, preserving all the words you hear exactly as spoken.
"""


# ═══════════════════════════════════════════════════════════════════════════
# TranscriptionManager using Gemini
# ═══════════════════════════════════════════════════════════════════════════


class TranscriptionManager:
    """
    Manages audio transcription via Google Gemini API with advanced features:
    - Splits audio into overlapping chunks (for better context at boundaries)
    - Transcribes in parallel using ThreadPoolExecutor
    - Deduplicates overlapping text using word-level fuzzy matching
    - Interpolates timestamps using character-index mapping
    - Splits into natural segments using sentence boundaries
    - Rotates across a pool of API keys, retrying failed chunks on a
      different key before giving up
    """

    def __init__(self, max_workers: int = 8):
        self.max_workers = max_workers

    @staticmethod
    def _parse_api_keys() -> list[str]:
        """Parse GEMINI_API_KEYS (comma-separated) into a list of individual keys.

        Example:
            GEMINI_API_KEYS="AIzaKey1,AIzaKey2,AIzaKey3"
            -> ['AIzaKey1', 'AIzaKey2', 'AIzaKey3']
        """
        raw = settings.GEMINI_API_KEYS
        if not raw:
            raise RuntimeError(
                "GEMINI_API_KEYS is not set. Add one or more comma-separated AI-Studio API keys to your .env file."
            )
        keys = [k.strip() for k in raw.split(",") if k.strip()]
        if not keys:
            raise RuntimeError(
                "GEMINI_API_KEYS contains no valid keys after parsing. "
                "Expected comma-separated values like: AIzaKey1,AIzaKey2"
            )
        return keys

    @staticmethod
    def _make_client(api_key: str) -> "genai.Client":
        """Build a Gemini client for a single api_key."""
        return genai.Client(api_key=api_key)

    def transcribe(
        self,
        audio_path: str,
        chunk_boundaries: list[dict] | None = None,
    ) -> dict:
        """
        Split audio into chunks with overlap, transcribe in parallel,
        then deduplicate and merge with proper timestamp interpolation.

        Args:
            audio_path: Path to the cleaned .wav file.

        Returns:
            {
                "source_file": str,
                "audio_duration_seconds": float,
                "chunk_count": int,
                "created_at": str (ISO format),
                "full_text": str,
                "segments": [{"start": float, "end": float, "text": str}, ...],
                "processing_time": float,
                "chunks_processed": int,
            }
        """

        total_start = time.time()

        logger.info(f"Starting transcription (Gemini) for: {audio_path}")

        # Split audio into chunks with overlap
        chunks = split_audio_to_memory(
            audio_path,
            default_chunk_minutes=5,  # 5-minute default chunks
            max_chunks=20,
            overlap_seconds=20,  # 20-second overlap for better context
            chunk_boundaries=chunk_boundaries,
        )

        logger.info(f"Created {len(chunks)} chunks for transcription (with overlap)")

        # Parse comma-separated keys and distribute across chunks round-robin.
        # e.g. 9 chunks, 3 keys -> chunks 0,3,6 use key[0]; 1,4,7 use key[1]; ...
        api_keys = self._parse_api_keys()
        logger.info(f"Transcription key pool: {len(api_keys)} key(s) for {len(chunks)} chunk(s)")

        # Transcribe chunks in parallel, each starting with its round-robin key.
        # Cap concurrency per API key (2 chunks/key) so a small key pool isn't
        # throttled into retries, while larger pools fully parallelize.
        results = []

        if chunks:
            max_workers = min(len(chunks), self.max_workers, max(2, len(api_keys) * 2))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._transcribe_chunk, chunk, api_keys) for chunk in chunks]

                for future in as_completed(futures):
                    chunk_result = future.result()
                    results.append(chunk_result)

            # Sort results by chunk number
            results.sort(key=lambda x: x.chunk_number)

            logger.info(f"Transcribed all {len(results)} chunks, now merging...")
        else:
            logger.warning(f"No chunks generated from audio file: {audio_path}")

        # Merge and deduplicate
        merged = self._merge_results(
            source_file=audio_path.rsplit("/", maxsplit=1)[-1],
            duration=chunks[-1]["end_time"] if chunks else 0.0,
            results=results,
        )

        total_time = round(time.time() - total_start, 2)

        logger.info(
            f"Transcription completed: {len(chunks)} chunks, {len(merged['segments'])} segments, {total_time}s total"
        )

        return {
            **merged,
            "processing_time": total_time,
            "chunks_processed": len(chunks),
        }

    def _transcribe_chunk(self, chunk_data: dict, all_keys: list[str]) -> ChunkResult:
        """
        Transcribe a single audio chunk via Google Gemini API.

        The chunk starts with a round-robin-assigned key (based on chunk_index)
        and, on failure, retries once per remaining key in the pool before
        giving up and returning an empty result.

        Args:
            chunk_data: Dict with chunk_index, offset_seconds, end_time, audio_bytes.
            all_keys:   Full key pool to try, in rotation order.
        """

        chunk_index = chunk_data["chunk_index"]
        offset_seconds = chunk_data["offset_seconds"]
        end_time = chunk_data["end_time"]

        start_time = time.time()

        # Build the ordered list of keys to try: start at this chunk's
        # round-robin key, then wrap around through the rest of the pool.
        start_idx = chunk_index % len(all_keys)
        keys_to_try = [all_keys[(start_idx + offset) % len(all_keys)] for offset in range(len(all_keys))]

        logger.info(f"Started transcribing chunk {chunk_index} (starting key index {start_idx})")

        last_error: Exception | None = None

        for attempt, key in enumerate(keys_to_try):
            try:
                # Created as a local variable so it stays alive for the
                # entire blocking HTTP call (prevents GC mid-request).
                client = self._make_client(key)

                logger.debug(f"Chunk {chunk_index}: attempt {attempt + 1}/{len(keys_to_try)}")

                response = client.models.generate_content(
                    model=settings.GOOGLE_AI_MODEL,
                    contents=[  # type: ignore[arg-type]  # mixed str + Part in one list
                        TRANSCRIPT_PROMPT,
                        types.Part.from_bytes(
                            data=chunk_data["audio_bytes"],
                            mime_type="audio/wav",
                        ),
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        top_k=1,
                        top_p=0.0,
                        max_output_tokens=4096,
                    ),
                )

                full_text = response.text.strip() if response.text else ""
                elapsed = round(time.time() - start_time, 2)

                logger.info(f"Finished chunk {chunk_index} in {elapsed}s (attempt {attempt + 1})")

                return ChunkResult(
                    chunk_number=chunk_index,
                    start_time=offset_seconds,
                    end_time=end_time,
                    text=full_text,
                    verbose_json={
                        "model": settings.GOOGLE_AI_MODEL,
                        "chunk_index": chunk_index,
                        "file_mime_type": "audio/wav",
                        "attempts": attempt + 1,
                    },
                )

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Chunk {chunk_index}: attempt {attempt + 1}/{len(keys_to_try)} "
                    f"failed with key ending '...{key[-4:]}': {e}"
                )
                continue

        # All keys exhausted for this chunk
        logger.error(f"Chunk {chunk_index}: all {len(keys_to_try)} key(s) failed. Last error: {last_error}")

        # Fail loudly instead of silently dropping the chunk: upstream does not
        # retry unless we raise, and losing a 5-minute section of the interview
        # is worse than retrying the whole transcription.
        raise TranscriptionChunkError(
            f"Chunk {chunk_index} failed after {len(keys_to_try)} key attempt(s). Last error: {last_error}"
        ) from last_error

    def _merge_results(
        self,
        source_file: str,
        duration: float,
        results: list[ChunkResult],
    ) -> dict[str, Any]:
        """
        Merge transcribed chunks using deduplication and character-index
        timeline interpolation to prevent timestamp drift.

        Args:
            source_file: Name of the source audio file.
            duration: Total audio duration in seconds.
            results: List of ChunkResult objects from all chunks.

        Returns:
            Merged result dict with full_text and segments.
        """

        # Deduplicate overlapping text
        deduplicated_chunks = deduplicate_overlapping_text(results)

        # Build full text and character mapping.
        #
        # OFFSET INVARIANT: each chunk is normalized in isolation FIRST, and
        # only that already-normalized text is joined into full_text_parts and
        # used to compute the offsets recorded in `mappings`. No
        # length-changing operation may run after an offset for that span has
        # been recorded. In particular there must be NO second
        # normalize_text() pass over the joined full string: normalize_text()
        # changes length (e.g. a bare em-dash "—", 1 char, becomes " - ",
        # 3 chars), which would invalidate every offset recorded after the
        # substitution and shift all downstream _interpolate_time timestamps.
        full_text_parts: list[str] = []
        mappings: list[dict[str, Any]] = []
        current_len = 0  # always == len(" ".join(full_text_parts))

        for chunk in deduplicated_chunks:
            # THE single normalization pass per chunk: happens BEFORE this
            # chunk touches full_text_parts or mappings.
            text = normalize_text(chunk["text"])
            if text:
                start_char = current_len + (1 if full_text_parts else 0)
                full_text_parts.append(text)
                end_char = start_char + len(text)
                current_len = end_char

                mappings.append(
                    {
                        "start_char": start_char,
                        "end_char": end_char,
                        "start_time": chunk["start_time"],
                        "end_time": chunk["end_time"],
                    }
                )

        # Join only. Parts are already normalized and stripped, so this adds
        # single-space separators and nothing else — no length-changing
        # operation touches the string after offsets were recorded.
        # (The old .strip() + normalize_text() second pass over the joined
        # string is intentionally gone; see the invariant above.)
        full_text = " ".join(full_text_parts)

        # Split into segments using natural boundaries
        raw_segments = split_into_segments(full_text, max_words=20)
        merged_segments = []

        current_char_idx = 0
        for seg_text in raw_segments:
            seg_start_char = full_text.find(seg_text, current_char_idx)
            if seg_start_char == -1:
                seg_start_char = current_char_idx

            seg_end_char = seg_start_char + len(seg_text)
            current_char_idx = seg_end_char

            # Interpolate timestamps
            start_time = self._interpolate_time(seg_start_char, mappings)
            end_time = self._interpolate_time(seg_end_char, mappings)

            merged_segments.append(
                {
                    "start": round(start_time, 3),
                    "end": round(end_time, 3),
                    "text": seg_text,
                }
            )

        logger.info(
            f"Merged {len(results)} chunks into {len(merged_segments)} segments, "
            f"total text length: {len(full_text)} chars"
        )

        return {
            "source_file": source_file,
            "audio_duration_seconds": duration,
            "chunk_count": len(results),
            "created_at": datetime.now(UTC).isoformat(),
            "model": settings.GOOGLE_AI_MODEL,
            "full_text": full_text,
            "segments": merged_segments,
        }

    def _interpolate_time(self, char_idx: int, mappings: list[dict]) -> float:
        """
        Interpolate timestamp for a given character index using character-based mappings.
        Prevents timestamp drift by using character positions as reference.

        Args:
            char_idx: Character index in the full text.
            mappings: List of character-to-time mappings from chunks.

        Returns:
            Interpolated timestamp in seconds.
        """

        if not mappings:
            return 0.0

        # Boundary cases
        if char_idx <= mappings[0]["start_char"]:
            return mappings[0]["start_time"]
        if char_idx >= mappings[-1]["end_char"]:
            return mappings[-1]["end_time"]

        # Find mapping containing this character
        for i, chunk in enumerate(mappings):
            if chunk["start_char"] <= char_idx <= chunk["end_char"]:
                char_range = chunk["end_char"] - chunk["start_char"]
                if char_range == 0:
                    return chunk["start_time"]

                ratio = (char_idx - chunk["start_char"]) / char_range
                return chunk["start_time"] + ratio * (chunk["end_time"] - chunk["start_time"])

            # Interpolate between chunks
            if i < len(mappings) - 1 and chunk["end_char"] < char_idx < mappings[i + 1]["start_char"]:
                t1 = chunk["end_time"]
                t2 = mappings[i + 1]["start_time"]
                c1 = chunk["end_char"]
                c2 = mappings[i + 1]["start_char"]

                ratio = (char_idx - c1) / (c2 - c1) if c2 > c1 else 0
                return t1 + ratio * (t2 - t1)

        return mappings[-1]["end_time"]


# Singleton instance
transcription_manager = TranscriptionManager()
