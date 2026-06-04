"""
A股回测数据集 — 80只股票
评分基于入场时点可得的公开信息（无前视偏差）

字段说明：
  name        股票名称
  code        股票代码
  entry_year  入场年份
  actual_1y   实际1年涨幅（0.80=+80%，2.0=+100%，3.0=+200%）
  label_2x    是否达到2x（+100%）
  label_3x    是否达到3x（+200%）

  -- MB-Score 输入参数（入场时点数据）--
  s1          业绩加速度 S1 [0,1]
  s2          催化剂强度 S2 [0,1]
  s3          估值安全边际 S3 [0,1]
  s4_moat     护城河分 [0,1]
  s4_ovmv     OV/MV 比值（原始值，评分用映射表）
  s4_tam      TAM确定性 [0,1]
  s4_ecowidth 生态宽度 [0,1]
  scp         战略控制点 [0,1]
  p_eff       有效渗透率 [%]
  crowd_disc  拥挤度折扣乘数
  p9_adj      机构动向乘数
  p9b_ovht    过热惩罚乘数
  p8_adj      内部人/收入质量乘数
  resonance   资金共振乘数
  catalyst_grade  催化剂等级 S+/S/A/B/C
  regime      当时宏观Regime R1-R5

  source      数据来源说明（用于溯源）
  category    分类：3x正样本/2x正样本/负样本
"""

STOCKS = [
    # =========================================================
    # 三倍正样本（22只，来自Prompt文件，入场时打分保守处理）
    # =========================================================
    {
        "name": "亿纬锂能", "code": "300014", "entry_year": 2019,
        "actual_1y": 3.50, "label_2x": True, "label_3x": True,
        "s1": 0.82, "s2": 0.88, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 4.2, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "领益智造", "code": "002600", "entry_year": 2019,
        "actual_1y": 2.10, "label_2x": True, "label_3x": True,
        "s1": 0.68, "s2": 0.78, "s3": 0.45, "s4_moat": 0.50,
        "s4_ovmv": 2.8, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.50, "p_eff": 18.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 0.90,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本（FN边缘）", "category": "3x"
    },
    {
        "name": "国联股份", "code": "603613", "entry_year": 2019,
        "actual_1y": 3.20, "label_2x": True, "label_3x": True,
        "s1": 0.80, "s2": 0.85, "s3": 0.50, "s4_moat": 0.70,
        "s4_ovmv": 3.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "闻泰科技", "code": "600745", "entry_year": 2019,
        "actual_1y": 3.80, "label_2x": True, "label_3x": True,
        "s1": 0.84, "s2": 0.88, "s3": 0.48, "s4_moat": 0.70,
        "s4_ovmv": 4.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "立讯精密", "code": "002475", "entry_year": 2019,
        "actual_1y": 4.20, "label_2x": True, "label_3x": True,
        "s1": 0.90, "s2": 0.92, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 5.5, "s4_tam": 1.00, "s4_ecowidth": 1.00,
        "scp": 0.80, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "韦尔股份", "code": "603501", "entry_year": 2019,
        "actual_1y": 5.50, "label_2x": True, "label_3x": True,
        "s1": 0.90, "s2": 0.94, "s3": 0.45, "s4_moat": 0.85,
        "s4_ovmv": 6.0, "s4_tam": 1.00, "s4_ecowidth": 1.00,
        "scp": 0.75, "p_eff": 6.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "北京君正", "code": "300223", "entry_year": 2019,
        "actual_1y": 2.20, "label_2x": True, "label_3x": True,
        "s1": 0.70, "s2": 0.78, "s3": 0.45, "s4_moat": 0.50,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.50, "p_eff": 20.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本（FN边缘）", "category": "3x"
    },
    {
        "name": "阳光电源", "code": "300274", "entry_year": 2020,
        "actual_1y": 4.50, "label_2x": True, "label_3x": True,
        "s1": 0.86, "s2": 0.88, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 5.0, "s4_tam": 1.00, "s4_ecowidth": 1.00,
        "scp": 0.75, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R1",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "宁德时代", "code": "300750", "entry_year": 2020,
        "actual_1y": 3.50, "label_2x": True, "label_3x": True,
        "s1": 0.92, "s2": 0.96, "s3": 0.50, "s4_moat": 1.00,
        "s4_ovmv": 8.0, "s4_tam": 1.00, "s4_ecowidth": 1.00,
        "scp": 0.90, "p_eff": 5.0,
        "crowd_disc": 1.00, "p9_adj": 1.03, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R1",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "隆基绿能", "code": "601012", "entry_year": 2020,
        "actual_1y": 3.20, "label_2x": True, "label_3x": True,
        "s1": 0.84, "s2": 0.88, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 4.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R1",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "智飞生物", "code": "300122", "entry_year": 2020,
        "actual_1y": 2.30, "label_2x": True, "label_3x": True,
        "s1": 0.70, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 2.8, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 15.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R1",
        "source": "Prompt文件原始样本（FN边缘）", "category": "3x"
    },
    {
        "name": "奥特维", "code": "688516", "entry_year": 2021,
        "actual_1y": 3.80, "label_2x": True, "label_3x": True,
        "s1": 0.82, "s2": 0.86, "s3": 0.50, "s4_moat": 0.70,
        "s4_ovmv": 4.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "天齐锂业", "code": "002466", "entry_year": 2021,
        "actual_1y": 4.20, "label_2x": True, "label_3x": True,
        "s1": 0.84, "s2": 0.88, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 5.0, "s4_tam": 1.00, "s4_ecowidth": 0.40,
        "scp": 0.80, "p_eff": 15.0,
        "crowd_disc": 0.97, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本（周期股）", "category": "3x"
    },
    {
        "name": "天合光能", "code": "688599", "entry_year": 2021,
        "actual_1y": 2.80, "label_2x": True, "label_3x": True,
        "s1": 0.80, "s2": 0.84, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "紫光国微", "code": "002049", "entry_year": 2021,
        "actual_1y": 3.60, "label_2x": True, "label_3x": True,
        "s1": 0.90, "s2": 0.92, "s3": 0.50, "s4_moat": 1.00,
        "s4_ovmv": 6.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "新易盛", "code": "300502", "entry_year": 2023,
        "actual_1y": 4.50, "label_2x": True, "label_3x": True,
        "s1": 0.86, "s2": 0.90, "s3": 0.45, "s4_moat": 0.85,
        "s4_ovmv": 5.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.75, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "寒武纪", "code": "688256", "entry_year": 2023,
        "actual_1y": 3.20, "label_2x": True, "label_3x": True,
        "s1": 0.82, "s2": 0.88, "s3": 0.40, "s4_moat": 0.85,
        "s4_ovmv": 5.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 6.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "万兴科技_23", "code": "300624", "entry_year": 2023,
        "actual_1y": 2.10, "label_2x": True, "label_3x": True,
        "s1": 0.70, "s2": 0.78, "s3": 0.40, "s4_moat": 0.50,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.35, "p_eff": 20.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本（FN边缘，AI概念）", "category": "3x"
    },
    {
        "name": "昆仑万维", "code": "300418", "entry_year": 2023,
        "actual_1y": 2.80, "label_2x": True, "label_3x": True,
        "s1": 0.78, "s2": 0.84, "s3": 0.40, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 15.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "中际旭创", "code": "300308", "entry_year": 2023,
        "actual_1y": 5.50, "label_2x": True, "label_3x": True,
        "s1": 0.92, "s2": 0.96, "s3": 0.45, "s4_moat": 1.00,
        "s4_ovmv": 7.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.90, "p_eff": 5.0,
        "crowd_disc": 1.00, "p9_adj": 1.03, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "罗博特科", "code": "688619", "entry_year": 2024,
        "actual_1y": 2.50, "label_2x": True, "label_3x": True,
        "s1": 0.80, "s2": 0.84, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },
    {
        "name": "寒武纪_24", "code": "688256", "entry_year": 2024,
        "actual_1y": 3.80, "label_2x": True, "label_3x": True,
        "s1": 0.94, "s2": 0.96, "s3": 0.38, "s4_moat": 0.85,
        "s4_ovmv": 6.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 8.0,
        "crowd_disc": 0.97, "p9_adj": 1.02, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "Prompt文件原始样本", "category": "3x"
    },

    # =========================================================
    # 两倍正样本（14只，来自Prompt 2x patch）
    # =========================================================
    {
        "name": "赣锋锂业", "code": "002460", "entry_year": 2020,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.82, "s2": 0.84, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.75, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R1",
        "source": "2x Patch样本（锂资源周期）", "category": "2x"
    },
    {
        "name": "赛力斯", "code": "601127", "entry_year": 2024,
        "actual_1y": 3.00, "label_2x": True, "label_3x": True,
        "s1": 0.80, "s2": 0.88, "s3": 0.45, "s4_moat": 0.50,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.50, "p_eff": 20.0,
        "crowd_disc": 0.97, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "2x Patch样本（新能源车）", "category": "2x"
    },
    {
        "name": "汇川技术", "code": "300124", "entry_year": 2020,
        "actual_1y": 2.50, "label_2x": True, "label_3x": False,
        "s1": 0.82, "s2": 0.76, "s3": 0.50, "s4_moat": 0.70,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 18.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "A", "regime": "R1",
        "source": "2x Patch样本（工控龙头）", "category": "2x"
    },
    {
        "name": "三花智控", "code": "002050", "entry_year": 2020,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.72, "s2": 0.72, "s3": 0.50, "s4_moat": 0.70,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 22.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R1",
        "source": "2x Patch样本（热管理）", "category": "2x"
    },
    {
        "name": "石头科技", "code": "688169", "entry_year": 2020,
        "actual_1y": 2.80, "label_2x": True, "label_3x": False,
        "s1": 0.88, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.55, "p_eff": 15.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R1",
        "source": "2x Patch样本（扫地机器人）", "category": "2x"
    },
    {
        "name": "药明康德", "code": "603259", "entry_year": 2020,
        "actual_1y": 3.00, "label_2x": True, "label_3x": True,
        "s1": 0.88, "s2": 0.84, "s3": 0.48, "s4_moat": 0.85,
        "s4_ovmv": 2.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.80, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R1",
        "source": "2x Patch样本（CXO）", "category": "2x"
    },
    {
        "name": "迈瑞医疗", "code": "300760", "entry_year": 2020,
        "actual_1y": 2.00, "label_2x": True, "label_3x": False,
        "s1": 0.65, "s2": 0.60, "s3": 0.45, "s4_moat": 0.85,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.75, "p_eff": 25.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R1",
        "source": "2x Patch样本（FN边缘，慢牛）", "category": "2x"
    },
    {
        "name": "海光信息", "code": "688041", "entry_year": 2023,
        "actual_1y": 2.50, "label_2x": True, "label_3x": False,
        "s1": 0.84, "s2": 0.88, "s3": 0.38, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 8.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "2x Patch样本（国产CPU）", "category": "2x"
    },
    {
        "name": "华测检测", "code": "300012", "entry_year": 2020,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.65, "s2": 0.60, "s3": 0.50, "s4_moat": 0.70,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.50, "p_eff": 28.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R1",
        "source": "2x Patch样本（FN边缘，检测）", "category": "2x"
    },
    {
        "name": "晶澳科技", "code": "002459", "entry_year": 2021,
        "actual_1y": 2.30, "label_2x": True, "label_3x": False,
        "s1": 0.78, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 2.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.55, "p_eff": 18.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 0.90,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "2x Patch样本（光伏组件）", "category": "2x"
    },
    {
        "name": "盐湖股份", "code": "000792", "entry_year": 2021,
        "actual_1y": 3.00, "label_2x": True, "label_3x": True,
        "s1": 0.84, "s2": 0.84, "s3": 0.50, "s4_moat": 0.85,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.80, "p_eff": 20.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "2x Patch样本（盐湖资源周期）", "category": "2x"
    },
    {
        "name": "科沃斯", "code": "603486", "entry_year": 2020,
        "actual_1y": 3.00, "label_2x": True, "label_3x": True,
        "s1": 0.84, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.50, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R1",
        "source": "2x Patch样本（扫地机器人）", "category": "2x"
    },
    {
        "name": "恒玄科技", "code": "688608", "entry_year": 2023,
        "actual_1y": 2.50, "label_2x": True, "label_3x": False,
        "s1": 0.88, "s2": 0.84, "s3": 0.40, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "2x Patch样本（TWS芯片）", "category": "2x"
    },
    {
        "name": "圣邦股份", "code": "300661", "entry_year": 2019,
        "actual_1y": 2.80, "label_2x": True, "label_3x": False,
        "s1": 0.82, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 15.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "2x Patch样本（模拟芯片）", "category": "2x"
    },

    # =========================================================
    # 扩展正样本（15只新增，补充覆盖年份/行业）
    # =========================================================
    {
        "name": "卓胜微", "code": "300782", "entry_year": 2020,
        "actual_1y": 3.50, "label_2x": True, "label_3x": True,
        "s1": 0.88, "s2": 0.90, "s3": 0.42, "s4_moat": 0.85,
        "s4_ovmv": 5.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.75, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R1",
        "source": "扩展正样本：射频芯片国产化，5G手机渗透加速", "category": "3x"
    },
    {
        "name": "澜起科技", "code": "688008", "entry_year": 2023,
        "actual_1y": 2.80, "label_2x": True, "label_3x": False,
        "s1": 0.84, "s2": 0.88, "s3": 0.40, "s4_moat": 0.85,
        "s4_ovmv": 4.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.80, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "扩展正样本：DDR5内存接口芯片，AI服务器内存扩张", "category": "2x"
    },
    {
        "name": "长川科技", "code": "300604", "entry_year": 2023,
        "actual_1y": 4.20, "label_2x": True, "label_3x": True,
        "s1": 0.90, "s2": 0.90, "s3": 0.38, "s4_moat": 0.85,
        "s4_ovmv": 5.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.80, "p_eff": 8.0,
        "crowd_disc": 0.97, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "扩展正样本：半导体测试设备国产化加速", "category": "3x"
    },
    {
        "name": "胜宏科技", "code": "300476", "entry_year": 2023,
        "actual_1y": 3.20, "label_2x": True, "label_3x": True,
        "s1": 0.86, "s2": 0.88, "s3": 0.42, "s4_moat": 0.70,
        "s4_ovmv": 4.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 5.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R2",
        "source": "扩展正样本：AI服务器PCB，P_eff=5.4%（价值量修正）", "category": "3x"
    },
    {
        "name": "英伟达供应链_沪电股份", "code": "002463", "entry_year": 2023,
        "actual_1y": 2.50, "label_2x": True, "label_3x": False,
        "s1": 0.82, "s2": 0.86, "s3": 0.42, "s4_moat": 0.70,
        "s4_ovmv": 3.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R2",
        "source": "扩展正样本：高速PCB，AI推动需求", "category": "2x"
    },
    {
        "name": "鼎阳科技", "code": "688112", "entry_year": 2022,
        "actual_1y": 2.30, "label_2x": True, "label_3x": False,
        "s1": 0.80, "s2": 0.80, "s3": 0.45, "s4_moat": 0.70,
        "s4_ovmv": 3.0, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "扩展正样本：示波器国产替代，研发加速", "category": "2x"
    },
    {
        "name": "金山办公", "code": "688111", "entry_year": 2020,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.72, "s2": 0.72, "s3": 0.35, "s4_moat": 0.70,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 30.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R1",
        "source": "扩展正样本：疫情驱动远程办公，国产替代", "category": "2x"
    },
    {
        "name": "迈为股份", "code": "300751", "entry_year": 2021,
        "actual_1y": 3.80, "label_2x": True, "label_3x": True,
        "s1": 0.86, "s2": 0.88, "s3": 0.45, "s4_moat": 0.85,
        "s4_ovmv": 5.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.75, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "扩展正样本：HJT丝网印刷设备龙头", "category": "3x"
    },
    {
        "name": "华友钴业", "code": "603799", "entry_year": 2020,
        "actual_1y": 2.50, "label_2x": True, "label_3x": False,
        "s1": 0.78, "s2": 0.80, "s3": 0.48, "s4_moat": 0.70,
        "s4_ovmv": 2.5, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.65, "p_eff": 15.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R1",
        "source": "扩展正样本：钴资源+三元前驱体，新能源周期", "category": "2x"
    },
    {
        "name": "工业富联", "code": "601138", "entry_year": 2023,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.80, "s2": 0.82, "s3": 0.48, "s4_moat": 0.70,
        "s4_ovmv": 2.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 12.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R2",
        "source": "扩展正样本：AI服务器代工，算力需求爆发", "category": "2x"
    },
    {
        "name": "中微公司", "code": "688012", "entry_year": 2022,
        "actual_1y": 2.80, "label_2x": True, "label_3x": False,
        "s1": 0.84, "s2": 0.90, "s3": 0.38, "s4_moat": 1.00,
        "s4_ovmv": 4.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 1.00, "p_eff": 8.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R3",
        "source": "扩展正样本：刻蚀设备，制裁加速国产替代", "category": "2x"
    },
    {
        "name": "拓荆科技", "code": "688072", "entry_year": 2022,
        "actual_1y": 2.20, "label_2x": True, "label_3x": False,
        "s1": 0.80, "s2": 0.86, "s3": 0.40, "s4_moat": 0.85,
        "s4_ovmv": 4.0, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 6.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S+", "regime": "R3",
        "source": "扩展正样本：CVD设备国产唯一选择", "category": "2x"
    },
    {
        "name": "天孚通信", "code": "300394", "entry_year": 2023,
        "actual_1y": 4.50, "label_2x": True, "label_3x": True,
        "s1": 0.90, "s2": 0.90, "s3": 0.40, "s4_moat": 0.85,
        "s4_ovmv": 5.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.80, "p_eff": 5.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 0.88,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R2",
        "source": "扩展正样本：光器件，AI光互连需求爆发", "category": "3x"
    },
    {
        "name": "电科芯片", "code": "688595", "entry_year": 2022,
        "actual_1y": 2.40, "label_2x": True, "label_3x": False,
        "s1": 0.80, "s2": 0.86, "s3": 0.42, "s4_moat": 0.85,
        "s4_ovmv": 3.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 10.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.05, "catalyst_grade": "S", "regime": "R3",
        "source": "扩展正样本：军用芯片国产化", "category": "2x"
    },
    {
        "name": "北方华创", "code": "002371", "entry_year": 2022,
        "actual_1y": 2.60, "label_2x": True, "label_3x": False,
        "s1": 0.84, "s2": 0.88, "s3": 0.38, "s4_moat": 0.85,
        "s4_ovmv": 4.5, "s4_tam": 1.00, "s4_ecowidth": 0.70,
        "scp": 0.80, "p_eff": 6.0,
        "crowd_disc": 1.00, "p9_adj": 1.02, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.10, "catalyst_grade": "S+", "regime": "R3",
        "source": "扩展正样本：半导体设备，制裁后国产化提速", "category": "2x"
    },

    # =========================================================
    # 负样本（原始12只）
    # =========================================================
    {
        "name": "景嘉微", "code": "300474", "entry_year": 2023,
        "actual_1y": 1.30, "label_2x": False, "label_3x": False,
        "s1": 0.52, "s2": 0.72, "s3": 0.35, "s4_moat": 0.50,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.45, "p_eff": 15.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R2",
        "source": "原始负样本：GPU量产延迟", "category": "neg"
    },
    {
        "name": "龙芯中科", "code": "688047", "entry_year": 2023,
        "actual_1y": 0.80, "label_2x": False, "label_3x": False,
        "s1": 0.38, "s2": 0.62, "s3": 0.40, "s4_moat": 0.50,
        "s4_ovmv": 1.8, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.50, "p_eff": 8.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "原始负样本：商业化证伪", "category": "neg"
    },
    {
        "name": "中科创达", "code": "300496", "entry_year": 2021,
        "actual_1y": 1.60, "label_2x": False, "label_3x": False,
        "s1": 0.62, "s2": 0.60, "s3": 0.40, "s4_moat": 0.50,
        "s4_ovmv": 2.0, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.45, "p_eff": 30.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R2",
        "source": "原始负样本：华为不确定性", "category": "neg"
    },
    {
        "name": "金山办公_21", "code": "688111", "entry_year": 2021,
        "actual_1y": 1.20, "label_2x": False, "label_3x": False,
        "s1": 0.58, "s2": 0.50, "s3": 0.30, "s4_moat": 0.70,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.70,
        "scp": 0.60, "p_eff": 42.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "原始负样本：估值消化期", "category": "neg"
    },
    {
        "name": "广联达", "code": "002410", "entry_year": 2021,
        "actual_1y": 0.90, "label_2x": False, "label_3x": False,
        "s1": 0.48, "s2": 0.40, "s3": 0.35, "s4_moat": 0.70,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.50, "p_eff": 35.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "原始负样本：地产拖累", "category": "neg"
    },
    {
        "name": "万兴科技_对照", "code": "300624", "entry_year": 2023,
        "actual_1y": 1.40, "label_2x": False, "label_3x": False,
        "s1": 0.62, "s2": 0.68, "s3": 0.35, "s4_moat": 0.50,
        "s4_ovmv": 1.8, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.35, "p_eff": 25.0,
        "crowd_disc": 0.82, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "原始负样本：AI概念退潮后对照组", "category": "neg"
    },
    {
        "name": "柏楚电子", "code": "688188", "entry_year": 2021,
        "actual_1y": 1.50, "label_2x": False, "label_3x": False,
        "s1": 0.68, "s2": 0.55, "s3": 0.38, "s4_moat": 0.70,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.60, "p_eff": 35.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R2",
        "source": "原始负样本：增速不够快", "category": "neg"
    },
    {
        "name": "安恒信息", "code": "688023", "entry_year": 2021,
        "actual_1y": 0.70, "label_2x": False, "label_3x": False,
        "s1": 0.48, "s2": 0.52, "s3": 0.35, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 25.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "原始负样本：安全赛道内卷", "category": "neg"
    },
    {
        "name": "信维通信", "code": "300136", "entry_year": 2019,
        "actual_1y": 1.30, "label_2x": False, "label_3x": False,
        "s1": 0.58, "s2": 0.62, "s3": 0.40, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 40.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "原始负样本：天线可替代", "category": "neg"
    },
    {
        "name": "恩捷股份", "code": "002812", "entry_year": 2021,
        "actual_1y": 1.45, "label_2x": False, "label_3x": False,
        "s1": 0.62, "s2": 0.60, "s3": 0.40, "s4_moat": 0.70,
        "s4_ovmv": 2.0, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.55, "p_eff": 38.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R2",
        "source": "原始负样本：隔膜竞争加剧", "category": "neg"
    },
    {
        "name": "蓝思科技", "code": "300433", "entry_year": 2019,
        "actual_1y": 1.25, "label_2x": False, "label_3x": False,
        "s1": 0.52, "s2": 0.52, "s3": 0.42, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 45.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "原始负样本：玻璃可替代", "category": "neg"
    },
    {
        "name": "北方华创_19", "code": "002371", "entry_year": 2019,
        "actual_1y": 1.80, "label_2x": False, "label_3x": False,
        "s1": 0.68, "s2": 0.68, "s3": 0.42, "s4_moat": 0.70,
        "s4_ovmv": 2.2, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 12.0,
        "crowd_disc": 1.00, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R2",
        "source": "原始负样本边缘：2019年时机不对，2022年才爆发", "category": "neg"
    },

    # =========================================================
    # 扩展负样本（15只新增，涵盖更多行业和年份）
    # =========================================================
    {
        "name": "隆基绿能_22", "code": "601012", "entry_year": 2022,
        "actual_1y": 0.65, "label_2x": False, "label_3x": False,
        "s1": 0.60, "s2": 0.72, "s3": 0.35, "s4_moat": 0.85,
        "s4_ovmv": 1.8, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.65, "p_eff": 45.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R3",
        "source": "扩展负样本：N型替代冲击，渗透率已高", "category": "neg"
    },
    {
        "name": "宁德时代_22", "code": "300750", "entry_year": 2022,
        "actual_1y": 0.75, "label_2x": False, "label_3x": False,
        "s1": 0.72, "s2": 0.80, "s3": 0.25, "s4_moat": 1.00,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 1.00,
        "scp": 0.90, "p_eff": 55.0,
        "crowd_disc": 0.70, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R4",
        "source": "扩展负样本：高渗透率+R4宏观，典型好股但时机差", "category": "neg"
    },
    {
        "name": "恒瑞医药", "code": "600276", "entry_year": 2021,
        "actual_1y": 0.55, "label_2x": False, "label_3x": False,
        "s1": 0.60, "s2": 0.60, "s3": 0.35, "s4_moat": 1.00,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.70, "p_eff": 40.0,
        "crowd_disc": 0.70, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R3",
        "source": "扩展负样本：医保集采政策黑天鹅", "category": "neg"
    },
    {
        "name": "迈瑞医疗_21", "code": "300760", "entry_year": 2021,
        "actual_1y": 0.80, "label_2x": False, "label_3x": False,
        "s1": 0.62, "s2": 0.58, "s3": 0.30, "s4_moat": 0.85,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 0.70,
        "scp": 0.75, "p_eff": 35.0,
        "crowd_disc": 0.70, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R3",
        "source": "扩展负样本：高PE消化，估值过高", "category": "neg"
    },
    {
        "name": "比亚迪_22", "code": "002594", "entry_year": 2022,
        "actual_1y": 0.85, "label_2x": False, "label_3x": False,
        "s1": 0.78, "s2": 0.78, "s3": 0.30, "s4_moat": 0.85,
        "s4_ovmv": 1.2, "s4_tam": 0.70, "s4_ecowidth": 1.00,
        "scp": 0.80, "p_eff": 50.0,
        "crowd_disc": 0.70, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "S", "regime": "R4",
        "source": "扩展负样本：大市值天花板+渗透率>50%", "category": "neg"
    },
    {
        "name": "汇顶科技", "code": "603160", "entry_year": 2021,
        "actual_1y": 0.60, "label_2x": False, "label_3x": False,
        "s1": 0.45, "s2": 0.50, "s3": 0.30, "s4_moat": 0.70,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.45, "p_eff": 60.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "扩展负样本：指纹芯片渗透率饱和", "category": "neg"
    },
    {
        "name": "博腾股份", "code": "300363", "entry_year": 2023,
        "actual_1y": 0.60, "label_2x": False, "label_3x": False,
        "s1": 0.42, "s2": 0.50, "s3": 0.35, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.50, "p_eff": 25.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "扩展负样本：CXO景气下行，客户推迟订单", "category": "neg"
    },
    {
        "name": "天齐锂业_22", "code": "002466", "entry_year": 2022,
        "actual_1y": 0.50, "label_2x": False, "label_3x": False,
        "s1": 0.65, "s2": 0.68, "s3": 0.35, "s4_moat": 0.85,
        "s4_ovmv": 1.2, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.80, "p_eff": 25.0,
        "crowd_disc": 0.82, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R4",
        "source": "扩展负样本：锂矿周期顶部，价格暴跌", "category": "neg"
    },
    {
        "name": "阳光电源_23", "code": "300274", "entry_year": 2023,
        "actual_1y": 0.70, "label_2x": False, "label_3x": False,
        "s1": 0.68, "s2": 0.72, "s3": 0.30, "s4_moat": 0.85,
        "s4_ovmv": 1.8, "s4_tam": 0.70, "s4_ecowidth": 1.00,
        "scp": 0.75, "p_eff": 45.0,
        "crowd_disc": 0.82, "p9_adj": 0.95, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "A", "regime": "R3",
        "source": "扩展负样本：逆变器渗透率已高，估值过热后下行", "category": "neg"
    },
    {
        "name": "开立医疗", "code": "300633", "entry_year": 2022,
        "actual_1y": 1.30, "label_2x": False, "label_3x": False,
        "s1": 0.55, "s2": 0.55, "s3": 0.40, "s4_moat": 0.70,
        "s4_ovmv": 1.8, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.55, "p_eff": 22.0,
        "crowd_disc": 0.97, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "扩展负样本：医疗器械集采预期压制", "category": "neg"
    },
    {
        "name": "中软国际", "code": "354", "entry_year": 2023,
        "actual_1y": 1.10, "label_2x": False, "label_3x": False,
        "s1": 0.50, "s2": 0.55, "s3": 0.38, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 30.0,
        "crowd_disc": 0.92, "p9_adj": 1.00, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R2",
        "source": "扩展负样本：IT服务，AI概念但无实质收益", "category": "neg"
    },
    {
        "name": "国轩高科", "code": "002074", "entry_year": 2022,
        "actual_1y": 0.90, "label_2x": False, "label_3x": False,
        "s1": 0.58, "s2": 0.60, "s3": 0.30, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.70, "s4_ecowidth": 0.40,
        "scp": 0.50, "p_eff": 40.0,
        "crowd_disc": 0.82, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R4",
        "source": "扩展负样本：动力电池二线，份额被宁德挤压", "category": "neg"
    },
    {
        "name": "卫宁健康", "code": "300253", "entry_year": 2021,
        "actual_1y": 0.75, "label_2x": False, "label_3x": False,
        "s1": 0.45, "s2": 0.45, "s3": 0.30, "s4_moat": 0.50,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.40, "p_eff": 35.0,
        "crowd_disc": 0.82, "p9_adj": 0.92, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R3",
        "source": "扩展负样本：医疗信息化增速放缓", "category": "neg"
    },
    {
        "name": "英科医疗", "code": "300677", "entry_year": 2021,
        "actual_1y": 0.35, "label_2x": False, "label_3x": False,
        "s1": 0.40, "s2": 0.45, "s3": 0.35, "s4_moat": 0.50,
        "s4_ovmv": 0.8, "s4_tam": 0.35, "s4_ecowidth": 0.40,
        "scp": 0.35, "p_eff": 55.0,
        "crowd_disc": 0.70, "p9_adj": 0.92, "p9b_ovht": 0.92, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "C", "regime": "R3",
        "source": "扩展负样本：一次性手套需求后疫情崩塌", "category": "neg"
    },
    {
        "name": "东方财富_22", "code": "300059", "entry_year": 2022,
        "actual_1y": 0.75, "label_2x": False, "label_3x": False,
        "s1": 0.55, "s2": 0.50, "s3": 0.30, "s4_moat": 0.85,
        "s4_ovmv": 1.5, "s4_tam": 0.35, "s4_ecowidth": 0.70,
        "scp": 0.55, "p_eff": 50.0,
        "crowd_disc": 0.82, "p9_adj": 0.92, "p9b_ovht": 1.00, "p8_adj": 1.00,
        "resonance": 1.00, "catalyst_grade": "B", "regime": "R4",
        "source": "扩展负样本：市场下行，券商经纪收入下滑", "category": "neg"
    },
]
