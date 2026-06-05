"""
真实数据回测 — 优先使用Tushare数据，无数据时用模拟器
用法:
  有数据: python backtest/run_realdata.py
  无数据: python backtest/run_realdata.py --sim
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from pathlib import Path

DATA_DIR   = Path(__file__).parent / 'data'
DAILY_FILE = DATA_DIR / 'daily_all.parquet'

# 最优参数 (2仓模式)
BEST_PARAMS = dict(
    trend_window=20, min_r2=0.4, min_slope=0.0002,
    ma_price_filter=20, min_hold=3,
    ma_stop=20, ma_stop_pct=0.07,
    switch_ratio=2.5, mkt_ma=0,
)

INITIAL = 1_000_000


def run_with_real_data():
    """使用真实Tushare缓存数据回测"""
    import pandas as pd
    from backtest.data_fetcher import load_price_dict
    from backtest.momentum_engine import run_backtest_multi, compute_stats

    print("  加载真实市场数据...")
    try:
        prices, volumes, dates = load_price_dict(
            start_date='20200101', end_date='20251231', min_days=250
        )
    except FileNotFoundError:
        return None

    print(f"  股票数: {len(prices)}  交易日: {len(dates)}")

    # 分段回测: 牛市(2020-2021) vs 熊市(2021-2023) vs 全程
    periods = [
        ('全程 2020-2025', '20200101', '20251231'),
        ('牛市 2020-2021', '20200101', '20211231'),
        ('震荡 2022-2023', '20220101', '20231231'),
        ('2024以后',       '20240101', '20251231'),
    ]

    for label, start, end in periods:
        p_slice = {}
        v_slice = {}
        s_idx = None; e_idx = None

        for i, d in enumerate(dates):
            ds = d.strftime('%Y%m%d') if hasattr(d, 'strftime') else str(d).replace('-', '')
            if ds >= start and s_idx is None:
                s_idx = i
            if ds <= end:
                e_idx = i

        if s_idx is None or e_idx is None or e_idx - s_idx < 100:
            continue

        for code in prices:
            if len(prices[code]) > e_idx:
                p_slice[code] = prices[code][s_idx:e_idx+1]
                v_slice[code] = volumes[code][s_idx:e_idx+1]

        if not p_slice:
            continue

        res = run_backtest_multi(p_slice, v_slice, n_positions=2,
                                 initial_capital=INITIAL, **BEST_PARAMS)
        s   = compute_stats(res, INITIAL)
        if not s: continue

        print(f"\n  {label}:")
        print(f"    月均收益: {s['monthly_mean']:.2f}%   Sharpe: {s['sharpe_ann']:.2f}")
        print(f"    年化收益: {s['ann_ret']:.1f}%   最大回撤: {-s['max_dd']:.1f}%")
        print(f"    胜率: {s['win_rate']:.1f}%   交易次数: {s['n_trades']}")
        print(f"    月均≥5%月份: {s['gt5_months']}/{s['n_months']}  "
              f"月均≥10%月份: {s['gt10_months']}/{s['n_months']}")

    return True


def run_with_simulation():
    """模拟数据回测（无真实数据时的备用）"""
    from backtest.market_sim_gem import generate_prices
    from backtest.momentum_engine import run_backtest_multi, compute_stats

    print("  使用校准版创业板/科创板模拟数据 (±20%, 妖股60-100%/年)...")
    print()

    results = []
    for seed in range(15):
        s_val  = 2024 + seed * 100
        prices, volumes, _ = generate_prices(200, 1820, seed=s_val)
        res = run_backtest_multi(prices, volumes, n_positions=2,
                                 initial_capital=INITIAL, **BEST_PARAMS)
        s   = compute_stats(res, INITIAL)
        if s:
            results.append((s_val, s))

    print(f"  {'seed':>6} {'月均%':>8} {'月std':>7} {'Sharpe':>8} {'年化%':>8} {'回撤%':>7} {'胜率%':>6}")
    print("  " + "-" * 56)
    mo_all = []
    for seed, s in results:
        mk = ' ★' if s['monthly_mean'] >= 10.0 else (' ●' if s['sharpe_ann'] >= 1.0 else '')
        print(f"  {seed:>6} {s['monthly_mean']:>8.2f}% {s['monthly_std']:>7.2f}% "
              f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>8.1f}% "
              f"{-s['max_dd']:>7.1f}% {s['win_rate']:>6.1f}%{mk}")
        mo_all.append(s['monthly_mean'])

    if mo_all:
        print("  " + "-" * 56)
        print(f"  均值: {sum(mo_all)/len(mo_all):.2f}%/月")
        print(f"  月均≥10%: {sum(1 for x in mo_all if x>=10.0)}/15次")
        print(f"  Sharpe≥1: {sum(1 for _,s in results if s['sharpe_ann']>=1.0)}/15次")

    print()
    print("  ★=月均≥10%  ●=Sharpe≥1")


def main():
    use_sim = '--sim' in sys.argv

    print("=" * 72)
    print("  龙头轮动 V3 — 创业板+科创板 回测")
    print(f"  2仓策略  |  W={BEST_PARAMS['trend_window']} R²≥{BEST_PARAMS['min_r2']} "
          f"止损MA{BEST_PARAMS['ma_stop']}×{1-BEST_PARAMS['ma_stop_pct']} "
          f"换仓{BEST_PARAMS['switch_ratio']}x")
    print("=" * 72)
    print()

    if use_sim or not DAILY_FILE.exists():
        if not use_sim:
            print("  未找到本地数据，使用模拟器")
            print("  提示: 运行 python backtest/data_fetcher.py 下载真实数据")
            print()
        run_with_simulation()
    else:
        result = run_with_real_data()
        if result is None:
            print("  切换到模拟器...")
            run_with_simulation()

    print()
    print("=" * 72)
    print("  最优操作SOP:")
    print("  1. 每日收盘后运行: python backtest/daily_scanner.py")
    print("  2. 查看明日操作信号 (买入/止损/换仓)")
    print("  3. 次日开盘前5分钟集合竞价执行")
    print("=" * 72)


if __name__ == '__main__':
    main()
