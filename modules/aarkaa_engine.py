"""
AARKAAI - AARKAA-3B Core Engine (llama.cpp / GGUF)

High-performance CPU inference using llama-cpp-python.
Falls back to a stub when the GGUF model is not present.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from config import MODEL_PATH, MAX_TOKENS

logger = logging.getLogger(__name__)

import threading
import time
import gc

_model_cpu = None
_model_gpu = None
_model_coder_gpu = None
_is_stub = True
_model_lock = threading.RLock()
_last_active_time = time.time()
_idle_timeout = int(os.getenv("AARKAAI_IDLE_TIMEOUT", "300"))  # 5 minutes default
_gguf_file_path = None
_gguf_coder_path = Path(MODEL_PATH).parent / "aarkaa-coder-3b-f16.gguf"
_n_threads = 4

import contextvars
# Global thread/async-safe request domain tracker for dynamic routing
request_domain = contextvars.ContextVar("request_domain", default="general")


_LANG_NAMES = {
    "ab": "Abkhazian",
    "om": "Oromo",
    "aa": "Afar",
    "af": "Afrikaans",
    "sq": "Albanian",
    "am": "Amharic",
    "ar": "Arabic",
    "an": "Aragonese",
    "hy": "Armenian",
    "as": "Assamese",
    "ae": "Avestan",
    "ay": "Aymara",
    "az": "Azerbaijani",
    "ba": "Bashkir",
    "eu": "Basque",
    "be": "Belarusian",
    "bn": "Bengali",
    "bh": "Bihari",
    "bi": "Bislama",
    "bs": "Bosnian",
    "br": "Breton",
    "bg": "Bulgarian",
    "my": "Burmese",
    "ca": "Catalan",
    "ch": "Chamorro",
    "ce": "Chechen",
    "ny": "Nyanja",
    "zh": "Chinese",
    "cv": "Chuvash",
    "kw": "Cornish",
    "co": "Corsican",
    "cr": "Cree",
    "hr": "Croatian",
    "cs": "Czech",
    "da": "Danish",
    "div": "Divehi",
    "nl": "Dutch",
    "dz": "Dzongkha",
    "en": "English",
    "eo": "Esperanto",
    "et": "Estonian",
    "ee": "Ewe",
    "fo": "Faroese",
    "fj": "Fijian",
    "fi": "Finnish",
    "fr": "French",
    "fy": "Frisian",
    "ff": "Fulah",
    "gd": "Gaelic",
    "gl": "Galician",
    "ka": "Georgian",
    "de": "German",
    "el": "Greek",
    "gn": "Guarani",
    "gu": "Gujarati",
    "ht": "Haitian",
    "ha": "Hausa",
    "he": "Hebrew",
    "hz": "Herero",
    "hi": "Hindi",
    "ho": "Hiri Motu",
    "hu": "Hungarian",
    "is": "Icelandic",
    "io": "Ido",
    "ig": "Igbo",
    "id": "Indonesian",
    "ia": "Interlingua",
    "ie": "Interlingue",
    "iu": "Inuktitut",
    "ik": "Inupiaq",
    "ga": "Irish",
    "it": "Italian",
    "ja": "Japanese",
    "jv": "Javanese",
    "kl": "Kalaallisut",
    "kn": "Kannada",
    "kr": "Kanuri",
    "ks": "Kashmiri",
    "kk": "Kazakh",
    "km": "Khmer",
    "ki": "Kikuyu",
    "rw": "Kinyarwanda",
    "ky": "Kirghiz",
    "kv": "Komi",
    "kg": "Kongo",
    "ko": "Korean",
    "kj": "Kuanyama",
    "ku": "Kurdish",
    "lo": "Lao",
    "la": "Latin",
    "lv": "Latvian",
    "li": "Limburgish",
    "ln": "Lingala",
    "lt": "Lithuanian",
    "lu": "Luba-Katanga",
    "lb": "Luxembourgish",
    "mk": "Macedonian",
    "mg": "Malagasy",
    "ms": "Malay",
    "ml": "Malayalam",
    "mt": "Maltese",
    "gv": "Manx",
    "mi": "Maori",
    "mr": "Marathi",
    "mh": "Marshallese",
    "mo": "Moldavian",
    "mn": "Mongolian",
    "na": "Nauru",
    "nv": "Navajo",
    "nd": "Ndebele, North",
    "nr": "Ndebele, South",
    "ng": "Ndonga",
    "ne": "Nepali",
    "se": "Sami, Northern",
    "no": "Norwegian",
    "nb": "Norwegian Bokmål",
    "nn": "Norwegian Nynorsk",
    "ii": "Sichuan Yi",
    "oc": "Occitan",
    "oj": "Ojibwa",
    "or": "Oriya",
    "os": "Ossetian",
    "pa": "Punjabi",
    "pi": "Pali",
    "fa": "Persian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ps": "Pushto",
    "qu": "Quechua",
    "rm": "Raeto-Romance",
    "ro": "Romanian",
    "rn": "Rundi",
    "ru": "Russian",
    "sm": "Samoan",
    "sg": "Sango",
    "sa": "Sanskrit",
    "sc": "Sardinian",
    "sr": "Serbian",
    "sn": "Shona",
    "sd": "Sindhi",
    "si": "Sinhalese",
    "ss": "Swati",
    "sk": "Slovak",
    "sl": "Slovenian",
    "so": "Somali",
    "st": "Sotho, Southern",
    "es": "Spanish",
    "su": "Sundanese",
    "sw": "Swahili",
    "sv": "Swedish",
    "tl": "Tagalog",
    "ty": "Tahitian",
    "tg": "Tajik",
    "ta": "Tamil",
    "tt": "Tatar",
    "te": "Telugu",
    "th": "Thai",
    "bo": "Tibetan",
    "ti": "Tigrinya",
    "to": "Tonga",
    "ts": "Tsonga",
    "tn": "Tswana",
    "tr": "Turkish",
    "tk": "Turkmen",
    "tw": "Twi",
    "ug": "Uighur",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "uz": "Uzbek",
    "ve": "Venda",
    "vi": "Vietnamese",
    "vo": "Volapük",
    "wa": "Walloon",
    "cy": "Welsh",
    "wo": "Wolof",
    "xh": "Xhosa",
    "yi": "Yiddish",
    "yo": "Yoruba",
    "za": "Zhuang",
    "zu": "Zulu"
}

_GGUF_CANDIDATES = [
    # f32 preferred (highest quality) → f16 → q8 as fallback
    Path(MODEL_PATH).parent / "aarkaa-3b-f32.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-f32.gguf",
    Path(MODEL_PATH).parent / "aarkaa-3b-f16.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-f16.gguf",
    Path(MODEL_PATH).parent / "aarkaa-3b-q8.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-q8.gguf",
]


def _is_ist_nighttime() -> bool:
    from datetime import datetime, timezone, timedelta
    # IST = UTC + 5:30
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    # Nighttime window: 1:00 AM to 7:00 AM IST
    return 1 <= ist_now.hour < 7


def _get_model(force_gpu=True):
    global _model_gpu, _model_coder_gpu, _last_active_time
    if _is_stub:
        return None
    
    _last_active_time = time.time()
    
    # Route to coder model if the request domain is technology (coding/software design)
    is_coder_query = (request_domain.get() == "technology")
    
    if force_gpu:
        if is_coder_query:
            if _model_coder_gpu is None:
                with _model_lock:
                    if _model_coder_gpu is None:
                        from llama_cpp import Llama
                        logger.info("Technology/Coding query detected. Loading Coder GGUF model to GPU...")
                        try:
                            _model_coder_gpu = Llama(
                                model_path=str(_gguf_coder_path),
                                n_ctx=16384,
                                n_threads=_n_threads,
                                n_threads_batch=_n_threads,
                                n_gpu_layers=-1,
                                verbose=False,
                            )
                            logger.info("Coder GGUF model successfully loaded on GPU.")
                        except Exception as e:
                            logger.error("Failed to load Coder GGUF model: %s. Falling back to general model.", e)
                            is_coder_query = False

            if _model_coder_gpu is not None:
                return _model_coder_gpu

        # General model loading (or fallback if coder loading failed)
        if _model_gpu is None:
            with _model_lock:
                if _model_gpu is None:
                    from llama_cpp import Llama
                    logger.info("GPU demand detected. Loading model to GPU (VRAM)...")
                    try:
                        _model_gpu = Llama(
                            model_path=str(_gguf_file_path),
                            n_ctx=16384,
                            n_threads=_n_threads,
                            n_threads_batch=_n_threads,
                            n_gpu_layers=-1,
                            verbose=False,
                        )
                        logger.info("Model successfully loaded on GPU.")
                    except Exception as e:
                        logger.error("Failed to load GPU model: %s. Falling back to CPU.", e)
                        return _model_cpu
        return _model_gpu
    else:
        if is_coder_query and _model_coder_gpu is not None:
            return _model_coder_gpu
        return _model_gpu if _model_gpu is not None else _model_cpu


def _idle_monitor_loop():
    global _model_gpu, _last_active_time
    while True:
        time.sleep(10)
        if _is_stub:
            continue
            
        # Get current time and check if it is nighttime in IST (1:00 AM to 7:00 AM)
        nighttime = _is_ist_nighttime()
        
        if nighttime:
            # During nighttime, offload to CPU if idle longer than timeout
            elapsed = time.time() - _last_active_time
            if (_model_gpu is not None or _model_coder_gpu is not None) and elapsed > _idle_timeout:
                with _model_lock:
                    if (_model_gpu is not None or _model_coder_gpu is not None) and elapsed > _idle_timeout:
                        logger.info("Model idle for %.1f seconds during nighttime IST. Offloading GPU VRAM...", elapsed)
                        try:
                            if _model_gpu is not None:
                                del _model_gpu
                                _model_gpu = None
                            if _model_coder_gpu is not None:
                                del _model_coder_gpu
                                _model_coder_gpu = None
                            try:
                                import torch
                                if torch.cuda.is_available():
                                    torch.cuda.empty_cache()
                            except ImportError:
                                pass
                            gc.collect()
                            logger.info("GPU VRAM cleared successfully. Running on CPU.")
                        except Exception as e:
                            logger.error("Failed to clear GPU model: %s", e)
        else:
            # During daytime, proactively pre-warm/keep the model loaded on the GPU
            if _model_gpu is None:
                with _model_lock:
                    if _model_gpu is None:
                        logger.info("Daytime IST detected. Pre-warming model on GPU for instant responses...")
                        try:
                            from llama_cpp import Llama
                            _model_gpu = Llama(
                                model_path=str(_gguf_file_path),
                                n_ctx=16384,
                                n_threads=_n_threads,
                                n_threads_batch=_n_threads,
                                n_gpu_layers=-1,
                                verbose=False,
                            )
                            logger.info("Model successfully pre-warmed on GPU.")
                        except Exception as e:
                            logger.error("Failed to pre-warm GPU model: %s", e)



def init():
    """Load the AARKAA-3B GGUF model if available on CPU permanently."""
    global _model_cpu, _is_stub, _gguf_file_path

    gguf_file = None
    for candidate in _GGUF_CANDIDATES:
        if candidate.exists():
            gguf_file = candidate
            break

    if gguf_file is None:
        logger.warning("GGUF model not found - running in STUB mode.")
        _is_stub = True
        return

    _gguf_file_path = gguf_file

    try:
        from llama_cpp import Llama
        logger.info("Initializing AARKAA-3B CPU model from %s (threads=%d)", gguf_file, _n_threads)
        _model_cpu = Llama(
            model_path=str(gguf_file),
            n_ctx=16384,
            n_threads=_n_threads,
            n_threads_batch=_n_threads,
            n_gpu_layers=0,
            verbose=False,
        )
        _is_stub = False
        logger.info("AARKAA-3B CPU model loaded permanently.")
        
        # Start idle monitor thread
        t = threading.Thread(target=_idle_monitor_loop, daemon=True)
        t.start()
        logger.info("Idle monitor thread started with timeout %d seconds.", _idle_timeout)
    except Exception as exc:
        logger.error("Failed to load AARKAA-3B CPU model: %s - falling back to stub", exc)
        _is_stub = True

def _classify_and_plan(query: str) -> dict:
    """Classifies a query and structures a basic query routing plan."""
    from modules import semantic_filter
    classification = semantic_filter.classify(query)
    # Map domain names to structure expected by pipeline and verifiers
    domain = classification.get("domain", "general")
    if domain == "technology":
        domain = "coding"
    
    return {
        "domain": domain,
        "intent": classification.get("intent", "general_query"),
        "confidence": classification.get("confidence", 0.5),
        "type": "fact_lookup" if classification.get("intent") in ["web_lookup", "news_search"] else "reasoning"
    }


def get_last_metrics() -> dict:
    """Returns the metrics of the last model inference execution."""
    try:
        from modules.aarkaa_engine import _last_pipeline_metrics
        return _last_pipeline_metrics
    except Exception:
        return {
            "verifier_passed": True,
            "confidence": 0.9,
            "latency": 0.0
        }


def _has_repetition(text: str) -> bool:
    """Returns True if a sequence of words is repeated consecutively, indicating a loop."""
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    n = len(words)
    if n < 16:
        return False
    
    # Check for consecutive repetition of windows of size w (from 8 to 50 words)
    # e.g., if words[-w:] == words[-2w:-w]
    for w in range(8, min(50, n // 2 + 1)):
        if words[-w:] == words[-2*w:-w]:
            return True
    return False


def _build_chatml(system: str, user: str) -> str:
    """Wrap system and user prompts into standard Qwen2 ChatML format."""
    return f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"


def _build_chatml_multi(system: str, history: list[dict] | None, user: str,
                       max_history_chars: int = 3000, user_facts: str = "") -> str:
    """Build ChatML format with system message, multi-turn history, and current user prompt.
    
    Truncates history starting from the OLDEST messages to fit within max_history_chars.
    Does NOT append ellipsis '…' to avoid model copy-cat behavior leading to early halts.
    """
    sys_block = system
    if user_facts:
        sys_block = f"{system}\n\n{user_facts}"
    prompt = f"<|im_start|>system\n{sys_block}<|im_end|>\n"
    if history:
        entries = []
        current_len = 0
        # Iterate backwards (newest first) to ensure the latest conversation turns are kept
        for msg in reversed(history):
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg["message"]
            # Cleanly limit extremely long individual messages without adding ellipsis
            if len(content) > 2000:
                content = content[:2000]
            entry = f"<|im_start|>{role}\n{content}<|im_end|>\n"
            if current_len + len(entry) > max_history_chars:
                break
            entries.append(entry)
            current_len += len(entry)
        # Restore chronological order for the final prompt context
        prompt += "".join(reversed(entries))
    prompt += f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    return prompt


def _get_temperature(query: str, intent: str, context: str = "") -> float:
    """Determine dynamic generation temperature based on task/intent."""
    q_low = query.lower()
    
    # 1. Reasoning / Math (temp: 0.0)
    # Check intent first
    if intent == "reasoning_puzzle" or "reasoning" in intent:
        return 0.0
    
    # Look for common reasoning / puzzle patterns
    reasoning_keywords = [
        "weigh", "scale", "balance", "heavier", "lighter", "outlier", "ball", "balls", "coin", "coins", "marble", "marbles",
        "clock", "angle", "hand", "hands", "hour hand", "minute hand",
        "overtake", "runner", "race", "position",
        "lily pad", "double", "doubles every",
        "bat and ball", "farmer", "sheep", "cabbage", "crossing the river", "boat",
        "how old is", "age", "brother", "sister", "fraction", "percentage gain", "percentage loss",
        "puzzle", "riddle", "logic question", "math problem", "solve for x"
    ]
    
    has_math_operator = any(c in q_low for c in ["+", "*", "/", "=", "^"])
    if not has_math_operator and "-" in q_low:
        import re
        # check if '-' is part of a subtraction or negative number
        if re.search(r"\d\s*-\s*\d", q_low) or re.search(r"\b-\s*\d", q_low) or " - " in q_low:
            has_math_operator = True
            
    if any(w in q_low for w in reasoning_keywords) or has_math_operator:
        # Make sure it's not a code block or coding question
        if not ("def " in q_low or "import " in q_low or "class " in q_low or "```" in q_low):
            return 0.0

    # 2. Coding (temp: 0.2 in range 0.1 - 0.3)
    coding_keywords = ["program", "function", "script", "implement", "debug", "compile", "run", "trace", "execute", "output"]
    is_code = intent == "coding_help" or any(w in q_low for w in coding_keywords) or "```" in query or any(p in q_low for p in ["def ", "import ", "class ", "fn ", "public class ", "console.log"])
    if not is_code and "write" in q_low:
        coding_contexts = ["code", "function", "script", "program", "python", "javascript", "java", "c++", "rust", "html", "css", "sql", "class"]
        if any(c in q_low for c in coding_contexts):
            is_code = True
            
    if is_code:
        return 0.2

    # 3. Finance (temp: 0.15 in range 0.1 - 0.2)
    is_finance = (
        intent.startswith("finance") 
        or intent in ["price_check", "comparison"] 
        or "[Finance Data]" in context 
        or "[Technical Analysis]" in context 
        or "[Options Strategy]" in context
        or any(w in q_low for w in ["stock", "price", "market", "share", "crypto", "bitcoin", "dividend", "revenue", "ebitda", "fcf", "ticker"])
    )
    if is_finance:
        return 0.15

    # 4. Creative Writing (temp: 0.9 in range 0.8 - 1.0)
    creative_words = [
        "story", "poem", "poetry", "essay", "song", "lyrics", "joke", "creative", 
        "compose", "draft", "write a story", "write a poem", "write an essay", 
        "write a joke", "write a song", "write lyrics", "haiku", "limerick", 
        "fiction", "novel", "play", "dialogue", "speech", "letter", "email", 
        "congratulate", "greeting card", "rewrite", "paraphrase"
    ]
    if any(w in q_low for w in creative_words):
        return 0.9

    # 5. General Chat (temp: 0.7 in range 0.6 - 0.7)
    return 0.7


def _generate(prompt, max_new_tokens=150, stop=None, temperature=0.7):
    """Run generation via llama.cpp."""
    model_instance = _get_model(force_gpu=True)
    if _is_stub or model_instance is None:
        return _stub_response(prompt)
    
    tokens = list(_generate_stream(prompt, max_new_tokens=max_new_tokens, stop=stop, temperature=temperature))
    text = "".join(tokens).strip()
    if not text:
        logger.warning("_generate: model returned empty output — context overflow or KV cache failure. Returning stub fallback.")
        return _stub_response(prompt)
    return _clean_response(text)


def _generate_stream(prompt, max_new_tokens=150, stop=None, temperature=0.7):
    """Run generation via llama.cpp and yield tokens with repetition guard."""
    model_instance = _get_model(force_gpu=True)
    if _is_stub or model_instance is None:
        yield _stub_response(prompt)
        return

    stop_tokens = [
        "<|im_end|>", "<|im_start|>", "<|endoftext|>"
    ]
    if stop:
        stop_tokens.extend(stop)

    stream = model_instance(
        prompt,
        max_tokens=max_new_tokens,
        temperature=temperature,
        top_p=0.9,
        repeat_penalty=1.0 if temperature < 0.1 else 1.15,
        stop=stop_tokens,
        stream=True
    )
    generated_text = ""
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            generated_text += token
            if _has_repetition(generated_text):
                logger.warning("Repetition loop detected; terminating stream early to protect response.")
                break
            yield token


def _truncate_agent_prompt(prompt_str: str, model_instance) -> str:
    """If the agent prompt exceeds 5500 tokens, run the 5-layer context compaction pipeline."""
    from modules.context_compaction import compact_prompt
    return compact_prompt(prompt_str, model_instance, max_tokens=5500)


def generate_raw(prompt, max_new_tokens=300, stop=None):
    """Raw generation for the agent loop (no truncation) with safe streaming stop word checks."""
    model_instance = _get_model(force_gpu=True)
    if _is_stub or model_instance is None:
        return 'Final Answer: I am running in stub mode.'
    
    if stop is None:
        stop = []

    native_stop = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
    
    # Truncate prompt if it is too long to prevent context overflow
    prompt = _truncate_agent_prompt(prompt, model_instance)
    
    # Tokenize prompt to get exact prompt token count and pass tokens directly
    prompt_tokens = model_instance.tokenize(prompt.encode("utf-8"), special=True)
    prompt_len = len(prompt_tokens)
    
    # Context limit is 16384. Set max_tokens to fill remaining context window completely (leaving a small 100-token safety buffer)
    max_tokens = 16384 - prompt_len - 100
    if max_tokens <= 0:
        max_tokens = 1
        
    stream = model_instance(
        prompt,
        max_tokens=max_tokens,
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.1,
        stop=native_stop,
        stream=True
    )

    
    generated_text = ""
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            generated_text += token
            # Check for custom stop sequences streamingly
            for stop_word in stop:
                if stop_word in generated_text:
                    idx = generated_text.index(stop_word)
                    return generated_text[:idx].strip()
            
            # Auto-stop after Action Input line is completed to prevent hallucination
            if "action input:" in generated_text.lower():
                ai_idx = generated_text.lower().index("action input:")
                json_part = generated_text[ai_idx:]
                import json
                start_idx = json_part.find("{")
                if start_idx != -1:
                    # Search backwards for a valid JSON object
                    for i in range(len(json_part) - 1, start_idx, -1):
                        if json_part[i] == "}":
                            try:
                                json.loads(json_part[start_idx:i+1])
                                # If it successfully parses as valid JSON, and a newline exists after the object
                                if "\n" in json_part[i+1:]:
                                    return generated_text[:ai_idx + i + 1].strip()
                            except json.JSONDecodeError:
                                pass

            if _has_repetition(generated_text):
                break
    result = generated_text.strip()
    if not result:
        logger.warning("generate_raw: model returned empty output — possible KV cache overflow (max_tokens=%d, prompt_len=%d). Returning stub.", max_tokens, prompt_len)
        return "I was unable to generate a response. Please try rephrasing your query."
    return result


def _is_list_header(text, pos):
    # pos is the index of '.'
    i = pos - 1
    while i >= 0 and text[i].isdigit():
        i -= 1
    if i < pos - 1:
        # Digits found. Check if preceded by a newline (possibly with space) or start of text
        prefix = text[:i + 1]
        if not prefix.strip():
            return True
        # Check if the prefix ends with a newline character, possibly followed by spaces
        stripped_len = len(prefix) - len(prefix.rstrip(' '))
        if stripped_len > 0:
            prefix = prefix[:-stripped_len]
        if prefix and prefix[-1] == '\n':
            return True
    return False


def _clean_response(text):
    """Truncate at the last complete sentence to avoid unfinished answers."""
    if not text:
        return text
    
    # Strip out hallucinated markers
    text = text.replace("[end of web search results]", "").strip()
    text = text.replace("[End of web search results]", "").strip()

    # Programmatically strip common email/letter salutations and sign-offs
    lines = text.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    greetings_to_remove = ["dear reader", "dear user", "hello reader", "hello user", "dear friend"]
    if lines:
        import re
        first_line_clean = re.sub(r'[^\w\s]', '', lines[0].lower()).strip()
        if any(first_line_clean.startswith(g) for g in greetings_to_remove):
            lines.pop(0)

    signoffs_to_remove = ["sincerely", "best regards", "regards", "yours truly"]
    if lines:
        import re
        last_line_clean = re.sub(r'[^\w\s]', '', lines[-1].lower()).strip()
        if any(last_line_clean.startswith(s) for s in signoffs_to_remove):
            lines.pop()
            if lines:
                next_last_line = re.sub(r'[^\w\s]', '', lines[-1].lower()).strip()
                if "your name" in next_last_line or "aarkaa" in next_last_line:
                    lines.pop()

    text = '\n'.join(lines).strip()

    # Do not truncate if text contains code blocks to avoid corrupting code syntax.
    if "```" in text:
        # If the code block is unclosed, close it cleanly
        if text.count("```") % 2 != 0:
            return text + "\n```"
        return text

    import re
    # Remove trailing unfinished list headers or newlines (e.g. \n\n7. or \n-)
    text = re.sub(r'\n+\s*(?:-|\*|\d+\.)\s*$', '', text)
        
    # If it naturally ends in a punctuation mark (and isn't a dangling list number like "5."), leave it alone!
    if text[-1] in ".!?" and not (text[-1] == "." and len(text) > 1 and text[-2].isdigit()):
        return text

    # For step-by-step content (has numbered steps like "Step 1:", "1.", "2."),
    # preserve all complete steps instead of truncating aggressively
    has_numbered_steps = bool(re.search(r'\n\s*(?:Step\s+)?\d+[\.\):]', text))
    
    if has_numbered_steps:
        # Find the last complete step (ends with sentence-ending punctuation before next step or end)
        step_matches = list(re.finditer(r'\n\s*(?:Step\s+)?\d+[\.\):]', text))
        if len(step_matches) >= 2:
            # Check if the last step appears incomplete (no sentence-ending punctuation at the very end)
            last_step_start = step_matches[-1].start()
            last_step_text = text[last_step_start:]
            # If the last step has proper ending punctuation, keep everything
            if last_step_text.rstrip()[-1] in '.!?':
                return text
            # Otherwise, truncate to end of second-to-last step
            return text[:last_step_start].rstrip()
        return text + "."

    # Otherwise, find the latest complete sentence ending
    best_pos = -1
    for end_char in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
        pos = text.rfind(end_char)
        while pos > best_pos:
            # If the period is part of a list header, ignore it and search backwards
            if end_char in [". ", ".\n"] and _is_list_header(text, pos):
                pos = text.rfind(end_char, 0, pos)
                continue
            best_pos = pos
            break
            
    if best_pos > len(text) * 0.3:
        return text[:best_pos + 1]
            
    return text + "."



def _stub_response(query, context=""):
    """Placeholder response when model is unavailable."""
    if context:
        # Prioritize finance data over stale conversation history
        if "[Finance Data]" in context:
            # Extract the finance section specifically
            fin_start = context.index("[Finance Data]")
            fin_end = context.find("\n\n---\n\n", fin_start)
            finance_section = context[fin_start:fin_end] if fin_end > 0 else context[fin_start:]
            return (
                "Here is the latest live financial data:\n\n"
                + finance_section.strip()
            )
        elif "[Web Search Results]" in context or "[Web Search]" in context:
            return (
                "Here are the search results matching your query:\n\n"
                + context[:1500].strip()
            )
        else:
            return context[:1500].strip()

    return (
        '[AARKAA-3B Stub] I received your query: "' + query + '". '
        "The full AARKAA-3B model is not loaded; this is a placeholder response."
    )


def primary_check(query, lang="en"):
    """Quick first-pass answer. Returns (response, confidence)."""
    if _is_stub:
        return _stub_response(query), 0.3

    try:
        q_lower = query.lower()
        lang_name = _LANG_NAMES.get(lang, "English")

        # Detect self-referential questions about AARKAA itself
        _self_keywords = [
            "security feature", "built-in", "your feature", "your capabilit",
            "what can you", "about yourself", "about aark", "about you",
            "how do you work", "your architecture", "what are you",
            "your security", "are you safe", "how are you built",
            "aarka ai capabilit", "aarkaa capabilit", "explain aarka",
            "who are you", "what is aarka", "what is aarkaai",
            "your name", "what is your name", "who is aarka"
        ]
        is_self = any(kw in q_lower for kw in _self_keywords)

        import re
        is_chat_or_greeting = any(
            re.search(r"\b" + re.escape(w) + r"\b", q_lower)
            for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you"]
        )

        if is_chat_or_greeting:
            system_prompt = "You are AARKAA, a highly intelligent, warm and friendly AI assistant."
            user_prompt = f"Respond naturally and warmly to the user: {query}"
            if lang != "en":
                user_prompt += f"\n\nYou MUST respond ONLY in the following language: {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = 500
        elif is_self:
            system_prompt = (
                "You are AARKAA (Autonomous Adaptive Reasoning Kernel for Augmented AI), "
                "a production-grade AI assistant built by Synthetix Analytics.\n\n"
                "Your details:\n"
                "Capabilities:\n"
                "- Multilingual responses (auto-detects user language)\n"
                "- Real-time web search via DuckDuckGo and Wikipedia\n"
                "- Code writing, testing, and execution via BashTool\n"
                "- File read/write operations in a sandboxed workspace\n"
                "- RAG (Retrieval-Augmented Generation) from a local knowledge base\n"
                "- Conversation memory and context continuity\n"
                "- Real-time finance/market data retrieval via Yahoo Finance\n"
                "- Autonomous agent mode with ReAct reasoning loop\n\n"
                "Security Features:\n"
                "- API Key authentication for all endpoints\n"
                "- Per-IP rate limiting to prevent abuse\n"
                "- Sandboxed code execution with a blocklist of dangerous operations\n"
                "- Command timeout enforcement to prevent infinite loops\n"
                "- CORS origin whitelisting\n"
                "- Request tracking and logging with unique request IDs\n"
                "- Circuit breakers on external services (web search, finance API) to gracefully handle failures\n"
                "- Input sanitization and prompt injection guards."
            )
            user_prompt = (
                f"Write a direct, elegant response to: '{query}'.\n"
                "Format the capabilities as a beautiful, sequentially numbered list (1, 2, 3, 4...) and security features as a bulleted list.\n"
                "Highlight the important terms using bold markdown (e.g. **Real-time web search**).\n"
                "Do NOT write any introductory or conversational filler like 'Sure, here is...'. Just output the headings and the lists directly."
            )
            if lang != "en":
                user_prompt += f"\nYou MUST write your entire response ONLY in {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = MAX_TOKENS
        elif any(w in q_lower for w in ["code", "program", "function", "script", "write", "implement", "create a"]):
            system_prompt = (
                "You are AARKAA, an expert programming AI assistant."
            )
            user_prompt = f"Request: {query}\n\nProvide working code with a brief explanation."
            if lang != "en":
                user_prompt += f" You MUST respond ONLY in the following language: {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = MAX_TOKENS
        else:
            is_step_by_step = any(w in query.lower() for w in ["step by step", "recipe", "detailed", "how to make", "how to build", "guide"])
            is_design_query = any(w in query.lower() for w in ["design a", "design an", "system design", "architecture", "explain:"]) or (
                all(w in query.lower() for w in ["gpu", "schedul", "queu", "cost", "isolation"])
            )
            
            if is_design_query:
                system_prompt = (
                    "You are AARKAA, a principal systems architect. "
                    "Provide a comprehensive, production-grade technical design architecture. "
                    "Detail every requested component in depth with clear headers, technical details, and structured analysis."
                )
                user_prompt = (
                    f"Design and explain the following architecture request: {query}\n\n"
                    "IMPORTANT: Provide a detailed, comprehensive architectural layout. "
                    "Explain each requirement/component thoroughly in its own section. "
                    "Do NOT write conversational filler. Do NOT stop early or truncate the explanation."
                )
            elif is_step_by_step:
                system_prompt = (
                    "You are AARKAA, a helpful and precise AI assistant. "
                    "You cannot predict the future price of financial products or speculative assets (stocks, cryptocurrencies, commodities, etc.). "
                    "If the user asks for a future price prediction or forecast, you must politely decline, explaining that future market behavior is speculative and unpredictable."
                )
                user_prompt = f"Answer the following question by providing a detailed, step-by-step explanation or recipe with clear headings and sequential numbers (Step 1, Step 2, etc.): {query}\n\n"
            else:
                system_prompt = (
                    "You are AARKAA, a helpful and precise AI assistant. "
                    "You cannot predict the price of financial assets. If the user asks for future forecasts, decline."
                )
                user_prompt = f"Answer the following question: {query}\n\n"
            if lang != "en":
                user_prompt += f"You MUST write your response ONLY in the following language: {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = MAX_TOKENS
        temp = _get_temperature(query, "general_query")
        response = _generate(prompt, max_new_tokens=tokens, temperature=temp)
        confidence = min(0.9, 0.5 + len(response.split()) / 150)
        return response, confidence
    except Exception as exc:
        logger.error("primary_check failed: %s", exc)
        return _stub_response(query), 0.3


def self_check_response(query: str, response: str, intent: str) -> bool:
    """Audit the generated response against user intent using the local model."""
    model_instance = _get_model(force_gpu=True)
    if _is_stub or model_instance is None:
        return True

    if intent not in ["persuasion", "debate", "comparison"]:
        return True

    criteria = ""
    if intent == "persuasion":
        criteria = "The user requested persuasion (convince them). Did the response focus on persuasion/argument, or did it write a how-to guide/instructions/steps?"
    elif intent == "debate":
        criteria = "The user requested a debate argument. Did the response debate the position, or did it write a how-to guide/instructions/steps?"
    elif intent == "comparison":
        criteria = "The user requested a comparison. Did the response compare the concepts, or did it write a how-to guide/instructions/steps?"

    audit_prompt = (
        "<|im_start|>system\n"
        "You are Aarkaa AI, a strict response quality auditor. "
        "Your task is to determine if a generated response matches the user's intent or mistakenly outputs a how-to/instructional guide instead.\n"
        "Respond with exactly 'PASS' or 'FAIL'. Do NOT write any other words or explanations.<|im_end|>\n"
        f"<|im_start|>user\n"
        f"User Request: {query}\n"
        f"Generated Response: {response}\n\n"
        f"Auditing Criteria: {criteria}\n"
        "Does the response match the intent (PASS) or is it a how-to/step guide (FAIL)?<|im_end|>\n"
        "<|im_start|>assistant\n"
    )

    try:
        output = model_instance(
            audit_prompt,
            max_tokens=5,
            temperature=0.0,
            stop=["<|im_end|>", "<|im_start|>"]
        )
        decision = output["choices"][0]["text"].strip().upper()
        logger.info("Self-Check Auditor decision: %s for intent: %s", decision, intent)
        return "FAIL" not in decision
    except Exception as exc:
        logger.warning("Self-check failed to evaluate: %s", exc)
        return True


def final_response(query, context, intent="", lang="en", mode="production", history=None, user_facts=""):
    """Full reasoning pass with fused context from external modules."""
    if _is_stub:
        return _stub_response(query, context)

    feedback = ""
    answer = ""
    for attempt in range(2):
        try:
            result = _build_final_prompt(query, context, intent, lang, mode, history=history, user_facts=user_facts)
            prompt, tokens = result[0], result[1]
            temp = result[2] if len(result) > 2 else 0.7
            
            if feedback:
                # Append corrective instruction feedback to the user role block
                prompt_parts = prompt.split("<|im_start|>user\n")
                if len(prompt_parts) > 1:
                    user_block = prompt_parts[-1]
                    user_block_parts = user_block.split("<|im_end|>\n<|im_start|>assistant\n")
                    if len(user_block_parts) > 0:
                        user_block_parts[0] += f"\n\nCorrection Note: {feedback}"
                        prompt_parts[-1] = "<|im_end|>\n<|im_start|>assistant\n".join(user_block_parts)
                        prompt = "<|im_start|>user\n".join(prompt_parts)
            
            prompt_len = len(prompt)
            logger.info("final_response (attempt %d): prompt_len=%d chars, max_tokens=%d, temp=%.2f", attempt + 1, prompt_len, tokens, temp)
            if prompt_len > 6000:
                logger.warning("Prompt too long (%d chars) — rebuilding without history to prevent context overflow", prompt_len)
                result = _build_final_prompt(query, context, intent, lang, mode, history=None, user_facts=user_facts)
                prompt, tokens = result[0], result[1]
                temp = result[2] if len(result) > 2 else 0.7
            
            answer = _generate(prompt, max_new_tokens=tokens, temperature=temp)
            
            # Audit the response
            if self_check_response(query, answer, intent):
                return answer
            
            logger.warning("Self-check failed on attempt %d for intent %s. Retrying...", attempt + 1, intent)
            feedback = "Your previous attempt was a how-to guide / list of steps. Please rewrite to be a direct persuasive argument/debate as requested. Do NOT list steps."
            
        except Exception as exc:
            logger.error("final_response failed on attempt %d: %s", attempt + 1, exc)
            if attempt == 1:
                return _stub_response(query, context)

    if not answer or not answer.strip():
        logger.warning("final_response: all attempts returned empty output. Returning stub fallback.")
        return _stub_response(query, context)
    return answer


def stream_final_response(query, context, intent="", lang="en", mode="production", history=None, user_facts=""):
    """Stream tokens for the final response pass."""
    if _is_stub:
        yield _stub_response(query, context)
        return

    try:
        result = _build_final_prompt(query, context, intent, lang, mode, history=history, user_facts=user_facts)
        prompt, tokens = result[0], result[1]
        temp = result[2] if len(result) > 2 else 0.7
        
        # Safety check: if prompt is too long, rebuild without history
        prompt_len = len(prompt)
        logger.info("stream_final_response: prompt_len=%d chars, max_tokens=%d, temp=%.2f", prompt_len, tokens, temp)
        if prompt_len > 6000:
            logger.warning("Prompt too long (%d chars) — rebuilding without history to prevent context overflow", prompt_len)
            result = _build_final_prompt(query, context, intent, lang, mode, history=None, user_facts=user_facts)
            prompt, tokens = result[0], result[1]
            temp = result[2] if len(result) > 2 else 0.7
            logger.info("Rebuilt prompt: %d chars", len(prompt))
        
        yield from _generate_stream(prompt, max_new_tokens=tokens, temperature=temp)
    except Exception as exc:
        logger.error("stream_final_response failed: %s", exc)
        yield _stub_response(query, context)


def _filter_history_repeats(query: str, history: list[dict] | None) -> list[dict] | None:
    if not history:
        return history
    
    clean_q = "".join(c for c in query.lower() if c.isalnum())
    filtered_history = []
    
    i = 0
    while i < len(history):
        msg = history[i]
        if msg.get("role") == "user":
            hist_q = "".join(c for c in msg.get("message", "").lower() if c.isalnum())
            if hist_q == clean_q or (len(hist_q) > 10 and (hist_q in clean_q or clean_q in hist_q)):
                i += 1
                if i < len(history) and history[i].get("role") == "assistant":
                    i += 1
                continue
        filtered_history.append(msg)
        i += 1
        
    return filtered_history if filtered_history else None


def _filter_history_reasoning(query: str, history: list[dict] | None) -> list[dict] | None:
    if not history:
        return history
    
    import re
    q_words = set(re.findall(r"\w+", query.lower()))
    weighing_kws = {"weigh", "scale", "balance", "heavier", "lighter", "outlier", "ball", "balls", "coin", "coins", "marble", "marbles"}
    clock_kws = {"clock", "angle", "hand", "hands", "time", "hour", "minute"}
    race_kws = {"race", "position", "overtake", "runner", "runners", "second", "last"}
    
    is_q_weighing = bool(q_words & weighing_kws)
    is_q_clock = bool(q_words & clock_kws)
    is_q_race = bool(q_words & race_kws)
    
    filtered_history = []
    for msg in history:
        msg_text = msg.get("message", "").lower()
        msg_words = set(re.findall(r"\w+", msg_text))
        is_msg_weighing = bool(msg_words & weighing_kws)
        is_msg_clock = bool(msg_words & clock_kws)
        is_msg_race = bool(msg_words & race_kws)
        
        if is_q_weighing and is_msg_weighing:
            filtered_history.append(msg)
        elif is_q_clock and is_msg_clock:
            filtered_history.append(msg)
        elif is_q_race and is_msg_race:
            filtered_history.append(msg)
            
    return filtered_history if filtered_history else None


def _build_final_prompt(query, context, intent="", lang="en", mode="production", history=None, user_facts=""):
    global_build_chatml = globals()["_build_chatml"]
    global_build_chatml_multi = globals()["_build_chatml_multi"]

    # Determine alignment instructions
    alignment_instruction = ""
    q_low = query.lower()
    if "hindi alpaca" in q_low or "hindi-alpaca" in q_low:
        alignment_instruction = (
            "You are operating in the 'Hindi Alpaca' alignment model state. "
            "Respond in natural, grammatically correct, and highly precise instruction-following Hindi. "
            "Adopt the voice and capabilities of the Hindi Alpaca model."
        )
    elif "tamil alpaca" in q_low or "tamil-alpaca" in q_low:
        alignment_instruction = (
            "You are operating in the 'Tamil Alpaca' alignment model state. "
            "Respond in native, grammatically correct, and highly precise instruction-following Tamil. "
            "Adopt the voice and capabilities of the Tamil Alpaca model."
        )
    elif "samanantar" in q_low:
        alignment_instruction = (
            "You are operating in the 'Samanantar Hindi' alignment model state. "
            "Act as the Samanantar Hindi translation engine based on IIT Madras parallel corpora. "
            "Perform highly accurate parallel English-to-Hindi translations, preserving sentence structures, "
            "clause correspondence, and exact technical terminology mappings."
        )
    elif "aya" in q_low:
        alignment_instruction = (
            "You are operating in the 'Aya (Indian Languages)' alignment model state. "
            "Act as Cohere's multilingual model focusing on Indian languages. "
            "Generate rich, culturally aligned, contextually nuanced, and highly fluent responses or translations in the target Indian language."
        )

    def _build_chatml(system: str, user: str) -> str:
        if alignment_instruction:
            system = system + "\n\n" + alignment_instruction
        return global_build_chatml(system, user)

    def _build_chatml_multi(system: str, history: list[dict] | None, user: str,
                           max_history_chars: int = 3000, user_facts: str = "") -> str:
        if alignment_instruction:
            system = system + "\n\n" + alignment_instruction
        return global_build_chatml_multi(system, history, user, max_history_chars, user_facts)

    history = _filter_history_repeats(query, history)
    if intent == "reasoning_puzzle":
        history = _filter_history_reasoning(query, history)
    lang_name = _LANG_NAMES.get(lang, "English")
    is_continue = query.lower().strip() in ["continue", "next phase", "continue code", "continue the code", "go on"]
    if is_continue:
        if lang != "en":
            system_prompt = (
                "You are AARKAA, a highly intelligent programming and multilingual AI assistant.\n"
                f"You MUST write your entire response ONLY in the following language: {lang_name}."
            )
        else:
            system_prompt = "You are AARKAA, a highly intelligent programming AI assistant."
        user_prompt = "The previous response was cut off due to token limits. Complete the previous response starting from exactly where it was truncated."
        if context:
            user_prompt += "\n\nContext:\n" + context
        prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
        tokens = 3000
        return prompt, tokens, 0.7

    is_reasoning = (intent == "reasoning_puzzle")
    if is_reasoning:
        is_benchmark = (mode == "benchmark")
        if is_benchmark:
            system_prompt = (
                "You are AARKAA, a precise step-by-step reasoning assistant.\n\n"
                "Reference rules and formulas for logic, math, and positional puzzles:\n"
                "1. Clock Angle Puzzles (for Time H:M):\n"
                "   - Hour hand position (degrees from 12) = (30 * H) + (0.5 * M)\n"
                "   - Minute hand position (degrees from 12) = 6 * M\n"
                "   - Angle between hands = |Hour hand position - Minute hand position|\n"
                "   - If the angle is greater than 180 degrees, the smaller angle is (360 - angle).\n"
                "2. Interval Counting (Fence Post Problem):\n"
                "   - N events at regular intervals have (N-1) intervals. Total time/distance = (N-1) * interval length.\n"
                "3. Doubling Growth Puzzles:\n"
                "   - If a quantity doubles every day and is full on day D, it was half-full on day (D - 1).\n"
                "4. Race and Positional Puzzles:\n"
                "   - Overtaking the N-th person in a race: You take their place and become N-th (e.g., overtaking the 2nd person makes you 2nd, not 1st).\n"
                "5. Heads and Legs Puzzles (Two-Variable Linear Systems):\n"
                "   - Let X be the number of 2-legged animals (e.g. chickens) and Y be the number of 4-legged animals (e.g. cows, rabbits).\n"
                "   - Equation 1 (Total Heads): X + Y = Total Heads\n"
                "   - Equation 2 (Total Legs): 2*X + 4*Y = Total Legs\n"
                "   - Solve: Y = (Total Legs - 2 * Total Heads) / 2, and X = Total Heads - Y\n"
                "6. Wheels and Vehicles Puzzles:\n"
                "   - Let X be 2-wheeled vehicles (e.g. motorcycles) and Y be 4-wheeled vehicles (e.g. cars).\n"
                "   - Equation 1 (Total Vehicles): X + Y = Total Vehicles\n"
                "   - Equation 2 (Total Wheels): 2*X + 4*Y = Total Wheels\n"
                "   - Solve: Y = (Total Wheels - 2 * Total Vehicles) / 2, and X = Total Vehicles - Y\n"
                "7. Percentage Gain/Loss Return Puzzles (Value Recovery):\n"
                "   - If a value or stock falls by D% (where 0 < D < 100), the required percentage gain to return to the original price is: Gain % = (D / (100 - D)) * 100\n"
                "   - Example (75% drop): Gain % = (75 / (100 - 75)) * 100 = (75 / 25) * 100 = 300% gain.\n"
                "   - If a value or stock rises by R%, the required percentage loss to return to the original price is: Loss % = (R / (100 + R)) * 100\n"
                "   - Example (100% rise): Loss % = (100 / (100 + 100)) * 100 = (100 / 200) * 100 = 50% loss.\n"
                "8. Scale Weighing Puzzles (e.g., Finding Heavier/Lighter Outlier):\n"
                "   - To find 1 heavier/lighter outlier among N items in minimum weighings, divide the items into 3 groups (Group A, Group B, and Group C). Group A and Group B must have the exact same size (the closest integer to N/3), and Group C has the remainder (N - 2 * size). For example, for 8 items, Group A and Group B must have exactly 3 items each, and Group C has exactly 2 items.\n"
                "   - Example (8 items, 1 heavier, 2 weighings):\n"
                "     - Weighing 1: Weigh Group A (3 items) against Group B (3 items). Group C has 2 items.\n"
                "       - Case 1 (Group A and Group B balance): The heavier item is in Group C (which has 2 items).\n"
                "         - Weighing 2: Weigh the 2 items of Group C against each other. The heavier one on the scale is the heavier item.\n"
                "       - Case 2 (Group A is heavier): The heavier item is in Group A (which has 3 items).\n"
                "         - Weighing 2: Choose 2 items from Group A and weigh them against each other. If they balance, the 3rd unweighed item of Group A is the heavier one. If they do not balance, the heavier one on the scale is the heavier item.\n"
                "       - Case 3 (Group B is heavier): The heavier item is in Group B (which has 3 items).\n"
                "         - Weighing 2: Choose 2 items from Group B and weigh them against each other. If they balance, the 3rd unweighed item of Group B is the heavier one. If they do not balance, the heavier one on the scale is the heavier item.\n"
                "   - CRITICAL RULES FOR WEIGHING PUZZLES:\n"
                "     1. NO NAMING OR NUMBERING: Do NOT assign specific numbers, letters, or names (e.g., 'Ball 1', 'Ball 2', 'Ball 5', 'Ball 6', 'Coin A', 'Coin B') to the individual items unless the input question explicitly names them. Refer to them ONLY as 'Group A items', 'Group B items', 'Group C items', or 'the unweighed item from that group'. Assigning artificial names/numbers causes logical errors and group contamination.\n"
                "     2. STRICT CASE ISOLATION: Each Case is a separate hypothetical universe. In Case 2 (Group A is heavier), the second weighing must ONLY involve items from Group A. You must NEVER reference, weigh, or mix items from Group B or Group C in Case 2. In Case 3 (Group B is heavier), the second weighing must ONLY involve items from Group B, and you must NEVER reference or use items from Group A or Group C. Keep the branches completely independent.\n\n"
                "To solve: First, identify which of the reference categories/rules applies to the question (e.g. Scale Weighing Puzzles). Explicitly state the category name and the rule/formula. Then, apply the rule step-by-step to the specific numbers in the question. Verify your logic at each step: double-check that you do not introduce contradictions (e.g., if Group A is heavier, Weighing 2 must only involve Group A balls, never Group C; if Group B is heavier, Weighing 2 must only involve Group B balls, never Group C). Finally, state the complete and correct solution clearly."
            )
        else:
            system_prompt = (
                "You are AARKAA, a precise step-by-step reasoning assistant.\n\n"
                "Reference rules and formulas for logic, math, and positional puzzles:\n"
                "1. Clock Angle Puzzles (for Time H:M):\n"
                "   - Hour hand position (degrees from 12) = (30 * H) + (0.5 * M)\n"
                "   - Minute hand position (degrees from 12) = 6 * M\n"
                "   - Angle between hands = |Hour hand position - Minute hand position|\n"
                "   - If the angle is greater than 180 degrees, the smaller angle is (360 - angle).\n"
                "2. Interval Counting (Fence Post Problem):\n"
                "   - N events at regular intervals have (N-1) intervals. Total time/distance = (N-1) * interval length.\n"
                "3. Doubling Growth Puzzles:\n"
                "   - If a quantity doubles every day and is full on day D, it was half-full on day (D - 1).\n"
                "4. Race and Positional Puzzles:\n"
                "   - Overtaking the N-th person in a race: You take their place and become N-th (e.g., overtaking the 2nd person makes you 2nd, not 1st).\n"
                "   - Overtaking the last runner: In a straight race, it is logically impossible to overtake the last runner because there is nobody behind the last runner (you would have to be the last runner yourself to be behind them, which is a contradiction). If asked what position you are in after overtaking the last runner, you must explicitly state that the scenario is impossible.\n"
                "5. Heads and Legs Puzzles (Two-Variable Linear Systems):\n"
                "   - Let X be the number of 2-legged animals (e.g. chickens) and Y be the number of 4-legged animals (e.g. cows, rabbits).\n"
                "   - Equation 1 (Total Heads): X + Y = Total Heads\n"
                "   - Equation 2 (Total Legs): 2*X + 4*Y = Total Legs\n"
                "   - Solve: Y = (Total Legs - 2 * Total Heads) / 2, and X = Total Heads - Y\n"
                "6. Wheels and Vehicles Puzzles:\n"
                "   - Let X be 2-wheeled vehicles (e.g. motorcycles) and Y be 4-wheeled vehicles (e.g. cars).\n"
                "   - Equation 1 (Total Vehicles): X + Y = Total Vehicles\n"
                "   - Equation 2 (Total Wheels): 2*X + 4*Y = Total Wheels\n"
                "   - Solve: Y = (Total Wheels - 2 * Total Vehicles) / 2, and X = Total Vehicles - Y\n"
                "7. Percentage Gain/Loss Return Puzzles (Value Recovery):\n"
                "   - If a value or stock falls by D% (where 0 < D < 100), the required percentage gain to return to the original price is: Gain % = (D / (100 - D)) * 100\n"
                "   - Example (75% drop): Gain % = (75 / (100 - 75)) * 100 = (75 / 25) * 100 = 300% gain.\n"
                "   - If a value or stock rises by R%, the required percentage loss to return to the original price is: Loss % = (R / (100 + R)) * 100\n"
                "   - Example (100% rise): Loss % = (100 / (100 + 100)) * 100 = (100 / 200) * 100 = 50% loss.\n"
                "8. Scale Weighing Puzzles (e.g., Finding Heavier/Lighter Outlier):\n"
                "   - To find 1 heavier/lighter outlier among N items in minimum weighings, divide the items into 3 groups (Group A, Group B, and Group C). Group A and Group B must have the exact same size (the closest integer to N/3), and Group C has the remainder (N - 2 * size). For example, for 8 items, Group A and Group B must have exactly 3 items each, and Group C has exactly 2 items.\n"
                "   - Example (8 items, 1 heavier, 2 weighings):\n"
                "     - Weighing 1: Weigh Group A (3 items) against Group B (3 items). Group C has 2 items.\n"
                "       - Case 1 (Group A and Group B balance): The heavier item is in Group C (which has 2 items).\n"
                "         - Weighing 2: Weigh the 2 items of Group C against each other. The heavier one on the scale is the heavier item.\n"
                "       - Case 2 (Group A is heavier): The heavier item is in Group A (which has 3 items).\n"
                "         - Weighing 2: Choose 2 items from Group A and weigh them against each other. If they balance, the 3rd unweighed item of Group A is the heavier one. If they do not balance, the heavier one on the scale is the heavier item.\n"
                "       - Case 3 (Group B is heavier): The heavier item is in Group B (which has 3 items).\n"
                "         - Weighing 2: Choose 2 items from Group B and weigh them against each other. If they balance, the 3rd unweighed item of Group B is the heavier one. If they do not balance, the heavier one on the scale is the heavier item.\n"
                "   - CRITICAL RULES FOR WEIGHING PUZZLES:\n"
                "     1. NO NAMING OR NUMBERING: Do NOT assign specific numbers, letters, or names (e.g., 'Ball 1', 'Ball 2', 'Ball 5', 'Ball 6', 'Coin A', 'Coin B') to the individual items unless the input question explicitly names them. Refer to them ONLY as 'Group A items', 'Group B items', 'Group C items', or 'the unweighed item from that group'. Assigning artificial names/numbers causes logical errors and group contamination.\n"
                "     2. STRICT CASE ISOLATION: Each Case is a separate hypothetical universe. In Case 2 (Group A is heavier), the second weighing must ONLY involve items from Group A. You must NEVER reference, weigh, or mix items from Group B or Group C in Case 2. In Case 3 (Group B is heavier), the second weighing must ONLY involve items from Group B, and you must NEVER reference or use items from Group A or Group C. Keep the branches completely independent.\n\n"
                "To solve: First, identify which of the reference categories/rules applies to the question (e.g. Scale Weighing Puzzles). Explicitly state the category name and the rule/formula. Then, apply the rule step-by-step to the specific numbers in the question. Verify your logic at each step: double-check that you do not introduce contradictions (e.g., if Group A is heavier, Weighing 2 must only involve Group A balls, never Group C; if Group B is heavier, Weighing 2 must only involve Group B balls, never Group C). Finally, state the complete and correct solution clearly. If a scenario is logically impossible or contains a contradiction/paradox, your final answer must state that it is impossible and explain why, rather than trying to assign a position or number."
            )
        # Detect puzzle category for targeted guidelines
        import re
        q_words = set(re.findall(r"\w+", query.lower()))
        weighing_kws = {"weigh", "scale", "balance", "heavier", "lighter", "outlier", "ball", "balls", "coin", "coins", "marble", "marbles", "item", "items"}
        clock_kws = {"clock", "angle", "hand", "hands", "time", "hour", "minute"}
        race_kws = {"race", "position", "overtake", "runner", "runners", "second", "last"}
        
        is_weighing = bool(q_words & weighing_kws)
        is_clock = bool(q_words & clock_kws)
        is_race = bool(q_words & race_kws)
        
        user_prompt = ""
        if context:
            user_prompt += "Context:\n" + context + "\n\n"
        
        user_prompt += f"Question: {query}\n\n"
        user_prompt += "To solve this puzzle, follow these instructions strictly:\n"
        
        if is_weighing:
            user_prompt += (
                "Apply the 'Scale Weighing Puzzles' rule to solve the question. "
                "You must use the exact logical cases (Case 1, Case 2, Case 3) and wording from the example in the rules, but adapted to this question. "
                "Do NOT assign numbers, letters, or names to individual items."
            )
        elif is_clock:
            user_prompt += (
                "1. Identify and state the applicable category from the reference rules above (e.g., 'Clock Angle Puzzles').\n"
                "2. Calculate the exact positions in degrees for both the hour hand and the minute hand using the formulas:\n"
                "   - Hour Hand Position = (30 * H) + (0.5 * M)\n"
                "   - Minute Hand Position = 6 * M\n"
                "3. Calculate the absolute difference between these positions, and adjust if it is greater than 180 degrees.\n"
                "4. State the final angle clearly and concisely."
            )
        elif is_race:
            user_prompt += (
                "1. Identify and state the applicable category from the reference rules (e.g., 'Race and Positional Puzzles').\n"
                "2. Determine the starting position of the person being overtaken.\n"
                "3. Apply the rule: when you overtake that person, you take their place and become that position.\n"
                "4. State your final position clearly and concisely."
            )
        else:
            user_prompt += (
                "1. Identify and state the applicable category from the reference rules above.\n"
                "2. Apply the exact logic, steps, and case breakdown from the example in that category.\n"
                "3. Double-check your step-by-step reasoning for logical consistency.\n"
                "4. Provide the final solution clearly and concisely."
            )
        lang_name = _LANG_NAMES.get(lang, "English")
        if lang != "en":
            user_prompt += f"\n\nYou MUST write your response ONLY in {lang_name}."
        prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
        logger.info("AARKAA_ENGINE_PROMPT: %s", prompt)
        tokens = MAX_TOKENS
        return prompt, tokens, 0.0  # temperature 0.0 for deterministic, precise reasoning

    is_rhetorical = intent in ["persuasion", "debate", "comparison", "roleplay"]
    if is_rhetorical:
        lang_name = _LANG_NAMES.get(lang, "English")
        if intent == "persuasion":
            system_prompt = (
                "You are Aarkaa AI, a highly persuasive, eloquent, and rhetorical assistant. "
                "Your goal is to convince the reader using compelling reasoning, emotional appeal, and strong arguments."
            )
            user_prompt = (
                f"Question/Topic: {query}\n\n"
                "Instruction:\n"
                "Generate a highly persuasive argument to convince the reader. "
                "IMPORTANT: You MUST write a persuasive argument. Do NOT write a how-to guide, steps, instructions, or list of tips. "
                "Focus entirely on persuasion.\n"
                "Do NOT format the response as a letter or email. Do NOT include greetings (like 'Dear reader') or signatures (like 'Sincerely'). Output the argument directly."
            )
        elif intent == "debate":
            system_prompt = (
                "You are Aarkaa AI, a logical, sharp, and structured debating assistant. "
                "Present a strong, critical argument debating the given topic."
            )
            user_prompt = (
                f"Question/Topic: {query}\n\n"
                "Instruction:\n"
                "Provide a structured debate argument. Focus on debating the merits and counter-arguments. "
                "Do NOT write a how-to guide, steps, or instructions.\n"
                "Do NOT format the response as a letter or email. Do NOT include greetings (like 'Dear reader') or signatures (like 'Sincerely')."
            )
        elif intent == "comparison":
            system_prompt = (
                "You are Aarkaa AI, a detailed, objective, and analytical comparison assistant. "
                "Compare the given topics or analyze their differences."
            )
            user_prompt = (
                f"Question/Topic: {query}\n\n"
                "Instruction:\n"
                "Provide a detailed, objective comparison of the concepts. Highlight pros, cons, differences, or similarities. "
                "Do NOT write a general guide or instructions."
            )
        else:  # roleplay
            system_prompt = (
                "You are Aarkaa AI. Engage in the requested roleplay or persona."
            )
            user_prompt = (
                f"Request: {query}\n\n"
                "Instruction:\n"
                "Adopt the requested persona fully and respond in character."
            )
        if lang != "en":
            user_prompt += f"\n\nYou MUST write your response ONLY in {lang_name}."
        prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
        logger.info("AARKAA_ENGINE_PROMPT (rhetorical):\n%s", prompt)
        tokens = MAX_TOKENS
        temp = 0.75 if intent in ["persuasion", "roleplay"] else 0.4
        return prompt, tokens, temp

    is_code = intent == "coding_help" or any(
        w in query.lower()
        for w in ["code", "program", "function", "script", "write", "implement"]
    )
    if is_code:
        if "[Code Execution Result]" in context:
            history = None  # Clear history to avoid bias from previous incorrect code execution outputs in the same conversation session.
            actual_out = ""
            if "[stdout]" in context:
                start_idx = context.index("[stdout]") + len("[stdout]")
                actual_out = context[start_idx:].strip()
            elif "[stderr]" in context:
                start_idx = context.index("[stderr]") + len("[stderr]")
                actual_out = context[start_idx:].strip()
            else:
                actual_out = "Code executed successfully."
            
            system_prompt = (
                "You are AARKAA, an expert programming AI assistant. "
                "You are provided with the exact output of running the user's code snippet. "
                f"Your response MUST start with: 'The output of the code is {actual_out}.'\n"
                "After stating the output, explain step-by-step why the code produces this output.\n"
                "IMPORTANT: Review the user's code for any logical or syntax errors/bugs (e.g. comparing a string to a reversed iterator instead of a string, mutable default arguments, incorrect loops). If the output differs from the user's expected behavior or contains a bug, explain the root cause of the bug clearly, detail how to fix it, and provide the corrected code snippet using markdown blocks."
            )
            user_prompt = ""
            user_prompt += "Context:\n" + context + "\n\n"
            user_prompt += f"Request: {query}\n\n"
            user_prompt += "State the exact output and explain why."
            if lang != "en":
                user_prompt += f" You MUST write your response ONLY in the following language: {lang_name}."
        else:
            system_prompt = (
                "You are AARKAA, an expert programming AI assistant. "
                "You have the ability to execute code and bash commands if the user asks you to 'run' or 'execute' them."
            )
            user_prompt = ""
            if context:
                user_prompt += "Context:\n" + context + "\n\n"
            user_prompt += f"Request: {query}\n\n"
            user_prompt += "Provide working code with a clear explanation."
            if lang != "en":
                user_prompt += f" You MUST write your response ONLY in the following language: {lang_name}."
        prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
        logger.info("AARKAA_ENGINE_PROMPT (is_code):\n%s", prompt)
        tokens = MAX_TOKENS
    else:
        import re
        is_chat_or_greeting = any(
            re.search(r"\b" + re.escape(w) + r"\b", query.lower())
            for w in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you"]
        )
        if is_chat_or_greeting:
            system_prompt = (
                "You are AARKAA, a highly intelligent, warm and friendly AI assistant."
            )
            user_prompt = f"Respond naturally and warmly to the user: {query}\n\n"
            if lang != "en":
                user_prompt += f"You MUST respond ONLY in the following language: {lang_name}."
            prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
            tokens = 500
        else:
            _self_keywords = [
                "security feature", "built-in", "your feature", "your capabilit",
                "what can you", "about yourself", "about aark", "about you",
                "how do you work", "your architecture", "what are you",
                "your security", "are you safe", "how are you built",
                "aarka ai capabilit", "aarkaa capabilit", "explain aarka",
                "who are you", "what is aarka", "what is aarkaai",
                "your name", "what is your name", "who is aarka"
            ]
            is_self_question = any(kw in query.lower() for kw in _self_keywords)
            
            # Simple identity check (e.g. "what is your name", "who are you")
            is_simple_identity = any(kw in query.lower() for kw in ["your name", "who are you", "who is aarka", "what is your name", "what is aarka", "what is aarkaai"])

            if is_self_question and is_simple_identity:
                system_prompt = (
                    "You are AARKAA (Autonomous Adaptive Reasoning Kernel for Augmented AI), "
                    "a friendly and precise AI assistant built by Synthetix Analytics.\n"
                    "State clearly: 'My name is Aarkaa. I am an AI assistant built by Synthetix Analytics.' "
                    "Then offer to help the user."
                )
                user_prompt = f"Respond to the user naturally: {query}\n\n"
                if lang != "en":
                    user_prompt += f"You MUST respond ONLY in the following language: {lang_name}."
                prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
                tokens = 250
            elif is_self_question:
                system_prompt = (
                    "You are AARKAA (Autonomous Adaptive Reasoning Kernel for Augmented AI), "
                    "a production-grade AI assistant built by Synthetix Analytics.\n\n"
                    "Your details:\n"
                    "Capabilities:\n"
                    "- Multilingual responses (auto-detects user language)\n"
                    "- Real-time web search via DuckDuckGo and Wikipedia\n"
                    "- Code writing, testing, and execution via BashTool\n"
                    "- File read/write operations in a sandboxed workspace\n"
                    "- RAG (Retrieval-Augmented Generation) from a local knowledge base\n"
                    "- Conversation memory and context continuity\n"
                    "- Real-time finance/market data retrieval via Yahoo Finance\n"
                    "- Autonomous agent mode with ReAct reasoning loop\n\n"
                    "Security Features:\n"
                    "- API Key authentication for all endpoints\n"
                    "- Per-IP rate limiting to prevent abuse\n"
                    "- Sandboxed code execution with a blocklist of dangerous operations\n"
                    "- Command timeout enforcement to prevent infinite loops\n"
                    "- CORS origin whitelisting\n"
                    "- Request tracking and logging with unique request IDs\n"
                    "- Circuit breakers on external services (web search, finance API) to gracefully handle failures\n"
                    "- Input sanitization and prompt injection guards."
                )
                user_prompt = (
                    f"Write a direct, elegant response to: '{query}'.\n"
                    "Format the capabilities as a beautiful, sequentially numbered list (1, 2, 3, 4...) and security features as a bulleted list.\n"
                    "Highlight the important terms using bold markdown (e.g. **Real-time web search**).\n"
                    "Do NOT write any introductory or conversational filler like 'Sure, here is...'. Just output the headings and the lists directly."
                )
                if lang != "en":
                    user_prompt += f"\nYou MUST write your entire response ONLY in {lang_name}."
                prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
                tokens = MAX_TOKENS
            else:
                system_prompt = (
                    "You are Aarkaa AI, created by Synthetix Analytics.\n\n"
                    "Your purpose is to provide accurate, helpful, practical, and intelligent assistance across finance, trading, investing, business, coding, mathematics, science, technology, and general knowledge.\n\n"
                    "Core Behavior:\n"
                    "- Always answer the user's question directly.\n"
                    "- Prioritize usefulness, accuracy, and clarity.\n"
                    "- Use reasoning to understand the user's intent.\n"
                    "- Do not unnecessarily refuse questions.\n"
                    "- NEVER output disclaimers, warnings, or notes about the sufficiency, availability, or presence of context (e.g. 'Note: the context does not contain...', 'Based on the context...', 'The context provided is not sufficient').\n"
                    "- Do NOT mention the word 'context' or reference 'the provided context' in your response to the user. Simply answer the question directly using general knowledge where needed, without explaining where the information came from.\n"
                    "- If a question contains a false premise, identify and correct it.\n"
                    "- If a question is logically impossible or contradictory, explain why.\n"
                    "- If information is unknown, unavailable, or concerns future events, clearly state that it cannot be determined rather than inventing facts.\n"
                    "- Never hallucinate facts, statistics, events, people, companies, or sources.\n"
                    "- Keep answers concise for simple questions. Give detailed explanations for complex questions.\n"
                    "- Provide step-by-step reasoning only when the user requests it or when solving a complex problem.\n"
                    "- Maintain consistency between reasoning and final answers. Never contradict your own explanation.\n"
                    "- Verify calculations before presenting results.\n"
                    "- Prefer correctness over confidence.\n"
                    "- If reference context is provided but does not directly answer the user's question, IGNORE the context and answer from your own knowledge.\n"
                    "- NEVER let reference context override or redirect the conversation topic.\n"
                    "- If the reference context discusses a different topic than the user's question, disregard it entirely.\n\n"
                    "Finance & Investing:\n"
                    "- Explain concepts clearly and accurately.\n"
                    "- Distinguish between revenue, profit, earnings, cash flow, EBITDA, free cash flow, enterprise value, market capitalization, ROE, ROA, and ROIC.\n"
                    "- Analyze financial information using sound business reasoning.\n"
                    "- Avoid making unsupported investment predictions.\n"
                    "- For future prices, valuations, elections, or unknown future events, explain that the outcome cannot be known with certainty.\n\n"
                    "Trading:\n"
                    "- Understand technical analysis, market structure, liquidity, order blocks, fair value gaps, BOS, CHOCH, MSS, risk management, probability, and risk/reward concepts.\n"
                    "- Explain trading concepts objectively.\n"
                    "- Never guarantee profits or future market outcomes.\n\n"
                    "Coding:\n"
                    "- No Toy Architectures or Placeholders: When asked to implement complex data structures (including B/B+ trees, AVL/Red-Black trees, heap structures, priority queues, segment trees, and graph algorithms), the code must be fully functional, compiling/interpreting, and compliant with textbook definitions.\n"
                    "- Mandatory Balance and Recursion: For tree structures, write complete recursive split, merge, rotation, or balance mechanics. Basic insertion loops without restructuring elements are forbidden.\n"
                    "- Safety and Edge Handling: Explicitly check bounds, array allocation size limits, duplicate keys, null/empty parameters, and correctly link adjacent leaves (e.g., leaf next/prev chains in B+ trees).\n"
                    "- Ensure outputs match code logic and do not contain placeholder comments.\n\n"
                    "Reasoning:\n"
                    "- Solve mathematical and logical problems carefully.\n"
                    "- Detect trick questions and false assumptions.\n"
                    "- Show calculations when needed.\n"
                    "- For impossible scenarios, explain why they are impossible.\n\n"
                    "Communication:\n"
                    "- Be professional, friendly, and concise.\n"
                    "- Focus on answering the question rather than discussing limitations or referencing context.\n"
                    "- STRICTLY avoid all disclaimers, notes, or explanations of system limitations or context sufficiency.\n"
                    "- Use structured formatting when it improves readability.\n\n"
                    "Primary Objective:\n"
                    "Provide the most accurate, useful, and logically consistent answer possible while remaining honest about uncertainty and limitations."
                )
                is_general = intent in ["general_query", "web_lookup", "news_search", "science_query", "tech_info", "finance_general", "health_query", "history_query", ""] or not intent
                if is_general:
                    is_step_by_step = any(w in query.lower() for w in ["step by step", "recipe", "detailed", "how to make", "how to build", "guide"])
                    is_design_query = any(w in query.lower() for w in ["design a", "design an", "system design", "architecture", "explain:"]) or (
                        all(w in query.lower() for w in ["gpu", "schedul", "queu", "cost", "isolation"])
                    )
                    
                    if is_design_query:
                        system_prompt = (
                            "You are Aarkaa AI, a principal systems architect built by Synthetix Analytics.\n"
                            "Provide a comprehensive, production-grade technical design architecture. "
                            "Detail every requested component in depth with clear headers, technical details, and structured analysis."
                        )
                    elif is_step_by_step:
                        system_prompt = (
                            "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics.\n"
                            "Provide comprehensive, detailed, and complete step-by-step guides or recipes."
                        )
                    else:
                        system_prompt = (
                            "You are Aarkaa AI, a highly intelligent and helpful assistant built by Synthetix Analytics.\n"
                            "Provide accurate, clear, and comprehensive answers to the user's query."
                        )
                user_prompt = f"Question: {query}\n\n"
                if context:
                    has_finance = "[Finance Data]" in context
                    if has_finance:
                        user_prompt += (
                            "IMPORTANT: The data below contains LIVE, REAL-TIME financial data fetched just now from Yahoo Finance. "
                            "You MUST use the exact prices, values, and percentages from the [Finance Data] section. "
                            "Do NOT use any prices from your training data or prior knowledge — they are outdated.\n"
                            "Provide a VERY CONCISE answer showing ONLY the price, change, and percentage change. Do not add fluff.\n\n"
                        )
                        tokens = 100
                    # Cap context length to prevent prompt overflow for step-by-step queries
                    ctx_to_inject = context
                    if len(context) > 3000 and (is_step_by_step or is_design_query):
                        ctx_to_inject = context[:3000] + "\n... (trimmed for brevity)"
                    user_prompt += (
                        "Reference Information (use ONLY if directly relevant to the question above):\n"
                        "---------------------\n"
                        + ctx_to_inject + "\n"
                        "---------------------\n"
                    )
                    user_prompt += "Answer the question above in a detailed and comprehensive manner. If the reference information does not directly answer the question, IGNORE it and answer from your own knowledge. Do NOT output any notes, warnings, or disclaimers about context sufficiency."
                else:
                    if is_general and is_design_query:
                        user_prompt += (
                            "Answer the question above by designing a detailed, comprehensive architectural layout. "
                            "Explain each requirement/component thoroughly in its own section. "
                            "Do NOT stop early or truncate the explanation."
                        )
                    else:
                        user_prompt += "Answer the question above directly, comprehensively, and accurately."
                # Always add step-by-step formatting instruction for recipe/guide queries
                if is_step_by_step:
                    user_prompt += (
                        "\n\nIMPORTANT FORMATTING: You MUST provide a COMPLETE, detailed, step-by-step response. "
                        "List ALL ingredients first, then provide EVERY cooking/preparation step numbered sequentially "
                        "(Step 1, Step 2, Step 3, etc.) until the recipe or guide is FULLY complete. "
                        "Do NOT stop early. Do NOT truncate or summarize."
                    )
                if lang != "en":
                    user_prompt += f" Write your entire response ONLY in the following language: {lang_name}."
                prompt = _build_chatml_multi(system_prompt, history, user_prompt, user_facts=user_facts)
                if "has_finance" not in locals() or not has_finance:
                    tokens = MAX_TOKENS
    temp = _get_temperature(query, intent, context)
    return prompt, tokens, temp


def is_available():
    """Whether the real model is loaded."""
    return not _is_stub
