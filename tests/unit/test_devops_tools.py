import sys
import traceback
import builtins

# Mocking input for HumanInput just in case
builtins.input = lambda x: 'test_input_response'

try:
    from modules.tools import (
        BashTool, FileReadTool, FileEditTool, WebSearchTool, ImageGenTool,
        HumanInput, GitTool, ASTTool, MemoryTool, LSPTool, SearchTool,
        FileTool, BuildTool, TestTool, DeployTool, SecurityTool, CoverageTool,
        ProfilerTool, PlannerTool, LinterTool, FormatterTool, DebuggerTool,
        PatchTool, SnapshotTool, HealthTool, RAGTool, VerifierTool, RepairTool,
        MonitorTool, SymbolTool, XrefTool, CallGraphTool, DependencyTool,
        DockerTool, DbMigrateTool, PkgManagerTool, BrowserTool, CiCdTool,
        BenchmarkTool, CodeReviewTool, DocGenTool, CoordinatorTool, ConfidenceTool,
        ListSkillsTool, GetSkillTool, CreateSkillTool, UpdateSkillTool,
        DeleteSkillTool, ValidateSkillTool, TestSkillTool
    )
except ImportError as e:
    print(f"Error importing tools: {e}")
    sys.exit(1)

tests = [
    (BashTool, {'command': 'echo hello'}),
    (FileReadTool, {'path': 'config.py'}),
    (FileEditTool, {'path': '/tmp/test.txt', 'content': 'test', 'action': 'write'}),
    (WebSearchTool, {'query': 'test'}),
    (ImageGenTool, {'prompt': 'test'}),
    (HumanInput, {'question': 'test'}),
    (GitTool, {'command': 'status'}),
    (ASTTool, {'code': 'x = 1', 'language': 'python'}),
    (MemoryTool, {'action': 'list'}),
    (LSPTool, {'action': 'diagnostics'}),
    (SearchTool, {'query': 'test', 'path': '.'}),
    (FileTool, {'action': 'list', 'path': '.'}),
    (BuildTool, {'command': 'check'}),
    (TestTool, {'command': 'list'}),
    (DeployTool, {'action': 'status'}),
    (SecurityTool, {'action': 'scan'}),
    (CoverageTool, {'action': 'report'}),
    (ProfilerTool, {'action': 'status'}),
    (PlannerTool, {'action': 'status'}),
    (LinterTool, {'action': 'check', 'path': '.'}),
    (FormatterTool, {'action': 'check'}),
    (DebuggerTool, {'action': 'status'}),
    (PatchTool, {'action': 'list'}),
    (SnapshotTool, {'action': 'list'}),
    (HealthTool, {'action': 'check'}),
    (RAGTool, {'query': 'test'}),
    (VerifierTool, {'action': 'status'}),
    (RepairTool, {'action': 'status'}),
    (MonitorTool, {'action': 'status'}),
    (SymbolTool, {'query': 'test'}),
    (XrefTool, {'query': 'test'}),
    (CallGraphTool, {'function': 'main'}),
    (DependencyTool, {'action': 'list'}),
    (DockerTool, {'action': 'status'}),
    (DbMigrateTool, {'action': 'status'}),
    (PkgManagerTool, {'action': 'list'}),
    (BrowserTool, {'action': 'status'}),
    (CiCdTool, {'action': 'status'}),
    (BenchmarkTool, {'action': 'status'}),
    (CodeReviewTool, {'action': 'review'}),
    (DocGenTool, {'action': 'generate'}),
    (CoordinatorTool, {'action': 'status'}),
    (ConfidenceTool, {'action': 'check'}),
    (ListSkillsTool, {}),
    (GetSkillTool, {'name': 'finance'}),
    (CreateSkillTool, {'name': 'test_skill', 'description': 'test'}),
    (UpdateSkillTool, {'name': 'test_skill', 'content': 'updated'}),
    (DeleteSkillTool, {'name': 'test_skill_nonexist'}),
    (ValidateSkillTool, {'name': 'finance'}),
    (TestSkillTool, {'name': 'finance'})
]

for ToolClass, params in tests:
    tool_name = ToolClass.__name__
    try:
        tool = ToolClass()
        result = tool.execute(params)
        if result is None:
            print(f"FAIL: {tool_name} returned None")
        else:
            result_str = str(result)
            output = result_str[:80].replace('\n', ' ')
            safe_output = output.encode('ascii', errors='replace').decode('ascii')
            print(f"PASS: {tool_name} - {safe_output}")
    except Exception as e:
        safe_error = str(e)[:80].replace('\n', ' ').encode('ascii', errors='replace').decode('ascii')
        print(f"FAIL: {tool_name} raised exception: {safe_error}")
