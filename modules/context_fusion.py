from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from modules.query_understanding import DataSource, SubQuery, SourceResult, QueryPlan
from config import HQR_CONTEXT_BUDGET

logger = logging.getLogger(__name__)


@dataclass
class FusedContext:
    """Result of context fusion."""
    context: str              # The merged context string for the LLM prompt
    sources_used: list[str]   # List of source names that contributed
    total_chars: int          # Total character count
    source_count: int         # Number of distinct sources
    metadata: dict[str, Any] = field(default_factory=dict)  # Timing, dedup stats, etc.


class ContextFusion:
    def __init__(self) -> None:
        self.priority_map = {
            DataSource.MARKET_API: 10,
            DataSource.FINANCIAL_TOOL: 20,
            DataSource.MONGODB: 30,
            DataSource.NEWS_SEARCH: 40,
            DataSource.RAG: 50,
            DataSource.WEB_SEARCH: 60,
            DataSource.CODE_EXECUTION: 70,
            DataSource.MODEL_ONLY: 100,
        }

    def _get_priority(self, result: SourceResult, plan: QueryPlan) -> int:
        """Get priority score for a result (lower means higher priority)."""
        base_priority = self.priority_map.get(result.source, 100)
        
        if self._is_required(result, plan):
            base_priority -= 100
            
        return base_priority

    def _is_required(self, result: SourceResult, plan: QueryPlan) -> bool:
        """Check if the given result comes from a required sub-query."""
        if hasattr(result, "sub_query_id"):
            for sq in plan.sub_queries:
                if sq.id == result.sub_query_id:
                    return bool(sq.required)
        else:
            # Fallback mapping if sub_query_id is not explicitly attached
            for sq in plan.sub_queries:
                if sq.source_type == result.source:
                    return bool(sq.required)
        return False

    def _sentence_overlap(self, text_a: str, text_b: str) -> float:
        """Returns 0.0-1.0 ratio of overlapping sentences between two text blocks."""
        def get_sentences(text: str) -> set[str]:
            # Simple sentence splitting on punctuation
            sentences = re.split(r'(?<=[.!?])\s+', text)
            return {s.strip().lower() for s in sentences if len(s.strip()) > 5}
            
        set_a = get_sentences(text_a)
        set_b = get_sentences(text_b)
        
        if not set_a or not set_b:
            return 0.0
            
        intersection = set_a.intersection(set_b)
        smaller_set_len = min(len(set_a), len(set_b))
        
        if smaller_set_len == 0:
            return 0.0
            
        return len(intersection) / smaller_set_len

    def _estimate_article_count(self, text: str) -> int:
        """Estimates the number of articles/results in a text block by counting numbered items or double-newlines."""
        if not text:
            return 0
        numbered_items = len(re.findall(r'(?m)^\s*\d+\.', text))
        double_newlines = len(re.findall(r'\n\s*\n', text.strip())) + 1
        return max(numbered_items, double_newlines)

    def format_source_label(self, source: DataSource, metadata: dict[str, Any]) -> str:
        """Returns the attribution header string for a given source."""
        if source == DataSource.MARKET_API:
            symbol = metadata.get("params", {}).get("symbol", "Live")
            return f"[Market Data — {symbol}]"
        elif source == DataSource.NEWS_SEARCH:
            count = metadata.get("count", "several")
            return f"[News — {count} articles]"
        elif source == DataSource.MONGODB:
            desc = metadata.get("description", "data")
            return f"[User Data — {desc}]"
        elif source == DataSource.RAG:
            count = metadata.get("count", "several")
            return f"[Knowledge Base — {count} entries]"
        elif source == DataSource.FINANCIAL_TOOL:
            tool_name = metadata.get("tool_name", "tool")
            return f"[Financial Analysis — {tool_name}]"
        elif source == DataSource.WEB_SEARCH:
            count = metadata.get("count", "several")
            return f"[Web Search — {count} results]"
        elif source == DataSource.CODE_EXECUTION:
            return "[Code Execution Result]"
        else:
            return f"[{source.name if hasattr(source, 'name') else str(source)}]"

    def fuse(
        self,
        results: list[SourceResult],
        plan: QueryPlan,
        chat_history: list[dict[str, Any]] | None = None,
        user_facts: str = "",
    ) -> FusedContext:
        """Merges results from multiple data sources into a single coherent context string."""
        if not results:
            return FusedContext(
                context="",
                sources_used=[],
                total_chars=0,
                source_count=0,
                metadata={"dedup_count": 0, "truncated_sources": [], "budget_used_pct": 0.0}
            )

        # Step 1: Filter Invalid Results
        valid_results: list[SourceResult] = []
        for res in results:
            if not getattr(res, "is_valid", True):
                logger.warning(f"ContextFusion: Filtering invalid result from {res.source}")
                continue
            if not res.data or not str(res.data).strip():
                logger.warning(f"ContextFusion: Filtering empty result from {res.source}")
                continue
            valid_results.append(res)

        # Step 2: Source Priority Ordering
        valid_results.sort(key=lambda x: self._get_priority(x, plan))

        # Step 3: Deduplication
        dedup_count = 0
        final_results: list[SourceResult] = []
        
        for current_res in valid_results:
            is_duplicate = False
            
            for accepted_res in final_results:
                # URL deduplication between NEWS_SEARCH and WEB_SEARCH
                if (current_res.source in (DataSource.NEWS_SEARCH, DataSource.WEB_SEARCH) and 
                    accepted_res.source in (DataSource.NEWS_SEARCH, DataSource.WEB_SEARCH)):
                    
                    curr_urls = set(current_res.metadata.get("urls", [])) if current_res.metadata else set()
                    acc_urls = set(accepted_res.metadata.get("urls", [])) if accepted_res.metadata else set()
                    
                    if curr_urls and acc_urls and curr_urls.intersection(acc_urls):
                        is_duplicate = True
                        break
                
                # Text-level dedup (>70% sentence overlap)
                overlap = self._sentence_overlap(str(current_res.data), str(accepted_res.data))
                if overlap > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                final_results.append(current_res)
            else:
                dedup_count += 1
                
        if dedup_count > 0:
            logger.info(f"ContextFusion: Deduplicated {dedup_count} overlapping results")

        # Step 4: Context Budget Allocation
        required_results = [r for r in final_results if self._is_required(r, plan)]
        optional_results = [r for r in final_results if not self._is_required(r, plan)]
        
        req_budget = 0
        opt_budget = 0
        
        if required_results and optional_results:
            req_budget = int(HQR_CONTEXT_BUDGET * 0.6)
            opt_budget = HQR_CONTEXT_BUDGET - req_budget
        elif required_results:
            req_budget = HQR_CONTEXT_BUDGET
        elif optional_results:
            opt_budget = HQR_CONTEXT_BUDGET

        req_quota = req_budget // len(required_results) if required_results else 0
        opt_quota = opt_budget // len(optional_results) if optional_results else 0
        
        truncated_sources = []
        processed_blocks = []
        sources_used = set()
        total_data_chars = 0
        
        for res in final_results:
            quota = req_quota if self._is_required(res, plan) else opt_quota
            
            if quota < 200:
                logger.warning(f"ContextFusion: Skipping {res.source} due to low budget quota ({quota} < 200)")
                continue
                
            text = str(res.data).strip()
            if len(text) > quota:
                text = text[:quota - 15] + "... [truncated]"
                truncated_sources.append(str(res.source))
                
            if not text:
                continue
                
            # Step 5: Source Attribution Tags
            metadata = res.metadata or {}
            if res.source in (DataSource.NEWS_SEARCH, DataSource.WEB_SEARCH, DataSource.RAG):
                if "count" not in metadata:
                    metadata["count"] = self._estimate_article_count(text)
                    
            tag = self.format_source_label(res.source, metadata)
            block = f"{tag}\n{text}"
            
            processed_blocks.append(block)
            sources_used.add(res.source.value if hasattr(res.source, 'value') else str(res.source).lower())
            total_data_chars += len(block)
            
        # Step 6 & 7: Chat History & User Facts Injection
        final_parts = []
        
        if chat_history:
            recent_history = chat_history[-6:]
            history_lines = ["[Conversation History]"]
            has_content = False
            for msg in recent_history:
                role = str(msg.get("role", "User")).capitalize()
                content = str(msg.get("message", msg.get("content", ""))).strip()
                if content:
                    has_content = True
                    history_lines.append(f"{role}: {content}")
            if has_content:
                final_parts.append("\n".join(history_lines))
                
        if user_facts and user_facts.strip():
            final_parts.append(f"[User Profile]\n{user_facts.strip()}")
            
        # Step 8: Final Assembly
        final_parts.extend(processed_blocks)
        
        final_context = "\n\n".join(final_parts)
        used_pct = (total_data_chars / HQR_CONTEXT_BUDGET) * 100 if HQR_CONTEXT_BUDGET > 0 else 0.0
        
        sources_list = sorted(list(sources_used))
        
        logger.info(f"ContextFusion: {len(sources_list)} sources, {len(final_context)} chars, budget {used_pct:.0f}% used")
        
        return FusedContext(
            context=final_context,
            sources_used=sources_list,
            total_chars=len(final_context),
            source_count=len(sources_list),
            metadata={
                "dedup_count": dedup_count,
                "truncated_sources": truncated_sources,
                "budget_used_pct": used_pct
            }
        )
