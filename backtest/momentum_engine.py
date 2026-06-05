"""
动量策略回测引擎 V3 — 精准入场版
新增:
  - 价格 > MA20 过滤
  - 回调入场: 价格在 MA10 ± 缓冲 内才买
  - 成交量突破入场 (备选)
  - 最短持仓天数
  - MA20×(1-stop_pct) 止损
"""
import math
import numpy as np
from typing import Dict, List, Optional, Tuple

COMMISSION = 0.0003
STAMP_DUTY = 0.001
LOT = 100


def build_arrays(prices, volumes=None):
    codes = sorted(prices.keys())
    arr = np.array([prices[c] for c in codes], dtype=np.float64).T
    vol_arr = np.array([volumes[c] for c in codes], dtype=np.float64).T if volumes else np.ones_like(arr)
    return codes, arr, vol_arr


def score_matrix(price_arr, window, min_r2, min_slope):
    n_days, n_stocks = price_arr.shape
    scores = np.zeros((n_days, n_stocks))
    x = np.arange(window, dtype=np.float64); x -= x.mean()
    sxx = float(np.dot(x, x))
    for d in range(window - 1, n_days):
        seg = price_arr[d - window + 1: d + 1, :]
        y_mean = seg.mean(axis=0); y_centered = seg - y_mean
        sxy = (x[:, None] * y_centered).sum(axis=0)
        syy = (y_centered ** 2).sum(axis=0)
        slope = sxy / sxx
        with np.errstate(invalid='ignore', divide='ignore'):
            r2 = np.where(syy > 0, sxy**2 / (sxx * syy), 0.0)
        r2 = np.clip(r2, 0.0, 1.0)
        slope_pct = np.where(y_mean > 0, slope / y_mean, 0.0)
        valid = (r2 >= min_r2) & (slope_pct >= min_slope)
        scores[d] = np.where(valid, slope_pct * r2, 0.0)
    return scores


def _ma(arr, window):
    n_days, n_stocks = arr.shape
    result = np.zeros_like(arr)
    for d in range(n_days):
        result[d] = arr[max(0, d - window + 1):d + 1].mean(axis=0)
    return result


def run_backtest(
    prices, volumes=None,
    trend_window=15, min_r2=0.5, min_slope=0.0002,
    ma_price_filter=20,
    pullback_ma=10, pullback_lo=-0.04, pullback_hi=0.03,
    vol_mult=1.5, slope_accel=1.1,
    min_hold=10,
    ma_stop=20, ma_stop_pct=0.03,
    switch_ratio=3.5,
    # 大盘择时参数
    mkt_ma=50,          # 大盘均线窗口 (0=关闭择时)
    mkt_pct_stocks=0.3, # 至少30%个股在均线上才认为是牛市
    initial_capital=1_000_000,
):
    codes, arr, vol_arr = build_arrays(prices, volumes)
    n_days, n_stocks = arr.shape
    n_days -= 1

    if vol_arr.shape[0] < arr.shape[0]:
        vol_arr = np.vstack([vol_arr[:1], vol_arr])

    sc_mat   = score_matrix(arr, trend_window, min_r2, min_slope)
    ma10_mat = _ma(arr, pullback_ma)
    ma20_mat = _ma(arr, ma_price_filter)
    stop_mat = _ma(arr, ma_stop)
    vma_mat  = _ma(vol_arr, 20)
    # 大盘择时: 用全体股票的长期均线来判断牛熊
    if mkt_ma > 0:
        mkt_ma_mat = _ma(arr, mkt_ma)   # (n_days+1, n_stocks)
    else:
        mkt_ma_mat = None

    cash = float(initial_capital)
    pos_idx = None; pos_shares = 0; pos_cost = 0.0; buy_day = -999
    equity_curve = [cash]; trades = []; monthly_equity = {}

    def do_sell(idx, day, reason):
        nonlocal cash, pos_idx, pos_shares, pos_cost
        price = float(arr[day, idx])
        proceeds = pos_shares * price * (1 - COMMISSION - STAMP_DUTY)
        pnl = proceeds - pos_shares * pos_cost * (1 + COMMISSION)
        trades.append({'code': codes[idx], 'buy_day': buy_day, 'sell_day': day,
                       'buy_price': pos_cost, 'sell_price': price, 'shares': pos_shares,
                       'pnl': pnl, 'pnl_pct': (price / pos_cost - 1) * 100,
                       'hold': day - buy_day, 'reason': reason, 'win': 1 if pnl > 0 else 0})
        cash += proceeds; pos_idx = None; pos_shares = 0

    def do_buy(idx, day):
        nonlocal cash, pos_idx, pos_shares, pos_cost, buy_day
        price = float(arr[day, idx])
        if price <= 0: return
        max_sh = int(cash / (price * (1 + COMMISSION))) // LOT * LOT
        if max_sh <= 0: return
        cash -= max_sh * price * (1 + COMMISSION)
        pos_idx = idx; pos_shares = max_sh; pos_cost = price; buy_day = day

    for day in range(max(trend_window, mkt_ma if mkt_ma > 0 else 0), n_days + 1):
        sc_today = sc_mat[day]; sc_prev = sc_mat[max(0, day - 1)]
        pt = arr[day]; ma10 = ma10_mat[day]; ma20 = ma20_mat[day]
        stop_line = stop_mat[day]; vol = vol_arr[day] if day < vol_arr.shape[0] else np.ones(n_stocks)
        vma = vma_mat[day]

        # 大盘择时: 统计多少股票价格在长期均线之上
        if mkt_ma_mat is not None:
            above_mkt_ma = float((pt > mkt_ma_mat[day]).mean())
            market_is_bull = (above_mkt_ma >= mkt_pct_stocks)
        else:
            market_is_bull = True

        valid = (sc_today > 0) & (pt > ma20)

        with np.errstate(invalid='ignore', divide='ignore'):
            rel_ma10 = np.where(ma10 > 0, pt / ma10 - 1, -1.0)
        pb_sig = (rel_ma10 >= pullback_lo) & (rel_ma10 <= pullback_hi)
        vb_sig = (vol > vma * vol_mult) & (pt > arr[day - 1]) & (sc_today > sc_prev * slope_accel) & (sc_prev > 0)

        entry_sc = np.where(valid & (pb_sig | vb_sig), sc_today, 0.0)
        best_e   = int(np.argmax(entry_sc)); best_es = float(entry_sc[best_e])
        all_best = int(np.argmax(sc_today)); all_bs  = float(sc_today[all_best])

        need_stop = False
        if pos_idx is not None and (day - buy_day) >= 1:
            if float(pt[pos_idx]) < float(stop_line[pos_idx]) * (1 - ma_stop_pct):
                need_stop = True
        if need_stop:
            do_sell(pos_idx, day, 'mkt_stop' if not market_is_bull else 'ma_stop')

        # 熊市: 持仓止损后不再建新仓
        if (not need_stop and not market_is_bull and pos_idx is not None and (day - buy_day) >= 1):
            if float(pt[pos_idx]) < float(stop_line[pos_idx]) * (1 - ma_stop_pct * 0.5):
                do_sell(pos_idx, day, 'bear_stop')

        if (not need_stop and pos_idx is not None and (day - buy_day) >= min_hold
                and all_bs > 0 and all_best != pos_idx):
            if all_bs > float(sc_today[pos_idx]) * switch_ratio:
                do_sell(pos_idx, day, 'switch')

        # 只在牛市（或无过滤）时建仓
        if pos_idx is None and best_es > 0 and market_is_bull:
            do_buy(best_e, day)

        equity = (cash + pos_shares * float(pt[pos_idx])) if pos_idx is not None else cash
        equity_curve.append(equity)
        monthly_equity[day // 21] = equity

    if pos_idx is not None:
        do_sell(pos_idx, n_days, 'end')

    return {'equity_curve': equity_curve, 'trades': trades,
            'monthly_equity': monthly_equity, 'final_equity': equity_curve[-1]}


def compute_stats(result, initial=1_000_000):
    trades = result['trades']; meq = result['monthly_equity']
    n_months = len(meq)
    if n_months < 3 or not trades: return {}

    final = result['final_equity']
    ann_ret = ((final / initial) ** (12 / max(n_months, 1)) - 1) * 100
    eq_vals = [meq[k] for k in sorted(meq.keys())]
    mr = [(eq_vals[i] - eq_vals[i-1]) / eq_vals[i-1] * 100 for i in range(1, len(eq_vals))]
    mr.insert(0, (eq_vals[0] - initial) / initial * 100)

    arr_m = np.array(mr)
    mn = float(arr_m.mean()); std = float(arr_m.std())
    sharpe_ann = (mn / std * math.sqrt(12)) if std > 0 else 0.0

    curve_a = np.array(result['equity_curve'])
    peak = np.maximum.accumulate(curve_a)
    max_dd = float(((peak - curve_a) / peak * 100).max())

    wins   = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win  = float(np.mean([t['pnl_pct'] for t in wins]))  if wins   else 0.0
    avg_loss = float(np.mean([t['pnl_pct'] for t in losses])) if losses else 0.0
    pf = sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses) + 1e-9)

    by_reason = {}
    for t in trades: by_reason[t['reason']] = by_reason.get(t['reason'], 0) + 1

    return {
        'final_equity': final, 'ann_ret': ann_ret, 'max_dd': max_dd,
        'sharpe_ann': sharpe_ann, 'monthly_mean': mn, 'monthly_std': std,
        'monthly_median': float(np.median(arr_m)),
        'pos_months': int((arr_m > 0).sum()), 'gt5_months': int((arr_m > 5).sum()),
        'gt10_months': int((arr_m > 10).sum()), 'n_months': n_months,
        'n_trades': len(trades), 'win_rate': win_rate,
        'avg_win': avg_win, 'avg_loss': avg_loss,
        'profit_factor': float(pf), 'avg_hold': float(np.mean([t['hold'] for t in trades])),
        'exit_reasons': by_reason,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 多仓位回测引擎 (持 top-N 只股票, 等权)
# ─────────────────────────────────────────────────────────────────────────────

def run_backtest_multi(
    prices, volumes=None,
    n_positions=3,              # 同时持有股票数
    trend_window=20, min_r2=0.4, min_slope=0.0002,
    ma_price_filter=20,
    min_hold=3,
    ma_stop=20, ma_stop_pct=0.07,
    switch_ratio=2.5,
    mkt_ma=0, mkt_pct_stocks=0.30,
    initial_capital=1_000_000,
):
    """
    等权多仓位版本: 每只股票分配 1/n_positions 资金
    换仓逻辑: 当持仓中某只股票被更强股票超越时换掉得分最低的那只
    """
    codes, arr, vol_arr = build_arrays(prices, volumes)
    n_days, n_stocks = arr.shape
    n_days -= 1

    if vol_arr.shape[0] < arr.shape[0]:
        vol_arr = np.vstack([vol_arr[:1], vol_arr])

    sc_mat   = score_matrix(arr, trend_window, min_r2, min_slope)
    ma20_mat = _ma(arr, ma_price_filter)
    stop_mat = _ma(arr, ma_stop)
    if mkt_ma > 0:
        mkt_ma_mat = _ma(arr, mkt_ma)
    else:
        mkt_ma_mat = None

    # 每个仓位独立跟踪
    slot_cash     = [initial_capital / n_positions] * n_positions
    slot_idx      = [None] * n_positions
    slot_shares   = [0]    * n_positions
    slot_cost     = [0.0]  * n_positions
    slot_buy_day  = [-999] * n_positions

    equity_curve   = [float(initial_capital)]
    trades         = []
    monthly_equity = {}

    def sell_slot(s, day, reason):
        if slot_idx[s] is None: return
        idx   = slot_idx[s]
        price = float(arr[day, idx])
        proceeds = slot_shares[s] * price * (1 - COMMISSION - STAMP_DUTY)
        pnl = proceeds - slot_shares[s] * slot_cost[s] * (1 + COMMISSION)
        trades.append({
            'slot': s, 'code': codes[idx],
            'buy_day': slot_buy_day[s], 'sell_day': day,
            'buy_price': slot_cost[s], 'sell_price': price,
            'pnl': pnl, 'pnl_pct': (price / slot_cost[s] - 1) * 100,
            'hold': day - slot_buy_day[s], 'reason': reason,
            'win': 1 if pnl > 0 else 0,
        })
        slot_cash[s]  += proceeds
        slot_idx[s]    = None
        slot_shares[s] = 0

    def buy_slot(s, idx, day):
        price = float(arr[day, idx])
        if price <= 0: return
        max_sh = int(slot_cash[s] / (price * (1 + COMMISSION))) // LOT * LOT
        if max_sh <= 0: return
        slot_cash[s]    -= max_sh * price * (1 + COMMISSION)
        slot_idx[s]      = idx
        slot_shares[s]   = max_sh
        slot_cost[s]     = price
        slot_buy_day[s]  = day

    start_day = max(trend_window, mkt_ma if mkt_ma > 0 else 0)

    for day in range(start_day, n_days + 1):
        sc_today = sc_mat[day]
        pt       = arr[day]
        ma20     = ma20_mat[day]
        stop_ln  = stop_mat[day]

        if mkt_ma_mat is not None:
            above_mkt = float((pt > mkt_ma_mat[day]).mean())
            market_is_bull = (above_mkt >= mkt_pct_stocks)
        else:
            market_is_bull = True

        # 有效候选: 趋势得分>0 且 价格>MA20
        valid = (sc_today > 0) & (pt > ma20)
        valid_scores = np.where(valid, sc_today, 0.0)

        # 当前持仓集合
        held_set = set(slot_idx[s] for s in range(n_positions) if slot_idx[s] is not None)

        # ── 止损检查 ──────────────────────────────────────────────────
        for s in range(n_positions):
            idx = slot_idx[s]
            if idx is None: continue
            if (day - slot_buy_day[s]) < 1: continue
            if float(pt[idx]) < float(stop_ln[idx]) * (1 - ma_stop_pct):
                sell_slot(s, day, 'ma_stop')

        # ── 换仓: 找未持仓中得分最高的 top-N ─────────────────────────
        # 对已持仓的换仓: 若场外最强股得分 > 持仓最弱股得分 × switch_ratio
        for s in range(n_positions):
            idx = slot_idx[s]
            if idx is None: continue
            if (day - slot_buy_day[s]) < min_hold: continue

            curr_score = float(sc_today[idx])
            # 排除当前所有持仓，找最强候选
            excl = set(slot_idx[ss] for ss in range(n_positions) if slot_idx[ss] is not None)
            excl_scores = valid_scores.copy()
            for ei in excl:
                excl_scores[ei] = 0.0
            best_outside = int(np.argmax(excl_scores))
            best_out_sc  = float(excl_scores[best_outside])

            if best_out_sc > curr_score * switch_ratio and market_is_bull:
                sell_slot(s, day, 'switch')

        # ── 建仓: 填满空闲仓位 ────────────────────────────────────────
        if market_is_bull:
            for s in range(n_positions):
                if slot_idx[s] is not None: continue
                # 不选已被其他槽持有的
                excl = set(slot_idx[ss] for ss in range(n_positions) if slot_idx[ss] is not None)
                avail = valid_scores.copy()
                for ei in excl:
                    avail[ei] = 0.0
                best = int(np.argmax(avail))
                if float(avail[best]) > 0:
                    buy_slot(s, best, day)

        # ── 权益 ─────────────────────────────────────────────────────
        equity = sum(slot_cash[s] for s in range(n_positions))
        for s in range(n_positions):
            if slot_idx[s] is not None:
                equity += slot_shares[s] * float(pt[slot_idx[s]])
        equity_curve.append(equity)
        monthly_equity[day // 21] = equity

    for s in range(n_positions):
        if slot_idx[s] is not None:
            sell_slot(s, n_days, 'end')

    return {'equity_curve': equity_curve, 'trades': trades,
            'monthly_equity': monthly_equity, 'final_equity': equity_curve[-1]}
