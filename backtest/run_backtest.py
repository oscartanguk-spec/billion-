"""
V18.2 回测主程序
运行: python backtest/run_backtest.py
输出: 控制台详细报告 + backtest/results.csv
"""
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest.stock_dataset import STOCKS
from backtest.mb_scorer import score_both


# ── 混淆矩阵工具 ──────────────────────────────────────────────────────
def confusion(predictions: list[bool], actuals: list[bool]):
    tp = sum(p and a for p, a in zip(predictions, actuals))
    fp = sum(p and not a for p, a in zip(predictions, actuals))
    fn = sum(not p and a for p, a in zip(predictions, actuals))
    tn = sum(not p and not a for p, a in zip(predictions, actuals))
    return tp, fp, fn, tn


def metrics(tp, fp, fn, tn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return precision, recall, f1


# ── Bootstrap 置信区间（精确率）────────────────────────────────────────
def bootstrap_precision_ci(predictions, actuals, n_boot=2000, ci=0.95):
    import random
    n = len(predictions)
    boot_precisions = []
    for _ in range(n_boot):
        idx = [random.randint(0, n - 1) for _ in range(n)]
        tp = sum(predictions[i] and actuals[i] for i in idx)
        fp = sum(predictions[i] and not actuals[i] for i in idx)
        if tp + fp > 0:
            boot_precisions.append(tp / (tp + fp))
    boot_precisions.sort()
    lo = boot_precisions[int((1 - ci) / 2 * n_boot)]
    hi = boot_precisions[int((1 + ci) / 2 * n_boot)]
    return lo, hi


# ── 主程序 ────────────────────────────────────────────────────────────
def main():
    results = []
    for s in STOCKS:
        scores = score_both(s)
        row = {**s, **scores}
        results.append(row)

    # ── 按 MB_3x 排序打印明细 ──────────────────────────────────────────
    results.sort(key=lambda r: r["mb_score_3x"], reverse=True)

    print("=" * 110)
    print("V18.2 回测结果明细（按 MB_3x 降序）")
    print("=" * 110)
    hdr = f"{'股票':<14} {'年份':<5} {'类别':<5} {'实际涨幅':>7} {'MB_3x':>6} {'通3x':>5} {'MB_2x':>6} {'通2x':>5} {'PTS':>5} {'floor':>5} {'s1':>4} {'s2':>4} {'scp':>4} {'P%':>4}"
    print(hdr)
    print("-" * 110)
    for r in results:
        flag3 = "✓" if r["pass_3x"] else "✗"
        flag2 = "✓" if r["pass_2x"] else "✗"
        actual_str = f"{r['actual_1y']:.2f}x"
        label_mark = ""
        if r["label_3x"]:   label_mark = "3x"
        elif r["label_2x"]: label_mark = "2x"
        else:                label_mark = "neg"
        print(
            f"{r['name']:<14} {r['entry_year']:<5} {label_mark:<5} {actual_str:>7} "
            f"{r['mb_score_3x']:>6.3f} {flag3:>5} "
            f"{r['mb_score_2x']:>6.3f} {flag2:>5} "
            f"{r['pts']:>5.3f} {r['floor']:>5.3f} "
            f"{r['s1']:>4.2f} {r['s2']:>4.2f} {r['scp']:>4.2f} {r['p_eff']:>4.0f}"
        )

    # ── 汇总统计 ──────────────────────────────────────────────────────
    preds_3x = [r["pass_3x"] for r in results]
    actual_3x = [r["label_3x"] for r in results]
    preds_2x = [r["pass_2x"] for r in results]
    actual_2x = [r["label_2x"] for r in results]

    tp3, fp3, fn3, tn3 = confusion(preds_3x, actual_3x)
    tp2, fp2, fn2, tn2 = confusion(preds_2x, actual_2x)
    prec3, rec3, f1_3 = metrics(tp3, fp3, fn3, tn3)
    prec2, rec2, f1_2 = metrics(tp2, fp2, fn2, tn2)

    ci_lo3, ci_hi3 = bootstrap_precision_ci(preds_3x, actual_3x)
    ci_lo2, ci_hi2 = bootstrap_precision_ci(preds_2x, actual_2x)

    print()
    print("=" * 60)
    print("  3x 模式（MB ≥ 0.80）汇总")
    print("=" * 60)
    print(f"  正样本总数 : {sum(actual_3x)}")
    print(f"  负样本总数 : {len(actual_3x) - sum(actual_3x)}")
    print(f"  TP={tp3}  FP={fp3}  FN={fn3}  TN={tn3}")
    print(f"  精确率 Precision : {prec3:.1%}  (95% CI: {ci_lo3:.1%}–{ci_hi3:.1%})")
    print(f"  召回率 Recall    : {rec3:.1%}")
    print(f"  F1-Score         : {f1_3:.3f}")

    print()
    print("=" * 60)
    print("  2x 模式（MB ≥ 0.68）汇总")
    print("=" * 60)
    print(f"  正样本总数 : {sum(actual_2x)}")
    print(f"  负样本总数 : {len(actual_2x) - sum(actual_2x)}")
    print(f"  TP={tp2}  FP={fp2}  FN={fn2}  TN={tn2}")
    print(f"  精确率 Precision : {prec2:.1%}  (95% CI: {ci_lo2:.1%}–{ci_hi2:.1%})")
    print(f"  召回率 Recall    : {rec2:.1%}")
    print(f"  F1-Score         : {f1_2:.3f}")

    # ── 假阳性分析 ────────────────────────────────────────────────────
    fps_3x = [r for r in results if r["pass_3x"] and not r["label_3x"]]
    fps_2x = [r for r in results if r["pass_2x"] and not r["label_2x"]]
    fns_3x = [r for r in results if not r["pass_3x"] and r["label_3x"]]
    fns_2x = [r for r in results if not r["pass_2x"] and r["label_2x"]]

    if fps_3x:
        print()
        print("── 3x 模式 假阳性（通过评分但实际未达3x）──")
        for r in fps_3x:
            print(f"  {r['name']}({r['entry_year']})  MB={r['mb_score_3x']:.3f}  "
                  f"实际={r['actual_1y']:.2f}x  SCP={r['scp']:.2f}  P%={r['p_eff']:.0f}  "
                  f"来源: {r['source']}")

    if fns_3x:
        print()
        print("── 3x 模式 假阴性（应通过但被漏掉）──")
        for r in fns_3x:
            print(f"  {r['name']}({r['entry_year']})  MB={r['mb_score_3x']:.3f}  "
                  f"实际={r['actual_1y']:.2f}x  SCP={r['scp']:.2f}  缺口={0.80 - r['mb_score_3x']:.3f}")

    if fps_2x:
        print()
        print("── 2x 模式 假阳性 ──")
        for r in fps_2x:
            print(f"  {r['name']}({r['entry_year']})  MB={r['mb_score_2x']:.3f}  "
                  f"实际={r['actual_1y']:.2f}x  SCP={r['scp']:.2f}  来源: {r['source']}")

    if fns_2x:
        print()
        print("── 2x 模式 假阴性 ──")
        for r in fns_2x:
            print(f"  {r['name']}({r['entry_year']})  MB={r['mb_score_2x']:.3f}  "
                  f"实际={r['actual_1y']:.2f}x  SCP={r['scp']:.2f}  缺口={0.68 - r['mb_score_2x']:.3f}")

    # ── 因子分析 ─────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("  因子区分力分析（均值差异）")
    print("=" * 60)

    pos_3x = [r for r in results if r["label_3x"]]
    neg_3x = [r for r in results if not r["label_3x"]]

    def avg(lst, key): return sum(x[key] for x in lst) / len(lst) if lst else 0

    factors = ["s1", "s2", "scp", "p_eff", "s4_ovmv", "s4_moat", "pts", "mb_score_3x"]
    print(f"  {'因子':<14} {'3x正样本均值':>13} {'非3x均值':>10} {'差异':>8}")
    for f in factors:
        pos_avg = avg(pos_3x, f)
        neg_avg = avg(neg_3x, f)
        diff = pos_avg - neg_avg
        print(f"  {f:<14} {pos_avg:>13.3f} {neg_avg:>10.3f} {diff:>+8.3f}")

    # ── Regime 分析 ──────────────────────────────────────────────────
    print()
    print("── 宏观Regime对回测结果的影响 ──")
    from collections import defaultdict
    regime_stats = defaultdict(lambda: {"total": 0, "hit_2x": 0, "hit_3x": 0})
    for r in results:
        rg = r["regime"]
        regime_stats[rg]["total"] += 1
        if r["label_2x"]: regime_stats[rg]["hit_2x"] += 1
        if r["label_3x"]: regime_stats[rg]["hit_3x"] += 1
    print(f"  {'Regime':<8} {'样本数':>6} {'2x命中率':>9} {'3x命中率':>9}")
    for rg in sorted(regime_stats):
        st = regime_stats[rg]
        r2 = st["hit_2x"] / st["total"] if st["total"] else 0
        r3 = st["hit_3x"] / st["total"] if st["total"] else 0
        print(f"  {rg:<8} {st['total']:>6} {r2:>9.1%} {r3:>9.1%}")

    # ── SCP 区分力分析 ────────────────────────────────────────────────
    print()
    print("── SCP 分层精确率分析 ──")
    scp_bands = [
        ("SCP≥0.70", lambda r: r["scp"] >= 0.70),
        ("SCP 0.50-0.69", lambda r: 0.50 <= r["scp"] < 0.70),
        ("SCP<0.50", lambda r: r["scp"] < 0.50),
    ]
    print(f"  {'SCP段':<15} {'样本':>5} {'2x实际比例':>11} {'3x实际比例':>11}")
    for label, fn in scp_bands:
        subset = [r for r in results if fn(r)]
        r2 = sum(r["label_2x"] for r in subset) / len(subset) if subset else 0
        r3 = sum(r["label_3x"] for r in subset) / len(subset) if subset else 0
        print(f"  {label:<15} {len(subset):>5} {r2:>11.1%} {r3:>11.1%}")

    # ── P_eff 分层分析 ────────────────────────────────────────────────
    print()
    print("── 渗透率 P_eff 分层精确率分析 ──")
    peff_bands = [
        ("P<10%", lambda r: r["p_eff"] < 10),
        ("P 10-25%", lambda r: 10 <= r["p_eff"] < 25),
        ("P 25-45%", lambda r: 25 <= r["p_eff"] < 45),
        ("P≥45%", lambda r: r["p_eff"] >= 45),
    ]
    print(f"  {'P_eff段':<12} {'样本':>5} {'2x实际比例':>11} {'3x实际比例':>11}")
    for label, fn in peff_bands:
        subset = [r for r in results if fn(r)]
        r2 = sum(r["label_2x"] for r in subset) / len(subset) if subset else 0
        r3 = sum(r["label_3x"] for r in subset) / len(subset) if subset else 0
        print(f"  {label:<12} {len(subset):>5} {r2:>11.1%} {r3:>11.1%}")

    # ── 周期股专项分析 ────────────────────────────────────────────────
    cyclical = ["赣锋锂业", "天齐锂业", "天齐锂业_22", "盐湖股份", "华友钴业", "英科医疗"]
    cyclical_results = [r for r in results if r["name"] in cyclical]
    if cyclical_results:
        print()
        print("── 周期股专项（看框架是否能正确区分周期上/下行）──")
        print(f"  {'股票':<12} {'年份':<5} {'实际':>6} {'MB_3x':>7} {'MB_2x':>7} {'PTS':>6} {'P_eff':>6}")
        for r in cyclical_results:
            print(f"  {r['name']:<12} {r['entry_year']:<5} {r['actual_1y']:.2f}x "
                  f"{r['mb_score_3x']:>7.3f} {r['mb_score_2x']:>7.3f} "
                  f"{r['pts']:>6.3f} {r['p_eff']:>6.0f}%")

    # ── MB得分分布箱统计 ─────────────────────────────────────────────
    print()
    print("── MB_3x 分布（正样本 vs 负样本）──")
    pos_scores = sorted([r["mb_score_3x"] for r in results if r["label_3x"] or r["label_2x"]])
    neg_scores = sorted([r["mb_score_3x"] for r in results if not r["label_2x"] and not r["label_3x"]])

    def percentile(lst, p):
        if not lst: return 0
        i = (len(lst) - 1) * p / 100
        lo, hi = int(i), min(int(i) + 1, len(lst) - 1)
        return lst[lo] + (i - lo) * (lst[hi] - lst[lo])

    print(f"  正样本 n={len(pos_scores)}: min={min(pos_scores):.3f}  "
          f"p25={percentile(pos_scores,25):.3f}  median={percentile(pos_scores,50):.3f}  "
          f"p75={percentile(pos_scores,75):.3f}  max={max(pos_scores):.3f}")
    print(f"  负样本 n={len(neg_scores)}: min={min(neg_scores):.3f}  "
          f"p25={percentile(neg_scores,25):.3f}  median={percentile(neg_scores,50):.3f}  "
          f"p75={percentile(neg_scores,75):.3f}  max={max(neg_scores):.3f}")

    # ── 输出 CSV ─────────────────────────────────────────────────────
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.csv")
    fieldnames = [
        "name", "code", "entry_year", "category", "actual_1y",
        "label_2x", "label_3x",
        "mb_score_3x", "pass_3x", "mb_score_2x", "pass_2x",
        "pts", "floor", "s1", "s2", "s3", "s4",
        "scp", "p_eff", "s4_ovmv", "catalyst_grade", "regime",
        "mb_raw", "secondary_mult", "resonance", "source",
    ]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    print()
    print(f"详细结果已保存至: {out_path}")
    print("=" * 110)


if __name__ == "__main__":
    main()
