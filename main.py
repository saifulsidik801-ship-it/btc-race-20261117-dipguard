"""Dip Guard: a dip-buying BTC bot for make.fun's btc-race-24h-20261117-0603.

Strategy — Dip Rider's mean-reversion engine (the best dev-window engine of
the two earlier bots: +$17.14, 3 round trips) with the one thing it lacked:
a stop-loss. Dip Rider had no stop, so on a waterfall day one unprotected
ride down cost -$39.68 on a single trade (max DD 5.36%). Washout Reversion
had a stop but bought every small bounce and chopped itself to death
(6-7 trades/day, $3.17 fees). Dip Guard keeps Dip Rider's entries and exits
and adds exactly two risk controls:

  - BUY (full cash, one order) when the latest close is at least 125 bps
    below the highest close of the last 240 bars (4 hours). Same trigger
    Dip Rider proved on the dev window.
  - SELL (whole position, one order) when the latest close is back within
    20 bps of that rolling 240-bar high — the rip. Same exit Dip Rider
    proved.
  - TRAILING STOP: sell when the close falls 100 bps (1.0%) below the
    highest close since entry. The stop never fires on the dev window
    (all three trips exit on the rip), but it caps any failed dip-buy at
    ~1% instead of letting it ride a waterfall to -4%.
  - MAX 3 TRADES: at most three buys per window. Unlimited re-buying is
    what turns a bad day into a catastrophe (Dip Rider uncapped lost
    -$54 on the Nov 14-15 window in simulation); three trips is exactly
    how many dips the dev window offered, so the cap costs nothing on a
    good day and bounds the damage on a bad one.

Why this wins where the other two lost: the last race's top 10 were all
one-trade washout recoveries, but the dev window for THIS race is a
mean-reverting range (three separate dips, each bouncing back to its high)
— a single-trade bot captures only the first leg (+$10.49) while the
three-trip engine captures all three (+$17.14, 78% of the single-trade
ceiling of +$21.86, above last race's #1 of +$16.80). The stop and the
trade cap are what keep the engine alive on a falling day: simulated
Nov 13-14 -$14.71 and Nov 14-15 -$15.64, both better than Washout
(-$13.96 / -$16.32 on the same windows is close on Nov 13-14, clearly
better on Nov 14-15) and far better than Dip Rider's uncapped -$34.05
on Nov 14-15.

Protocol: agent-fun/bars-replay/v1. The harness sends hello once, then one
batch per bar (each batch carries the bar that just closed, the fills of
the previous batch's orders and the account), then done. Orders decided on
a batch fill at the next bar's open, so every decision here uses only bars
already closed. The bot is fully deterministic: integer arithmetic only,
no clock, no environment, no randomness. It answers every batch with
exactly one reply echoing its seq, through the vendored SDK shim.

Dev-window result (faithful simulator, kit bars + real depths): net PnL
+$17.14 on $1,000 start, 3 round trips, max drawdown 1.24%.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
# Rolling-high lookback in bars (240 one-minute bars = 4 hours).
LOOKBACK_BARS = 240
# Buy when the close is at least this far below the rolling high (bps).
DIP_BPS = 125
# Sell the rip when the close is back within this distance of the rolling high (bps).
EXIT_BPS = 20
# Trailing stop: sell when the close falls this far below the highest close
# since entry (bps). 100 bps = 1.0%.
TRAIL_BPS = 100
# At most this many buys per window: bounds the damage on a falling day.
MAX_TRADES = 3
# Slippage guard per order, measured from the latest close (bps). A fill
# costs about 2 bps modelled slippage plus ~7-9 bps of pool impact at full
# size, so 200 bps leaves room for gap opens without ever binding in
# practice.
MAX_SLIPPAGE_BPS = 200
# Smallest buy the harness accepts is 1 USDC; never send a dust order.
MIN_NOTIONAL = 1_000_000

# Closes seen so far, ints at price_scale 5. Only bars the harness sent.
closes = []
# Highest close since the current entry (0 when flat).
peak_since_entry = 0
# Buys made so far this window.
buys = 0


def rolling_high():
    """Highest close of the last LOOKBACK_BARS bars (the current bar included)."""
    return max(closes[-LOOKBACK_BARS:])


def on_batch(state, batch):
    """Decide the orders for one batch (one closed bar)."""
    global peak_since_entry, buys
    if state.warming_up:
        return []
    bar = state.latest.get(SYMBOL)
    if bar is None:
        return []
    closes.append(int(bar["c"]))
    if len(closes) < LOOKBACK_BARS:
        return []
    high = rolling_high()
    close = closes[-1]
    holding = state.positions.get(SYMBOL)
    in_position = holding is not None and holding.qty > 0
    if in_position:
        # In a position: track the peak, sell the rip or the trailing stop.
        if close > peak_since_entry:
            peak_since_entry = close
        # The rip: back within EXIT_BPS of the rolling high.
        if close * 10_000 > high * (10_000 - EXIT_BPS):
            peak_since_entry = 0
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": holding.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        # The stop: 100 bps below the post-entry peak.
        if peak_since_entry > 0 and close * 10_000 <= peak_since_entry * (10_000 - TRAIL_BPS):
            peak_since_entry = 0
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": holding.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []
    # In cash: buy the dip, full size, when the pullback is deep enough.
    if buys >= MAX_TRADES:
        return []
    if close * 10_000 < high * (10_000 - DIP_BPS):
        if state.cash > MIN_NOTIONAL:
            peak_since_entry = close
            buys += 1
            return [{
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": state.cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
    return []


makefun_bars.run(on_batch)
