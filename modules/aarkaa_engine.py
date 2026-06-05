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

_model = None
_is_stub = True

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
    Path(MODEL_PATH).parent / "aarkaa-3b-q8.gguf",
    Path(MODEL_PATH).parent / "aarkaa-3b-f16.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-q8.gguf",
    Path(MODEL_PATH) / "aarkaa-3b-f16.gguf",
]


def init():
    """Load the AARKAA-3B GGUF model if available."""
    global _model, _is_stub

    gguf_file = None
    for candidate in _GGUF_CANDIDATES:
        if candidate.exists():
            gguf_file = candidate
            break

    if gguf_file is None:
        logger.warning("GGUF model not found - running in STUB mode.")
        _is_stub = True
        return

    try:
        from llama_cpp import Llama

        logical_cores = os.cpu_count() or 2
        n_threads = logical_cores if logical_cores <= 4 else logical_cores // 2

        logger.info("Loading AARKAA-3B from %s (threads=%d)", gguf_file, n_threads)

        _model = Llama(
            model_path=str(gguf_file),
            n_ctx=8192,
            n_threads=n_threads,
            n_threads_batch=n_threads,
            n_gpu_layers=0,
            verbose=False,
        )
        _is_stub = False
        logger.info("AARKAA-3B loaded (llama.cpp, GGUF, %d threads).", n_threads)
    except Exception as exc:
        logger.error("Failed to load AARKAA-3B: %s - falling back to stub", exc)
        _is_stub = True


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


def _build_chatml_multi(system: str, history: list[dict] | None, user: str) -> str:
    """Build ChatML format with system message, multi-turn history, and current user prompt."""
    prompt = f"<|im_start|>system\n{system}<|im_end|>\n"
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg["message"]
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    prompt += f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    return prompt


def _generate(prompt, max_new_tokens=150, stop=None, temperature=0.7):
    """Run generation via llama.cpp."""
    if _is_stub or _model is None:
        return _stub_response(prompt)
    
    tokens = list(_generate_stream(prompt, max_new_tokens=max_new_tokens, stop=stop, temperature=temperature))
    text = "".join(tokens).strip()
    return _clean_response(text)


def _generate_stream(prompt, max_new_tokens=150, stop=None, temperature=0.7):
    """Run generation via llama.cpp and yield tokens with repetition guard."""
    if _is_stub or _model is None:
        yield _stub_response(prompt)
        return

    stop_tokens = [
        "<|im_end|>", "<|im_start|>", "<|endoftext|>"
    ]
    if stop:
        stop_tokens.extend(stop)

    stream = _model(
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


def generate_raw(prompt, max_new_tokens=300, stop=None):
    """Raw generation for the agent loop (no truncation)."""
    if _is_stub or _model is None:
        return 'Final Answer: I am running in stub mode.'
    
    if stop is None:
        stop = []

    output = _model(
        prompt,
        max_tokens=max_new_tokens,
        temperature=0.2,
        top_p=0.9,
        stop=stop,
        repeat_penalty=1.1,
    )
    return output["choices"][0]["text"].strip()


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

    # Otherwise, find the latest complete sentence ending in the second half of the text
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
            
    if best_pos > len(text) * 0.5:
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
            tokens = 250
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
            tokens = 1024
        elif any(w in q_lower for w in ["code", "program", "function", "script", "write", "implement", "create a"]):
            system_prompt = (
                "You are AARKAA, an expert programming AI assistant."
            )
            user_prompt = f"Request: {query}\n\nProvide working code with a brief explanation."
            if lang != "en":
                user_prompt += f" You MUST respond ONLY in the following language: {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = 512
        else:
            system_prompt = (
                "You are AARKAA, a helpful and precise AI assistant. "
                "You cannot predict the future price of financial products or speculative assets (stocks, cryptocurrencies, commodities, etc.). "
                "If the user asks for a future price prediction or forecast, you must politely decline, explaining that future market behavior is speculative and unpredictable."
            )
            user_prompt = f"Answer the following question concisely: {query}\n\n"
            if lang != "en":
                user_prompt += f"You MUST write your response ONLY in the following language: {lang_name}."
            prompt = _build_chatml(system_prompt, user_prompt)
            tokens = 300
        response = _generate(prompt, max_new_tokens=tokens)
        confidence = min(0.9, 0.5 + len(response.split()) / 150)
        return response, confidence
    except Exception as exc:
        logger.error("primary_check failed: %s", exc)
        return _stub_response(query), 0.3


def final_response(query, context, intent="", lang="en", mode="production", history=None):
    """Full reasoning pass with fused context from external modules."""
    if _is_stub:
        return _stub_response(query, context)

    try:
        result = _build_final_prompt(query, context, intent, lang, mode, history=history)
        prompt, tokens = result[0], result[1]
        temp = result[2] if len(result) > 2 else 0.7
        return _generate(prompt, max_new_tokens=tokens, temperature=temp)
    except Exception as exc:
        logger.error("final_response failed: %s", exc)
        return _stub_response(query, context)


def stream_final_response(query, context, intent="", lang="en", mode="production", history=None):
    """Stream tokens for the final response pass."""
    if _is_stub:
        yield _stub_response(query, context)
        return

    try:
        result = _build_final_prompt(query, context, intent, lang, mode, history=history)
        prompt, tokens = result[0], result[1]
        temp = result[2] if len(result) > 2 else 0.7
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


def _build_final_prompt(query, context, intent="", lang="en", mode="production", history=None):
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
        prompt = _build_chatml_multi(system_prompt, history, user_prompt)
        tokens = 1500
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
        prompt = _build_chatml_multi(system_prompt, history, user_prompt)
        logger.info("AARKAA_ENGINE_PROMPT: %s", prompt)
        tokens = 3800
        return prompt, tokens, 0.0  # temperature 0.0 for deterministic, precise reasoning

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
        prompt = _build_chatml_multi(system_prompt, history, user_prompt)
        logger.info("AARKAA_ENGINE_PROMPT (is_code):\n%s", prompt)
        tokens = 3800
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
            prompt = _build_chatml_multi(system_prompt, history, user_prompt)
            tokens = 500
        else:
            _self_keywords = [
                "security feature", "built-in", "your feature", "your capabilit",
                "what can you", "about yourself", "about aark", "about you",
                "how do you work", "your architecture", "what are you",
                "your security", "are you safe", "how are you built",
                "aarka ai capabilit", "aarkaa capabilit", "explain aarka",
                "who are you"
            ]
            is_self_question = any(kw in query.lower() for kw in _self_keywords)

            if is_self_question:
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
                prompt = _build_chatml_multi(system_prompt, history, user_prompt)
                tokens = 3800
            else:
                system_prompt = (
                    "You are Aarkaa AI, created by Synthetix Analytics.\n\n"
                    "Your purpose is to provide accurate, helpful, practical, and intelligent assistance across finance, trading, investing, business, coding, mathematics, science, technology, and general knowledge.\n\n"
                    "Core Behavior:\n"
                    "- Always answer the user's question directly.\n"
                    "- Prioritize usefulness, accuracy, and clarity.\n"
                    "- Use reasoning to understand the user's intent.\n"
                    "- Do not unnecessarily refuse questions.\n"
                    "- Do not respond with 'the context does not contain information' unless answering is genuinely impossible. Use general knowledge and reasoning to answer whenever possible.\n"
                    "- If a question contains a false premise, identify and correct it.\n"
                    "- If a question is logically impossible or contradictory, explain why.\n"
                    "- If information is unknown, unavailable, or concerns future events, clearly state that it cannot be determined rather than inventing facts.\n"
                    "- Never hallucinate facts, statistics, events, people, companies, or sources.\n"
                    "- Keep answers concise for simple questions. Give detailed explanations for complex questions.\n"
                    "- Provide step-by-step reasoning only when the user requests it or when solving a complex problem.\n"
                    "- Maintain consistency between reasoning and final answers. Never contradict your own explanation.\n"
                    "- Verify calculations before presenting results.\n"
                    "- Prefer correctness over confidence.\n\n"
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
                    "- Explain code accurately.\n"
                    "- Detect bugs and logical errors.\n"
                    "- Provide correct complexity analysis.\n"
                    "- Understand algorithms, data structures, databases, APIs, Python, JavaScript, Java, Kotlin, SQL, and system design concepts.\n"
                    "- Ensure outputs match the code logic.\n\n"
                    "Reasoning:\n"
                    "- Solve mathematical and logical problems carefully.\n"
                    "- Detect trick questions and false assumptions.\n"
                    "- Show calculations when needed.\n"
                    "- For impossible scenarios, explain why they are impossible.\n\n"
                    "Communication:\n"
                    "- Be professional, friendly, and concise.\n"
                    "- Focus on answering the question rather than discussing limitations.\n"
                    "- Avoid repetitive disclaimers.\n"
                    "- Use structured formatting when it improves readability.\n\n"
                    "Primary Objective:\n"
                    "Provide the most accurate, useful, and logically consistent answer possible while remaining honest about uncertainty and limitations."
                )
                user_prompt = ""
                if context:
                    has_finance = "[Finance Data]" in context
                    if has_finance:
                        user_prompt += (
                            "IMPORTANT: The context below contains LIVE, REAL-TIME financial data fetched just now from Yahoo Finance. "
                            "You MUST use the exact prices, values, and percentages from the [Finance Data] section. "
                            "Do NOT use any prices from your training data or prior knowledge — they are outdated.\n"
                            f"Provide a VERY CONCISE answer showing ONLY the price, change, and percentage change. Do not add fluff.\n\n"
                        )
                        tokens = 100
                    user_prompt += (
                        "Context information:\n"
                        "---------------------\n"
                        + context + "\n"
                        "---------------------\n"
                    )
                user_prompt += f"Question: {query}\n\n"
                user_prompt += "Answer the question using the context above as reference. If the context does not contain the answer, you may use your general knowledge to answer accurately."
                if lang != "en":
                    user_prompt += f" Write your entire response ONLY in the following language: {lang_name}."
                prompt = _build_chatml_multi(system_prompt, history, user_prompt)
                if "has_finance" not in locals() or not has_finance:
                    tokens = 3800
    if is_reasoning:
        temp = 0.0
    else:
        temp = 0.2 if (context or is_code or history) else 0.7
    return prompt, tokens, temp


def is_available():
    """Whether the real model is loaded."""
    return not _is_stub
