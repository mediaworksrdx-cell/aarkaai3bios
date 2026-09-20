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

def test_build_tool_namespace(tmp_path, monkeypatch):
    from modules.approval_store import SQLiteApprovalStore
    store = SQLiteApprovalStore(tmp_path / "test_approvals.db")
    monkeypatch.setattr("modules.approval_store.get_approval_store", lambda: store)

    mock_registry = MagicMock()
    mock_registry.execute_tool.return_value = "Success"
    
    rec = store.create_request(
        user_id="user1",
        session_id="sess1",
        tool_name="BashTool",
        args={"command": "ls"},
        risk_level="HIGH",
        human_summary="Run ls",
    )
    store.resolve_request(rec.approval_id, "user1", "APPROVED")

    executor = CodeModeExecutor(
        mock_registry, str(tmp_path), 10, 5, 1024,
        approval_context={
            "human_approved": True,
            "approval_id": rec.approval_id,
            # force_exec_fallback=True bypasses the Docker requirement for EXEC tools
            # in test environments where Docker is unavailable.
            "force_exec_fallback": True,
            "user_id": "user1",
            "session_id": "sess1",
        }
    )
    namespace = executor.build_tool_namespace(["BashTool", "FileEditTool"])
    
    assert "BashTool" in namespace
    assert "FileEditTool" in namespace
    
    result = namespace["BashTool"](command="ls")
    assert result == "Success"
    mock_registry.execute_tool.assert_called_with("BashTool", {"command": "ls"})

def test_tool_call_counter_limit(tmp_path):
    mock_registry = MagicMock()
    mock_registry.execute_tool.return_value = "Success"
    executor = CodeModeExecutor(
        mock_registry, str(tmp_path), 10, 2, 1024,
        approval_context={"human_approved": True, "force_exec_fallback": True}
    )
    namespace = executor.build_tool_namespace(["FileReadTool"])
    
    namespace["FileReadTool"](path=str(tmp_path / "f1.txt"))
    namespace["FileReadTool"](path=str(tmp_path / "f2.txt"))
    
    with pytest.raises(RuntimeError, match="Max tool calls \\(2\\) exceeded"):
        namespace["FileReadTool"](path=str(tmp_path / "f3.txt"))


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
