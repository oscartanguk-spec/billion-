"""
A股市场模拟器 V8 — 含成交量版
- 价格: GBM + 板块热点
- 成交量: 与价格变动相关 (涨时放量/跌时缩量 + 随机噪声)
"""
import math
import numpy as np
from typing import Dict, Tuple, Optional


def generate_prices(
    n_stocks: int = 300,
    n_days: int = 1820,
    seed: int = 42,
) -> Tuple[Dict[str, list], Dict[str, list], np.ndarray]:
    """
    Returns:
        prices:  {code: [price_day0, ..., price_dayN]}
        volumes: {code: [vol_day0, ..., vol_dayN]}
        market_rets: np.ndarray shape (n_days,)
    """
    rng_mkt    = np.random.RandomState(seed)
    rng_stocks = np.random.RandomState(seed + 1000)
    rng_boost  = np.random.RandomState(seed + 2000)
    rng_prices = np.random.RandomState(seed + 3000)
    rng_vol    = np.random.RandomState(seed + 4000)

    # ── 市场因子 ──────────────────────────────────────────────────────────
    sigma_mkt   = 0.22 / math.sqrt(252)
    mu_log_mkt  = (0.04 - 0.22**2 / 2) / 252
    log_rets_mkt = rng_mkt.normal(0.0, sigma_mkt, n_days)
    log_rets_mkt = log_rets_mkt - log_rets_mkt.mean() + mu_log_mkt
    market_rets  = np.clip(np.exp(log_rets_mkt) - 1, -0.10, 0.10)

    # ── 股票分层 ──────────────────────────────────────────────────────────
    n_super  = max(3, int(n_stocks * 0.02))
    n_strong = max(15, int(n_stocks * 0.15))
    n_normal = n_stocks - n_super - n_strong

    super_mu  = rng_stocks.uniform(0.18, 0.28, n_super)
    super_sig = rng_stocks.uniform(0.35, 0.50, n_super)
    stg_mu    = rng_stocks.uniform(0.08, 0.16, n_strong)
    stg_sig   = rng_stocks.uniform(0.25, 0.38, n_strong)
    norm_mu   = np.clip(rng_stocks.normal(-0.01, 0.07, n_normal), -0.15, 0.10)
    norm_sig  = rng_stocks.uniform(0.18, 0.32, n_normal)

    def geo2log(mu_geo, sigma_ann):
        return (mu_geo - sigma_ann**2 / 2) / 252, sigma_ann / math.sqrt(252)

    all_idx    = rng_stocks.permutation(n_stocks)
    super_list = list(all_idx[:n_super])
    stg_list   = list(all_idx[n_super:n_super + n_strong])
    betas      = np.clip(rng_stocks.lognormal(math.log(0.85), 0.25, n_stocks), 0.2, 1.8)

    mu_log  = np.zeros(n_stocks)
    sig_log = np.zeros(n_stocks)
    for j, i in enumerate(super_list):
        mu_log[i], sig_log[i] = geo2log(super_mu[j], super_sig[j])
    for j, i in enumerate(stg_list):
        mu_log[i], sig_log[i] = geo2log(stg_mu[j], stg_sig[j])
    normal_list = list(all_idx[n_super + n_strong:])
    for j, i in enumerate(normal_list):
        mu_log[i], sig_log[i] = geo2log(norm_mu[j], norm_sig[j])

    # ── 板块热点 ──────────────────────────────────────────────────────────
    boost_arr = np.zeros((n_days, n_stocks))
    d = 0
    while d < n_days:
        hot_len  = int(rng_boost.uniform(15, 35))
        cool_len = int(rng_boost.uniform(30, 70))
        leaders  = rng_boost.choice(super_list, min(3, len(super_list)), replace=False)
        fols     = rng_boost.choice(stg_list,   min(8, len(stg_list)),   replace=False)
        for dd in range(hot_len):
            if d + dd >= n_days: break
            heat = math.sin((dd + 0.5) / hot_len * math.pi)
            for i in leaders: boost_arr[d + dd, i] += rng_boost.uniform(0.001, 0.004) * heat
            for i in fols:    boost_arr[d + dd, i] += rng_boost.uniform(0.0003, 0.001) * heat
        d += hot_len + cool_len

    # ── 价格路径 ──────────────────────────────────────────────────────────
    init_prices  = np.clip(rng_prices.lognormal(math.log(10), 0.7, n_stocks), 2.0, 50.0)
    price_matrix = np.zeros((n_days + 1, n_stocks))
    price_matrix[0] = init_prices
    daily_rets   = np.zeros((n_days, n_stocks))

    for d in range(n_days):
        mkt_log = math.log(1 + market_rets[d])
        z       = rng_prices.randn(n_stocks)
        extreme = rng_prices.random(n_stocks) < 0.04
        z       = np.where(extreme, rng_prices.randn(n_stocks) * 2.0, z)
        log_r   = mu_log + betas * mkt_log + boost_arr[d] + z * sig_log
        r       = np.clip(np.exp(log_r) - 1, -0.10, 0.10)
        price_matrix[d + 1] = price_matrix[d] * (1 + r)
        daily_rets[d] = r

    # ── 成交量 (与收益相关) ───────────────────────────────────────────────
    # 基础成交量: 对数正态, 各股票量级不同
    base_vol = rng_vol.lognormal(10.0, 1.5, n_stocks)  # 万股为单位
    vol_matrix = np.zeros((n_days, n_stocks))

    for d in range(n_days):
        r_abs = np.abs(daily_rets[d])
        # 放量因子: 大涨大跌时成交量增加
        vol_factor = 1.0 + 3.0 * r_abs + rng_vol.exponential(0.3, n_stocks)
        # 趋势中的热点股额外放量
        vol_factor += boost_arr[d] * 50.0
        vol_matrix[d] = base_vol * vol_factor * rng_vol.lognormal(0, 0.3, n_stocks)
        vol_matrix[d] = np.maximum(vol_matrix[d], 100.0)

    codes   = [f"{i+1:06d}" for i in range(n_stocks)]
    prices  = {c: list(price_matrix[:, i]) for i, c in enumerate(codes)}
    volumes = {c: list(vol_matrix[:, i])   for i, c in enumerate(codes)}
    return prices, volumes, market_rets
