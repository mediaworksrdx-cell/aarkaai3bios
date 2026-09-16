import pytest
from unittest.mock import MagicMock
from modules.code_mode import CodeModeExecutor, CodeModeResult
from modules.coordinator import _is_code_mode_eligible, _extract_python_code

def test_validate_code_clean():
    code = "def my_func():\n    return 42\nx = my_func()"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert is_valid
    assert err is None

def test_validate_code_forbidden_import_os():
    code = "import os\nos.system('echo hi')"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert not is_valid
    assert "Forbidden import" in err

def test_validate_code_forbidden_import_subprocess():
    code = "from subprocess import run\nrun(['ls'])"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert not is_valid
    assert "Forbidden import" in err

def test_validate_code_forbidden_eval():
    code = "x = eval('2 + 2')"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert not is_valid
    assert "Forbidden builtin" in err

def test_validate_code_forbidden_dunder():
    code = "x = __import__('os')"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert not is_valid
    assert "Forbidden builtin" in err

def test_validate_code_syntax_error():
    code = "def my_func(:"
    is_valid, err = CodeModeExecutor.validate_code(code)
    assert not is_valid
    assert "Syntax Error" in err

def test_build_tool_namespace():
    mock_registry = MagicMock()
    mock_registry.execute_tool.return_value = "Success"
    
    executor = CodeModeExecutor(mock_registry, "/tmp", 10, 5, 1024)
    namespace = executor.build_tool_namespace(["BashTool", "FileEditTool"])
    
    assert "BashTool" in namespace
    assert "FileEditTool" in namespace
    
    result = namespace["BashTool"](command="ls")
    assert result == "Success"
    mock_registry.execute_tool.assert_called_with("BashTool", {"command": "ls"})

def test_tool_call_counter_limit():
    mock_registry = MagicMock()
    executor = CodeModeExecutor(mock_registry, "/tmp", 10, 2, 1024)
    namespace = executor.build_tool_namespace(["BashTool"])
    
    namespace["BashTool"](command="ls")
    namespace["BashTool"](command="ls")
    
    with pytest.raises(RuntimeError, match="Max tool calls \\(2\\) exceeded"):
        namespace["BashTool"](command="ls")

def test_code_mode_result_format():
    res = CodeModeResult(
        success=True,
        output="Command ran successfully",
        tool_calls=[{"tool": "BashTool", "args": {"command": "echo hi"}}]
    )
    formatted = res.format_final_answer()
    assert "I executed the requested multi-step plan" in formatted
    assert "BashTool" in formatted
    assert "Command ran successfully" in formatted
    
    res_err = CodeModeResult(success=False, output="", tool_calls=[], error="Failed")
    assert "Code Mode Execution Failed" in res_err.format_final_answer()

def test_is_code_mode_eligible_multi_tool():
    query = "Create a file called test.py and then run it to test."
    assert _is_code_mode_eligible(query, "")

def test_is_code_mode_eligible_simple():
    query = "What is the capital of France?"
    assert not _is_code_mode_eligible(query, "")

def test_extract_python_code_from_fences():
    text = "Here is the code:\n```python\nprint('hello')\n```\nEnjoy!"
    code = _extract_python_code(text)
    assert code == "print('hello')"

def test_extract_python_code_raw():
    text = "print('hello')"
    code = _extract_python_code(text)
    assert code == "print('hello')"
