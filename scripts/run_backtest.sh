#!/usr/bin/env bash
# 4 stratejiyi aynı dönemde çalıştır → karşılaştırma tablosu
# Usage: scripts/run_backtest.sh [config.json] [YYYYMMDD-]
set -e

CONFIG="${1:-user_data/config.okx.json}"
TIMERANGE="${2:-20260301-}"
FT="${FT:-freqtrade}"

echo "Config: $CONFIG"
echo "Timerange: $TIMERANGE"
echo

$FT backtesting \
    --config "$CONFIG" \
    --strategy-list \
        MeanReversionMTF \
        TrendContinuation \
        SqueezeBreakout \
        OrderFlowProxy \
    --timeframe 5m \
    --timerange "$TIMERANGE"
