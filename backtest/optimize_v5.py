"""
龙头轮动 V5 — 回调入场 + 动量加速 优化
用户原始参数:
  15日斜率×R², R²>0.5, slope>0.02%/天
  入场: 回调到MA10附近 (-4%~+3%)
  止损: MA20×0.97
  换仓: 3.5x
  最短持仓: 10天

本脚本在用户参数附近大范围搜索，目标: 月均≥10%, Sharpe≥1
"""
import sys, time, itertools
import numpy as np
sys.path.insert(0, '/home/user/billion-')
from backtest.market_sim_gem import generate_prices as simulate_market_gem
from backtest.momentum_engine import run_backtest_multi, compute_stats

# ── 参数网格 ────────────────────────────────────────────────────────
TREND_WINDOWS   = [10, 15, 20]
MIN_R2_LIST     = [0.3, 0.4, 0.5]
STOP_MA_LIST    = [15, 20]
STOP_PCT_LIST   = [0.03, 0.05, 0.07]
SWITCH_LIST     = [2.5, 3.0, 3.5, 4.0]
MIN_HOLD_LIST   = [5, 10, 15]
PULLBACK_MA_LIST = [10, 15, 0]  # 0=关闭回调过滤
PULLBACK_LO     = -0.04
PULLBACK_HI     = 0.03
N_POS_LIST      = [1, 2]

SEEDS = [2024, 2124, 2224, 2324, 2424, 2524, 2624]

combos = list(itertools.product(
    TREND_WINDOWS, MIN_R2_LIST, STOP_MA_LIST, STOP_PCT_LIST,
    SWITCH_LIST, MIN_HOLD_LIST, PULLBACK_MA_LIST, N_POS_LIST
))
print(f"{'='*80}")
print(f"  龙头轮动 V5 — 回调入场优化")
print(f"  目标: 月均≥10% AND Sharpe≥1.0")
print(f"  测试 {len(combos)} 组合 × {len(SEEDS)} seeds")
print(f"{'='*80}")

# 预生成模拟数据
N_STOCKS = 200
print(f"\n  预生成 {len(SEEDS)} 套市场数据...")
all_data = []
for seed in SEEDS:
    prices, volumes, market_rets = simulate_market_gem(
        n_stocks=N_STOCKS, n_days=1840, seed=seed
    )
    all_data.append((prices, volumes))
print(f"  完成\n")

results = []
t0 = time.time()
done = 0

for combo in combos:
    tw, r2, sma, spct, sw, mhold, pb_ma, npos = combo
    min_slope = 0.0002

    seed_stats = []
    for prices, volumes in all_data:
        res = run_backtest_multi(
            prices, volumes,
            n_positions=npos,
            trend_window=tw, min_r2=r2, min_slope=min_slope,
            ma_price_filter=20,
            min_hold=mhold,
            ma_stop=sma, ma_stop_pct=spct,
            switch_ratio=sw,
            pullback_ma=pb_ma,
            pullback_lo=PULLBACK_LO,
            pullback_hi=PULLBACK_HI,
        )
        st = compute_stats(res)
        if st:
            seed_stats.append(st)

    done += 1
    if not seed_stats:
        continue

    mn  = np.mean([s['monthly_mean'] for s in seed_stats])
    mmax= np.max([s['monthly_mean'] for s in seed_stats])
    sh  = np.mean([s['sharpe_ann']   for s in seed_stats])
    shx = np.max([s['sharpe_ann']    for s in seed_stats])
    dd  = np.mean([s['max_dd']       for s in seed_stats])
    hit10 = sum(1 for s in seed_stats if s['monthly_mean'] >= 10)
    hitsh = sum(1 for s in seed_stats if s['sharpe_ann']   >= 1.0)

    results.append({
        'params': combo, 'mn': mn, 'mmax': mmax,
        'sh': sh, 'shx': shx, 'dd': dd,
        'hit10': hit10, 'hitsh': hitsh,
    })

    if done % 50 == 0 or done == len(combos):
        elapsed = time.time() - t0
        eta = elapsed / done * (len(combos) - done)
        print(f"  {done}/{len(combos)}  {elapsed:.0f}s  ETA {eta:.0f}s")

# ── 结果输出 ────────────────────────────────────────────────────────
results.sort(key=lambda x: x['mn'], reverse=True)
top = results[:30]

print(f"\n{'='*110}")
print(f"  TOP 30 (月均排序)  有效组合: {len(results)}")
print(f"{'='*110}")
print(f"  {'#':>3}  {'月均%':>7}  {'月MAX%':>7}  {'SharpeA':>8}  {'ShMAX':>6}  {'回撤%':>7}  {'10%x':>4}  {'Shx':>4} | 参数")
print(f"  {'-'*100}")
for i, r in enumerate(top):
    tw, r2, sma, spct, sw, mhold, pb_ma, npos = r['params']
    pb_str = f"PB{pb_ma}" if pb_ma > 0 else "noPB"
    both = r['hit10'] > 0 and r['hitsh'] > 0
    star = " ★BOTH" if both else (" ★Sh≥1" if r['hitsh'] > 0 else "")
    print(f"  {i+1:>3}  {r['mn']:>7.2f}%  {r['mmax']:>7.2f}%  {r['sh']:>8.2f}  {r['shx']:>6.2f}  {r['dd']:>7.1f}%  {r['hit10']:>4}  {r['hitsh']:>4} | "
          f"W{tw} R²≥{r2} Stop{sma}({spct*100:.0f}%) SW{sw} Hold{mhold} {pb_str} Pos{npos}{star}")

print(f"\n{'='*60}")
print(f"  月均 ≥ 10%    : {sum(1 for r in results if r['mn']>=10):>4} / {len(results)}")
print(f"  Sharpe ≥ 1.0  : {sum(1 for r in results if r['sh']>=1.0):>4} / {len(results)}")
print(f"  同时达到      : {sum(1 for r in results if r['mn']>=10 and r['sh']>=1.0):>4} / {len(results)}")
print(f"  最高月均:  {max(r['mn'] for r in results):.2f}%")
print(f"  最高Sharpe: {max(r['sh'] for r in results):.2f}")

# ── 最优配置深度验证 ────────────────────────────────────────────────
if results:
    best = results[0]
    tw, r2, sma, spct, sw, mhold, pb_ma, npos = best['params']
    print(f"\n{'='*60}")
    print(f"  最优参数 12-seed 深度验证")
    print(f"  W={tw} R²≥{r2} Stop{sma}×(1-{spct*100:.0f}%) SW={sw} Hold={mhold}")
    pb_str = f"回调MA{pb_ma} [{PULLBACK_LO*100:.0f}%~+{PULLBACK_HI*100:.0f}%]" if pb_ma > 0 else "无回调过滤"
    print(f"  {pb_str}  N_POS={npos}")
    print(f"{'='*60}")

    deep_seeds = list(range(2024, 2024 + 12 * 100, 100))
    print(f"  {'seed':>6}  {'月均%':>7}  {'月std%':>7}  {'Sharpe':>8}  {'年化%':>8}  {'回撤%':>7}  {'胜率%':>7}")
    print(f"  {'-'*60}")
    deep_means = []
    for seed in deep_seeds:
        prices, volumes, _ = simulate_market_gem(n_stocks=N_STOCKS, n_years=7.3, seed=seed)
        res = run_backtest_multi(
            prices, volumes,
            n_positions=npos,
            trend_window=tw, min_r2=r2, min_slope=0.0002,
            ma_price_filter=20,
            min_hold=mhold,
            ma_stop=sma, ma_stop_pct=spct,
            switch_ratio=sw,
            pullback_ma=pb_ma,
            pullback_lo=PULLBACK_LO,
            pullback_hi=PULLBACK_HI,
        )
        st = compute_stats(res)
        if not st:
            continue
        star = " ★" if st['monthly_mean'] >= 10 else ""
        print(f"  {seed:>6}  {st['monthly_mean']:>7.2f}%  {st['monthly_std']:>7.2f}%  "
              f"{st['sharpe_ann']:>8.2f}  {st['ann_ret']:>8.1f}%  "
              f"{st['max_dd']:>7.1f}%  {st['win_rate']:>7.1f}%{star}")
        deep_means.append(st['monthly_mean'])

    if deep_means:
        hit10 = sum(1 for m in deep_means if m >= 10)
        avg_mn = np.mean(deep_means)
        print(f"  {'-'*60}")
        print(f"  12-seed均值  {avg_mn:.2f}%  月均≥10%: {hit10}/12次")

print(f"\n{'='*60}\n")
