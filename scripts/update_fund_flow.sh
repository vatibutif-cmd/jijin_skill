#!/bin/bash
# 更新板块资金流向数据
# 用法: ./update_fund_flow.sh  (每周日收盘后运行)
#
# 数据来源: 用户提供的资金流向表，或从可用的数据源抓取
# 本脚本负责:
#   1. 确认数据目录
#   2. 提示用户粘贴最新一周的资金流向数据
#   3. 调用 fund_flow_tracker.py 导入

cd "$(dirname "$0")/.."
echo "=== FAMAS 资金流向数据更新 ==="
echo ""
echo "请提供最新一周的板块资金流向数据（CSV格式）："
echo "板块名称,周数,涨幅,暗盘资金,主力行为"
echo "示例: 软件服务,第六周,3.2,280.5,抢筹"
echo ""
echo "将数据保存为文件后执行:"
echo "  python3 scripts/fund_flow_tracker.py --add-csv <文件> <周数标签>"
echo ""
echo "或者直接粘贴数据，用 Ctrl-D 结束输入:"
cat > /tmp/fund_flow_new.csv
echo ""
echo "已接收输入，导入数据..."
python3 scripts/fund_flow_tracker.py --add-csv /tmp/fund_flow_new.csv $(date +%Y%m)
echo ""
echo "=== 更新后的资金连续性评分 ==="
python3 scripts/fund_flow_tracker.py --export
