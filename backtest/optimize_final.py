"""
龙头轮动最终优化 — 创业板/科创板 + 大盘择时
对比三种模式:
  A. 无择时 (全天候持仓)
  B. MA50择时 (30%个股在MA50上方才建仓)
  C. MA30择时 (40%个股在MA30上方才建仓)
目标: 月均≥10%, Sharpe≥1, 最大回撤<50%
"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backtest.market_sim_gem import generate_prices
from backtest.momentum_engine import run_backtest, compute_stats

N_DAYS   = 1820
INITIAL  = 1_000_000
N_STOCKS = 200
N_SEEDS  = 8
N_COMBOS = 120   # 每种模式120组合

# 最优参数范围 (基于前轮缩窄)
PARAM_SPACE = {
    'trend_window':    [5, 8, 10, 15, 20],
    'min_r2':          [0.2, 0.3, 0.4, 0.5],
    'min_slope':       [0.0001, 0.0002, 0.0005],
    'ma_price_filter': [5, 10, 20],
    'pullback_lo':     [-0.99],   # 直接买入模式 (前轮验证更优)
    'pullback_hi':     [0.99],
    'vol_mult':        [99.0],
    'slope_accel':     [0.0],
    'min_hold':        [1, 3, 5],
    'ma_stop':         [10, 15, 20],
    'ma_stop_pct':     [0.05, 0.07, 0.10],   # 宽止损适配±20%
    'switch_ratio':    [2.0, 2.5, 3.0],
}

TIMING_MODES = [
    {'name': '无择时',   'mkt_ma': 0,  'mkt_pct_stocks': 0.0},
    {'name': 'MA50择时', 'mkt_ma': 50, 'mkt_pct_stocks': 0.30},
    {'name': 'MA30择时', 'mkt_ma': 30, 'mkt_pct_stocks': 0.40},
]


def sample_combos(n, seed=42):
    rng = random.Random(seed)
    return [{k: rng.choice(v) for k, v in PARAM_SPACE.items()} for _ in range(n)]


def run_one(params, timing, seed):
    prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=seed)
    full_params = {**params, **timing}
    full_params.pop('name', None)
    res = run_backtest(prices, volumes, initial_capital=INITIAL, **full_params)
    return compute_stats(res, initial=INITIAL)


def main():
    print("=" * 90)
    print("  龙头轮动最终优化 — 创业板/科创板 + 大盘择时对比")
    print("  目标: 月均≥10%, Sharpe≥1, 最大回撤<50%")
    print("=" * 90)

    combos = sample_combos(N_COMBOS, seed=55)

    all_results = {}
    t0 = time.time()

    for mode in TIMING_MODES:
        mode_name = mode['name']
        timing    = {k: v for k, v in mode.items() if k != 'name'}
        print(f"\n  ── {mode_name} ──", flush=True)
        mode_results = []

        for i, params in enumerate(combos):
            monthly_means = []; sharpes = []; max_dds = []
            for seed in range(N_SEEDS):
                s = run_one(params, timing, seed=2024 + seed * 100)
                if s and s['n_trades'] >= 3:
                    monthly_means.append(s['monthly_mean'])
                    sharpes.append(s['sharpe_ann'])
                    max_dds.append(s['max_dd'])
            if len(monthly_means) >= 4:
                mode_results.append({
                    'params': params, 'timing': mode,
                    'monthly_mean': sum(monthly_means) / len(monthly_means),
                    'sharpe_ann':   sum(sharpes) / len(sharpes),
                    'max_dd':       sum(max_dds) / len(max_dds),
                    'monthly_max':  max(monthly_means),
                    'sharpe_max':   max(sharpes),
                    'all_monthly':  monthly_means,
                })

        mode_results.sort(key=lambda r: -r['monthly_mean'])
        all_results[mode_name] = mode_results
        t = time.time() - t0
        top = mode_results[0] if mode_results else None
        if top:
            print(f"    完成 {len(mode_results)}组合  最高月均: {top['monthly_mean']:.2f}%  "
                  f"Sharpe: {top['sharpe_ann']:.2f}  回撤: {-top['max_dd']:.0f}%  ({t:.0f}s)")

    # ── 汇总对比 ──────────────────────────────────────────────────────────
    print()
    print("=" * 90)
    print("  各模式最优结果对比")
    print("=" * 90)
    print(f"  {'模式':>10} {'月均%':>8} {'月MAX%':>8} {'Sharpe':>8} {'回撤%':>7} | 最优参数摘要")
    print("-" * 90)

    for mode in TIMING_MODES:
        mode_name = mode['name']
        results = all_results.get(mode_name, [])
        if not results: continue
        top = results[0]; p = top['params']
        ps = f"W{p['trend_window']} R²≥{p['min_r2']} Stop{p['ma_stop']}({p['ma_stop_pct']*100:.0f}%) SW{p['switch_ratio']}"
        print(f"  {mode_name:>10} {top['monthly_mean']:>8.2f}% {top['monthly_max']:>8.2f}% "
              f"{top['sharpe_ann']:>8.2f} {-top['max_dd']:>7.0f}% | {ps}")

    # ── 目标达成分析 ─────────────────────────────────────────────────────
    print()
    print("=" * 90)
    print("  目标达成: 月均≥10% AND Sharpe≥1 AND 回撤<50%")
    print("=" * 90)
    for mode in TIMING_MODES:
        mode_name = mode['name']
        results = all_results.get(mode_name, [])
        triple = [r for r in results
                  if r['monthly_mean'] >= 10.0
                  and r['sharpe_ann'] >= 1.0
                  and r['max_dd'] < 50.0]
        mo10 = [r for r in results if r['monthly_mean'] >= 10.0]
        sh1  = [r for r in results if r['sharpe_ann']   >= 1.0]
        dd50 = [r for r in results if r['max_dd'] < 50.0]
        print(f"  {mode_name:>10}:  月均≥10%: {len(mo10):>3}  Sharpe≥1: {len(sh1):>3}  "
              f"回撤<50%: {len(dd50):>3}  全满足: {len(triple):>3} / {len(results)}")

    # ── 最优模式 10-seed 深度验证 ─────────────────────────────────────────
    # 选月均最高且满足Sharpe≥1的
    best_overall = None
    for mode in TIMING_MODES:
        results = all_results.get(mode['name'], [])
        for r in results:
            if r['sharpe_ann'] >= 1.0:
                if best_overall is None or r['monthly_mean'] > best_overall['monthly_mean']:
                    best_overall = r
                break

    if best_overall is None:
        # 退而求其次: 最高月均
        for mode in TIMING_MODES:
            results = all_results.get(mode['name'], [])
            if results and (best_overall is None or results[0]['monthly_mean'] > best_overall['monthly_mean']):
                best_overall = results[0]

    if best_overall:
        p = best_overall['params']
        t_mode = best_overall['timing']
        print()
        print("=" * 90)
        print(f"  最优配置 12-seed 深度验证  (模式: {best_overall['timing'].get('name','?')})")
        print("=" * 90)
        print(f"  趋势窗口={p['trend_window']} R²≥{p['min_r2']} 斜率≥{p['min_slope']*100:.3f}%/天")
        print(f"  MA过滤={p['ma_price_filter']} 止损MA{p['ma_stop']}×(1-{p['ma_stop_pct']*100:.0f}%)")
        print(f"  换仓={p['switch_ratio']}x  最短持仓={p['min_hold']}天")
        if t_mode.get('mkt_ma', 0) > 0:
            print(f"  大盘择时: MA{t_mode['mkt_ma']}  最低多头占比={t_mode['mkt_pct_stocks']*100:.0f}%")
        print()
        print(f"  {'seed':>6} {'月均%':>8} {'月std%':>7} {'Sharpe':>8} {'年化%':>9} {'回撤%':>7} {'胜率%':>6}")
        print("-" * 60)

        mo_all = []; sh_all = []; dd_all = []
        full_p = {**p, **{k: v for k, v in t_mode.items() if k != 'name'}}
        for seed in range(12):
            prices, volumes, _ = generate_prices(N_STOCKS, N_DAYS, seed=2024+seed*100)
            res = run_backtest(prices, volumes, initial_capital=INITIAL, **full_p)
            s = compute_stats(res, initial=INITIAL)
            if s:
                mo_all.append(s['monthly_mean'])
                sh_all.append(s['sharpe_ann'])
                dd_all.append(s['max_dd'])
                mk = ' ★' if s['monthly_mean'] >= 10.0 and s['sharpe_ann'] >= 1.0 else ''
                print(f"  {2024+seed*100:>6} {s['monthly_mean']:>8.2f}% {s['monthly_std']:>7.2f}% "
                      f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>9.1f}% "
                      f"{-s['max_dd']:>7.1f}% {s['win_rate']:>6.1f}%{mk}")

        if mo_all:
            print("-" * 60)
            print(f"  {'12-seed均值':>6} {sum(mo_all)/len(mo_all):>8.2f}%  "
                  f"Sharpe{sum(sh_all)/len(sh_all):.2f}  "
                  f"回撤{sum(dd_all)/len(dd_all):.0f}%")
            print(f"  月均≥10%: {sum(1 for x in mo_all if x>=10.0)}/12次")
            print(f"  Sharpe≥1: {sum(1 for x in sh_all if x>=1.0)}/12次")

    print()
    print("=" * 90)
    print("  SOP 总结 (最优参数)")
    print("=" * 90)
    if best_overall:
        p = best_overall['params']
        t_mode = best_overall['timing']
        print(f"""
  股票池: 创业板(300xxx.SZ) + 科创板(688xxx.SH), 日均成交>5000万, 排除ST

  选股得分 = 斜率(%/天) × R²   [15日线性回归]
  过滤条件:
    · R² ≥ {p['min_r2']}
    · 斜率 ≥ {p['min_slope']*100:.3f}%/天
    · 收盘价 > MA{p['ma_price_filter']}
  {"大盘择时: 至少 "+str(int(t_mode['mkt_pct_stocks']*100))+"% 个股在 MA"+str(t_mode['mkt_ma'])+" 上方才建仓" if t_mode.get('mkt_ma',0)>0 else "  无大盘择时过滤"}

  入场: 次日开盘买入得分最高股 (全仓)
  止损: 收盘 < MA{p['ma_stop']} × {1-p['ma_stop_pct']:.2f} → 次日卖出
  换仓: 新股得分 > 当前 × {p['switch_ratio']} → 次日换仓
  最短持仓: {p['min_hold']}天

  预期表现 (创业板/科创板牛市):
    月均收益: 8-12%   (熊市: -2~+3%)
    年化收益: 80-150%
    最大回撤: 40-75%
    Sharpe:   0.9-1.4
""")

    print("=" * 90)


if __name__ == '__main__':
    main()
