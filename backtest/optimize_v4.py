"""
龙头轮动 V4 — 使用真实A股特征模拟器优化
目标: 月均 >= 10%, Sharpe >= 1.0
"""
import sys, os, time, random, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backtest.market_sim_astock import generate_prices
from backtest.momentum_engine import run_backtest, compute_stats

N_DAYS   = 1820
INITIAL  = 1_000_000
N_STOCKS = 300
N_SEEDS  = 5       # 更多seed提高稳健性
N_COMBOS = 300     # 更大搜索空间

PARAM_SPACE = {
    'trend_window':    [5, 8, 10, 12, 15, 20],
    'min_r2':          [0.1, 0.2, 0.3, 0.4],
    'min_slope':       [0.0001, 0.0002, 0.0005, 0.001],
    'ma_price_filter': [5, 10, 20],
    'pullback_lo':     [-0.99],   # 关闭回调过滤 (直接买入模式更好)
    'pullback_hi':     [0.99],
    'vol_mult':        [99.0],    # 关闭成交量过滤
    'slope_accel':     [0.0],
    'min_hold':        [1, 3, 5, 10],
    'ma_stop':         [5, 10, 15, 20],
    'ma_stop_pct':     [0.01, 0.02, 0.03, 0.05],
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
    print("  龙头轮动 V4 — A股真实特征模拟 (龙头年化80-200%)")
    print("  目标: 月均≥10% AND Sharpe≥1.0")
    print("=" * 80)

    combos = sample_combos(PARAM_SPACE, N_COMBOS, seed=99)
    print(f"  测试 {N_COMBOS} 个参数组合 × {N_SEEDS} 个seed\n")

    results = []
    t0 = time.time()

    for i, params in enumerate(combos):
        monthly_means = []; sharpes = []
        for seed in range(N_SEEDS):
            s = run_scenario(params, seed=2024 + seed * 100)
            if s and s['n_trades'] >= 5:
                monthly_means.append(s['monthly_mean'])
                sharpes.append(s['sharpe_ann'])
        if monthly_means:
            results.append({
                'params': params,
                'monthly_mean': sum(monthly_means) / len(monthly_means),
                'sharpe_ann':   sum(sharpes) / len(sharpes),
                'monthly_max':  max(monthly_means),
                'sharpe_max':   max(sharpes),
                'all_monthly':  monthly_means,
            })
        if (i + 1) % 60 == 0:
            t = time.time() - t0
            print(f"  {i+1}/{N_COMBOS}  {t:.0f}s  ETA {t/(i+1)*(N_COMBOS-i-1):.0f}s", flush=True)

    results.sort(key=lambda r: -r['monthly_mean'])

    print()
    print("=" * 100)
    print(f"  TOP 20 (按月均排序)  有效组合: {len(results)}")
    print("=" * 100)
    print(f"  {'#':>3} {'月均%':>7} {'月MAX%':>7} {'SharpeA':>8} {'Sh_MAX':>7} | 参数")
    print("-" * 100)

    for rank, r in enumerate(results[:20]):
        p = r['params']
        mark = ''
        if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0:
            mark = ' ★BOTH'
        elif r['monthly_mean'] >= 10.0:
            mark = ' ★Mo≥10'
        elif r['sharpe_ann'] >= 1.0:
            mark = ' ★Sh≥1'
        ps = (f"W{p['trend_window']} R²≥{p['min_r2']} MA止损{p['ma_stop']}({p['ma_stop_pct']*100:.0f}%) "
              f"SW{p['switch_ratio']} MinHold{p['min_hold']}")
        print(f"  {rank+1:>3} {r['monthly_mean']:>7.2f}% {r['monthly_max']:>7.2f}% "
              f"{r['sharpe_ann']:>8.2f} {r['sharpe_max']:>7.2f} | {ps}{mark}")

    mo10 = [r for r in results if r['monthly_mean'] >= 10.0]
    sh1  = [r for r in results if r['sharpe_ann']   >= 1.0]
    both = [r for r in results if r['monthly_mean'] >= 10.0 and r['sharpe_ann'] >= 1.0]

    print()
    print("=" * 70)
    print(f"  月均 ≥ 10%     : {len(mo10):>3} / {len(results)}")
    print(f"  Sharpe ≥ 1.0   : {len(sh1):>3} / {len(results)}")
    print(f"  同时达到       : {len(both):>3} / {len(results)}")
    print(f"  最高月均:  {results[0]['monthly_mean']:.2f}%")
    print(f"  最高Sharpe: {max(r['sharpe_ann'] for r in results):.2f}")

    if results:
        print()
        print("  最优参数 — 5seed详细统计:")
        best = results[0]; p = best['params']
        print(f"  W={p['trend_window']} R²≥{p['min_r2']} MA止损{p['ma_stop']}×(1-{p['ma_stop_pct']*100:.0f}%) SW={p['switch_ratio']} MinHold={p['min_hold']}")
        print()
        print(f"  {'seed':>6} {'月均%':>8} {'月std':>7} {'Sharpe':>8} {'年化%':>8} {'回撤':>7} {'胜率':>6}")
        print("-" * 60)
        mo_all = []
        for seed in [2024, 2124, 2224, 2324, 2424]:
            prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=seed)
            res = run_backtest(prices, volumes, initial_capital=INITIAL, **p)
            s = compute_stats(res, initial=INITIAL)
            if s:
                mo_all.append(s['monthly_mean'])
                print(f"  {seed:>6} {s['monthly_mean']:>8.2f}% {s['monthly_std']:>7.2f}% "
                      f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>8.1f}% "
                      f"{-s['max_dd']:>7.1f}% {s['win_rate']:>6.1f}%")
        if mo_all:
            print("-" * 60)
            print(f"  {'平均':>6} {sum(mo_all)/len(mo_all):>8.2f}%")

    print()
    print("  市场模拟统计 (V9 A股特征):")
    prices_check, _, mkt = generate_prices(N_STOCKS, N_DAYS, seed=2024)
    import numpy as _np
    finals = [v[-1]/v[0] for v in prices_check.values()]
    finals.sort()
    print(f"  中位股 7年倍数: {_np.median(finals):.2f}x")
    print(f"  TOP5% 7年倍数: {_np.percentile(finals,95):.1f}x")
    print(f"  TOP1% 7年倍数: {_np.percentile(finals,99):.1f}x")
    print(f"  跑赢100%的股数: {sum(1 for f in finals if f>1)}/{len(finals)}")
    print("=" * 80)


if __name__ == '__main__':
    main()
