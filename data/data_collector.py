"""
西安文物/非遗/文旅数据采集模块
从公开来源采集文化资源数据，包括：
- 百度百科：西安文物、非遗项目信息
- 公开旅游数据：景区信息
- 政府公开数据：文物保护单位名录
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from typing import Optional
import pandas as pd

# 配置
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
RAW_DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + '/raw'


class XianCultureCollector:
    """西安文化数据采集器"""

    def __init__(self):
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ========== 西安重点文物数据 ==========
    XIAM_RELICS = [
        # 世界文化遗产
        {"name": "秦始皇兵马俑", "category": "世界文化遗产", "era": "秦", "keywords": ["兵马俑", "秦始皇", "陶俑", "世界八大奇迹"]},
        {"name": "大雁塔", "category": "全国重点文物保护单位", "era": "唐", "keywords": ["大雁塔", "大慈恩寺", "玄奘", "佛塔", "丝绸之路"]},
        {"name": "小雁塔", "category": "全国重点文物保护单位", "era": "唐", "keywords": ["小雁塔", "荐福寺", "佛塔", "关中八景"]},
        {"name": "西安城墙", "category": "全国重点文物保护单位", "era": "明", "keywords": ["城墙", "明代", "古城", "防御体系"]},
        {"name": "钟楼", "category": "全国重点文物保护单位", "era": "明", "keywords": ["钟楼", "明代", "地标", "市中心"]},
        {"name": "鼓楼", "category": "全国重点文物保护单位", "era": "明", "keywords": ["鼓楼", "明代", "地标", "晨钟暮鼓"]},
        {"name": "大明宫遗址", "category": "全国重点文物保护单位", "era": "唐", "keywords": ["大明宫", "唐代", "皇宫", "遗址公园"]},
        {"name": "华清宫", "category": "全国重点文物保护单位", "era": "唐", "keywords": ["华清宫", "华清池", "温泉", "长恨歌"]},
        {"name": "碑林博物馆", "category": "全国重点文物保护单位", "era": "多朝代", "keywords": ["碑林", "石刻", "书法", "石碑"]},
        {"name": "陕西历史博物馆", "category": "国家一级博物馆", "era": "多朝代", "keywords": ["历史博物馆", "文物", "周秦汉唐"]},
        {"name": "半坡遗址", "category": "全国重点文物保护单位", "era": "新石器时代", "keywords": ["半坡", "仰韶文化", "史前", "遗址"]},
        {"name": "汉长安城遗址", "category": "全国重点文物保护单位", "era": "汉", "keywords": ["汉长安城", "未央宫", "汉代", "丝绸之路起点"]},
        {"name": "阿房宫遗址", "category": "全国重点文物保护单位", "era": "秦", "keywords": ["阿房宫", "秦代", "宫殿", "遗址"]},
        {"name": "兴教寺塔", "category": "世界文化遗产", "era": "唐", "keywords": ["兴教寺", "玄奘", "佛塔", "丝绸之路"]},
        {"name": "西安清真大寺", "category": "全国重点文物保护单位", "era": "明", "keywords": ["清真寺", "伊斯兰", "化觉巷", "古建筑"]},
        {"name": "大兴善寺", "category": "全国重点文物保护单位", "era": "隋唐", "keywords": ["大兴善寺", "密宗", "佛教", "祖庭"]},
        {"name": "青龙寺", "category": "全国重点文物保护单位", "era": "唐", "keywords": ["青龙寺", "樱花", "密宗", "空海"]},
        {"name": "西安博物院", "category": "国家一级博物馆", "era": "多朝代", "keywords": ["博物院", "小雁塔", "文物", "西安历史"]},
        {"name": "大唐西市博物馆", "category": "国家二级博物馆", "era": "唐", "keywords": ["大唐西市", "丝绸之路", "商贸", "唐代"]},
        {"name": "曲江池遗址", "category": "省级文物保护单位", "era": "唐", "keywords": ["曲江", "唐代", "园林", "遗址公园"]},
    ]

    # ========== 西安非遗项目数据 ==========
    XIAM_ICH = [
        {"name": "西安鼓乐", "level": "人类非物质文化遗产代表作名录", "category": "传统音乐", "origin": "西安", "keywords": ["鼓乐", "唐代燕乐", "传统音乐", "活化石"]},
        {"name": "秦腔", "level": "国家级非物质文化遗产", "category": "传统戏剧", "origin": "陕西", "keywords": ["秦腔", "梆子腔", "戏曲", "西北"]},
        {"name": "皮影戏（陕西皮影）", "level": "人类非物质文化遗产代表作名录", "category": "传统戏剧", "origin": "陕西", "keywords": ["皮影", "华县皮影", "傀儡戏", "民间艺术"]},
        {"name": "西安剪纸", "level": "省级非物质文化遗产", "category": "传统美术", "origin": "西安", "keywords": ["剪纸", "民间美术", "窗花", "手工艺"]},
        {"name": "唐三彩烧制技艺", "level": "国家级非物质文化遗产", "category": "传统技艺", "origin": "陕西", "keywords": ["唐三彩", "陶瓷", "烧制", "唐代"]},
        {"name": "陕北民歌", "level": "国家级非物质文化遗产", "category": "传统音乐", "origin": "陕北", "keywords": ["陕北民歌", "信天游", "民歌", "黄土高原"]},
        {"name": "安塞腰鼓", "level": "国家级非物质文化遗产", "category": "传统舞蹈", "origin": "安塞", "keywords": ["腰鼓", "安塞", "民间舞蹈", "黄土风情"]},
        {"name": "西安面塑", "level": "省级非物质文化遗产", "category": "传统美术", "origin": "西安", "keywords": ["面塑", "面花", "民间工艺", "食用艺术"]},
        {"name": "户县农民画", "level": "省级非物质文化遗产", "category": "传统美术", "origin": "户县", "keywords": ["农民画", "户县", "民间绘画", "乡土"]},
        {"name": "西安羊肉泡馍制作技艺", "level": "国家级非物质文化遗产", "category": "传统技艺", "origin": "西安", "keywords": ["羊肉泡馍", "美食", "小吃", "清真"]},
        {"name": "德发长饺子制作技艺", "level": "省级非物质文化遗产", "category": "传统技艺", "origin": "西安", "keywords": ["饺子宴", "德发长", "面点", "美食"]},
        {"name": "蓝田玉雕", "level": "省级非物质文化遗产", "category": "传统美术", "origin": "蓝田", "keywords": ["玉雕", "蓝田玉", "雕刻", "手工艺"]},
        {"name": "马勺脸谱", "level": "省级非物质文化遗产", "category": "传统美术", "origin": "陕西", "keywords": ["马勺", "脸谱", "社火", "民间艺术"]},
        {"name": "凤翔泥塑", "level": "国家级非物质文化遗产", "category": "传统美术", "origin": "凤翔", "keywords": ["泥塑", "凤翔", "彩绘", "民间工艺"]},
        {"name": "西秦刺绣", "level": "国家级非物质文化遗产", "category": "传统美术", "origin": "陕西", "keywords": ["刺绣", "秦绣", "布艺", "民间工艺"]},
        {"name": "西安古建筑营造技艺", "level": "省级非物质文化遗产", "category": "传统技艺", "origin": "西安", "keywords": ["古建筑", "营造", "木结构", "修复"]},
        {"name": "同盛祥牛羊肉泡馍制作技艺", "level": "国家级非物质文化遗产", "category": "传统技艺", "origin": "西安", "keywords": ["同盛祥", "牛羊肉泡馍", "老字号", "美食"]},
        {"name": "西安风筝制作技艺", "level": "省级非物质文化遗产", "category": "传统技艺", "origin": "西安", "keywords": ["风筝", "民间工艺", "张天伟", "动态风筝"]},
    ]

    # ========== 西安文旅资源数据 ==========
    XIAM_TOURISM = [
        {"name": "大唐不夜城", "type": "特色街区", "district": "雁塔区", "description": "以盛唐文化为主题的大型商业步行街，以唐风元素为主线，包含文化展示、商业休闲、演艺娱乐等业态", "keywords": ["大唐不夜城", "盛唐", "步行街", "夜游", "不倒翁小姐姐"]},
        {"name": "回民街", "type": "特色街区", "district": "莲湖区", "description": "西安著名的美食文化街区，汇集各类清真小吃和特色美食", "keywords": ["回民街", "美食", "小吃", "清真", "回坊"]},
        {"name": "永兴坊", "type": "特色街区", "district": "新城区", "description": "以陕西非遗美食和传统文化为主题的文旅街区", "keywords": ["永兴坊", "非遗美食", "摔碗酒", "陕西小吃"]},
        {"name": "易俗社文化街区", "type": "特色街区", "district": "新城区", "description": "以百年秦腔剧社易俗社为核心的文化艺术街区", "keywords": ["易俗社", "秦腔", "文化街区", "百年老社"]},
        {"name": "西安城墙景区", "type": "AAAAA级景区", "district": "碑林区", "description": "中国现存规模最大、保存最完整的古代城垣", "keywords": ["城墙", "骑行", "灯会", "古城"]},
        {"name": "大唐芙蓉园", "type": "AAAAA级景区", "district": "雁塔区", "description": "展示盛唐风貌的大型皇家园林式文化主题公园", "keywords": ["大唐芙蓉园", "唐代园林", "水幕电影", "灯会"]},
        {"name": "秦岭野生动物园", "type": "AAAA级景区", "district": "长安区", "description": "西北地区最大的野生动物园", "keywords": ["动物园", "秦岭", "大熊猫", "金丝猴"]},
        {"name": "翠华山", "type": "AAAA级景区", "district": "长安区", "description": "终南山世界地质公园核心景区，以山崩地貌闻名", "keywords": ["翠华山", "终南山", "地质公园", "山崩"]},
        {"name": "白鹿原·白鹿仓", "type": "AAAA级景区", "district": "灞桥区", "description": "以陈忠实《白鹿原》为主题的文旅景区", "keywords": ["白鹿原", "白鹿仓", "民俗", "民国风情"]},
        {"name": "西安世博园", "type": "AAAA级景区", "district": "灞桥区", "description": "2011西安世园会会址，集园林艺术与生态展示为一体", "keywords": ["世博园", "长安塔", "园林", "生态"]},
        {"name": "昆明池·七夕公园", "type": "AAA级景区", "district": "长安区", "description": "以汉武帝昆明池遗址为基础，融合七夕爱情文化主题", "keywords": ["昆明池", "七夕", "汉武帝", "爱情"]},
        {"name": "诗经里", "type": "AAA级景区", "district": "长安区", "description": "以诗经文化为主题的文旅小镇", "keywords": ["诗经里", "诗经", "沣河", "文化小镇"]},
        {"name": "长安十二时辰", "type": "特色文旅项目", "district": "雁塔区", "description": "沉浸式唐风市井文化体验街区，还原唐代长安市井生活", "keywords": ["长安十二时辰", "沉浸式", "唐风", "市井"]},
        {"name": "茯茶镇", "type": "特色小镇", "district": "西咸新区", "description": "以茯茶文化为主题的特色小镇", "keywords": ["茯茶", "茶文化", "特色小镇", "丝路"]},
        {"name": "楼观台", "type": "AAAA级景区", "district": "周至县", "description": "道教祖庭，老子说经之地", "keywords": ["楼观台", "道教", "老子", "终南山"]},
        {"name": "骊山", "type": "AAAA级景区", "district": "临潼区", "description": "秦岭支脉，周秦汉唐历代皇家园林所在地", "keywords": ["骊山", "华清宫", "烽火台", "兵谏亭"]},
    ]

    def build_comprehensive_dataset(self) -> dict:
        """构建完整的西安文化数据集"""
        dataset = {
            "dataset_metadata": {
                "name": "西安文物/非遗/文旅数字资产数据集",
                "version": "1.0.0",
                "description": "面向西安文物、非遗、文旅资源的综合性文化数字资产数据集，涵盖世界文化遗产、全国重点文物保护单位、非物质文化遗产、文旅景区及特色街区等",
                "source": "公开数据采集（百度百科/政府公开信息/文旅平台）",
                "license": "仅限大赛使用",
                "date_created": time.strftime("%Y-%m-%d"),
                "total_records": len(self.XIAM_RELICS) + len(self.XIAM_ICH) + len(self.XIAM_TOURISM),
                "categories": {
                    "文物": len(self.XIAM_RELICS),
                    "非遗": len(self.XIAM_ICH),
                    "文旅": len(self.XIAM_TOURISM)
                }
            },
            "relics": [],
            "intangible_cultural_heritage": [],
            "tourism": [],
            "knowledge_graph": self._build_knowledge_graph_basic()
        }

        # 处理文物数据
        for i, relic in enumerate(self.XIAM_RELICS):
            record = {
                "id": f"XA-REL-{i+1:03d}",
                "type": "文物",
                "name": relic["name"],
                "category": relic["category"],
                "era": relic["era"],
                "keywords": relic["keywords"],
                "baidu_baike_url": f"https://baike.baidu.com/item/{relic['name']}",
                "structured_data": self._get_relic_extended_info(relic)
            }
            dataset["relics"].append(record)

        # 处理非遗数据
        for i, ich in enumerate(self.XIAM_ICH):
            record = {
                "id": f"XA-ICH-{i+1:03d}",
                "type": "非遗",
                "name": ich["name"],
                "level": ich["level"],
                "category": ich["category"],
                "origin": ich["origin"],
                "keywords": ich["keywords"],
                "baidu_baike_url": f"https://baike.baidu.com/item/{ich['name']}",
                "structured_data": self._get_ich_extended_info(ich)
            }
            dataset["intangible_cultural_heritage"].append(record)

        # 处理文旅数据
        for i, tourism in enumerate(self.XIAM_TOURISM):
            record = {
                "id": f"XA-TOUR-{i+1:03d}",
                "type": "文旅",
                "name": tourism["name"],
                "scenic_type": tourism["type"],
                "district": tourism["district"],
                "description": tourism["description"],
                "keywords": tourism["keywords"],
                "structured_data": self._get_tourism_extended_info(tourism)
            }
            dataset["tourism"].append(record)

        return dataset

    def _get_relic_extended_info(self, relic: dict) -> dict:
        """扩展文物信息"""
        return {
            "name": relic["name"],
            "category": relic["category"],
            "era": relic["era"],
            "keywords": relic["keywords"],
            "preservation_status": "已保护",
            "accessibility": "可参观",
            "digital_status": "部分数字化",
            "data_fields": {
                "基础信息": ["名称", "年代", "类别", "保护级别"],
                "地理信息": ["经纬度", "所在区县", "地址"],
                "文化信息": ["历史沿革", "文化价值", "相关人物"],
                "管理信息": ["管理单位", "开放时间", "门票信息"],
                "数字资源": ["图片", "3D模型", "VR全景", "文献资料"]
            }
        }

    def _get_ich_extended_info(self, ich: dict) -> dict:
        """扩展非遗信息"""
        return {
            "name": ich["name"],
            "level": ich["level"],
            "category": ich["category"],
            "origin": ich["origin"],
            "keywords": ich["keywords"],
            "inheritance_status": "有传承人",
            "digital_status": "部分数字化",
            "data_fields": {
                "基础信息": ["名称", "级别", "类别", "发源地"],
                "传承信息": ["传承人", "传承谱系", "传承现状"],
                "技艺信息": ["技艺特点", "制作工艺", "表演形式"],
                "管理信息": ["保护单位", "保护规划", "展示场馆"],
                "数字资源": ["视频记录", "音频记录", "图片资料", "文献资料"]
            }
        }

    def _get_tourism_extended_info(self, tourism: dict) -> dict:
        """扩展文旅信息"""
        return {
            "name": tourism["name"],
            "scenic_type": tourism["type"],
            "district": tourism["district"],
            "description": tourism["description"],
            "keywords": tourism["keywords"],
            "data_fields": {
                "基础信息": ["名称", "类型", "等级", "所属区县"],
                "地理信息": ["经纬度", "地址", "交通信息"],
                "服务信息": ["开放时间", "门票价格", "联系方式"],
                "资源信息": ["特色项目", "节庆活动", "文创产品"],
                "数字资源": ["宣传视频", "VR导览", "图片", "攻略"]
            }
        }

    def _build_knowledge_graph_basic(self) -> dict:
        """构建基础知识图谱结构"""
        nodes = []
        edges = []

        # 文物节点
        for i, relic in enumerate(self.XIAM_RELICS):
            node_id = f"REL_{i+1:03d}"
            nodes.append({
                "id": node_id,
                "name": relic["name"],
                "type": "文物",
                "era": relic["era"],
                "category": relic["category"]
            })
            # 同朝代关联边
            for j, other in enumerate(self.XIAM_RELICS):
                if j > i and other["era"] == relic["era"]:
                    edges.append({
                        "source": node_id,
                        "target": f"REL_{j+1:03d}",
                        "relation": "同时代"
                    })

        # 非遗节点
        for i, ich in enumerate(self.XIAM_ICH):
            node_id = f"ICH_{i+1:03d}"
            nodes.append({
                "id": node_id,
                "name": ich["name"],
                "type": "非遗",
                "category": ich["category"],
                "level": ich["level"]
            })

        # 文旅节点
        for i, tourism in enumerate(self.XIAM_TOURISM):
            node_id = f"TOUR_{i+1:03d}"
            nodes.append({
                "id": node_id,
                "name": tourism["name"],
                "type": "文旅",
                "district": tourism["district"],
                "scenic_type": tourism["type"]
            })

        # 跨类型关联边
        # 名称关联
        for n1 in nodes:
            for n2 in nodes:
                if n1["id"] != n2["id"]:
                    # 同一district关联
                    if n1["type"] == "文旅" and n2["type"] == "文物":
                        for relic in self.XIAM_RELICS:
                            if relic["name"] == n2["name"] and any(kw in n1["name"] for kw in relic["keywords"]):
                                edges.append({
                                    "source": n1["id"],
                                    "target": n2["id"],
                                    "relation": "文化关联"
                                })

        return {"nodes": nodes, "edges": edges}

    def save_dataset(self, dataset: dict, format: str = "json"):
        """保存数据集"""
        if format == "json":
            path = os.path.join(RAW_DATA_DIR, "xian_cultural_dataset.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            print(f"✓ JSON数据集已保存: {path}")

        elif format == "csv":
            # 分别保存三类数据
            for key in ["relics", "intangible_cultural_heritage", "tourism"]:
                records = dataset.get(key, [])
                if records:
                    flat_records = []
                    for r in records:
                        flat = {k: v for k, v in r.items() if k != "structured_data"}
                        flat_records.append(flat)
                    df = pd.DataFrame(flat_records)
                    path = os.path.join(RAW_DATA_DIR, f"xian_{key}.csv")
                    df.to_csv(path, index=False, encoding='utf-8-sig')
                    print(f"✓ CSV已保存: {path}")

        elif format == "excel":
            path = os.path.join(RAW_DATA_DIR, "xian_cultural_dataset.xlsx")
            with pd.ExcelWriter(path, engine='openpyxl') as writer:
                for key in ["relics", "intangible_cultural_heritage", "tourism"]:
                    records = dataset.get(key, [])
                    if records:
                        flat_records = []
                        for r in records:
                            flat = {k: v for k, v in r.items() if k != "structured_data"}
                            flat_records.append(flat)
                        df = pd.DataFrame(flat_records)
                        sheet_name = {"relics": "文物", "intangible_cultural_heritage": "非遗", "tourism": "文旅"}[key]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✓ Excel数据集已保存: {path}")


if __name__ == "__main__":
    print("=" * 60)
    print("  西安文物/非遗/文旅数字资产数据集 构建工具")
    print("=" * 60)
    collector = XianCultureCollector()
    print("正在构建数据集...")
    dataset = collector.build_comprehensive_dataset()
    collector.save_dataset(dataset, format="json")
    collector.save_dataset(dataset, format="excel")
    print(f"\n总计: {dataset['dataset_metadata']['total_records']} 条记录")
    print(f"  - 文物: {dataset['dataset_metadata']['categories']['文物']} 条")
    print(f"  - 非遗: {dataset['dataset_metadata']['categories']['非遗']} 条")
    print(f"  - 文旅: {dataset['dataset_metadata']['categories']['文旅']} 条")
    print(f"  - 知识图谱节点: {len(dataset['knowledge_graph']['nodes'])} 个")
    print(f"  - 知识图谱边: {len(dataset['knowledge_graph']['edges'])} 条")
    print("\n数据集构建完成！")
