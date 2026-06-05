"""
创业板/科创板 龙头轮动策略优化
目标: 月均 >= 10%, Sharpe >= 1.0
"""
import sys, os, time, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backtest.market_sim_gem import generate_prices
from backtest.momentum_engine import run_backtest, compute_stats

N_DAYS   = 1820
INITIAL  = 1_000_000
N_STOCKS = 200    # 创业板+科创板约200-300只流动性好的
N_SEEDS  = 7      # 更多seed提高稳健性
N_COMBOS = 300

PARAM_SPACE = {
    'trend_window':    [5, 8, 10, 12, 15, 20],
    'min_r2':          [0.1, 0.2, 0.3, 0.4, 0.5],
    'min_slope':       [0.0001, 0.0002, 0.0005, 0.001, 0.002],
    'ma_price_filter': [5, 10, 20],
    # 两种入场模式都测
    'pullback_lo':     [-0.99, -0.08, -0.05],
    'pullback_hi':     [0.99,   0.05,  0.03],
    'vol_mult':        [99.0, 1.5, 2.0],
    'slope_accel':     [0.0, 1.05, 1.1],
    'min_hold':        [1, 3, 5, 10],
    'ma_stop':         [5, 10, 15, 20],
    'ma_stop_pct':     [0.02, 0.03, 0.05, 0.07],  # 宽止损适配±20%波动
    'switch_ratio':    [1.2, 1.5, 2.0, 2.5, 3.0],
}


def sample_combos(space, n, seed=42):
    rng = random.Random(seed)
    return [{k: rng.choice(v) for k, v in space.items()} for _ in range(n)]


def run_scenario(params, seed):
    prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=seed)
    res = run_backtest(prices, volumes, initial_capital=INITIAL, **params)
    return compute_stats(res, initial=INITIAL)


def main():
    print("=" * 80)
    print("  创业板/科创板 龙头轮动优化  (±20%涨停 + 妖股年化150-400%)")
    print("  目标: 月均≥10% AND Sharpe≥1.0")
    print("=" * 80)

    # 先验证市场特征
    prices_s, _, mkt = generate_prices(N_STOCKS, N_DAYS, seed=2024)
    finals = sorted([v[-1]/v[0] for v in prices_s.values()])
    import numpy as _np
    print(f"  市场特征验证 (7.3年):")
    print(f"    中位股倍数:    {_np.median(finals):.2f}x")
    print(f"    TOP10% 倍数:   {_np.percentile(finals,90):.1f}x")
    print(f"    TOP 5% 倍数:   {_np.percentile(finals,95):.1f}x")
    print(f"    TOP 1% 倍数:   {_np.percentile(finals,99):.1f}x")
    print(f"    跑赢大市股数:  {sum(1 for f in finals if f > 1)}/{len(finals)}")
    del prices_s
    print()

    combos = sample_combos(PARAM_SPACE, N_COMBOS, seed=77)
    print(f"  测试 {N_COMBOS} 组合 × {N_SEEDS} seeds  ({N_STOCKS}只股票)\n")

    results = []
    t0 = time.time()

    for i, params in enumerate(combos):
        monthly_means = []; sharpes = []
        for seed in range(N_SEEDS):
            s = run_scenario(params, seed=2024 + seed * 100)
            if s and s['n_trades'] >= 5:
                monthly_means.append(s['monthly_mean'])
                sharpes.append(s['sharpe_ann'])
        if len(monthly_means) >= 3:
            results.append({
                'params':       params,
                'monthly_mean': sum(monthly_means) / len(monthly_means),
                'sharpe_ann':   sum(sharpes) / len(sharpes),
                'monthly_max':  max(monthly_means),
                'sharpe_max':   max(sharpes),
                'all_monthly':  monthly_means,
            })
        if (i + 1) % 60 == 0:
            t = time.time() - t0
            eta = t / (i+1) * (N_COMBOS - i - 1)
            print(f"  {i+1}/{N_COMBOS}  {t:.0f}s  ETA {eta:.0f}s", flush=True)

    results.sort(key=lambda r: -r['monthly_mean'])

    print()
    print("=" * 110)
    print(f"  TOP 25 (月均排序)  有效组合: {len(results)}")
    print("=" * 110)
    print(f"  {'#':>3} {'月均%':>8} {'月MAX%':>8} {'SharpeA':>8} {'ShMAX':>7} | 参数")
    print("-" * 110)

    best_both = []
    for rank, r in enumerate(results[:25]):
        p = r['params']
        mark = ''
        if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0:
            mark = ' ★BOTH'
            best_both.append(r)
        elif r['monthly_mean'] >= 10.0:
            mark = ' ★Mo≥10'
        elif r['sharpe_ann'] >= 1.0:
            mark = ' ★Sh≥1'
        ps = (f"W{p['trend_window']} R²≥{p['min_r2']} "
              f"Stop{p['ma_stop']}({p['ma_stop_pct']*100:.0f}%) "
              f"SW{p['switch_ratio']} Hold{p['min_hold']}")
        print(f"  {rank+1:>3} {r['monthly_mean']:>8.2f}% {r['monthly_max']:>8.2f}% "
              f"{r['sharpe_ann']:>8.2f} {r['sharpe_max']:>7.2f} | {ps}{mark}")

    mo10 = [r for r in results if r['monthly_mean'] >= 10.0]
    sh1  = [r for r in results if r['sharpe_ann']   >= 1.0]
    both = [r for r in results if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0]

    print()
    print("=" * 70)
    print(f"  月均 ≥ 10%    : {len(mo10):>4} / {len(results)}")
    print(f"  Sharpe ≥ 1.0  : {len(sh1):>4} / {len(results)}")
    print(f"  同时达到      : {len(both):>4} / {len(results)}")
    print(f"  最高月均:   {results[0]['monthly_mean']:.2f}%")
    best_sh = max(r['sharpe_ann'] for r in results) if results else 0
    print(f"  最高Sharpe: {best_sh:.2f}")

    # 最优参数多seed深测
    best = results[0]
    p = best['params']
    print()
    print("=" * 70)
    print(f"  最优参数 10-seed 深度验证")
    print("=" * 70)
    print(f"  W={p['trend_window']} R²≥{p['min_r2']} Slope≥{p['min_slope']*100:.3f}%/天")
    print(f"  MA过滤={p['ma_price_filter']} 止损MA{p['ma_stop']}×(1-{p['ma_stop_pct']*100:.0f}%)")
    print(f"  换仓倍数={p['switch_ratio']} 最短持仓={p['min_hold']}天")
    print()
    print(f"  {'seed':>6} {'月均%':>8} {'月std%':>7} {'Sharpe':>8} {'年化%':>8} {'回撤%':>7} {'胜率%':>7}")
    print("-" * 65)

    mo_10s = []
    for seed in range(10):
        prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=2024+seed*100)
        res = run_backtest(prices, volumes, initial_capital=INITIAL, **p)
        s = compute_stats(res, initial=INITIAL)
        if s:
            mo_10s.append(s['monthly_mean'])
            mk = ' ★' if s['monthly_mean'] >= 10.0 else ''
            print(f"  {2024+seed*100:>6} {s['monthly_mean']:>8.2f}% {s['monthly_std']:>7.2f}% "
                  f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>8.1f}% "
                  f"{-s['max_dd']:>7.1f}% {s['win_rate']:>7.1f}%{mk}")

    if mo_10s:
        print("-" * 65)
        print(f"  {'10-seed均值':>6} {sum(mo_10s)/len(mo_10s):>8.2f}%")
        print(f"  {'达到10%':>6} {sum(1 for x in mo_10s if x>=10.0)}/{len(mo_10s)} 次")

    # 找最优Sharpe配置
    results_by_sh = sorted(results, key=lambda r: -r['sharpe_ann'])
    if results_by_sh and results_by_sh[0]['sharpe_ann'] >= 1.0:
        print()
        print("=" * 70)
        print("  最高Sharpe配置详情")
        print("=" * 70)
        br = results_by_sh[0]; bp = br['params']
        print(f"  月均{br['monthly_mean']:.2f}% Sharpe{br['sharpe_ann']:.2f}")
        print(f"  W={bp['trend_window']} Stop{bp['ma_stop']}({bp['ma_stop_pct']*100:.0f}%) SW{bp['switch_ratio']}")

    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
