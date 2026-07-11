"""
西安文化数字资产项目 - 一键运行脚本
按顺序执行：数据采集 → 数据清洗 → 知识图谱构建 → 内容生成

用法：
    python run_all.py          # 运行完整流程
    python run_all.py --web    # 运行流程后启动Web平台
    python run_all.py --skip-collect  # 跳过数据采集（使用已有数据）
"""

import sys
import os
import argparse

PYTHON = sys.executable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 自动加载.env环境变量
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("✓ 已加载 .env 配置文件")


def run_step(step_name, script_path):
    """运行一个步骤"""
    print(f"\n{'='*60}")
    print(f"  [{step_name}]")
    print(f"{'='*60}")
    cmd = f'cd "{BASE_DIR}" && PYTHONUTF8=1 "{PYTHON}" "{script_path}"'
    ret = os.system(cmd)
    if ret != 0:
        print(f"\n⚠ [{step_name}] 执行出错，但继续后续步骤...")
    return ret


def main():
    parser = argparse.ArgumentParser(description='西安文化数字资产项目 - 一键运行')
    parser.add_argument('--web', action='store_true', help='运行完成后启动Web展示平台')
    parser.add_argument('--skip-collect', action='store_true', help='跳过数据采集步骤')
    parser.add_argument('--skip-process', action='store_true', help='跳过数据清洗步骤')
    parser.add_argument('--skip-kg', action='store_true', help='跳过知识图谱构建')
    parser.add_argument('--skip-generate', action='store_true', help='跳过内容生成')
    args = parser.parse_args()

    print("="*60)
    print("  西安文物/非遗/文旅数字资产项目")
    print("  一键运行脚本")
    print("="*60)

    if not args.skip_collect:
        run_step("1/5 数据采集", "data/data_collector.py")
    else:
        print("\n⏭ 跳过数据采集")

    if not args.skip_process:
        run_step("2/5 数据清洗与结构化", "data/data_processor.py")
    else:
        print("\n⏭ 跳过数据清洗")

    if not args.skip_kg:
        run_step("3/5 知识图谱构建", "data/knowledge_graph_builder.py")
    else:
        print("\n⏭ 跳过知识图谱构建")

    if not args.skip_generate:
        run_step("4/5 多模态内容生成", "agent/cultural_agent.py")
        # 批量生成
        print("\n  正在批量生成8个主题的多模态内容...")
        os.system(f'cd "{BASE_DIR}" && PYTHONUTF8=1 "{PYTHON}" -c "from agent.cultural_agent import CulturalContentAgent; CulturalContentAgent().batch_generate()"')
    else:
        print("\n⏭ 跳过内容生成")

    run_step("5/5 生成提交文档", "docs/gen_docs.py")

    print("\n" + "="*60)
    print("  ✅ 所有步骤已完成！")
    print("="*60)
    print(f"""
项目输出：
  数据资产：
    data/raw/xian_cultural_dataset.json        - 原始数据集(JSON)
    data/raw/xian_cultural_dataset.xlsx         - 原始数据集(Excel)
    data/processed/xian_cultural_dataset_processed.json - 处理后数据集
    data/processed/cleaning_report.json         - 清洗报告

  知识图谱：
    data/knowledge_graph/knowledge_graph.json   - 知识图谱(JSON)
    data/knowledge_graph/knowledge_graph.graphml - 知识图谱(GraphML)
    data/knowledge_graph/knowledge_graph.ttl    - 知识图谱(RDF/Turtle)
    data/knowledge_graph/knowledge_graph.html   - 知识图谱(HTML可视化)

  生成内容：
    outputs/generated_contents.json             - 批量生成内容库

  提交文档：
    docs/赛题方案文档.docx                       - 赛题方案文档
    docs/数据资产元数据标准与知识图谱设计文档.docx  - 元数据标准文档

  演示视频脚本：
    outputs/demo_video_script.md                - 演示视频脚本
""")

    if args.web:
        print("\n🚀 启动Web展示平台...")
        os.chdir(os.path.join(BASE_DIR, 'web'))
        os.system(f'"{PYTHON}" -m streamlit run app.py')


if __name__ == '__main__':
    main()
