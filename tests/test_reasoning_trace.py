import pytest
from modules.reasoning_trace import ReasoningTraceStateMachine

def test_clean_think_block():
    sm = ReasoningTraceStateMachine()
    out1 = sm.feed("<think>some trace</think>some answer")
    assert out1 == "some answer"
    assert sm.traces == ["some trace"]
    out2, traces = sm.finish()
    assert out2 == ""

def test_tag_split_two_tokens():
    sm = ReasoningTraceStateMachine()
    out1 = sm.feed("<thi")
    out2 = sm.feed("nk>content</think>answer")
    assert out1 == ""
    assert out2 == "answer"
    assert sm.traces == ["content"]

def test_tag_split_three_tokens():
    sm = ReasoningTraceStateMachine()
    out1 = sm.feed("<")
    out2 = sm.feed("think")
    out3 = sm.feed(">content</think>answer")
    assert out1 == ""
    assert out2 == ""
    assert out3 == "answer"
    assert sm.traces == ["content"]

def test_nested_tags():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("<think>outer<think>inner</think>outer</think>answer")
    assert out == "answer"
    assert sm.traces == ["outer<think>inner</think>outer"]

def test_malformed_discard():
    sm = ReasoningTraceStateMachine(unclosed_trace_policy="discard")
    out1 = sm.feed("<think>content...")
    assert out1 == ""
    out2, traces = sm.finish()
    assert out2 == ""
    assert traces == []

def test_malformed_yield():
    sm = ReasoningTraceStateMachine(unclosed_trace_policy="yield")
    out1 = sm.feed("<think>content...")
    assert out1 == ""
    out2, traces = sm.finish()
    assert out2 == "<think>content..."
    assert traces == []

def test_buffer_overflow():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("<think>" + "a" * 16385)
    assert out == "<think>" + "a" * 16385

def test_false_positive_mid_sentence():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("The user should <think> about this carefully")
    assert out == "The user should <think> about this carefully"
    assert sm.traces == []

def test_alternate_format():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("[THINKING]trace[/THINKING]answer")
    assert out == "answer"
    assert sm.traces == ["trace"]

def test_empty_trace():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("<think></think>answer")
    assert out == "answer"
    assert sm.traces == [""]

def test_multiple_traces():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("answer1<think>t1</think>answer2<think>t2</think>answer3")
    assert out == "answer1answer2answer3"
    assert sm.traces == ["t1", "t2"]

def test_no_traces():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("Just a normal response")
    assert out == "Just a normal response"
    assert sm.traces == []

def test_tag_at_start():
    sm = ReasoningTraceStateMachine()
    out = sm.feed("<think>trace</think>answer")
    assert out == "answer"
    assert sm.traces == ["trace"]

def test_close_tag_split():
    sm = ReasoningTraceStateMachine()
    out1 = sm.feed("<think>content</thi")
    out2 = sm.feed("nk>answer")
    assert out1 == ""
    assert out2 == "answer"
    assert sm.traces == ["content"]
