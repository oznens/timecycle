#!/usr/bin/env bash
# 3 stratejiyi sırayla hyperopt (15-pair config, single-thread for stability)
set -e

FT="${FT:-/opt/ftvenv/bin/freqtrade}"
CONFIG="${CONFIG:-user_data/config.okx_partial.json}"
EPOCHS="${EPOCHS:-50}"
TIMERANGE="${TIMERANGE:-20260301-}"

for STRAT in TrendContinuation SqueezeBreakout OrderFlowProxy; do
    echo
    echo "==================== $STRAT ===================="
    $FT hyperopt --config "$CONFIG" --strategy "$STRAT" \
        --hyperopt-loss SharpeHyperOptLoss \
        --spaces buy roi stoploss \
        --epochs "$EPOCHS" --timeframe 5m \
        --timerange "$TIMERANGE" -j 1 \
        > "/tmp/hyperopt_${STRAT}.log" 2>&1
    echo "Done. Log: /tmp/hyperopt_${STRAT}.log"
    grep -A 35 "Best result" "/tmp/hyperopt_${STRAT}.log" | head -45
done

echo
echo "===== ALL DONE ====="
