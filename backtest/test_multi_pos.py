"""
单仓 vs 2仓 vs 3仓 对比测试
最优参数: W20, R²≥0.4, 斜率≥0.02%, MA20过滤, 止损MA20×0.93, 换仓2.5x
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backtest.market_sim_gem import generate_prices
from backtest.momentum_engine import run_backtest, run_backtest_multi, compute_stats

N_DAYS   = 1820
INITIAL  = 1_000_000
N_STOCKS = 200
N_SEEDS  = 15

# 最优单仓参数
BEST_PARAMS = dict(
    trend_window=20, min_r2=0.4, min_slope=0.0002,
    ma_price_filter=20, pullback_lo=-0.99, pullback_hi=0.99,
    vol_mult=99.0, slope_accel=0.0, min_hold=3,
    ma_stop=20, ma_stop_pct=0.07, switch_ratio=2.5, mkt_ma=0,
)

MULTI_PARAMS = dict(
    trend_window=20, min_r2=0.4, min_slope=0.0002,
    ma_price_filter=20, min_hold=3,
    ma_stop=20, ma_stop_pct=0.07, switch_ratio=2.5, mkt_ma=0,
)

def main():
    print("=" * 80)
    print("  单仓 vs 2仓 vs 3仓 — 15-seed 对比")
    print("=" * 80)
    print(f"  {'seed':>6} | {'单仓月均':>8} {'Sh':>5} {'回撤':>6} | "
          f"{'2仓月均':>8} {'Sh':>5} {'回撤':>6} | "
          f"{'3仓月均':>8} {'Sh':>5} {'回撤':>6}")
    print("-" * 80)

    results = {1: [], 2: [], 3: []}

    for seed in range(N_SEEDS):
        s_val = 2024 + seed * 100
        prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=s_val)

        # 单仓
        r1 = run_backtest(prices, volumes, initial_capital=INITIAL, **BEST_PARAMS)
        s1 = compute_stats(r1, INITIAL) or {}

        # 2仓
        r2 = run_backtest_multi(prices, volumes, n_positions=2,
                                initial_capital=INITIAL, **MULTI_PARAMS)
        s2 = compute_stats(r2, INITIAL) or {}

        # 3仓
        r3 = run_backtest_multi(prices, volumes, n_positions=3,
                                initial_capital=INITIAL, **MULTI_PARAMS)
        s3 = compute_stats(r3, INITIAL) or {}

        for d, s in [(1, s1), (2, s2), (3, s3)]:
            results[d].append(s)

        m1 = s1.get('monthly_mean', 0); sh1 = s1.get('sharpe_ann', 0); dd1 = s1.get('max_dd', 0)
        m2 = s2.get('monthly_mean', 0); sh2 = s2.get('sharpe_ann', 0); dd2 = s2.get('max_dd', 0)
        m3 = s3.get('monthly_mean', 0); sh3 = s3.get('sharpe_ann', 0); dd3 = s3.get('max_dd', 0)

        mk = ' ★' if m1 >= 10.0 or m2 >= 10.0 or m3 >= 10.0 else ''
        print(f"  {s_val:>6} | {m1:>8.2f}% {sh1:>5.2f} {-dd1:>5.0f}% | "
              f"{m2:>8.2f}% {sh2:>5.2f} {-dd2:>5.0f}% | "
              f"{m3:>8.2f}% {sh3:>5.2f} {-dd3:>5.0f}%{mk}")

    print("-" * 80)
    for n in [1, 2, 3]:
        valid = [s for s in results[n] if s]
        if not valid: continue
        avg_mo  = sum(s['monthly_mean'] for s in valid) / len(valid)
        avg_sh  = sum(s['sharpe_ann']   for s in valid) / len(valid)
        avg_dd  = sum(s['max_dd']       for s in valid) / len(valid)
        cnt10   = sum(1 for s in valid if s['monthly_mean'] >= 10.0)
        cnt_sh1 = sum(1 for s in valid if s['sharpe_ann']   >= 1.0)
        print(f"  {n}仓均值: 月均{avg_mo:.2f}%  Sharpe{avg_sh:.2f}  "
              f"回撤{-avg_dd:.0f}%  | 月均≥10%: {cnt10}/{len(valid)}  Sharpe≥1: {cnt_sh1}/{len(valid)}")

    print("=" * 80)

if __name__ == '__main__':
    main()
