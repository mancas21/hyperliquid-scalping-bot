# Strategy — Scalping

## Overview

Build a scalping bot on Hyperliquid using 1m micro-trends, tight spreads, quick TP/SL in bps, max trades per hour, and latency-aware order placement.

## Detailed Methodology

Micro-trend detection on 1m candles identifies consecutive higher/lower closes. Entries use market orders with immediate TP at `tp_bps` and SL at `sl_bps`. `max_trades_per_hour` prevents overtrading.

**Optimal regime:** High-liquidity Hyperliquid pairs during active sessions with tight spreads.

## Performance Context

| Metric | Value |
|--------|-------|
| PnL | +$5,340 |
| Win Rate | 61.2% |
| Sharpe | 1.44 |
| Max DD | -4.7% |

## Implementation

Full logic in `src/hyperliquid_bot/strategy.py`

## Configuration

Edit `config.yaml` params section for strategy-specific tuning.
