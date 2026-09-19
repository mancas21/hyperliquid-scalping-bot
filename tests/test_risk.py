from hyperliquid_bot.risk import RiskManager
from hyperliquid_bot.types import PositionSnapshot,RiskLimits

def pos(size=0,price=100): return PositionSnapshot("ETH",size,price,price,0,1)

def test_daily_loss_blocks():
    r=RiskManager(RiskLimits(max_daily_loss_usd=100))
    r.sync_realized_pnl(-100)
    assert r.can_trade(pos())[0] is False

def test_position_limit_blocks():
    r=RiskManager(RiskLimits(max_position_usd=100))
    assert r.can_trade(pos(2,100))[0] is False
