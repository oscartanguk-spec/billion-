"""
A股市场模拟器 V7 — 精确版

用分离随机种子确保参数可控:
  - 市场年化 4-5%, 波动 22%
  - 超强股(2%): 年化 18-28%, 7年约 3-7x
  - 强势股(15%): 年化 8-16%, 7年约 1.5-3x
  - 普通股(83%): 年化 -8%~+5%, 7年约 0.5-1.5x
  - 板块热点: 额外短期提振
"""
import math
import numpy as np
from typing import Dict, Tuple


def generate_prices(
    n_stocks: int = 300,
    n_days: int = 1820,
    seed: int = 42,
) -> Tuple[Dict[str, list], np.ndarray]:

    # 分离的 RNG, 各自独立
    rng_mkt    = np.random.RandomState(seed)
    rng_stocks = np.random.RandomState(seed + 1000)
    rng_boost  = np.random.RandomState(seed + 2000)
    rng_prices = np.random.RandomState(seed + 3000)

    # ── 市场因子: 年化4%, 波动22% ─────────────────────────────────────────
    # 使用对数收益以保证正确的几何均值
    # μ_geo = 0.04, σ = 0.22
    # log-return: r_log = N(μ_log, σ_log)
    # 其中 μ_log = μ_geo - σ²/2 = 0.04 - 0.0242 = 0.0158
    # 转回算术: exp(r_log) - 1
    sigma_mkt = 0.22 / math.sqrt(252)
    mu_log_mkt = (0.04 - 0.22**2 / 2) / 252

    log_rets_mkt = rng_mkt.normal(0.0, sigma_mkt, n_days)
    # 强制归一化到目标均值, 消除随机种子偏差
    log_rets_mkt = log_rets_mkt - log_rets_mkt.mean() + mu_log_mkt
    market_rets = np.exp(log_rets_mkt) - 1
    market_rets = np.clip(market_rets, -0.10, 0.10)

    # ── 股票分层 ─────────────────────────────────────────────────────────
    n_super = max(3, int(n_stocks * 0.02))
    n_strong = max(15, int(n_stocks * 0.15))
    n_normal = n_stocks - n_super - n_strong

    # 超强股: 年化 18-28% → 7年约 3.1-6.2x
    super_mu_geo = rng_stocks.uniform(0.18, 0.28, n_super)
    super_sig = rng_stocks.uniform(0.35, 0.50, n_super)

    # 强势股: 年化 8-16%
    strong_mu_geo = rng_stocks.uniform(0.08, 0.16, n_strong)
    strong_sig = rng_stocks.uniform(0.25, 0.38, n_strong)

    # 普通股: 年化 -8%~+5%
    normal_mu_geo = rng_stocks.normal(-0.01, 0.07, n_normal)
    normal_mu_geo = np.clip(normal_mu_geo, -0.15, 0.10)
    normal_sig = rng_stocks.uniform(0.18, 0.32, n_normal)

    # 转换为日对数收益参数
    def geo_to_log(mu_geo, sigma_ann):
        mu_log = (mu_geo - sigma_ann**2 / 2) / 252
        sig_log = sigma_ann / math.sqrt(252)
        return mu_log, sig_log

    # 组合参数
    all_idx = rng_stocks.permutation(n_stocks)
    super_list = list(all_idx[:n_super])
    strong_list = list(all_idx[n_super:n_super + n_strong])
    normal_list = list(all_idx[n_super + n_strong:])

    mu_log = np.zeros(n_stocks)
    sig_log = np.zeros(n_stocks)
    betas = rng_stocks.lognormal(math.log(0.85), 0.25, n_stocks)
    betas = np.clip(betas, 0.2, 1.8)

    for j, i in enumerate(super_list):
        mu_log[i], sig_log[i] = geo_to_log(super_mu_geo[j], super_sig[j])
    for j, i in enumerate(strong_list):
        mu_log[i], sig_log[i] = geo_to_log(strong_mu_geo[j], strong_sig[j])
    for j, i in enumerate(normal_list):
        mu_log[i], sig_log[i] = geo_to_log(normal_mu_geo[j], normal_sig[j])

    # ── 板块热点: 轻微短期提振 ───────────────────────────────────────────
    boost_arr = np.zeros((n_days, n_stocks))
    d = 0
    while d < n_days:
        hot_len = int(rng_boost.uniform(15, 35))
        cool_len = int(rng_boost.uniform(30, 70))

        leaders = rng_boost.choice(super_list, min(3, len(super_list)), replace=False)
        followers = rng_boost.choice(strong_list, min(8, len(strong_list)), replace=False)

        for dd in range(hot_len):
            if d + dd >= n_days:
                break
            heat = math.sin((dd + 0.5) / hot_len * math.pi)
            for i in leaders:
                boost_arr[d + dd, i] += rng_boost.uniform(0.001, 0.004) * heat
            for i in followers:
                boost_arr[d + dd, i] += rng_boost.uniform(0.0003, 0.001) * heat
        d += hot_len + cool_len

    # ── 生成价格路径 (对数收益, 精确GBM) ────────────────────────────────
    init_prices = rng_prices.lognormal(math.log(10), 0.7, n_stocks)
    init_prices = np.clip(init_prices, 2.0, 50.0)
    price_matrix = np.zeros((n_days + 1, n_stocks))
    price_matrix[0] = init_prices

    for d in range(n_days):
        mkt_log = math.log(1 + market_rets[d])
        boost = boost_arr[d]

        # 个股对数收益
        z = rng_prices.randn(n_stocks)
        # fat tails
        extreme = rng_prices.random(n_stocks) < 0.04
        z_fat = rng_prices.randn(n_stocks) * 2.0
        z_use = np.where(extreme, z_fat, z)

        log_r_stock = mu_log + betas * mkt_log + boost + z_use * sig_log
        r = np.exp(log_r_stock) - 1
        r = np.clip(r, -0.10, 0.10)
        price_matrix[d + 1] = price_matrix[d] * (1 + r)

    codes = [f"{i+1:06d}" for i in range(n_stocks)]
    prices = {c: list(price_matrix[:, i]) for i, c in enumerate(codes)}
    return prices, market_rets
