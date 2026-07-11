"""
文化内容创作智能体 - 交互式运行脚本
支持命令行交互和批量生成
"""

import os
import sys

# 加载环境变量
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from cultural_agent import CulturalContentAgent


def main():
    print("=" * 60)
    print("  西安文化内容创作智能体")
    print("=" * 60)

    agent = CulturalContentAgent()

    # 交互提示
    quick_topics = [
        "秦始皇兵马俑", "大雁塔", "西安城墙", "大唐不夜城",
        "西安鼓乐", "秦腔", "回民街", "华清宫",
        "碑林博物馆", "长安十二时辰", "羊肉泡馍", "皮影戏",
    ]

    print("\n快捷主题：")
    for i, t in enumerate(quick_topics):
        print(f"  {i+1}. {t}")
    print(f"  0. 自定义主题")
    print(f"  b. 批量生成全部主题")

    choice = input("\n请选择 (默认1): ").strip()

    if choice == "b":
        print("\n🚀 开始批量生成...")
        results = agent.batch_generate()
        print(f"✅ 完成！共生成 {results['statistics']['total_pieces']} 条内容")
    elif choice == "0":
        topic = input("请输入主题: ").strip()
        if topic:
            platform = input("目标平台 (小红书/抖音/微博/B站/微信公众号，默认小红书): ").strip() or "小红书"
            types_input = input("内容类型 (1=文案 2=图片描述 3=视频脚本, 逗号分隔，默认1,2,3): ").strip()
            type_map = {"1": "文案", "2": "图片描述", "3": "视频脚本"}
            content_types = [type_map.get(x.strip(), "文案") for x in types_input.split(",")] if types_input else ["文案", "图片描述", "视频脚本"]

            results = agent.generate_content(topic, content_types=content_types, target_platform=platform)
            for c in results:
                print(f"\n{'='*40}")
                print(f"【{c.content_type}】{c.title}")
                print(f"{'='*40}")
                print(c.body)
    else:
        idx = int(choice) - 1 if choice else 0
        topic = quick_topics[idx] if 0 <= idx < len(quick_topics) else quick_topics[0]
        print(f"\n🎯 主题: {topic}")
        results = agent.generate_content(topic, content_types=["文案", "图片描述", "视频脚本"])
        for c in results:
            print(f"\n{'='*40}")
            print(f"【{c.content_type}】{c.title}")
            print(f"标签: {', '.join(c.tags)}")
            print(f"{'='*40}")
            print(c.body[:800])
            if len(c.body) > 800:
                print(f"\n... (共{c.word_count}字，已截断)")

    # 合规检查
    print("\n" + "="*40)
    if choice not in ["b", "0"]:
        check = agent.compliance_check(results[0].body if results else "")
        print(f"合规性评分: {check['score']}/100")
        if check['issues']:
            print(f"问题: {check['issues']}")
        if check['warnings']:
            print(f"提示: {check['warnings']}")


if __name__ == "__main__":
    main()
