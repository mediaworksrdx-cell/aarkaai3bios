from modules.tools.base import ToolRegistry
from modules.tools.bash import BashTool
from modules.tools.fs import FileReadTool, FileEditTool
from modules.tools.web import WebSearchTool
from modules.tools.image import ImageGenTool
from modules.tools.human_input import HumanInput
from modules.tools.git_tool import GitTool
from modules.tools.ast_tool import ASTTool
from modules.tools.memory_tool import MemoryTool
from modules.tools.lsp_tool import LSPTool
from modules.tools.search_tool import SearchTool
from modules.tools.file_tool import FileTool
from modules.tools.build_tool import BuildTool
from modules.tools.test_tool import TestTool
from modules.tools.deploy_tool import DeployTool
from modules.tools.security_tool import SecurityTool
from modules.tools.coverage_tool import CoverageTool
from modules.tools.profiler_tool import ProfilerTool
from modules.tools.planner_tool import PlannerTool

from modules.tools.linter_tool import LinterTool
from modules.tools.formatter_tool import FormatterTool
from modules.tools.debugger_tool import DebuggerTool
from modules.tools.patch_tool import PatchTool
from modules.tools.snapshot_tool import SnapshotTool
from modules.tools.health_tool import HealthTool
from modules.tools.rag_tool import RAGTool
from modules.tools.verifier_tool import VerifierTool
from modules.tools.repair_tool import RepairTool
from modules.tools.monitor_tool import MonitorTool
from modules.tools.symbol_tool import SymbolTool
from modules.tools.xref_tool import XrefTool
from modules.tools.call_graph_tool import CallGraphTool
from modules.tools.dependency_tool import DependencyTool
from modules.tools.docker_tool import DockerTool
from modules.tools.db_migrate_tool import DbMigrateTool
from modules.tools.pkg_manager_tool import PkgManagerTool
from modules.tools.browser_tool import BrowserTool
from modules.tools.cicd_tool import CiCdTool
from modules.tools.benchmark_tool import BenchmarkTool
from modules.tools.code_review_tool import CodeReviewTool
from modules.tools.doc_gen_tool import DocGenTool
from modules.tools.coordinator_tool import CoordinatorTool
from modules.tools.confidence_tool import ConfidenceTool

from modules.tools.skill_tools import (
    ListSkillsTool, GetSkillTool, CreateSkillTool,
    UpdateSkillTool, DeleteSkillTool, ValidateSkillTool, TestSkillTool
)

# ─── 14 Core Financial Tools ─────────────────────────────────────────────────
from modules.tools.market_data_tool import MarketDataTool
from modules.tools.financial_data_tool import FinancialDataTool
from modules.tools.financial_news_tool import FinancialNewsTool
from modules.tools.financial_calculator_tool import FinancialCalculatorTool
from modules.tools.portfolio_tool import PortfolioTool
from modules.tools.technical_analysis_tool import TechnicalAnalysisTool
from modules.tools.fno_analytics_tool import FnOAnalyticsTool
from modules.tools.knowledge_search_tool import KnowledgeSearchTool
from modules.tools.finance_code_tool import FinanceCodeTool
from modules.tools.market_datetime_tool import MarketDateTimeTool
from modules.tools.document_parser_tool import DocumentParserTool
from modules.tools.database_query_tool import DatabaseQueryTool
from modules.tools.notification_tool import NotificationTool
from modules.tools.auth_permission_tool import AuthPermissionTool

registry = ToolRegistry()
registry.register(BashTool())
registry.register(FileReadTool())
registry.register(FileEditTool())
registry.register(WebSearchTool())
registry.register(ImageGenTool())
registry.register(HumanInput())
registry.register(GitTool())
registry.register(ASTTool())
registry.register(MemoryTool())
registry.register(LSPTool())
registry.register(SearchTool())
registry.register(FileTool())
registry.register(BuildTool())
registry.register(TestTool())
registry.register(DeployTool())
registry.register(SecurityTool())
registry.register(CoverageTool())
registry.register(ProfilerTool())
registry.register(PlannerTool())

registry.register(LinterTool())
registry.register(FormatterTool())
registry.register(DebuggerTool())
registry.register(PatchTool())
registry.register(SnapshotTool())
registry.register(HealthTool())
registry.register(RAGTool())
registry.register(VerifierTool())
registry.register(RepairTool())
registry.register(MonitorTool())
registry.register(SymbolTool())
registry.register(XrefTool())
registry.register(CallGraphTool())
registry.register(DependencyTool())
registry.register(DockerTool())
registry.register(DbMigrateTool())
registry.register(PkgManagerTool())
registry.register(BrowserTool())
registry.register(CiCdTool())
registry.register(BenchmarkTool())
registry.register(CodeReviewTool())
registry.register(DocGenTool())
registry.register(CoordinatorTool())
registry.register(ConfidenceTool())

registry.register(ListSkillsTool())
registry.register(GetSkillTool())
registry.register(CreateSkillTool())
registry.register(UpdateSkillTool())
registry.register(DeleteSkillTool())
registry.register(ValidateSkillTool())
registry.register(TestSkillTool())

# ─── 14 Core Financial Tools Registration ────────────────────────────────────
registry.register(MarketDataTool())
registry.register(FinancialDataTool())
registry.register(FinancialNewsTool())
registry.register(FinancialCalculatorTool())
registry.register(PortfolioTool())
registry.register(TechnicalAnalysisTool())
registry.register(FnOAnalyticsTool())
registry.register(KnowledgeSearchTool())
registry.register(FinanceCodeTool())
registry.register(MarketDateTimeTool())
registry.register(DocumentParserTool())
registry.register(DatabaseQueryTool())
registry.register(NotificationTool())
registry.register(AuthPermissionTool())

