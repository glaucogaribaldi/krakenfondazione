from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class GlobalStrategicIntent(BaseModel):
    intent_id: str
    raw_directive: str
    objective: str
    aggressiveness_score: float = Field(ge=0.0, le=1.0)
    exploration_score: float = Field(ge=0.0, le=1.0)
    volatility_tolerance: str
    concentration_preference: str
    timestamp: int

class MarketSnapshot(BaseModel):
    timestamp: int
    asset: str
    price: float
    features: Dict[str, float]
    portfolio_exposure_pct: float

class StrategistView(BaseModel):
    regime: str
    confidence: float
    rationale: str

class MentorAdvice(BaseModel):
    past_similar_trades_found: int
    success_rate_of_past_trades: float
    advice: str
    confidence: float
    active_belief_invoked: Optional[str] = None
    thesis: str

class TraderDecision(BaseModel):
    trader_view: str
    confidence: float
    disagrees_with: List[str] = []
    decision: Dict[str, Any] # action, pair, volume, invalidation_price
    
class DisagreementRecord(BaseModel):
    present: bool
    agents_against: List[str] = []

class T0DecisionRecord(BaseModel):
    decision_id: str
    timestamp: int
    intent_id: str
    market_snapshot: MarketSnapshot
    strategist_view: Optional[StrategistView] = None
    mentor_view: Optional[MentorAdvice] = None
    trader_decision: TraderDecision
    disagreement: DisagreementRecord

class T1OutcomeRecord(BaseModel):
    decision_id: str
    exit_timestamp: int
    pnl_pct: float
    mae_pct: float
    mfe_pct: float
    exit_reason: str

if __name__ == "__main__":
    # Test valid JSON schema generation
    print("MarketSnapshot Schema:")
    print(MarketSnapshot.schema_json(indent=2))
