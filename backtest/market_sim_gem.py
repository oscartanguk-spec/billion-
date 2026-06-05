"""
创业板/科创板 专用模拟器 V2 — 校准版
校准标准:
  - TOP1% 7年倍数: 100-500x (对标真实A股妖股)
  - TOP5% 7年倍数: 20-80x
  - 中位股 7年倍数: 0.5-1.2x
  - 涨跌幅限制: ±20% (创业板/科创板)
"""
import math
import numpy as np
from typing import Dict, Tuple


def generate_prices(
    n_stocks: int = 300,
    n_days:   int = 1820,
    seed:     int = 42,
) -> Tuple[Dict[str, list], Dict[str, list], np.ndarray]:

    rng_mkt    = np.random.RandomState(seed)
    rng_stocks = np.random.RandomState(seed + 1000)
    rng_boost  = np.random.RandomState(seed + 2000)
    rng_prices = np.random.RandomState(seed + 3000)
    rng_vol    = np.random.RandomState(seed + 4000)

    # ── 牛/熊/震荡三态 ────────────────────────────────────────────────────
    regime = np.zeros(n_days)
    d = 0
    while d < n_days:
        r = rng_mkt.random()
        if r < 0.40:
            length = int(rng_mkt.uniform(80, 250))
            regime[d:d+length] = 1.0      # 牛市
        elif r < 0.70:
            length = int(rng_mkt.uniform(60, 160))
            regime[d:d+length] = -1.0     # 熊市
        else:
            length = int(rng_mkt.uniform(30, 80))
            regime[d:d+length] = 0.0      # 震荡
        d += length

    # 市场指数 (创业板指: 年化约8%, 波动30%)
    sigma_mkt    = 0.30 / math.sqrt(252)
    mu_log_base  = (0.08 - 0.30**2/2) / 252
    log_rets_mkt = rng_mkt.normal(0.0, sigma_mkt, n_days)
    drift        = regime * 0.0010    # 牛+0.1%/天, 熊-0.1%/天
    log_rets_mkt = log_rets_mkt - log_rets_mkt.mean() + mu_log_base + drift
    market_rets  = np.clip(np.exp(log_rets_mkt) - 1, -0.20, 0.20)

    # ── 股票分层 (校准版) ─────────────────────────────────────────────────
    n_yao    = max(3,  int(n_stocks * 0.02))   # 妖股2%: 60-100%/年
    n_super  = max(8,  int(n_stocks * 0.08))   # 龙头8%: 35-65%/年
    n_strong = max(20, int(n_stocks * 0.15))   # 强势15%: 15-35%/年
    n_normal = n_stocks - n_yao - n_super - n_strong

    yao_mu    = rng_stocks.uniform(0.60, 1.00, n_yao)    # 60-100%/年
    yao_sig   = rng_stocks.uniform(0.55, 0.80, n_yao)
    super_mu  = rng_stocks.uniform(0.35, 0.65, n_super)  # 35-65%/年
    super_sig = rng_stocks.uniform(0.42, 0.62, n_super)
    stg_mu    = rng_stocks.uniform(0.15, 0.35, n_strong) # 15-35%/年
    stg_sig   = rng_stocks.uniform(0.32, 0.50, n_strong)
    norm_mu   = np.clip(rng_stocks.normal(-0.05, 0.10, n_normal), -0.25, 0.12)
    norm_sig  = rng_stocks.uniform(0.25, 0.45, n_normal)

    def geo2log(mu_geo, sigma_ann):
        return (mu_geo - sigma_ann**2/2) / 252, sigma_ann / math.sqrt(252)

    all_idx    = rng_stocks.permutation(n_stocks)
    yao_list   = list(all_idx[:n_yao])
    super_list = list(all_idx[n_yao:n_yao+n_super])
    stg_list   = list(all_idx[n_yao+n_super:n_yao+n_super+n_strong])
    norm_list  = list(all_idx[n_yao+n_super+n_strong:])
    betas      = np.clip(rng_stocks.lognormal(math.log(1.05), 0.30, n_stocks), 0.3, 2.2)

    mu_log  = np.zeros(n_stocks)
    sig_log = np.zeros(n_stocks)
    for j, i in enumerate(yao_list):
        mu_log[i], sig_log[i] = geo2log(yao_mu[j],   yao_sig[j])
    for j, i in enumerate(super_list):
        mu_log[i], sig_log[i] = geo2log(super_mu[j],  super_sig[j])
    for j, i in enumerate(stg_list):
        mu_log[i], sig_log[i] = geo2log(stg_mu[j],    stg_sig[j])
    for j, i in enumerate(norm_list):
        mu_log[i], sig_log[i] = geo2log(norm_mu[j],   norm_sig[j])

    # ── 板块题材轮动 (校准版: 0.3-1.5%/天) ───────────────────────────────
    boost_arr = np.zeros((n_days, n_stocks))
    d = 0
    while d < n_days:
        is_bull = (regime[min(d, n_days-1)] > 0)
        is_bear = (regime[min(d, n_days-1)] < 0)
        if is_bear:
            d += int(rng_boost.uniform(20, 60))
            continue

        hot_len  = int(rng_boost.uniform(15, 30))
        cool_len = int(rng_boost.uniform(20, 45))
        strength = 1.8 if is_bull else 0.9

        leaders = rng_boost.choice(yao_list,   min(2, len(yao_list)),  replace=False)
        fols    = rng_boost.choice(super_list, min(5, len(super_list)), replace=False)
        stg_fols = rng_boost.choice(stg_list, min(8, len(stg_list)),   replace=False)

        for dd in range(hot_len):
            if d + dd >= n_days: break
            heat = math.sin((dd + 0.5) / hot_len * math.pi)
            # 妖股龙头: +0.5-1.5%/天 (校准后, 原来是4%)
            for i in leaders:
                boost_arr[d+dd, i] += rng_boost.uniform(0.005, 0.015) * heat * strength
            # 龙头股: +0.2-0.8%/天
            for i in fols:
                boost_arr[d+dd, i] += rng_boost.uniform(0.002, 0.008) * heat * strength
            # 强势股跟风: +0.05-0.3%/天
            for i in stg_fols:
                boost_arr[d+dd, i] += rng_boost.uniform(0.0005, 0.003) * heat * strength
        d += hot_len + cool_len

    # ── 价格路径 (±20%限制) ───────────────────────────────────────────────
    init_prices  = np.clip(rng_prices.lognormal(math.log(15), 0.8, n_stocks), 3.0, 120.0)
    price_matrix = np.zeros((n_days+1, n_stocks))
    price_matrix[0] = init_prices
    daily_rets_mat = np.zeros((n_days, n_stocks))

    for d in range(n_days):
        mkt_log = math.log(1 + market_rets[d])
        z = rng_prices.randn(n_stocks)
        extreme = rng_prices.random(n_stocks) < 0.06
        z = np.where(extreme, rng_prices.randn(n_stocks) * 2.8, z)
        log_r = mu_log + betas * mkt_log + boost_arr[d] + z * sig_log
        r = np.clip(np.exp(log_r) - 1, -0.20, 0.20)
        price_matrix[d+1] = price_matrix[d] * (1 + r)
        daily_rets_mat[d] = r

    # ── 成交量 ────────────────────────────────────────────────────────────
    base_vol   = rng_vol.lognormal(9.5, 1.5, n_stocks)
    vol_matrix = np.zeros((n_days, n_stocks))
    for d in range(n_days):
        r_abs  = np.abs(daily_rets_mat[d])
        is_bull_d = regime[d] > 0
        vf = 1.0 + 5.0 * r_abs + boost_arr[d] * 50.0
        if is_bull_d: vf *= 1.6
        vol_matrix[d] = base_vol * vf * rng_vol.lognormal(0, 0.4, n_stocks)
        vol_matrix[d] = np.maximum(vol_matrix[d], 100.0)

    codes   = [f"{i+1:06d}" for i in range(n_stocks)]
    prices  = {c: list(price_matrix[:, i]) for i, c in enumerate(codes)}
    volumes = {c: list(vol_matrix[:, i])   for i, c in enumerate(codes)}
    return prices, volumes, market_rets
