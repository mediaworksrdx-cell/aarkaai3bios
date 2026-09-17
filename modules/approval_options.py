"""
AARKAAI – Dynamic Contextual Approval Options Engine.
Synthesizes query-specific, domain-tailored, and model-aware authorization choices
for Aarka Autonomous Engine, Gemini Pro/Flash, and Claude Sonnet/Opus.
"""
from typing import List, Dict, Any

def detect_model_persona(model_name: str = "") -> Dict[str, str]:
    """Detects provider persona branding and badging."""
    norm = (model_name or "aarka").lower()
    if "claude" in norm:
        return {
            "provider": "claude",
            "name": "Claude Sonnet",
            "badge": "Claude · Constitutional Safety",
            "badge_color": "border-[#D97706]/40 bg-[#D97706]/15 text-[#F59E0B]",
            "accent_color": "#D97706",
            "agent_ref": "Claude",
        }
    elif "gemini" in norm:
        return {
            "provider": "gemini",
            "name": "Gemini Pro",
            "badge": "Gemini · Multimodal Verification",
            "badge_color": "border-indigo-500/40 bg-indigo-500/15 text-indigo-400",
            "accent_color": "#6366F1",
            "agent_ref": "Gemini",
        }
    else:
        return {
            "provider": "aarka",
            "name": "Aarka AI",
            "badge": "Aarka Engine · Autonomous Execution",
            "badge_color": "border-teal-500/40 bg-teal-500/15 text-teal-400",
            "accent_color": "#14B8A6",
            "agent_ref": "Aarka",
        }


def generate_dynamic_approval_options(
    query: str,
    tool_name: str,
    args: Dict[str, Any],
    model_name: str = "aarka"
) -> List[Dict[str, Any]]:
    """Generates 5 context-rich, query-tailored options for human authorization."""
    persona = detect_model_persona(model_name)
    agent = persona["agent_ref"]
    query_clean = query.strip()
    query_low = query_clean.lower()

    if tool_name == "FileEditTool":
        path = str(args.get("path", "workspace_file.py"))
        is_py = path.endswith(".py")
        
        topic = "script"
        if "healthcheck" in query_low or "disk" in query_low:
            topic = "disk health monitor script"
        elif "test" in query_low:
            topic = "test suite"
        elif "api" in query_low or "server" in query_low:
            topic = "API service"
        elif "clean" in query_low or "format" in query_low:
            topic = "utility script"

        return [
            {
                "id": 1,
                "action": "allow_once",
                "label": f"Allow & save '{path}' to workspace",
                "detail": f"Write verified {topic} directly into the workspace root.",
                "recommended": True,
            },
            {
                "id": 2,
                "action": "allow_and_run" if is_py else "allow_in_conversation",
                "label": f"Save '{path}' and execute immediately ({'python ' + path if is_py else 'inspect in workspace'})",
                "detail": "Atomic disk write followed by automatic execution in sandbox.",
            },
            {
                "id": 3,
                "action": "customize",
                "label": f"Inspect & customize '{path}' code before committing",
                "detail": "Review diff lines, modify parameters, or adjust imports.",
            },
            {
                "id": 4,
                "action": "always_allow",
                "label": f"Always allow workspace file modifications in this session (Always Allow)",
                "detail": f"Auto-approves future file writes by {agent} for the remainder of this session.",
            },
            {
                "id": 5,
                "action": "deny",
                "label": f"No (tell {agent} what to do instead)",
                "detail": "Reject this file write and provide alternate requirements or corrections.",
            },
        ]

    elif tool_name == "BashTool":
        cmd = str(args.get("command", "")).strip()
        cmd_short = cmd[:45] + "..." if len(cmd) > 45 else cmd

        is_test = any(k in cmd.lower() for k in ["pytest", "test", "jest", "vitest"])
        is_build = any(k in cmd.lower() for k in ["npm run build", "make", "compile", "docker"])
        is_read = any(cmd.lower().startswith(k) for k in ["ls", "cat", "git status", "find", "grep", "echo"])

        action_type = "read command" if is_read else "test suite" if is_test else "build command" if is_build else "shell command"

        return [
            {
                "id": 1,
                "action": "allow_once",
                "label": f"Execute '{cmd_short}' in isolated sandbox",
                "detail": f"Run {action_type} safely within workspace execution constraints.",
                "recommended": True,
            },
            {
                "id": 2,
                "action": "allow_and_stream",
                "label": f"Execute '{cmd_short}' and stream live terminal output",
                "detail": "Stream stdout & stderr chunks directly to chat console.",
            },
            {
                "id": 3,
                "action": "customize",
                "label": "Edit command parameters before execution",
                "detail": "Modify flags, arguments, or environment variables.",
            },
            {
                "id": 4,
                "action": "always_allow",
                "label": f"Always allow '{cmd_short}' in this session (Always Allow)",
                "detail": "Whitelist this command pattern to prevent redundant authorization gates.",
            },
            {
                "id": 5,
                "action": "deny",
                "label": f"No (tell {agent} what to do instead)",
                "detail": "Halt command execution and redirect agent workflow.",
            },
        ]

    elif tool_name == "DeployTool":
        target = str(args.get("target", "production")).strip()
        return [
            {
                "id": 1,
                "action": "allow_once",
                "label": f"Proceed with deployment to {target}",
                "detail": "Initiate production container build and service rollout.",
                "recommended": True,
            },
            {
                "id": 2,
                "action": "dry_run",
                "label": "Run pre-flight dry-run validation check first",
                "detail": "Verify credentials, routing rules, and dependencies before deploying.",
            },
            {
                "id": 3,
                "action": "customize",
                "label": "Inspect & edit deployment environment variables",
                "detail": "Review manifest configurations and ingress policies.",
            },
            {
                "id": 4,
                "action": "always_allow",
                "label": f"Always allow automated deployments to {target} this session (Always Allow)",
                "detail": "Trust this deployment pipeline for current session.",
            },
            {
                "id": 5,
                "action": "deny",
                "label": f"No (tell {agent} what to do instead)",
                "detail": "Cancel rollout and preserve previous stable version.",
            },
        ]

    elif tool_name == "FinanceStrategyMasterSelection":
        candidates = args.get("candidates", [])
        master = args.get("master_recommended", "")
        master_cand = next((c for c in candidates if c.get("candidate_id") == master), candidates[0] if candidates else {})
        strat_name = master_cand.get("strategy_name", "Master Algorithmic Strategy")

        return [
            {
                "id": 1,
                "action": "allow_once",
                "label": f"Execute Master Strategy ({strat_name})",
                "detail": f"Optimal win rate: {master_cand.get('win_rate_est', '74%')} • Max loss: {master_cand.get('max_loss_per_lot', '₹2,200')}.",
                "recommended": True,
            },
            {
                "id": 2,
                "action": "select_alternative",
                "label": "Execute Alternative Directional Momentum Breakout Ladder",
                "detail": "Higher momentum breakout strategy with dynamic trail stop.",
            },
            {
                "id": 3,
                "action": "customize",
                "label": "Customize strike prices, premium limits & expiry dates",
                "detail": "Manually tune legs, lots, and risk allocation.",
            },
            {
                "id": 4,
                "action": "always_allow",
                "label": "Always auto-execute strategies matching risk profile (Always Allow)",
                "detail": "Authorize automated multi-leg position sizing within risk limit.",
            },
            {
                "id": 5,
                "action": "deny",
                "label": f"No (tell {agent} what to do instead)",
                "detail": "Reject strategy recommendation and scan alternative sectors.",
            },
        ]

    else:
        return [
            {
                "id": 1,
                "action": "allow_once",
                "label": f"Allow execution of {tool_name}",
                "detail": f"Authorize single execution of {tool_name} with specified parameters.",
                "recommended": True,
            },
            {
                "id": 2,
                "action": "allow_in_conversation",
                "label": f"Allow {tool_name} for this task in conversation",
                "detail": "Permits sequential steps without prompt interruption.",
            },
            {
                "id": 3,
                "action": "customize",
                "label": f"Inspect & modify {tool_name} arguments",
                "detail": "Review and edit payload parameters before execution.",
            },
            {
                "id": 4,
                "action": "always_allow",
                "label": f"Always allow {tool_name} in this session (Always Allow)",
                "detail": f"Auto-approves {tool_name} calls for remainder of session.",
            },
            {
                "id": 5,
                "action": "deny",
                "label": f"No (tell {agent} what to do instead)",
                "detail": "Cancel action and request an alternative solution.",
            },
        ]