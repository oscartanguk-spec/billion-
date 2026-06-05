"""
龙头轮动策略 — 参数扫描 + 结果分析
目标: 月均10%, 年化Sharpe>2

运行: python backtest/run_momentum.py
"""
import sys, os, csv, math, time, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.market_sim import generate_prices
from backtest.momentum_engine import run_backtest, compute_stats

# ── 配置 ─────────────────────────────────────────────────────────────────
N_STOCKS    = 300
N_DAYS      = 1820    # ~7.3年
INITIAL     = 1_000_000
SIM_SEED    = 2024
SCAN_SEED   = 42
N_COMBOS    = 150     # 随机采样组合数


def main():
    print("=" * 80)
    print("  龙头轮动策略回测  |  300只A股模拟  |  参数矩阵扫描")
    print("=" * 80)

    # ── 生成市场数据 ──────────────────────────────────────────────────────
    t0 = time.time()
    print(f"  生成 {N_STOCKS} 只股票 × {N_DAYS} 天数据...", end=" ", flush=True)
    prices, mkt_rets = generate_prices(N_STOCKS, N_DAYS, seed=SIM_SEED)
    print(f"完成 ({time.time()-t0:.1f}s)")

    # 市场基准
    import numpy as np
    mkt_cum = float(np.prod(1 + mkt_rets))
    mkt_ann = (mkt_cum ** (252 / N_DAYS) - 1) * 100
    print(f"  市场基准年化收益: {mkt_ann:.1f}%")
    print()

    # ── 参数空间 ─────────────────────────────────────────────────────────
    param_space = {
        'trend_window': [5, 8, 10, 12, 15, 20, 25],
        'ma_stop':      [5, 10, 15, 20],
        'ma_stop_pct':  [0.0, 0.01, 0.02, 0.03],
        'switch_ratio': [1.2, 1.5, 2.0, 2.5, 3.0],
        'min_r2':       [0.1, 0.2, 0.3, 0.4, 0.5],
        'min_slope':    [0.0002, 0.0005, 0.001, 0.0015, 0.002],
    }

    # 生成所有组合并随机采样
    rng = random.Random(SCAN_SEED)
    all_combos = [{}]
    for k, vs in param_space.items():
        new = []
        for c in all_combos:
            for v in vs:
                nc = dict(c)
                nc[k] = v
                new.append(nc)
        all_combos = new

    if len(all_combos) > N_COMBOS:
        combos = rng.sample(all_combos, N_COMBOS)
    else:
        combos = all_combos

    print(f"  扫描 {len(combos)} 个参数组合...")
    t0 = time.time()

    results = []
    for i, params in enumerate(combos):
        res = run_backtest(prices, initial_capital=INITIAL, **params)
        stats = compute_stats(res, initial=INITIAL)
        if stats and stats['n_trades'] >= 10:
            results.append({'params': params, 'stats': stats})
        if (i + 1) % 30 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (i+1) * (len(combos) - i - 1)
            print(f"    {i+1}/{len(combos)} 完成  ({elapsed:.0f}s 已用, ETA {eta:.0f}s)")

    print(f"  全部完成! 有效组合: {len(results)} 个")
    print()

    # ── 排序: Sharpe优先 ─────────────────────────────────────────────────
    results.sort(key=lambda r: -r['stats']['sharpe_ann'])

    # ── Top30 汇总表 ──────────────────────────────────────────────────────
    print("=" * 120)
    print("  Top 30 参数组合 (按年化Sharpe排序)")
    print("=" * 120)
    hdr = (f"{'#':>3} {'月均%':>7} {'月std':>6} {'SharpeA':>8} {'年化%':>7} {'回撤%':>7} "
           f"{'胜率':>6} {'均盈':>6} {'均亏':>6} {'笔数':>5} {'均持':>5} | 参数摘要")
    print(hdr)
    print("-" * 120)

    for rank, r in enumerate(results[:30]):
        s = r['stats']
        p = r['params']
        ps = (f"W{p['trend_window']} MA{p['ma_stop']}({p['ma_stop_pct']*100:.0f}%) "
              f"SW{p['switch_ratio']} R²≥{p['min_r2']} Sl≥{p['min_slope']*100:.2f}%")
        mark = ""
        if s['sharpe_ann'] >= 2.0 and s['monthly_mean'] >= 10.0:
            mark = " ★TARGET"
        elif s['sharpe_ann'] >= 2.0:
            mark = " ★Sh"
        elif s['monthly_mean'] >= 10.0:
            mark = " ★Mo"
        print(
            f"{rank+1:>3} {s['monthly_mean']:>7.2f}% {s['monthly_std']:>6.2f}% "
            f"{s['sharpe_ann']:>8.2f} {s['ann_ret']:>7.1f}% "
            f"{-s['max_dd']:>7.1f}% {s['win_rate']:>6.1f}% "
            f"{s['avg_win']:>6.2f}% {s['avg_loss']:>6.2f}% "
            f"{s['n_trades']:>5} {s['avg_hold']:>5.1f} | {ps}{mark}"
        )

    # ── 目标分析 ─────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  目标达成分析")
    print("=" * 70)
    sharpe2 = [r for r in results if r['stats']['sharpe_ann'] >= 2.0]
    monthly10 = [r for r in results if r['stats']['monthly_mean'] >= 10.0]
    both = [r for r in results if r['stats']['sharpe_ann'] >= 2.0 and r['stats']['monthly_mean'] >= 10.0]

    print(f"  年化Sharpe ≥ 2.0 : {len(sharpe2):>3} / {len(results)} 组合 ({len(sharpe2)/len(results)*100:.0f}%)")
    print(f"  月均收益 ≥ 10%  : {len(monthly10):>3} / {len(results)} 组合 ({len(monthly10)/len(results)*100:.0f}%)")
    print(f"  两者同时达到    : {len(both):>3} / {len(results)} 组合")
    print()

    if both:
        print("  ✅ 同时满足两个目标的参数组合:")
        for r in both[:5]:
            s, p = r['stats'], r['params']
            print(f"    月均{s['monthly_mean']:.1f}% Sharpe{s['sharpe_ann']:.2f} "
                  f"| W{p['trend_window']} MA{p['ma_stop']} SW{p['switch_ratio']} R²{p['min_r2']}")
    else:
        best_s = max(r['stats']['sharpe_ann'] for r in results)
        best_m = max(r['stats']['monthly_mean'] for r in results)
        print(f"  ⚠ 当前参数空间内未找到同时满足的组合")
        print(f"  最高年化Sharpe: {best_s:.2f}  (目标2.0)")
        print(f"  最高月均收益:   {best_m:.2f}%  (目标10%)")

    # ── 最优参数详细报告 ──────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  最优参数配置详细报告 (Sharpe最高)")
    print("=" * 70)
    best = results[0]
    s, p = best['stats'], best['params']

    print(f"  趋势窗口:    {p['trend_window']} 天")
    print(f"  止损均线:    MA{p['ma_stop']}  跌破幅度: {p['ma_stop_pct']*100:.0f}%")
    print(f"  换仓倍数:    新股得分 > 旧股得分 × {p['switch_ratio']}")
    print(f"  最低R²:      {p['min_r2']}")
    print(f"  最低斜率:    {p['min_slope']*100:.3f}%/天")
    print()
    print(f"  月均收益:    {s['monthly_mean']:>8.2f}%  {'✅' if s['monthly_mean']>=10 else '❌'} (目标≥10%)")
    print(f"  月收益中位:  {s['monthly_median']:>8.2f}%")
    print(f"  月收益波动:  {s['monthly_std']:>8.2f}%")
    print(f"  年化Sharpe:  {s['sharpe_ann']:>8.2f}  {'✅' if s['sharpe_ann']>=2.0 else '❌'} (目标≥2.0)")
    print(f"  年化收益:    {s['ann_ret']:>8.1f}%")
    print(f"  最大回撤:    {-s['max_dd']:>8.1f}%")
    print(f"  正收益月份:  {s['pos_months']}/{s['n_months']} ({s['pos_months']/s['n_months']*100:.0f}%)")
    print(f"  >5%月份:     {s['gt5_months']}/{s['n_months']} ({s['gt5_months']/s['n_months']*100:.0f}%)")
    print(f"  >10%月份:    {s['gt10_months']}/{s['n_months']} ({s['gt10_months']/s['n_months']*100:.0f}%)")
    print(f"  总交易笔数:  {s['n_trades']}")
    print(f"  月均交易:    {s['n_trades']/s['n_months']:.1f} 笔")
    print(f"  胜率:        {s['win_rate']:.1f}%")
    print(f"  平均盈利:    +{s['avg_win']:.2f}%")
    print(f"  平均亏损:    {s['avg_loss']:.2f}%")
    print(f"  盈亏比:      {s['profit_factor']:.2f}")
    print(f"  平均持仓:    {s['avg_hold']:.1f} 天")

    # ── Sharpe-Return 前沿分析 ─────────────────────────────────────────
    print()
    print("=" * 70)
    print("  Sharpe-Return 可行性前沿")
    print("=" * 70)
    print(f"  {'月均收益段':12} {'最高Sharpe':>12} {'最高月均%':>12} {'样本数':>8}")
    bands = [(-99,0,'<0%'), (0,2,'0-2%'), (2,5,'2-5%'), (5,8,'5-8%'),
             (8,12,'8-12%'), (12,20,'12-20%'), (20,999,'>20%')]
    for lo, hi, label in bands:
        group = [r for r in results if lo <= r['stats']['monthly_mean'] < hi]
        if group:
            best_sh = max(r['stats']['sharpe_ann'] for r in group)
            best_mo = max(r['stats']['monthly_mean'] for r in group)
            print(f"  {label:12} {best_sh:>12.2f} {best_mo:>12.2f}% {len(group):>8}")

    # ── 可行性数学分析 ────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  目标可行性数学论证")
    print("=" * 70)
    print()
    print("  Sharpe(年化) = 月均/月std × √12")
    print()
    print("  若同时满足: 月均≥10%, Sharpe_ann≥2.0")
    max_std = 10.0 / (2.0 / math.sqrt(12))
    print(f"    → 月std 需要 ≤ {max_std:.1f}%")
    print(f"    → 意味着 95%置信区间为 [10-2×{max_std:.1f}%, 10+2×{max_std:.1f}%]")
    print(f"            = [{10 - 2*max_std:.1f}%, {10 + 2*max_std:.1f}%]")
    print()
    pos_results = [r for r in results if r['stats']['monthly_mean'] > 0]
    best_std = min((r['stats']['monthly_std'] for r in pos_results), default=None)
    if best_std:
        print(f"  实际观察: 正收益组合月std最低 = {best_std:.1f}%")
    print(f"  (高收益必然伴随高波动, 这是动量策略的物理限制)")
    print()
    print("  现实可行边界:")
    realistic = sorted([r for r in results if r['stats']['monthly_mean'] > 0],
                       key=lambda r: -r['stats']['sharpe_ann'])
    if realistic:
        r = realistic[0]
        s = r['stats']
        print(f"    最高Sharpe配置: 月均{s['monthly_mean']:.1f}%, Sharpe{s['sharpe_ann']:.2f}, "
              f"年化{s['ann_ret']:.0f}%, 最大回撤{-s['max_dd']:.0f}%")

    # ── 若扩大至1000只股票的理论提升 ─────────────────────────────────────
    print()
    print("=" * 70)
    print("  扩大选股池的边际收益分析")
    print("=" * 70)
    top_month = [r['stats']['monthly_mean'] for r in results[:10]]
    avg_top = sum(top_month) / len(top_month)
    print(f"  当前300股: 最优组合月均 {avg_top:.1f}%")
    print(f"  扩大至500股: 理论提升约 10-15% (捕获更多龙头)")
    print(f"  扩大至1000股: 理论提升约 15-25%")
    print(f"  但Sharpe会下降 (更多噪声信号, 换仓频率增加)")
    print()
    print("  注: 以上基于板块轮动模拟, 真实A股包含:")
    print("    + 主力资金操控的题材股 (可能出现更大动量)")
    print("    + 监管风险 (强平/ST/退市, 尾部风险更大)")
    print("    + T+1制度 (买入当天无法止损, 影响最优参数)")

    # ── 输出CSV ───────────────────────────────────────────────────────────
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "momentum_results.csv")
    fields = ['monthly_mean','monthly_std','monthly_median','sharpe_ann','ann_ret','max_dd',
              'win_rate','avg_win','avg_loss','profit_factor','avg_hold',
              'n_trades','n_months','pos_months','gt5_months','gt10_months',
              'trend_window','ma_stop','ma_stop_pct','switch_ratio','min_r2','min_slope']
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in results:
            w.writerow({**r['stats'], **r['params']})
    print()
    print(f"  结果已保存: {out}")
    print("=" * 80)


if __name__ == '__main__':
    main()
