from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional

from modules.screener.strategies import (
    GoldenCrossMomentum, BreakoutVolumeSurge, EarningsMomentum, SupertrendBuy, AccumulationBreakout,
    DeathCrossDistribution, BreakdownVolumeSurge, EarningsDeterioration, SupertrendSell, DistributionBreakdown,
    RangeBoundMeanReversion, FairValueZone, LowVolatilityDividend, ConsolidationSqueeze, SectorRelativeStability,
    BullishRSIDivergence, BearishRSIDivergence, HammerEngulfingReversal, OverboughtReversal, VWAPReclaimReversal
)
from modules.screener.schemas import StrategyCategory

logger = logging.getLogger(__name__)

class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies = {
            GoldenCrossMomentum.name: GoldenCrossMomentum(),
            BreakoutVolumeSurge.name: BreakoutVolumeSurge(),
            EarningsMomentum.name: EarningsMomentum(),
            SupertrendBuy.name: SupertrendBuy(),
            AccumulationBreakout.name: AccumulationBreakout(),
            
            DeathCrossDistribution.name: DeathCrossDistribution(),
            BreakdownVolumeSurge.name: BreakdownVolumeSurge(),
            EarningsDeterioration.name: EarningsDeterioration(),
            SupertrendSell.name: SupertrendSell(),
            DistributionBreakdown.name: DistributionBreakdown(),
            
            RangeBoundMeanReversion.name: RangeBoundMeanReversion(),
            FairValueZone.name: FairValueZone(),
            LowVolatilityDividend.name: LowVolatilityDividend(),
            ConsolidationSqueeze.name: ConsolidationSqueeze(),
            SectorRelativeStability.name: SectorRelativeStability(),
            
            BullishRSIDivergence.name: BullishRSIDivergence(),
            BearishRSIDivergence.name: BearishRSIDivergence(),
            HammerEngulfingReversal.name: HammerEngulfingReversal(),
            OverboughtReversal.name: OverboughtReversal(),
            VWAPReclaimReversal.name: VWAPReclaimReversal()
        }
        
    def get(self, name: str) -> Optional[Any]:
        """Get a strategy by its snake_case name."""
        return self._strategies.get(name)
        
    def get_by_category(self, category: StrategyCategory | str) -> List[Any]:
        """Get all strategies in a specific category."""
        target_category = category if isinstance(category, StrategyCategory) else StrategyCategory(category)
        return [s for s in self._strategies.values() if s.category == target_category]
        
    def get_all(self) -> List[Any]:
        """Get all strategy instances."""
        return list(self._strategies.values())
        
    def list_names(self) -> List[str]:
        """List all registered strategy names."""
        return list(self._strategies.keys())
        
    def list_strategies_info(self) -> List[Dict[str, str]]:
        """Return basic info for all registered strategies."""
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "category": s.category.value if isinstance(s.category, StrategyCategory) else s.category,
                "description": s.description
            }
            for s in self._strategies.values()
        ]
