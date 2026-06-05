"""
动量策略回测引擎 V2 — 向量化加速版
"""
import math
import numpy as np
from typing import Dict, List, Optional


COMMISSION = 0.0003   # 单边佣金
STAMP_DUTY = 0.001    # 卖出印花税
LOT = 100             # 最小100股


def build_arrays(prices: Dict[str, List[float]]) -> tuple:
    """将价格字典转成 numpy 矩阵 (n_days+1, n_stocks)"""
    codes = sorted(prices.keys())
    arr = np.array([prices[c] for c in codes], dtype=np.float64).T  # (days, stocks)
    return codes, arr


def score_matrix(price_arr: np.ndarray, window: int, min_r2: float, min_slope: float) -> np.ndarray:
    """
    向量化计算所有股票每天的 slope×R² 趋势得分
    返回 (n_days, n_stocks) 得分矩阵
    """
    n_days, n_stocks = price_arr.shape
    scores = np.zeros((n_days, n_stocks))

    x = np.arange(window, dtype=np.float64)
    x -= x.mean()
    sxx = np.dot(x, x)

    for d in range(window - 1, n_days):
        seg = price_arr[d - window + 1: d + 1, :]   # (window, n_stocks)
        y_mean = seg.mean(axis=0)
        y_centered = seg - y_mean
        sxy = (x[:, None] * y_centered).sum(axis=0)
        syy = (y_centered ** 2).sum(axis=0)
        # slope (raw, price unit)
        slope = sxy / sxx
        # r²
        with np.errstate(invalid='ignore', divide='ignore'):
            r2 = np.where(syy > 0, sxy ** 2 / (sxx * syy), 0.0)
        r2 = np.clip(r2, 0, 1)
        # slope as %/day of mean price
        slope_pct = np.where(y_mean > 0, slope / y_mean, 0.0)
        # filter
        valid = (r2 >= min_r2) & (slope_pct >= min_slope)
        scores[d] = np.where(valid, slope_pct * r2, 0.0)

    return scores


def run_backtest(
    prices: Dict[str, List[float]],
    trend_window: int = 15,
    ma_stop: int = 5,
    ma_stop_pct: float = 0.0,
    switch_ratio: float = 1.5,
    min_r2: float = 0.3,
    min_slope: float = 0.001,
    initial_capital: float = 1_000_000,
) -> Dict:
    codes, arr = build_arrays(prices)
    n_days, n_stocks = arr.shape
    n_days -= 1  # 第0行是初始价

    # 计算得分矩阵 (n_days+1, n_stocks)
    sc_mat = score_matrix(arr, trend_window, min_r2, min_slope)

    # 计算移动平均 (n_days+1, n_stocks)
    ma_arr = np.zeros_like(arr)
    for d in range(n_days + 1):
        start = max(0, d - ma_stop + 1)
        ma_arr[d] = arr[start:d + 1].mean(axis=0)

    equity = initial_capital
    cash = initial_capital
    pos_idx: Optional[int] = None
    pos_shares: int = 0
    pos_cost: float = 0.0
    buy_day: int = -2

    equity_curve = [equity]
    trades = []
    monthly_equity = {}

    def do_sell(idx, day, reason):
        nonlocal cash, pos_idx, pos_shares, pos_cost
        price = arr[day, idx]
        proceeds = pos_shares * price * (1 - COMMISSION - STAMP_DUTY)
        pnl = proceeds - pos_shares * pos_cost * (1 + COMMISSION)
        trades.append({
            'code': codes[idx], 'buy_day': buy_day, 'sell_day': day,
            'buy_price': pos_cost, 'sell_price': price,
            'shares': pos_shares, 'pnl': pnl,
            'pnl_pct': (price / pos_cost - 1) * 100,
            'hold': day - buy_day, 'reason': reason,
            'win': 1 if pnl > 0 else 0
        })
        cash += proceeds
        pos_idx = None
        pos_shares = 0

    def do_buy(idx, day):
        nonlocal cash, pos_idx, pos_shares, pos_cost, buy_day
        price = arr[day, idx]
        if price <= 0:
            return
        max_sh = int(cash / (price * (1 + COMMISSION))) // LOT * LOT
        if max_sh <= 0:
            return
        cash -= max_sh * price * (1 + COMMISSION)
        pos_idx = idx
        pos_shares = max_sh
        pos_cost = price
        buy_day = day

    for day in range(trend_window, n_days + 1):
        sc_today = sc_mat[day]  # (n_stocks,)
        best_idx = int(np.argmax(sc_today))
        best_score = sc_today[best_idx]

        # 止损 (T+1)
        need_stop = False
        if pos_idx is not None and day > buy_day:
            close = arr[day, pos_idx]
            ma = ma_arr[day, pos_idx]
            if close < ma * (1 - ma_stop_pct):
                need_stop = True

        if need_stop:
            do_sell(pos_idx, day, 'ma_stop')

        # 切仓
        if (not need_stop and pos_idx is not None
                and day > buy_day
                and best_score > 0
                and best_idx != pos_idx):
            curr_score = sc_today[pos_idx]
            if best_score > curr_score * switch_ratio:
                do_sell(pos_idx, day, 'switch')

        # 买入
        if pos_idx is None and best_score > 0:
            do_buy(best_idx, day)

        # 权益
        if pos_idx is not None:
            port = cash + pos_shares * arr[day, pos_idx]
        else:
            port = cash
        equity = port
        equity_curve.append(equity)

        month_key = day // 21
        monthly_equity[month_key] = equity

    # 平仓
    if pos_idx is not None:
        do_sell(pos_idx, n_days, 'end')

    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'monthly_equity': monthly_equity,
        'final_equity': equity,
    }


def compute_stats(result: Dict, initial: float = 1_000_000) -> Dict:
    curve = result['equity_curve']
    trades = result['trades']
    meq = result['monthly_equity']
    n_months = len(meq)
    if n_months < 3:
        return {}

    final = result['final_equity']
    total_ret = (final / initial - 1) * 100
    ann_ret = ((final / initial) ** (12 / max(n_months, 1)) - 1) * 100

    eq_vals = [meq[k] for k in sorted(meq.keys())]
    monthly_rets = [(eq_vals[i] - eq_vals[i-1]) / eq_vals[i-1] * 100
                    for i in range(1, len(eq_vals))]
    monthly_rets.insert(0, (eq_vals[0] - initial) / initial * 100)

    arr = np.array(monthly_rets)
    mn = float(arr.mean())
    std = float(arr.std())
    sharpe_ann = (mn / std * math.sqrt(12)) if std > 0 else 0.0

    # 最大回撤
    curve_a = np.array(curve)
    peak = np.maximum.accumulate(curve_a)
    dd = (peak - curve_a) / peak * 100
    max_dd = float(dd.max())

    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0.0
    avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0.0
    pf = (sum(t['pnl'] for t in wins) /
          abs(sum(t['pnl'] for t in losses) + 1e-9))
    avg_hold = np.mean([t['hold'] for t in trades]) if trades else 0.0

    return {
        'final_equity': final,
        'total_ret': total_ret,
        'ann_ret': ann_ret,
        'max_dd': max_dd,
        'sharpe_ann': sharpe_ann,
        'monthly_mean': mn,
        'monthly_std': std,
        'monthly_median': float(np.median(arr)),
        'pos_months': int((arr > 0).sum()),
        'gt5_months': int((arr > 5).sum()),
        'gt10_months': int((arr > 10).sum()),
        'n_months': n_months,
        'n_trades': len(trades),
        'win_rate': win_rate,
        'avg_win': float(avg_win),
        'avg_loss': float(avg_loss),
        'profit_factor': float(pf),
        'avg_hold': float(avg_hold),
    }
