#!/usr/bin/env python3
"""板块资金流向追踪器 — 记录周度主力资金数据，计算资金连续性评分

功能:
  1. 记录每周末各板块的资金数据（涨幅、暗盘资金、主力行为）
  2. 追加式存储到 data/fund_flow/ 目录
  3. 计算资金连续性评分（连续抢筹/连续出货）
  4. 导出资金连续性维度得分，供评分引擎使用

用法:
  python3 fund_flow_tracker.py --add <JSON文件>   # 添加一周数据
  python3 fund_flow_tracker.py --view             # 查看已记录数据
  python3 fund_flow_tracker.py --score            # 计算资金连续性评分
  python3 fund_flow_tracker.py --export           # 导出供评分引擎使用
"""
import sys, os, json, csv
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fund_flow")
DATA_DIR = os.path.abspath(DATA_DIR)

# 主力行为权重
BEHAVIOR_WEIGHT = {"抢筹": 3, "建仓": 1, "洗盘": 0, "出货": -3, "——": 0}

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_data():
    """加载所有周度资金数据"""
    ensure_dir()
    all_data = {}
    for f in os.listdir(DATA_DIR):
        if f.endswith(".json") and not f.startswith("_"):
            with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fh:
                d = json.load(fh)
            week = f.replace(".json", "")
            all_data[week] = d
    return all_data

def add_week(week_name, data):
    """添加一周数据"""
    ensure_dir()
    path = os.path.join(DATA_DIR, f"{week_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存 {week_name} 周数据到 {path}")

def add_from_csv(csv_path, week_name=None):
    """从 CSV 添加数据
    CSV 格式: 板块名称,周数,涨幅,暗盘资金,主力行为
    """
    ensure_dir()
    data = {}
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sector = row.get("板块名称", "").strip()
            week = row.get("周数", "").strip()
            gain = row.get("涨幅", "—").strip()
            flow = row.get("暗盘资金", "0").strip()
            behavior = row.get("主力行为", "").strip()
            # 组装 key: 板块_周数
            key = f"{sector}_{week}"
            try:
                flow_val = float(flow) if flow not in ("—", "", "——") else 0
            except:
                flow_val = 0
            data[key] = {
                "sector": sector, "week": week,
                "gain": gain, "flow": flow_val, "behavior": behavior,
                "score": BEHAVIOR_WEIGHT.get(behavior, 0)
            }
    # 保存到统一文件
    if week_name is None:
        week_name = datetime.now().strftime("%Y%m%d")
    path = os.path.join(DATA_DIR, f"batch_{week_name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已从 CSV 导入 {len(data)} 条记录")

def view():
    data = load_data()
    print(f"已记录 {len(data)} 周/批次数据:")
    for week, d in sorted(data.items()):
        print(f"\n[{week}] {len(d)} 条")
        # 打印前几个板块
        for k, v in list(d.items())[:5]:
            print(f"  {v.get('sector')} {v.get('week')}: {v.get('gain')}% 资金{v.get('flow')} {v.get('behavior')}")

def score():
    """计算资金连续性评分（每板块 0-10 分）"""
    data = load_data()
    # 汇总每板块的资金轨迹
    sector_history = {}
    for week, d in data.items():
        for k, v in d.items():
            sector = v.get("sector", "")
            if sector not in sector_history:
                sector_history[sector] = []
            sector_history[sector].append(v)
    
    results = []
    for sector, history in sector_history.items():
        # 按周数排序
        def week_num(w):
            try:
                import re
                m = re.search(r'(\d+)', w or '')
                return int(m.group(1)) if m else 99
            except: return 99
        history.sort(key=lambda x: week_num(x.get("week", "")))
        
        # 连续性评分
        behavior_seq = [h.get("behavior", "") for h in history]
        flow_seq = [h.get("flow", 0) for h in history]
        
        # 最近3周行为
        recent = behavior_seq[-3:] if len(behavior_seq) >= 3 else behavior_seq
        recent_flows = flow_seq[-3:] if len(flow_seq) >= 3 else flow_seq
        
        # 评分规则
        score_val = 0
        for b in recent:
            score_val += BEHAVIOR_WEIGHT.get(b, 0)
        
        # 连续抢筹奖励
        if recent and all(b == "抢筹" for b in recent[-2:]):
            score_val += 2
        # 连续出货惩罚
        if recent and all(b == "出货" for b in recent[-2:]):
            score_val -= 2
        
        # 资金趋势（最近3周资金均值）
        avg_flow = sum(recent_flows) / len(recent_flows) if recent_flows else 0
        
        # 归一化到 0-10
        # 基准: 3周连续抢筹 ≈ 满分, 3周连续出货 ≈ 0
        normalized = max(0, min(10, (score_val + 6) / 1.2))
        
        results.append({
            "sector": sector, "score": round(normalized, 1),
            "behavior_seq": behavior_seq, "flows": flow_seq,
            "avg_flow": round(avg_flow, 1),
        })
    
    results.sort(key=lambda x: -x["score"])
    
    print(f"{'板块':<12}{'资金连续性':<10}{'行为序列':<25}{'资金轨迹'}")
    print("-"*70)
    for r in results:
        print(f"{r['sector']:<12}{r['score']:<10}{'→'.join(r['behavior_seq']):<25}{r['flows']}")
    
    return results

def export():
    """导出资金连续性评分，供评分引擎使用"""
    results = score()
    # 保存为 JSON 供其他脚本读取
    export_path = os.path.join(DATA_DIR, "_latest_scores.json")
    out = {r["sector"]: r["score"] for r in results}
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已导出资金连续性评分到 {export_path}")
    print("评分引擎可通过读取该文件获取资金维度得分")
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "--add":
        add_week(sys.argv[2], json.load(open(sys.argv[3])))
    elif cmd == "--add-csv":
        add_from_csv(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "--view":
        view()
    elif cmd == "--score":
        score()
    elif cmd == "--export":
        export()
    else:
        print(__doc__)
