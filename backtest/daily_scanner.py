"""
龙头轮动每日扫描器 — 生产版
用法: python backtest/daily_scanner.py
输出: 明日操作信号 (买入/持有/止损/换仓)

依赖: backtest/data/ 目录有 Tushare 下载的数据
      如无数据, 先运行: python backtest/data_fetcher.py
"""
import sys, os, math
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── 策略参数 V5 最优 ──────────────────────────────────────────────────────
TREND_WINDOW    = 20      # 趋势计算窗口
MIN_R2          = 0.3     # 最低趋势拟合度 (V5优化: 0.3 比 0.4 更好)
MIN_SLOPE       = 0.0002  # 最低斜率 0.02%/天
MA_FILTER       = 20      # 价格需在MA20上方
MA_STOP         = 20      # 止损均线
MA_STOP_PCT     = 0.10    # 跌破止损线10%触发 (V5优化: 更宽止损减少噪音)
SWITCH_RATIO    = 2.5     # 换仓倍数
MIN_HOLD        = 3       # 最短持仓天数
N_POSITIONS     = 1       # 单仓集中持有 (V5优化: 集中胜过分散)
MIN_VOLUME      = 5e6     # 日均成交金额最低5000万

# 动量广度过滤 (V5新增): 股票池中满足趋势条件的比例
# 低于此阈值时停止建仓 (市场转弱信号)
BREADTH_MIN     = 0.10    # 10%的股票有有效趋势才可建仓

TUSHARE_TOKEN = os.environ.get(
    'TUSHARE_TOKEN',
    'b35d868fade2d6267cd045eff84ffa1f6991bdce88bff0d57a006f54'
)
DATA_DIR   = Path(__file__).parent / 'data'
DAILY_FILE = DATA_DIR / 'daily_all.parquet'

STATE_FILE = Path(__file__).parent / 'scanner_state.json'  # 持仓状态存储


def load_state():
    import json
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {'positions': [], 'last_scan': None}


def save_state(state):
    import json
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def linreg(y):
    """返回 (slope_pct/day, r2, mean_price)"""
    n = len(y)
    x = np.arange(n, dtype=float)
    x -= x.mean()
    y = np.array(y, dtype=float)
    sxx = float(np.dot(x, x))
    y_mean = y.mean()
    y_c = y - y_mean
    sxy = float(np.dot(x, y_c))
    syy = float(np.dot(y_c, y_c))
    slope = sxy / sxx if sxx > 0 else 0.0
    r2 = (sxy**2 / (sxx * syy)) if (sxx > 0 and syy > 0) else 0.0
    slope_pct = slope / y_mean if y_mean > 0 else 0.0
    return slope_pct, min(r2, 1.0), y_mean


def moving_avg(arr, window):
    if len(arr) < window:
        return np.mean(arr)
    return np.mean(arr[-window:])


def scan_today(df_today, lookback_df):
    """
    扫描全市场, 返回候选股列表 (按得分排序)
    df_today:    今日行情 DataFrame
    lookback_df: 过去 TREND_WINDOW + MA_STOP 天的行情数据
    """
    from pandas import DataFrame

    results = []
    codes = df_today['ts_code'].unique()

    for code in codes:
        hist = lookback_df[lookback_df['ts_code'] == code].sort_values('trade_date')
        if len(hist) < max(TREND_WINDOW, MA_STOP, MA_FILTER) + 5:
            continue

        closes = hist['close'].values
        volumes = hist['amount'].values  # 成交金额

        # 成交量过滤: 日均成交金额 > 5000万
        avg_amt = volumes[-20:].mean() if len(volumes) >= 20 else volumes.mean()
        if avg_amt < MIN_VOLUME:
            continue

        # 今日数据
        today_row = df_today[df_today['ts_code'] == code]
        if len(today_row) == 0:
            continue
        close_today = float(today_row['close'].iloc[0])
        name        = str(today_row.get('name', [code]).iloc[0]) if 'name' in today_row.columns else code

        # MA 过滤: 收盘 > MA20
        ma20_val = moving_avg(closes, MA_FILTER)
        if close_today < ma20_val:
            continue

        # 止损检查
        ma_stop_val = moving_avg(closes, MA_STOP)
        stop_line   = ma_stop_val * (1 - MA_STOP_PCT)

        # 趋势得分
        if len(closes) < TREND_WINDOW:
            continue
        slope_pct, r2, _ = linreg(closes[-TREND_WINDOW:])
        if r2 < MIN_R2 or slope_pct < MIN_SLOPE:
            continue

        score = slope_pct * r2

        results.append({
            'ts_code':    code,
            'name':       name,
            'close':      close_today,
            'score':      score,
            'slope_pct':  slope_pct * 100,  # 转为%
            'r2':         r2,
            'ma20':       ma20_val,
            'stop_line':  stop_line,
            'ma_stop':    ma_stop_val,
            'avg_amt_w':  avg_amt / 1e6,  # 亿元
        })

    results.sort(key=lambda x: -x['score'])
    return results


def get_tushare_today():
    """实时拉取今日行情 (运行时用)"""
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        pro = ts.pro_api()
        today = datetime.now().strftime('%Y%m%d')
        df = pro.daily(trade_date=today,
                       fields='ts_code,close,vol,amount,pct_chg')
        return df
    except Exception as e:
        print(f"  ⚠ 实时数据获取失败: {e}")
        return None


def load_from_cache(n_days_back=60):
    """从本地缓存加载数据"""
    if not DAILY_FILE.exists():
        return None, None
    import pandas as pd
    df = pd.read_parquet(DAILY_FILE)
    df = df.sort_values(['ts_code', 'trade_date'])
    cutoff = df['trade_date'].max() - pd.Timedelta(days=n_days_back)
    return df[df['trade_date'] >= cutoff], df['trade_date'].max()


def generate_signal(candidates, state, market_ok=True):
    """
    根据候选股列表和当前持仓状态, 生成明日操作信号
    market_ok: 市场广度是否充足 (False时收紧止损, 不建新仓)
    返回 signals: list of {'action', 'ts_code', 'name', 'reason'}
    """
    signals = []
    current_positions = {p['ts_code']: p for p in state.get('positions', [])}

    # 熊市时收紧止损
    eff_stop_pct = MA_STOP_PCT * 1.5 if not market_ok else MA_STOP_PCT

    # 1. 检查现有持仓是否需要止损
    for code, pos in current_positions.items():
        candidate = next((c for c in candidates if c['ts_code'] == code), None)
        if candidate is None:
            # 今天没有数据 (停牌?) → 继续持有
            continue
        eff_stop_line = candidate['ma_stop'] * (1 - eff_stop_pct)
        if candidate['close'] < eff_stop_line:
            signals.append({
                'action': '🔴 止损卖出',
                'ts_code': code,
                'name':    candidate['name'],
                'close':   candidate['close'],
                'stop_line': eff_stop_line,
                'reason':  f"收盘 {candidate['close']:.2f} < 止损线 {eff_stop_line:.2f} "
                           f"(MA{MA_STOP}×{1-eff_stop_pct:.2f}{'熊市紧止' if not market_ok else ''})",
                'score':   candidate['score'],
            })

    # 止损后的剩余持仓
    stop_codes = {s['ts_code'] for s in signals}
    remaining  = {c: p for c, p in current_positions.items() if c not in stop_codes}

    # 2. 检查换仓: 场外最强股得分 > 当前最弱持仓得分 × SWITCH_RATIO
    held_scores = {}
    for code in remaining:
        c = next((x for x in candidates if x['ts_code'] == code), None)
        held_scores[code] = c['score'] if c else 0.0

    if held_scores:
        weakest_code  = min(held_scores, key=lambda c: held_scores[c])
        weakest_score = held_scores[weakest_code]

        # 找不在持仓中且得分最高的
        outside_cands = [c for c in candidates if c['ts_code'] not in remaining and c['ts_code'] not in stop_codes]
        if outside_cands:
            best_outside = outside_cands[0]
            if best_outside['score'] > weakest_score * SWITCH_RATIO:
                # 检查最短持仓天数
                pos_info = current_positions.get(weakest_code, {})
                hold_days = pos_info.get('hold_days', MIN_HOLD + 1)
                if hold_days >= MIN_HOLD:
                    weakest_cand = next((c for c in candidates if c['ts_code'] == weakest_code), None)
                    signals.append({
                        'action': '🔄 换仓',
                        'ts_code': weakest_code,
                        'name':    weakest_cand['name'] if weakest_cand else weakest_code,
                        'reason':  f"卖出 → 买入 {best_outside['name']}({best_outside['ts_code']}) "
                                   f"新股得分{best_outside['score']:.4f} > "
                                   f"当前×{SWITCH_RATIO}={weakest_score*SWITCH_RATIO:.4f}",
                        'score':   weakest_score,
                        'switch_to': best_outside,
                    })

    # 3. 空仓建仓 (仅在广度充足时)
    if not market_ok:
        return signals  # 弱势/熊市: 只止损, 不建新仓
    n_empty = N_POSITIONS - len(remaining) - len([s for s in signals if s['action'] == '🔄 换仓'])
    held_and_switching = set(remaining.keys()) | {s['ts_code'] for s in signals}
    buy_cands = [c for c in candidates if c['ts_code'] not in held_and_switching]
    for i in range(min(n_empty, len(buy_cands))):
        c = buy_cands[i]
        signals.append({
            'action':  '🟢 买入建仓',
            'ts_code': c['ts_code'],
            'name':    c['name'],
            'close':   c['close'],
            'score':   c['score'],
            'reason':  f"得分#{i+1}: slope={c['slope_pct']:.3f}%/天 R²={c['r2']:.2f}",
        })

    # 4. 持仓中没有信号的 → 继续持有
    acted = {s['ts_code'] for s in signals}
    for code, pos in remaining.items():
        if code not in acted:
            c = next((x for x in candidates if x['ts_code'] == code), None)
            signals.append({
                'action':  '⚪ 继续持有',
                'ts_code': code,
                'name':    c['name'] if c else code,
                'close':   c['close'] if c else pos.get('cost', 0),
                'score':   c['score'] if c else 0,
                'reason':  '趋势持续, 无换仓信号',
            })

    return signals


def print_report(candidates, signals, scan_date):
    print()
    print("=" * 72)
    print(f"  龙头轮动每日扫描报告  |  {scan_date}")
    print(f"  参数: W={TREND_WINDOW} R²≥{MIN_R2} 斜率≥{MIN_SLOPE*100:.3f}%  "
          f"止损MA{MA_STOP}×{1-MA_STOP_PCT}  换仓{SWITCH_RATIO}x")
    print("=" * 72)

    # 广度指标
    print(f"\n  📊 市场广度: {len(candidates)} 只通过趋势过滤  "
          f"({'✅ 广度充足，可操作' if len(candidates) >= BREADTH_MIN * 100 else '⚠️ 广度不足，谨慎建仓'})")
    print(f"     候选TOP 10 (得分排序):")
    print(f"  {'#':>3} {'代码':>12} {'名称':>8} {'收盘':>7} {'斜率/天':>8} {'R²':>5} "
          f"{'得分':>7} {'日均亿':>6}")
    print("  " + "-" * 64)
    for i, c in enumerate(candidates[:10]):
        held_mark = ' ←持仓' if any(s['ts_code'] == c['ts_code'] for s in signals
                                    if '持有' in s['action'] or '换仓' in s['action']) else ''
        print(f"  {i+1:>3} {c['ts_code']:>12} {c['name']:>8} {c['close']:>7.2f} "
              f"{c['slope_pct']:>7.3f}% {c['r2']:>5.2f} {c['score']:>7.4f} "
              f"{c['avg_amt_w']:>6.1f}{held_mark}")

    print(f"\n  📋 明日操作信号 (单仓集中策略):")
    print("  " + "-" * 64)
    for s in signals:
        print(f"  {s['action']}  {s.get('ts_code',''):>12} {s.get('name',''):>8}  "
              f"{s.get('reason','')}")

    if not any('买入' in s['action'] or '换仓' in s['action'] for s in signals):
        if not signals:
            print("  ⚠ 当前无满足条件的股票，建议空仓等待")

    print()
    print("  ⚠ 注意:")
    print("    · 以上信号基于今日收盘数据，明日开盘执行 (A股T+1)")
    print("    · 请在开盘集合竞价前确认信号仍然有效")
    print("    · 单仓策略: 全仓持有得分最高股")
    print(f"    · 广度低于{BREADTH_MIN*100:.0f}%时停止建仓，等待市场企稳")
    print("=" * 72)


def main():
    print("  龙头轮动每日扫描器 启动...")

    # 加载数据
    df, last_date = load_from_cache(n_days_back=80)
    if df is None:
        print()
        print("  ❌ 未找到本地数据，请先运行:")
        print("     python backtest/data_fetcher.py")
        print()
        print("  或在本机设置环境变量后运行:")
        print(f"     TUSHARE_TOKEN={TUSHARE_TOKEN}")
        return

    import pandas as pd
    scan_date = last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else str(last_date)

    # 今日行情 (最新一天)
    today_df  = df[df['trade_date'] == last_date].copy()
    # 过去N天历史
    lookback  = df.copy()

    print(f"  数据日期: {scan_date}  股票数: {today_df['ts_code'].nunique()}")

    # 扫描
    candidates = scan_today(today_df, lookback)
    total_stocks = today_df['ts_code'].nunique()
    breadth = len(candidates) / max(total_stocks, 1)
    market_ok = breadth >= BREADTH_MIN
    print(f"  通过过滤: {len(candidates)} 只 / {total_stocks} 只  广度={breadth:.1%}  "
          f"{'✅牛市' if market_ok else '⚠️弱势/熊市'}")

    # 读取持仓状态
    state = load_state()

    # 生成信号
    signals = generate_signal(candidates, state, market_ok=market_ok)

    # 打印报告
    print_report(candidates, signals, scan_date)


if __name__ == '__main__':
    main()
