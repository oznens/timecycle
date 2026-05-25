#!/usr/bin/env bash
# Tek strateji için hyperopt — Sharpe loss + buy/sell/roi/stoploss spaces
# Usage: scripts/run_hyperopt.sh <Strategy> [epochs] [config.json]
set -e

STRAT="${1:?Strategy name required, e.g.: MeanReversionMTF}"
EPOCHS="${2:-300}"
CONFIG="${3:-user_data/config.okx.json}"
FT="${FT:-freqtrade}"

echo "Strategy: $STRAT  Epochs: $EPOCHS  Config: $CONFIG"

$FT hyperopt \
    --config "$CONFIG" \
    --strategy "$STRAT" \
    --hyperopt-loss SharpeHyperOptLoss \
    --spaces buy sell roi stoploss trailing \
    --epochs "$EPOCHS" \
    --timeframe 5m \
    --timerange 20260301- \
    --print-all

echo
echo "Best params:"
$FT hyperopt-show --best --no-details
