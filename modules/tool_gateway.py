"""
AARKAAI - Tool Gateway (FIX-9)

Resolves the Code Mode sandbox boundary violation: tool calls originating
from inside the Docker sandbox are dispatched through this gateway on the
host side. The gateway enforces per-tool isolation BEFORE executing any
side effects, so the sandbox boundary is meaningful.

Architecture:
    [Docker sandbox: user code]
        -> ToolProxy.__call__() -> JSON over stdin/stdout
        -> [Host: code_mode.py dispatch loop]
            -> ToolGateway.dispatch(tool_name, args, context)
                -> READ_ONLY tools  : path-validated, runs on host (low risk)
                -> EXEC tools       : re-enters a secondary sandbox container
                -> MUTATING tools   : requires ApprovalStore gate first

All dispatches emit an audit_event() entry regardless of outcome.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, Optional

from modules.security_audit import audit_event

logger = logging.getLogger(__name__)


class ToolClass(str, Enum):
    """Classification of a tool by its isolation requirement."""
    READ_ONLY = "READ_ONLY"      # Read filesystem/memory; no subprocess; no mutation
    EXEC = "EXEC"                # Spawns subprocess; must run in secondary sandbox
    MUTATING = "MUTATING"        # Writes files, deploys, or deletes; requires approval


# ─── Tool Classification Map ──────────────────────────────────────────────────
# Every tool that can be invoked from Code Mode must be listed here.
# Tools absent from this map default to MUTATING (deny-by-default via approval gate).
TOOL_CLASSIFICATIONS: Dict[str, ToolClass] = {
    # Read-only tools — safe to execute on host with scope validation
    "FileReadTool":             ToolClass.READ_ONLY,
    "SearchTool":               ToolClass.READ_ONLY,
    "ASTTool":                  ToolClass.READ_ONLY,
    "LSPTool":                  ToolClass.READ_ONLY,
    "XRefTool":                 ToolClass.READ_ONLY,
    "SymbolTool":               ToolClass.READ_ONLY,
    "CallGraphTool":            ToolClass.READ_ONLY,
    "KnowledgeSearchTool":      ToolClass.READ_ONLY,
    "MarketDataTool":           ToolClass.READ_ONLY,
    "FinancialCalculatorTool":  ToolClass.READ_ONLY,
    "MarketDateTimeTool":       ToolClass.READ_ONLY,
    "TechnicalAnalysisTool":    ToolClass.READ_ONLY,
    "FinancialNewsTool":        ToolClass.READ_ONLY,
    "FnOAnalyticsTool":         ToolClass.READ_ONLY,
    "DatabaseQueryTool":        ToolClass.READ_ONLY,
    "PortfolioTool":            ToolClass.READ_ONLY,
    "MemoryTool":               ToolClass.READ_ONLY,
    "HealthTool":               ToolClass.READ_ONLY,
    "VerifierTool":             ToolClass.READ_ONLY,
    "ConfidenceTool":           ToolClass.READ_ONLY,
    "AuthPermissionTool":       ToolClass.READ_ONLY,
    "RAGTool":                  ToolClass.READ_ONLY,
    "WebSearchTool":            ToolClass.READ_ONLY,
    "FinancialDataTool":        ToolClass.READ_ONLY,
    "SnapshotTool":             ToolClass.READ_ONLY,

    # Exec tools — spawn subprocesses; routed through secondary sandbox
    "BashTool":                 ToolClass.EXEC,
    "FinanceCodeTool":          ToolClass.EXEC,
    "LinterTool":               ToolClass.EXEC,
    "FormatterTool":            ToolClass.EXEC,
    "TestTool":                 ToolClass.EXEC,
    "CoverageTool":             ToolClass.EXEC,
    "ProfilerTool":             ToolClass.EXEC,
    "BenchmarkTool":            ToolClass.EXEC,
    "DebuggerTool":             ToolClass.EXEC,
    "BuildTool":                ToolClass.EXEC,
    "GitTool":                  ToolClass.EXEC,
    "PkgManagerTool":           ToolClass.EXEC,
    "DockerTool":               ToolClass.EXEC,
    "CICDTool":                 ToolClass.EXEC,

    # Mutating tools — filesystem writes, deployments; require approval gate
    "FileEditTool":             ToolClass.MUTATING,
    "PatchTool":                ToolClass.MUTATING,
    "FileTool":                 ToolClass.MUTATING,
    "FsTool":                   ToolClass.MUTATING,
    "CreateSkillTool":          ToolClass.MUTATING,
    "UpdateSkillTool":          ToolClass.MUTATING,
    "DeleteSkillTool":          ToolClass.MUTATING,
    "DeployTool":               ToolClass.MUTATING,
    "DbMigrateTool":            ToolClass.MUTATING,
    "NotificationTool":         ToolClass.MUTATING,
    "ImageTool":                ToolClass.MUTATING,
}


class ToolGatewayError(Exception):
    """Raised when the gateway blocks tool execution."""
    pass


class ToolGateway:
    """
    Host-side gateway that enforces isolation policy before executing any tool
    call originating from within the Code Mode Docker sandbox.

    Usage (in code_mode.py dispatch loop):
        gateway = ToolGateway(registry, approval_context, user_id, session_id)
        result = gateway.dispatch(tool_name, args)
    """

    def __init__(
        self,
        registry: Any,
        approval_context: Dict[str, Any],
        user_id: str,
        session_id: str,
        workspace_dir: str = "",
    ):
        self.registry = registry
        self.approval_context = approval_context or {}
        self.user_id = user_id
        self.session_id = session_id
        self.workspace_dir = workspace_dir

    def classify(self, tool_name: str) -> ToolClass:
        """Return the isolation class for a tool. Defaults to MUTATING (deny-by-default)."""
        return TOOL_CLASSIFICATIONS.get(tool_name, ToolClass.MUTATING)

    def dispatch(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Dispatch a tool call with the appropriate isolation level.

        - READ_ONLY: executed directly with scope validation
        - EXEC: re-routed through a secondary sandbox container
        - MUTATING: gated behind the ApprovalStore; blocked if not approved

        All calls produce an audit trail entry.
        """
        tool_class = self.classify(tool_name)

        audit_event(
            "gateway.dispatch",
            tool=tool_name,
            classification=tool_class.value,
            user_id=self.user_id,
            session_id=self.session_id,
        )

        if tool_class == ToolClass.READ_ONLY:
            return self._dispatch_read_only(tool_name, args)
        elif tool_class == ToolClass.EXEC:
            return self._dispatch_exec(tool_name, args)
        else:  # MUTATING
            return self._dispatch_mutating(tool_name, args)

    # ── READ_ONLY ──────────────────────────────────────────────────────────────

    def _dispatch_read_only(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute read-only tool directly. Validates path arguments are workspace-scoped."""
        self._validate_path_args(args)
        try:
            result = self.registry.execute_tool(tool_name, args)
            audit_event("gateway.executed", tool=tool_name, classification="READ_ONLY",
                        user_id=self.user_id, status="success")
            return result
        except Exception as e:
            audit_event("gateway.error", tool=tool_name, error=str(e)[:200],
                        user_id=self.user_id)
            raise

    # ── EXEC ──────────────────────────────────────────────────────────────────

    def _dispatch_exec(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Route EXEC tools through a secondary CodeModeExecutor sandbox.

        This ensures that subprocess-spawning tools (BashTool, FinanceCodeTool, etc.)
        run inside a container, not on the host application process.

        Falls back to direct execution with a SECURITY WARNING if Docker is unavailable
        and force_exec_fallback is set in approval_context. Otherwise fails closed.
        """
        force_fallback = self.approval_context.get("force_exec_fallback", False)

        try:
            from modules.code_mode import CodeModeExecutor, SandboxUnavailableError

            if not CodeModeExecutor.is_docker_available():
                if force_fallback:
                    logger.warning(
                        "SECURITY WARNING: Docker unavailable; EXEC tool '%s' running on host. "
                        "force_exec_fallback=True in approval_context.", tool_name
                    )
                    audit_event("gateway.exec_host_fallback", tool=tool_name,
                                user_id=self.user_id, warning="Docker unavailable, fallback active")
                    return self.registry.execute_tool(tool_name, args)
                else:
                    audit_event("gateway.blocked", tool=tool_name, reason="docker_unavailable",
                                user_id=self.user_id)
                    raise ToolGatewayError(
                        f"EXEC tool '{tool_name}' requires Docker sandbox. "
                        f"Docker is not available. Set force_exec_fallback=True in approval_context "
                        f"only if you have verified the host is sufficiently hardened."
                    )

            # Build a minimal code block that invokes the tool and returns its result.
            # The tool runs inside the container via the registry proxy mechanism.
            import json
            safe_args = json.dumps(args)
            code_block = (
                f"import json as _json\n"
                f"_args = _json.loads({safe_args!r})\n"
                f"_result = {tool_name}(**_args)\n"
                f"print(_result)\n"
            )

            # Build namespace with only this specific tool exposed
            executor = CodeModeExecutor(
                tool_registry=self.registry,
                workspace_dir=self.workspace_dir or ".",
                timeout=self.approval_context.get("exec_timeout", 30.0),
                max_tool_calls=1,
                max_output_bytes=524288,
            )
            namespace = executor.build_tool_namespace([tool_name])
            exec_result = executor.execute_code_block(
                code_block, namespace,
                user_id=self.user_id,
                session_id=self.session_id,
            )

            if exec_result.success:
                audit_event("gateway.executed", tool=tool_name, classification="EXEC",
                            user_id=self.user_id, status="success")
                return exec_result.output
            else:
                audit_event("gateway.exec_failed", tool=tool_name,
                            error=str(exec_result.error)[:200], user_id=self.user_id)
                raise ToolGatewayError(f"EXEC tool '{tool_name}' failed in sandbox: {exec_result.error}")

        except ToolGatewayError:
            raise
        except Exception as e:
            audit_event("gateway.error", tool=tool_name, error=str(e)[:200],
                        user_id=self.user_id)
            raise ToolGatewayError(f"Gateway error dispatching EXEC tool '{tool_name}': {e}") from e

    # ── MUTATING ──────────────────────────────────────────────────────────────

    def _dispatch_mutating(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Gate MUTATING tools behind the ApprovalStore.

        If human_approved=True is in approval_context, executes immediately.
        Otherwise creates an approval request and waits for resolution.
        Fails closed if approval is denied or times out.
        """
        # Check pre-approved flag
        if self.approval_context.get("human_approved", False):
            audit_event("gateway.pre_approved", tool=tool_name, user_id=self.user_id)
            return self.registry.execute_tool(tool_name, args)

        # Check CI token
        ci_token = self.approval_context.get("ci_token")
        signing_key = self.approval_context.get("ci_signing_key", "")
        if ci_token and signing_key:
            try:
                from modules.ci_nonce_store import verify_ci_approval_token, CINonceStore
                from pathlib import Path
                nonce_db = Path(self.approval_context.get("ci_nonce_db", "var/ci_nonces.db"))
                store = CINonceStore(nonce_db)
                valid, reason = verify_ci_approval_token(
                    token=ci_token,
                    signing_keys={"k1": signing_key},
                    expected_repo=self.approval_context.get("repo", ""),
                    expected_commit=self.approval_context.get("commit_sha", ""),
                    nonce_store=store,
                )
                if valid:
                    audit_event("gateway.ci_approved", tool=tool_name, user_id=self.user_id)
                    return self.registry.execute_tool(tool_name, args)
                else:
                    audit_event("gateway.ci_rejected", tool=tool_name,
                                reason=reason, user_id=self.user_id)
                    raise ToolGatewayError(f"CI approval token rejected for '{tool_name}': {reason}")
            except ToolGatewayError:
                raise
            except Exception as e:
                logger.warning("CI token verification error: %s", e)

        # Interactive approval via ApprovalStore
        if self.approval_context.get("interactive_approval", False):
            from modules.approval_store import get_approval_store
            approval_store = get_approval_store()

            cmd_preview = args.get("command", args.get("cmd", ""))
            diff_preview = args.get("diff", args.get("content", ""))
            target_res = args.get("path", args.get("target", ""))

            summary_map = {
                "FileEditTool": f"Modify file: {target_res}",
                "DeployTool": f"Deploy to: {target_res}",
                "DeleteSkillTool": f"Delete skill: {args.get('name', '')}",
            }
            summary = summary_map.get(tool_name, f"Execute mutating tool: {tool_name}")
            risk = "CRITICAL" if tool_name in ("DeployTool", "DeleteSkillTool") else "HIGH"

            record = approval_store.create_request(
                user_id=self.user_id,
                session_id=self.session_id,
                tool_name=tool_name,
                args=args,
                risk_level=risk,
                human_summary=summary,
                workspace_id=self.approval_context.get("workspace_id", "default"),
                target_resource=target_res,
                diff_preview=diff_preview or None,
                command_preview=cmd_preview or None,
                timeout_seconds=float(self.approval_context.get("approval_timeout", 60.0)),
            )

            emitter = self.approval_context.get("event_emitter")
            if callable(emitter):
                try:
                    emitter({"type": "approval_request", "payload": record.to_dict()})
                except Exception as emit_err:
                    logger.warning("Failed emitting approval_request: %s", emit_err)

            approved, reason = approval_store.await_resolution(
                approval_id=record.approval_id,
                expected_action_hash=record.action_hash,
                timeout_seconds=float(self.approval_context.get("approval_timeout", 60.0)),
            )

            if approved:
                audit_event("gateway.approved", tool=tool_name, user_id=self.user_id,
                            approval_id=record.approval_id)
                result = self.registry.execute_tool(tool_name, args)
                audit_event("gateway.executed", tool=tool_name, classification="MUTATING",
                            user_id=self.user_id, status="success")
                return result
            else:
                audit_event("gateway.denied", tool=tool_name, user_id=self.user_id,
                            reason=reason, approval_id=record.approval_id)
                raise ToolGatewayError(
                    f"Mutating tool '{tool_name}' was not approved: {reason}"
                )

        # No approval mechanism configured — fail closed
        audit_event("gateway.blocked", tool=tool_name,
                    reason="no_approval_mechanism", user_id=self.user_id)
        raise ToolGatewayError(
            f"Mutating tool '{tool_name}' requires an approval gate. "
            f"Set human_approved=True, provide a ci_token, or enable interactive_approval "
            f"in the approval_context."
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate_path_args(self, args: Dict[str, Any]) -> None:
        """
        Validate that any 'path' or 'file' argument in args does not escape the workspace.
        Raises ToolGatewayError on path traversal attempts.
        """
        if not self.workspace_dir:
            return
        from pathlib import Path
        workspace = Path(self.workspace_dir).resolve()
        for key in ("path", "file", "filepath", "target", "src", "dst"):
            val = args.get(key)
            if val and isinstance(val, str):
                try:
                    resolved = (workspace / val).resolve()
                    if not resolved.is_relative_to(workspace):
                        audit_event("gateway.path_traversal_blocked",
                                    key=key, value=val[:100], user_id=self.user_id)
                        raise ToolGatewayError(
                            f"Path traversal detected in argument '{key}': '{val}' "
                            f"resolves outside workspace boundary."
                        )
                except ToolGatewayError:
                    raise
                except Exception:
                    pass  # Non-path values may fail resolve safely
