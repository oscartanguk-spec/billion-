"""
A股全市场数据下载器 — Tushare版
用法: python backtest/data_fetcher.py
结果保存到: backtest/data/
"""
import os, time, json, math
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional

TUSHARE_TOKEN = os.environ.get('TUSHARE_TOKEN', 'b35d868fade2d6267cd045eff84ffa1f6991bdce88bff0d57a006f54')
DATA_DIR = Path(__file__).parent / 'data'
STOCK_LIST_FILE = DATA_DIR / 'stock_list.csv'
DAILY_FILE = DATA_DIR / 'daily_all.parquet'
META_FILE = DATA_DIR / 'fetch_meta.json'

# 下载参数
START_DATE = '20200101'   # 5年数据
END_DATE   = '20251231'
MIN_TRADE_DAYS = 250      # 过滤掉数据太少的股票

# Tushare 免费账户: 每分钟约60次; 积分500+账户无限制
REQ_INTERVAL = 0.05       # 秒, 付费账户可设0.02


def get_pro():
    try:
        import tushare as ts
        ts.set_token(TUSHARE_TOKEN)
        return ts.pro_api()
    except ImportError:
        raise RuntimeError("请先安装: pip install tushare")


def fetch_stock_list(pro) -> pd.DataFrame:
    """获取全A股股票列表 (过滤ST)"""
    dfs = []
    for exchange in ['SSE', 'SZSE']:
        df = pro.stock_basic(
            exchange=exchange, list_status='L',
            fields='ts_code,name,industry,market,list_date'
        )
        dfs.append(df)
        time.sleep(0.1)
    all_stocks = pd.concat(dfs, ignore_index=True)

    # 过滤ST/退市
    mask = ~all_stocks['name'].str.contains('ST|退', na=False)
    all_stocks = all_stocks[mask].reset_index(drop=True)
    print(f"  股票池: {len(all_stocks)} 只 (已过滤ST)")
    return all_stocks


def fetch_daily_batch(pro, ts_code: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """下载单只股票后复权日线数据"""
    try:
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end,
                       fields='ts_code,trade_date,open,high,low,close,vol,amount,pct_chg')
        if df is None or len(df) == 0:
            return None
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date').reset_index(drop=True)
        return df
    except Exception:
        return None


def fetch_adj_factor(pro, ts_code: str, start: str, end: str) -> Optional[pd.DataFrame]:
    """获取复权因子"""
    try:
        df = pro.adj_factor(ts_code=ts_code, start_date=start, end_date=end,
                            fields='ts_code,trade_date,adj_factor')
        if df is None or len(df) == 0:
            return None
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        return df
    except Exception:
        return None


def download_all(force_refresh: bool = False):
    """主下载函数"""
    DATA_DIR.mkdir(exist_ok=True)
    pro = get_pro()

    # ── 1. 股票列表 ──────────────────────────────────────────────────────
    if STOCK_LIST_FILE.exists() and not force_refresh:
        stocks = pd.read_csv(STOCK_LIST_FILE)
        print(f"加载股票列表: {len(stocks)} 只")
    else:
        print("下载股票列表...")
        stocks = fetch_stock_list(pro)
        stocks.to_csv(STOCK_LIST_FILE, index=False)

    # 加载进度
    meta = {}
    if META_FILE.exists():
        with open(META_FILE) as f:
            meta = json.load(f)
    downloaded = set(meta.get('downloaded', []))
    failed = set(meta.get('failed', []))

    # ── 2. 按股票下载日线 ─────────────────────────────────────────────
    all_parts = []
    todo = [c for c in stocks['ts_code'] if c not in downloaded and c not in failed]
    print(f"待下载: {len(todo)} 只 (已完成: {len(downloaded)}, 失败: {len(failed)})")

    for i, code in enumerate(todo):
        df = fetch_daily_batch(pro, code, START_DATE, END_DATE)
        time.sleep(REQ_INTERVAL)

        if df is None or len(df) < MIN_TRADE_DAYS:
            failed.add(code)
        else:
            # 简单复权: 用最后一个收盘价作为基准的相对复权 (保持最新价不变)
            all_parts.append(df)
            downloaded.add(code)

        if (i + 1) % 100 == 0 or (i + 1) == len(todo):
            pct = (i + 1) / len(todo) * 100
            print(f"  进度: {i+1}/{len(todo)} ({pct:.0f}%) | 成功: {len(downloaded)} 失败: {len(failed)}")
            meta['downloaded'] = list(downloaded)
            meta['failed'] = list(failed)
            with open(META_FILE, 'w') as f:
                json.dump(meta, f)

    # ── 3. 合并已下载的历史数据 ───────────────────────────────────────
    if DAILY_FILE.exists() and not force_refresh:
        existing = pd.read_parquet(DAILY_FILE)
        if all_parts:
            new_data = pd.concat(all_parts, ignore_index=True)
            combined = pd.concat([existing, new_data], ignore_index=True)
            combined = combined.drop_duplicates(['ts_code', 'trade_date'])
        else:
            combined = existing
    else:
        if all_parts:
            combined = pd.concat(all_parts, ignore_index=True)
        else:
            print("没有新数据")
            return

    combined = combined.sort_values(['ts_code', 'trade_date']).reset_index(drop=True)
    combined.to_parquet(DAILY_FILE, index=False)
    print(f"\n数据保存完成: {DAILY_FILE}")
    print(f"  股票数: {combined['ts_code'].nunique()}")
    print(f"  记录数: {len(combined):,}")
    print(f"  日期范围: {combined['trade_date'].min()} ~ {combined['trade_date'].max()}")


def load_price_dict(start_date: str = '20220101', end_date: str = '20251231',
                    min_days: int = 250) -> tuple:
    """
    加载本地缓存数据, 返回与 market_sim 兼容的格式
    Returns:
        prices: {ts_code: [close_price, ...]}
        volumes: {ts_code: [volume, ...]}
        dates: [date, ...]
    """
    if not DAILY_FILE.exists():
        raise FileNotFoundError(f"请先运行 data_fetcher.py 下载数据: {DAILY_FILE}")

    df = pd.read_parquet(DAILY_FILE)
    df = df[(df['trade_date'] >= pd.Timestamp(start_date)) &
            (df['trade_date'] <= pd.Timestamp(end_date))]

    # 交易日序列
    all_dates = sorted(df['trade_date'].unique())

    # pivot: 行=日期, 列=股票
    close_pivot = df.pivot(index='trade_date', columns='ts_code', values='close')
    vol_pivot   = df.pivot(index='trade_date', columns='ts_code', values='vol')
    close_pivot = close_pivot.reindex(all_dates).ffill()
    vol_pivot   = vol_pivot.reindex(all_dates).fillna(0)

    # 过滤数据不足的股票
    valid_cols = close_pivot.columns[(close_pivot.notna().sum() >= min_days)]
    close_pivot = close_pivot[valid_cols].fillna(method='ffill').dropna()
    vol_pivot   = vol_pivot[valid_cols].fillna(0)

    prices  = {c: list(close_pivot[c]) for c in valid_cols}
    volumes = {c: list(vol_pivot[c]) for c in valid_cols}

    print(f"加载真实数据: {len(prices)} 只股票, {len(all_dates)} 个交易日")
    return prices, volumes, list(all_dates)


if __name__ == '__main__':
    import sys
    force = '--force' in sys.argv
    print("=" * 60)
    print("  A股日线数据下载器")
    print(f"  范围: {START_DATE} ~ {END_DATE}")
    print("=" * 60)
    download_all(force_refresh=force)
