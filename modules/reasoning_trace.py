import enum
import logging

logger = logging.getLogger(__name__)

class State(enum.Enum):
    PASSTHRU = 1
    TAG_SCANNING = 2
    BUFFERING = 3
    FLUSH_ABORT = 4

class ReasoningTraceStateMachine:
    """
    State machine for isolating reasoning traces from LLM responses.
    Supports streaming token processing, nested tags, and multiple traces.
    """
    MAX_TRACE_BUFFER = 16384
    MAX_TAG_LEN = 12

    def __init__(self, tag_pairs=None, unclosed_trace_policy="discard"):
        self.tag_pairs = tag_pairs or [
            ("<think>", "</think>"),
            ("[THINKING]", "[/THINKING]"),
            ("<reasoning>", "</reasoning>")
        ]
        self.unclosed_trace_policy = unclosed_trace_policy
        self.state = State.PASSTHRU
        self.scan_buffer = ""
        self.trace_buffer = ""
        self._collected_traces = []
        
        self.total_chars_seen = 0
        self.depth = 0
        self.active_open_tag = None
        self.active_close_tag = None
        
        self.last_emitted_char = '\n'
        self.has_emitted_non_whitespace = False
        self.output_buffer = []

    @property
    def traces(self) -> list[str]:
        """All collected reasoning traces so far."""
        return self._collected_traces

    def _emit(self, text: str):
        self.output_buffer.append(text)
        for c in text:
            self.last_emitted_char = c
            if not c.isspace():
                self.has_emitted_non_whitespace = True

    def feed(self, token: str) -> str:
        """Feed a token, return characters safe to yield to the client."""
        self.output_buffer = []
        for char in token:
            self._process_char(char)
        return "".join(self.output_buffer)

    def _process_char(self, char: str):
        self.total_chars_seen += 1
        
        if self.state == State.FLUSH_ABORT:
            self._emit(char)
            return

        if self.state == State.PASSTHRU:
            # Activate if at the very beginning, immediately after a newline, or within first 200 chars but not preceded by space (mid-sentence)
            is_valid_start = (
                (not self.has_emitted_non_whitespace) or
                (self.last_emitted_char == '\n') or
                (self.total_chars_seen <= 200 and not self.last_emitted_char.isspace())
            )
            if is_valid_start:
                self.scan_buffer = char
                if any(tag[0].startswith(self.scan_buffer) for tag in self.tag_pairs):
                    self.state = State.TAG_SCANNING
                    return
            self._emit(char)
            return

        elif self.state == State.TAG_SCANNING:
            self.scan_buffer += char
            
            for open_tag, close_tag in self.tag_pairs:
                if self.scan_buffer == open_tag:
                    self.state = State.BUFFERING
                    self.active_open_tag = open_tag
                    self.active_close_tag = close_tag
                    self.depth = 1
                    self.trace_buffer = ""
                    self.scan_buffer = ""
                    return
            
            is_prefix = False
            for open_tag, _ in self.tag_pairs:
                if open_tag.startswith(self.scan_buffer):
                    is_prefix = True
                    break
                    
            if is_prefix:
                return
            else:
                self._emit(self.scan_buffer)
                self.scan_buffer = ""
                self.state = State.PASSTHRU
                return

        elif self.state == State.BUFFERING:
            self.trace_buffer += char
            
            if len(self.trace_buffer) > self.MAX_TRACE_BUFFER:
                logger.warning("Reasoning trace buffer overflow")
                self.state = State.FLUSH_ABORT
                self._emit(self.active_open_tag + self.trace_buffer)
                self.active_open_tag = None
                self.active_close_tag = None
                self.trace_buffer = ""
                return
                
            if self.trace_buffer.endswith(self.active_open_tag):
                self.depth += 1
            elif self.trace_buffer.endswith(self.active_close_tag):
                self.depth -= 1
                if self.depth == 0:
                    trace_content = self.trace_buffer[:-len(self.active_close_tag)]
                    self._collected_traces.append(trace_content)
                    self.state = State.PASSTHRU
                    self.trace_buffer = ""
                    self.scan_buffer = ""
                    self.active_open_tag = None
                    self.active_close_tag = None
                    return
                    
            return

    def finish(self) -> tuple[str, list[str]]:
        """End of stream. Returns (remaining_output, collected_traces)."""
        self.output_buffer = []
        if self.state == State.TAG_SCANNING:
            self._emit(self.scan_buffer)
        elif self.state == State.BUFFERING:
            if self.unclosed_trace_policy == "yield":
                self._emit(self.active_open_tag + self.trace_buffer)
            else:
                logger.warning("Discarding unclosed reasoning trace")
        
        self.state = State.PASSTHRU
        return "".join(self.output_buffer), self._collected_traces
