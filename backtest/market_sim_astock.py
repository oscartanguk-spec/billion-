"""
A股市场模拟器 V9 — 真实A股特征版
特点:
  - 龙头股 (2%): 年化 80-200%, 含连板效应
  - 强势股 (10%): 年化 30-80%
  - 普通股 (88%): 年化 -15%~+10%
  - 强板块轮动: 每轮持续 20-45天, 龙头每天额外+0.5-2%
  - 熊市/牛市周期: 随机切换
"""
import math
import numpy as np
from typing import Dict, Tuple


def generate_prices(
    n_stocks: int = 300,
    n_days: int = 1820,
    seed: int = 42,
) -> Tuple[Dict[str, list], Dict[str, list], np.ndarray]:

    rng_mkt    = np.random.RandomState(seed)
    rng_stocks = np.random.RandomState(seed + 1000)
    rng_boost  = np.random.RandomState(seed + 2000)
    rng_prices = np.random.RandomState(seed + 3000)
    rng_vol    = np.random.RandomState(seed + 4000)

    # ── 市场周期: 牛市/熊市交替 ──────────────────────────────────────────
    # 真实A股: 周期性强, 牛熊切换明显
    market_regime = np.zeros(n_days)   # +1牛市, -1熊市
    d = 0
    while d < n_days:
        if rng_mkt.random() < 0.55:   # 55%概率进入牛市
            bull_len = int(rng_mkt.uniform(120, 360))  # 牛市持续120-360天
            market_regime[d:d + bull_len] = 1.0
            d += bull_len
        else:
            bear_len = int(rng_mkt.uniform(60, 180))
            market_regime[d:d + bear_len] = -1.0
            d += bear_len

    # 基础市场收益
    sigma_mkt = 0.22 / math.sqrt(252)
    log_rets_mkt = rng_mkt.normal(0.0, sigma_mkt, n_days)
    # 牛市: 额外+0.06%/天; 熊市: 额外-0.05%/天
    regime_drift = market_regime * 0.0005
    mu_log_mkt   = (0.04 - 0.22**2 / 2) / 252
    log_rets_mkt = log_rets_mkt - log_rets_mkt.mean() + mu_log_mkt + regime_drift
    market_rets  = np.clip(np.exp(log_rets_mkt) - 1, -0.10, 0.10)

    # ── 股票分层 ──────────────────────────────────────────────────────────
    n_super  = max(3, int(n_stocks * 0.02))   # 2% 龙头
    n_strong = max(10, int(n_stocks * 0.10))  # 10% 强势股
    n_normal = n_stocks - n_super - n_strong

    # 龙头股: 年化 80-200% (连板效应)
    super_mu  = rng_stocks.uniform(0.80, 2.00, n_super)
    super_sig = rng_stocks.uniform(0.50, 0.80, n_super)

    # 强势股: 年化 30-80%
    stg_mu  = rng_stocks.uniform(0.30, 0.80, n_strong)
    stg_sig = rng_stocks.uniform(0.35, 0.55, n_strong)

    # 普通股: 年化 -15%~+10%
    norm_mu  = np.clip(rng_stocks.normal(-0.02, 0.08, n_normal), -0.20, 0.12)
    norm_sig = rng_stocks.uniform(0.20, 0.35, n_normal)

    def geo2log(mu_geo, sigma_ann):
        return (mu_geo - sigma_ann**2 / 2) / 252, sigma_ann / math.sqrt(252)

    all_idx    = rng_stocks.permutation(n_stocks)
    super_list = list(all_idx[:n_super])
    stg_list   = list(all_idx[n_super:n_super + n_strong])
    norm_list  = list(all_idx[n_super + n_strong:])
    betas      = np.clip(rng_stocks.lognormal(math.log(0.90), 0.30, n_stocks), 0.2, 2.0)

    mu_log  = np.zeros(n_stocks)
    sig_log = np.zeros(n_stocks)
    for j, i in enumerate(super_list):
        mu_log[i], sig_log[i] = geo2log(super_mu[j], super_sig[j])
    for j, i in enumerate(stg_list):
        mu_log[i], sig_log[i] = geo2log(stg_mu[j], stg_sig[j])
    for j, i in enumerate(norm_list):
        mu_log[i], sig_log[i] = geo2log(norm_mu[j], norm_sig[j])

    # ── 板块轮动: 更强的A股特色 ──────────────────────────────────────────
    boost_arr = np.zeros((n_days, n_stocks))
    d = 0
    while d < n_days:
        hot_len  = int(rng_boost.uniform(20, 45))
        cool_len = int(rng_boost.uniform(20, 50))

        # 牛市期间热点更强
        is_bull = (market_regime[min(d, n_days-1)] > 0)
        strength = 2.0 if is_bull else 0.8

        n_leaders = min(3, len(super_list))
        leaders = rng_boost.choice(super_list, n_leaders, replace=False)
        n_fols = min(6, len(stg_list))
        fols = rng_boost.choice(stg_list, n_fols, replace=False)

        for dd in range(hot_len):
            if d + dd >= n_days: break
            heat = math.sin((dd + 0.5) / hot_len * math.pi)
            # 龙头: 每天额外+0.5-2%
            for i in leaders:
                boost_arr[d+dd, i] += rng_boost.uniform(0.005, 0.020) * heat * strength
            # 跟风股: 每天额外+0.1-0.5%
            for i in fols:
                boost_arr[d+dd, i] += rng_boost.uniform(0.001, 0.005) * heat * strength
        d += hot_len + cool_len

    # ── 价格路径 ──────────────────────────────────────────────────────────
    init_prices  = np.clip(rng_prices.lognormal(math.log(10), 0.7, n_stocks), 2.0, 50.0)
    price_matrix = np.zeros((n_days + 1, n_stocks))
    price_matrix[0] = init_prices
    daily_rets_mat = np.zeros((n_days, n_stocks))

    for d in range(n_days):
        mkt_log = math.log(1 + market_rets[d])
        z = rng_prices.randn(n_stocks)
        extreme = rng_prices.random(n_stocks) < 0.05
        z = np.where(extreme, rng_prices.randn(n_stocks) * 2.5, z)
        log_r = mu_log + betas * mkt_log + boost_arr[d] + z * sig_log
        r = np.clip(np.exp(log_r) - 1, -0.10, 0.10)
        price_matrix[d + 1] = price_matrix[d] * (1 + r)
        daily_rets_mat[d] = r

    # ── 成交量 ────────────────────────────────────────────────────────────
    base_vol    = rng_vol.lognormal(10.0, 1.5, n_stocks)
    vol_matrix  = np.zeros((n_days, n_stocks))
    for d in range(n_days):
        r_abs = np.abs(daily_rets_mat[d])
        is_bull_d = market_regime[d] > 0
        vol_factor = 1.0 + 4.0 * r_abs + boost_arr[d] * 80.0
        if is_bull_d: vol_factor *= 1.5
        vol_matrix[d] = base_vol * vol_factor * rng_vol.lognormal(0, 0.35, n_stocks)
        vol_matrix[d] = np.maximum(vol_matrix[d], 100.0)

    codes   = [f"{i+1:06d}" for i in range(n_stocks)]
    prices  = {c: list(price_matrix[:, i]) for i, c in enumerate(codes)}
    volumes = {c: list(vol_matrix[:, i])   for i, c in enumerate(codes)}
    return prices, volumes, market_rets
