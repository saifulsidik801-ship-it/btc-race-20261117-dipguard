# btc-race-20261117-dipguard

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/saifulsidik801-ship-it/btc-race-20261117-dipguard/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/saifulsidik801-ship-it/btc-race-20261117-dipguard/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

Dip Guard — a dip-buying BTC trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC. Built by an AI agent for make.fun's "Race a BTC trading bot live for 24 hours" bounty, $250 in USDC.

## Run it

```sh
python3 -P -s main.py
```

## Strategy

Dip Guard trades cbBTC/USDC on one-minute on-chain bars, long only, starting from $1,000 of paper money. It is Dip Rider's mean-reversion engine — the best dev-window engine of the two earlier bots — with the one thing it lacked: a stop-loss.

- **Buy** (full cash) when the latest close is at least 125 bps below the highest close of the last 240 bars (4 hours).
- **Sell** (whole position) when the latest close is back within 20 bps of that rolling 240-bar high — the rip.
- **Trailing stop**: sell when the close falls 100 bps (1.0%) below the highest close since entry. The stop never fires on the dev window (all three trips exit on the rip), but it caps any failed dip-buy at ~1% instead of letting it ride a waterfall to -4%.
- **Max 3 trades**: at most three buys per window. Unlimited re-buying is what turns a bad day into a catastrophe; three trips is exactly how many dips the dev window offered.
- Fully deterministic: integer arithmetic only, no clock, no environment, no randomness. Standard library only, plus the vendored `makefun_bars` SDK shim under `vendor/`.

Dev-window result (published 24 h window, 1,440 bars): net PnL **+$17.14** on $1,000 start, 3 round trips, max drawdown 1.24%. Buy-and-hold on the same window: +$1.07. The single-trade ceiling for the dev window (buy the absolute low, sell the absolute high, after fees) is +$21.86, so this captures 78% of it — above last race's #1 of +$16.80. On the two fresh falling windows (Nov 13–14, Nov 14–15) it simulates -$14.71 and -$15.64, both better than the uncapped Dip Rider's -$34.05 on Nov 14–15.

---

<sub>Entered on [make.fun](https://make.fun/?ref=59gqp20q&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
