"""
龙头轮动 V3 全参数优化
目标: 月均 >= 10%, Sharpe >= 1.0
测试多种入场模式 + 大幅扩参数空间
"""
import sys, os, time, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backtest.market_sim import generate_prices
from backtest.momentum_engine import run_backtest, compute_stats

N_DAYS   = 1820
INITIAL  = 1_000_000
N_STOCKS = 300
N_SEEDS  = 3
N_COMBOS = 200

# ── 激进参数空间 ──────────────────────────────────────────────────────────────
PARAM_SPACE = {
    'trend_window':    [5, 8, 10, 12, 15, 20],
    'min_r2':          [0.2, 0.3, 0.4, 0.5],
    'min_slope':       [0.0001, 0.0002, 0.0003, 0.0005],
    'ma_price_filter': [10, 20],
    'pullback_ma':     [5, 10],
    'pullback_lo':     [-0.06, -0.04, -0.02],
    'pullback_hi':     [0.02, 0.03, 0.05],
    'vol_mult':        [1.2, 1.5, 2.0],
    'slope_accel':     [1.05, 1.1, 1.2],
    'min_hold':        [3, 5, 10],
    'ma_stop':         [10, 15, 20],
    'ma_stop_pct':     [0.02, 0.03, 0.05],
    'switch_ratio':    [1.5, 2.0, 2.5, 3.0, 3.5],
}

# 另外测试无入场过滤版本 (直接买最强)
DIRECT_SPACE = {
    'trend_window':    [5, 8, 10, 12, 15, 20, 25],
    'min_r2':          [0.1, 0.2, 0.3, 0.4, 0.5],
    'min_slope':       [0.0001, 0.0002, 0.0005, 0.001],
    'ma_price_filter': [5, 10, 20],
    'pullback_lo':     [-0.99],   # 实质上关闭回调过滤 → 任何位置都可买
    'pullback_hi':     [0.99],
    'vol_mult':        [99.0],    # 关闭成交量过滤
    'slope_accel':     [0.0],     # 关闭斜率加速过滤
    'min_hold':        [1, 3, 5],
    'ma_stop':         [5, 10, 15, 20],
    'ma_stop_pct':     [0.01, 0.02, 0.03],
    'switch_ratio':    [1.2, 1.5, 2.0, 2.5],
}


def sample_combos(space, n, seed=42):
    rng = random.Random(seed)
    keys = list(space.keys())
    combos = []
    for _ in range(n):
        c = {k: rng.choice(v) for k, v in space.items()}
        combos.append(c)
    return combos


def run_scenario(params, n_stocks, seed):
    prices, volumes, _ = generate_prices(n_stocks, N_DAYS, seed=seed)
    res = run_backtest(prices, volumes, initial_capital=INITIAL, **params)
    return compute_stats(res, initial=INITIAL)


def main():
    print("=" * 80)
    print("  龙头轮动 V3 全参数优化  |  目标: 月均≥10% AND Sharpe≥1")
    print("=" * 80)

    # 生成组合
    pullback_combos = sample_combos(PARAM_SPACE, N_COMBOS // 2, seed=1)
    direct_combos   = sample_combos(DIRECT_SPACE, N_COMBOS // 2, seed=2)

    all_combos = [('回调入场', c) for c in pullback_combos] + \
                 [('直接买入', c) for c in direct_combos]

    print(f"  总测试组合: {len(all_combos)} | 每组 {N_SEEDS} 个seed | 股票池 {N_STOCKS}只")
    print()

    results = []
    t0 = time.time()

    for i, (mode, params) in enumerate(all_combos):
        monthly_means = []; sharpes = []
        for seed in range(N_SEEDS):
            s = run_scenario(params, N_STOCKS, seed=2024 + seed * 100)
            if s and s['n_trades'] >= 5:
                monthly_means.append(s['monthly_mean'])
                sharpes.append(s['sharpe_ann'])
        if monthly_means:
            results.append({
                'mode': mode,
                'params': params,
                'monthly_mean': sum(monthly_means) / len(monthly_means),
                'sharpe_ann':   sum(sharpes) / len(sharpes),
                'monthly_max':  max(monthly_means),
                'sharpe_max':   max(sharpes),
                'monthly_all':  monthly_means,
            })

        if (i + 1) % 50 == 0:
            t = time.time() - t0
            eta = t / (i + 1) * (len(all_combos) - i - 1)
            print(f"  {i+1}/{len(all_combos)}  {t:.0f}s 已用  ETA {eta:.0f}s", flush=True)

    # 按月均排序
    results.sort(key=lambda r: -r['monthly_mean'])

    print()
    print("=" * 110)
    print(f"  TOP 30 (按月均收益排序)   有效组合: {len(results)}")
    print("=" * 110)
    print(f"  {'#':>3} {'模式':>8} {'月均%':>7} {'月MAX%':>7} {'SharpeA':>8} {'月std':>6} | 参数摘要")
    print("-" * 110)

    best_both = []
    for rank, r in enumerate(results[:30]):
        p = r['params']
        mark = ''
        if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0:
            mark = ' ★BOTH'
            best_both.append(r)
        elif r['monthly_mean'] >= 10.0:
            mark = ' ★Mo≥10'
        elif r['sharpe_ann'] >= 1.0:
            mark = ' ★Sh≥1'

        # 参数摘要
        ps = (f"W{p['trend_window']} R²≥{p['min_r2']} Sl≥{p['min_slope']*100:.2f}% "
              f"SW{p['switch_ratio']} Stop{p['ma_stop']}({p['ma_stop_pct']*100:.0f}%)")

        # 计算月std
        all_mo = r.get('monthly_all', [r['monthly_mean']])
        mo_std = (sum((x - r['monthly_mean'])**2 for x in all_mo) / max(len(all_mo)-1,1))**0.5

        print(f"  {rank+1:>3} {r['mode']:>8} {r['monthly_mean']:>7.2f}% "
              f"{r['monthly_max']:>7.2f}% {r['sharpe_ann']:>8.2f} "
              f"{mo_std:>6.2f}% | {ps}{mark}")

    # 目标统计
    mo10  = [r for r in results if r['monthly_mean'] >= 10.0]
    sh1   = [r for r in results if r['sharpe_ann']   >= 1.0]
    both  = [r for r in results if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0]

    print()
    print("=" * 70)
    print("  目标达成分析")
    print("=" * 70)
    print(f"  月均 ≥ 10%       : {len(mo10):>3} / {len(results)} ({len(mo10)/len(results)*100:.0f}%)")
    print(f"  Sharpe ≥ 1.0     : {len(sh1):>3} / {len(results)} ({len(sh1)/len(results)*100:.0f}%)")
    print(f"  两者同时达到     : {len(both):>3} / {len(results)}")

    if both:
        print()
        print("  ✅ 同时满足月均≥10% AND Sharpe≥1 的配置:")
        for r in both[:5]:
            p = r['params']
            print(f"    月均{r['monthly_mean']:.1f}% Sharpe{r['sharpe_ann']:.2f} "
                  f"模式:{r['mode']} W{p['trend_window']} SW{p['switch_ratio']}")
    else:
        best_m = results[0]['monthly_mean'] if results else 0
        best_s = max(r['sharpe_ann'] for r in results) if results else 0
        print(f"\n  当前最高月均: {best_m:.2f}%  目标: 10%")
        print(f"  当前最高Sharpe: {best_s:.2f}  目标: 1.0")

    # 最优组合详情
    print()
    print("=" * 70)
    print("  最优月均配置详细结果 (多seed重跑)")
    print("=" * 70)
    if results:
        best = results[0]
        p = best['params']
        print(f"  模式: {best['mode']}")
        print(f"  参数: W={p['trend_window']} R²≥{p['min_r2']} Sl≥{p['min_slope']*100:.3f}%")
        print(f"        MA止损={p['ma_stop']}×(1-{p['ma_stop_pct']*100:.0f}%)")
        print(f"        换仓={p['switch_ratio']}x  最短持仓={p['min_hold']}天")
        print()

        # 5个seed详细跑
        print("  5-seed详细统计:")
        print(f"  {'seed':>6} {'月均%':>8} {'月std':>7} {'Sharpe':>8} {'年化%':>8} {'回撤':>7} {'笔数':>6} {'胜率':>6}")
        print("-" * 70)
        all_mo_5 = []
        for seed in [2024, 2124, 2224, 2324, 2424]:
            prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=seed)
            res = run_backtest(prices, volumes, initial_capital=INITIAL, **p)
            s = compute_stats(res, initial=INITIAL)
            if s:
                all_mo_5.append(s['monthly_mean'])
                print(f"  {seed:>6} {s['monthly_mean']:>8.2f}% {s['monthly_std']:>7.2f}% "
                      f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>8.1f}% "
                      f"{-s['max_dd']:>7.1f}% {s['n_trades']:>6} {s['win_rate']:>6.1f}%")

        if all_mo_5:
            print("-" * 70)
            avg5 = sum(all_mo_5) / len(all_mo_5)
            print(f"  {'平均':>6} {avg5:>8.2f}%")

    print()
    print("=" * 70)


if __name__ == '__main__':
    main()
