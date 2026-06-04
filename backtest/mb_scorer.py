"""
V18.2 MB-Score 计算引擎
实现完整的 3x 模式和 2x 模式评分
"""
import math


# ── OV/MV → OptionSpace 映射 ──────────────────────────────────────────
def option_space_3x(ovmv: float) -> float:
    if ovmv > 8:   return 1.00
    if ovmv > 5:   return 0.90
    if ovmv > 3:   return 0.78
    if ovmv > 1.5: return 0.62
    if ovmv > 0.5: return 0.45
    return 0.25


def option_space_2x(ovmv: float) -> float:
    if ovmv > 5:   return 1.00
    if ovmv > 3:   return 0.92
    if ovmv > 2:   return 0.82
    if ovmv > 1.5: return 0.68
    if ovmv > 1.0: return 0.50
    return 0.25


# ── S3 近似（渗透率<15%时固定0.50）────────────────────────────────────
def compute_s3(s3_raw: float, p_eff: float) -> float:
    if p_eff < 15:
        return 0.50
    return s3_raw


# ── S4 评分 ────────────────────────────────────────────────────────────
def compute_s4_3x(moat: float, ovmv: float, tam: float, eco: float) -> float:
    os = option_space_3x(ovmv)
    return 0.35 * moat + 0.30 * os + 0.20 * tam + 0.15 * eco


def compute_s4_2x(moat: float, ovmv: float, tam: float, eco: float, scp: float) -> float:
    os = option_space_2x(ovmv)
    return 0.30 * moat + 0.20 * os + 0.20 * tam + 0.15 * eco + 0.15 * scp


# ── PTS 主矛盾强度 ──────────────────────────────────────────────────────
_CATALYST_INTENSITY = {"S+": 1.00, "S": 0.85, "A": 0.60, "B": 0.35, "C": 0.10}

def _runway_score(p_eff: float) -> float:
    if p_eff < 10:   return 1.00
    if p_eff < 20:   return 0.85
    if p_eff < 35:   return 0.65
    if p_eff < 55:   return 0.40
    return 0.15


def compute_pts_3x(catalyst_grade: str, p_eff: float, ovmv: float, moat: float) -> float:
    cat = _CATALYST_INTENSITY.get(catalyst_grade, 0.60)
    runway = _runway_score(p_eff)
    os = option_space_3x(ovmv)
    return 0.30 * cat + 0.25 * runway + 0.25 * os + 0.20 * moat


def compute_pts_2x(catalyst_grade: str, p_eff: float, ovmv: float, moat: float, scp: float) -> float:
    cat = _CATALYST_INTENSITY.get(catalyst_grade, 0.60)
    runway = _runway_score(p_eff)
    os = option_space_2x(ovmv)
    return 0.25 * cat + 0.25 * runway + 0.20 * os + 0.15 * moat + 0.15 * scp


# ── 次矛盾保护 floor ────────────────────────────────────────────────────
def pts_floor_3x(pts: float) -> float:
    if pts >= 0.80: return 0.88
    if pts >= 0.65: return 0.82
    if pts >= 0.50: return 0.75
    return 0.0


def pts_floor_2x(pts: float) -> float:
    if pts >= 0.80: return 0.90
    if pts >= 0.65: return 0.85
    if pts >= 0.50: return 0.78
    return 0.0


# ── Cat_Mult ────────────────────────────────────────────────────────────
_CAT_MULT_3X = {"S+": 1.15, "S": 1.10, "A": 1.05, "B": 1.00, "C": 0.95}
_CAT_MULT_2X = {"S+": 1.12, "S": 1.08, "A": 1.04, "B": 1.00, "C": 0.95}


# ── 核心评分函数 ──────────────────────────────────────────────────────
def score_3x(stock: dict) -> dict:
    s = stock
    s3 = compute_s3(s["s3"], s["p_eff"])
    s4 = compute_s4_3x(s["s4_moat"], s["s4_ovmv"], s["s4_tam"], s["s4_ecowidth"])

    synergy = math.sqrt(s["s2"] * s4)
    linear = 0.22 * s["s1"] + 0.22 * s["s2"] + 0.22 * s3 + 0.22 * s4 + 0.12 * synergy

    price_in_penalty = -0.06 * max(0, s["s1"] - 0.80) * max(0, 0.50 - s3)
    mb_raw = linear + price_in_penalty

    pts = compute_pts_3x(s["catalyst_grade"], s["p_eff"], s["s4_ovmv"], s["s4_moat"])
    floor = pts_floor_3x(pts)

    secondary_raw = s["crowd_disc"] * s["p9_adj"] * s["p9b_ovht"]
    secondary_mult = max(floor, secondary_raw)

    cat_mult = _CAT_MULT_3X.get(s["catalyst_grade"], 1.00)
    mb_score = min(1.35, mb_raw * s["resonance"] * cat_mult * secondary_mult * s["p8_adj"])

    return {
        "s3": s3, "s4": s4, "synergy": synergy, "linear": linear,
        "mb_raw": mb_raw, "pts": pts, "floor": floor,
        "secondary_raw": secondary_raw, "secondary_mult": secondary_mult,
        "cat_mult": cat_mult, "mb_score_3x": mb_score,
        "pass_3x": mb_score >= 0.80,
    }


def score_2x(stock: dict) -> dict:
    s = stock
    s3 = compute_s3(s["s3"], s["p_eff"])
    s4 = compute_s4_2x(s["s4_moat"], s["s4_ovmv"], s["s4_tam"], s["s4_ecowidth"], s["scp"])

    synergy = math.sqrt(s["s2"] * s4)
    linear = 0.22 * s["s1"] + 0.22 * s["s2"] + 0.22 * s3 + 0.22 * s4 + 0.12 * synergy

    price_in_penalty = -0.06 * max(0, s["s1"] - 0.80) * max(0, 0.50 - s3)
    mb_raw = linear + price_in_penalty

    pts = compute_pts_2x(s["catalyst_grade"], s["p_eff"], s["s4_ovmv"], s["s4_moat"], s["scp"])
    floor = pts_floor_2x(pts)

    secondary_raw = s["crowd_disc"] * s["p9_adj"] * s["p9b_ovht"]
    secondary_mult = max(floor, secondary_raw)

    cat_mult = _CAT_MULT_2X.get(s["catalyst_grade"], 1.00)
    mb_score = min(1.35, mb_raw * s["resonance"] * cat_mult * secondary_mult * s["p8_adj"])

    return {
        "s3": s3, "s4": s4, "synergy": synergy, "linear": linear,
        "mb_raw": mb_raw, "pts": pts, "floor": floor,
        "secondary_raw": secondary_raw, "secondary_mult": secondary_mult,
        "cat_mult": cat_mult, "mb_score_2x": mb_score,
        "pass_2x": mb_score >= 0.68,
    }


def score_both(stock: dict) -> dict:
    r3 = score_3x(stock)
    r2 = score_2x(stock)
    return {**r3, **r2}
