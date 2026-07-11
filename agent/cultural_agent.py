"""
西安文化内容创作智能体 (Cultural Content Creation Agent)
功能：
1. 文化数据智能分类与标注
2. 文化要素提取与关键词标签生成
3. 多模态内容生成（文案、图片、视频脚本）
4. 内容合规性检查（文博/非遗传播规范）
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# 尝试导入OpenAI SDK
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("[!] OpenAI SDK未安装，将使用基于规则的生成模式")

# 项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ========== 数据模型 ==========

class CulturalElement(BaseModel):
    """文化要素模型"""
    element_type: str = Field(description="要素类型：人物/事件/朝代/技艺/符号/地点")
    name: str = Field(description="要素名称")
    significance: str = Field(description="文化意义")
    confidence: float = Field(description="识别置信度", ge=0.0, le=1.0)


class KeywordTag(BaseModel):
    """关键词标签模型"""
    tag: str = Field(description="标签内容")
    category: str = Field(description="标签类别：文物/非遗/美食/历史/地理/艺术/建筑")
    weight: float = Field(description="标签权重", ge=0.0, le=1.0)


class ContentPiece(BaseModel):
    """内容片段模型"""
    content_type: str = Field(description="内容类型：文案/图片描述/视频脚本/社交媒体")
    title: str = Field(description="内容标题")
    body: str = Field(description="内容正文")
    tags: List[str] = Field(description="关联标签")
    cultural_elements: List[str] = Field(description="文化要素")
    target_platform: str = Field(description="目标平台")
    word_count: int = Field(description="字数")


# ========== 核心智能体 ==========

class CulturalContentAgent:
    """文化内容创作智能体"""

    SYSTEM_PROMPT = """你是一位精通西安历史文化的数字人文专家和内容创作专家。
你的职责是：
1. 对西安文物、非遗、文旅资源进行专业分类和标注
2. 提取文化要素，挖掘文化内涵
3. 生成符合文博/非遗传播规范的多模态内容（文案、图片提示词、视频脚本）
4. 确保内容尊重历史事实，弘扬中华优秀传统文化

内容生成原则：
- 准确性：基于真实的历史文化知识，不编造
- 规范性：符合文物保护和文化遗产传播的规范要求
- 吸引力：内容生动有趣，适合大众传播
- 教育性：传递正确的历史文化知识
- 版权意识：不侵犯他人知识产权

输出格式要求：
- 文案类：提供可直接使用的文稿
- 图片类：提供详细的图片生成提示词（英文+中文）
- 视频类：提供分镜头脚本"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com"

        if HAS_OPENAI and self.api_key:
            # 清除代理环境变量以避免SOCKS冲突
            for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
                os.environ.pop(k, None)
            try:
                from httpx import Client
                import httpx
                http_client = httpx.Client(proxy=None)
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, http_client=http_client)
            except:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self.model = "deepseek-chat"
            self.use_ai = True
            print(f"[OK] 智能体已连接AI模型: {self.model}")
        else:
            self.use_ai = False
            print("[!] 使用基于规则的生成模式（未配置API Key）")

        # 加载数据集
        self.dataset = self._load_dataset()
        self.content_history = []

    def _load_dataset(self) -> dict:
        """加载处理后的数据集"""
        dataset_path = os.path.join(DATA_DIR, 'xian_cultural_dataset_processed.json')
        if os.path.exists(dataset_path):
            with open(dataset_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        # 尝试原始数据
        raw_path = os.path.join(BASE_DIR, 'data', 'raw', 'xian_cultural_dataset.json')
        if os.path.exists(raw_path):
            with open(raw_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    # ========== 功能1：智能分类与标注 ==========

    def classify_and_tag(self, text: str) -> Dict[str, Any]:
        """对输入文本进行文化分类和关键词标注"""
        if self.use_ai:
            return self._ai_classify(text)
        return self._rule_classify(text)

    def _ai_classify(self, text: str) -> Dict[str, Any]:
        """使用AI进行分类和标注"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"""请对以下关于西安文化的内容进行分类和标注：

内容：{text}

请输出JSON格式：
{{
  "category": "文物/非遗/文旅/综合",
  "sub_category": "细分类别",
  "era": "涉及朝代",
  "keywords": ["关键词1", "关键词2", ...],
  "cultural_elements": [{{"element_type": "类型", "name": "名称", "significance": "意义", "confidence": 0.9}}],
  "sentiment": "正面/中性/负面",
  "compliance_check": {{"is_compliant": true, "issues": []}},
  "suggested_tags": ["标签1", "标签2", ...]
}}"""}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            content = response.choices[0].message.content
            # 尝试提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            return json.loads(content.strip())
        except Exception as e:
            print(f"AI分类出错: {e}，回退到规则模式")
            return self._rule_classify(text)

    def _rule_classify(self, text: str) -> Dict[str, Any]:
        """基于规则的分类和标注"""
        result = {
            "category": "综合",
            "sub_category": "",
            "era": "",
            "keywords": [],
            "cultural_elements": [],
            "sentiment": "中性",
            "compliance_check": {"is_compliant": True, "issues": []},
            "suggested_tags": []
        }

        # 关键词匹配
        category_keywords = {
            "文物": ["兵马俑", "大雁塔", "城墙", "钟楼", "鼓楼", "碑林", "博物馆", "遗址", "古墓",
                    "宫殿", "佛塔", "石刻", "青铜器", "陶俑", "唐三彩"],
            "非遗": ["鼓乐", "秦腔", "皮影", "剪纸", "面塑", "泥塑", "民歌", "腰鼓",
                    "刺绣", "风筝", "脸谱", "农民画", "泡馍", "饺子宴"],
            "文旅": ["不夜城", "回民街", "芙蓉园", "永兴坊", "白鹿原", "秦岭", "华山",
                    "昆明池", "诗经里", "小镇", "街区", "景区", "打卡", "旅游"]
        }

        era_keywords = {
            "秦": ["秦", "兵马俑", "秦始皇", "阿房宫"],
            "唐": ["唐", "大明宫", "大雁塔", "华清宫", "长安", "芙蓉园", "曲江"],
            "明": ["明", "城墙", "钟楼", "鼓楼"],
            "汉": ["汉", "长安城", "未央宫", "汉武帝"],
        }

        matched_categories = []
        for cat, kws in category_keywords.items():
            if any(kw in text for kw in kws):
                matched_categories.append(cat)
                result["keywords"].extend([kw for kw in kws if kw in text])

        if matched_categories:
            result["category"] = matched_categories[0]
            if len(matched_categories) > 1:
                result["category"] = "综合"
                result["sub_category"] = "/".join(matched_categories)

        for era, kws in era_keywords.items():
            if any(kw in text for kw in kws):
                result["era"] = era
                break

        result["suggested_tags"] = list(set(result["keywords"]))
        return result

    # ========== 功能2：文化要素提取 ==========

    def extract_cultural_elements(self, text: str) -> List[CulturalElement]:
        """从文本中提取文化要素"""
        elements = []

        # 人物要素
        figure_patterns = {
            "秦始皇": "中国第一位皇帝，统一六国",
            "玄奘": "唐代高僧，大慈恩寺首任住持，西行取经",
            "李白": "唐代诗仙，曾居长安",
            "杜甫": "唐代诗圣，在长安生活十年",
            "杨贵妃": "唐玄宗贵妃，与华清宫密切相关",
            "汉武帝": "汉代皇帝，开疆拓土",
            "老子": "道家创始人，楼观台讲经",
            "空海": "日本遣唐僧，青龙寺学法",
        }
        for name, desc in figure_patterns.items():
            if name in text:
                elements.append(CulturalElement(
                    element_type="人物",
                    name=name,
                    significance=desc,
                    confidence=0.95
                ))

        # 地点要素
        place_patterns = {
            "兵马俑": "世界第八大奇迹，秦代军事陶俑群",
            "大雁塔": "唐代佛塔，玄奘译经之所，丝绸之路地标",
            "城墙": "中国现存最完整的古代城垣",
            "华清宫": "唐代皇家温泉园林",
            "回民街": "西安美食文化街区",
            "大唐不夜城": "盛唐文化主题商业街区",
        }
        for name, desc in place_patterns.items():
            if name in text:
                elements.append(CulturalElement(
                    element_type="地点",
                    name=name,
                    significance=desc,
                    confidence=0.9
                ))

        return elements

    # ========== 功能3：多模态内容生成 ==========

    def generate_content(self, topic: str, content_types: List[str] = None,
                         target_platform: str = "小红书") -> List[ContentPiece]:
        """生成多模态内容"""
        if content_types is None:
            content_types = ["文案", "图片描述", "视频脚本"]

        results = []

        for ctype in content_types:
            if self.use_ai:
                content = self._ai_generate(topic, ctype, target_platform)
            else:
                content = self._rule_generate(topic, ctype, target_platform)
            results.append(content)

        self.content_history.extend(results)
        return results

    def _ai_generate(self, topic: str, content_type: str, platform: str) -> ContentPiece:
        """使用AI生成内容"""
        platform_specs = {
            "小红书": "字数1000以内，风格亲切活泼，多用emoji，带#话题标签",
            "抖音": "简洁有力，3-5句话，强调视觉冲击",
            "微信公众号": "深度长文，800-2000字，严谨专业",
            "微博": "140字以内，话题性强，适合传播",
            "B站": "弹幕文化，互动性强，可加入梗和二次元元素",
        }

        content_type_specs = {
            "文案": "生成可直接发布的完整文案",
            "图片描述": "生成适用于AI图像生成的详细提示词（中文+英文），包含构图、风格、色彩指导",
            "视频脚本": "生成分镜头脚本，包含镜头号、画面描述、旁白/对白、时长、运镜方式",
            "社交媒体": "生成适合社交媒体的短内容，包含互动引导",
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"""请为以下西安文化主题生成{content_type}：

主题：{topic}
目标平台：{platform}
平台要求：{platform_specs.get(platform, "")}
内容类型要求：{content_type_specs.get(content_type, "")}

请输出JSON格式：
{{
  "title": "内容标题",
  "body": "完整内容正文",
  "tags": ["标签1", "标签2"],
  "cultural_elements": ["文化要素1"],
  "word_count": 字数
}}"""}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            data = json.loads(content.strip())

            return ContentPiece(
                content_type=content_type,
                title=data.get("title", f"关于{topic}的{content_type}"),
                body=data.get("body", ""),
                tags=data.get("tags", []),
                cultural_elements=data.get("cultural_elements", []),
                target_platform=platform,
                word_count=data.get("word_count", len(data.get("body", "")))
            )
        except Exception as e:
            print(f"AI生成出错: {e}，回退到规则模式")
            return self._rule_generate(topic, content_type, platform)

    def _rule_generate(self, topic: str, content_type: str, platform: str) -> ContentPiece:
        """基于规则的内容生成（无需API）"""
        # 查找相关数据
        related_data = self._find_related_data(topic)

        if content_type == "文案":
            return self._generate_copy(topic, related_data, platform)
        elif content_type == "图片描述":
            return self._generate_image_prompt(topic, related_data)
        elif content_type == "视频脚本":
            return self._generate_video_script(topic, related_data)
        else:
            return self._generate_social(topic, related_data, platform)

    def _find_related_data(self, topic: str) -> Dict:
        """查找与主题相关的数据"""
        related = {"relics": [], "ich": [], "tourism": []}
        for category, key in [("relics", "relics"), ("ich", "intangible_cultural_heritage"), ("tourism", "tourism")]:
            for item in self.dataset.get(key, []):
                name = item.get("name", "")
                keywords = item.get("keywords", [])
                if topic in name or any(kw in topic for kw in keywords) or topic in " ".join(keywords):
                    related[category].append(item)
        return related

    def _generate_copy(self, topic: str, data: Dict, platform: str) -> ContentPiece:
        """生成文案"""
        parts = []
        tags = []

        # 标题
        parts.append(f"【{topic}】探秘千年古都的文化瑰宝 ✨\n")

        # 文物相关
        if data["relics"]:
            parts.append("🏛️ 【文物古迹】")
            for r in data["relics"][:3]:
                name = r["name"]
                era = r.get("era", "")
                parts.append(f"📍 {name}（{era}）")
                tags.append(name)
            parts.append("")

        # 非遗相关
        if data["ich"]:
            parts.append("🎭 【非遗传承】")
            for ich in data["ich"][:3]:
                name = ich["name"]
                level = ich.get("level", "")
                parts.append(f"🔸 {name} | {level}")
                tags.append(name)
            parts.append("")

        # 文旅相关
        if data["tourism"]:
            parts.append("🎪 【文旅体验】")
            for t in data["tourism"][:3]:
                name = t["name"]
                desc = t.get("description", "")[:80]
                parts.append(f"🎯 {name}")
                if desc:
                    parts.append(f"   {desc}...")
                tags.append(name)
            parts.append("")

        # 结尾
        parts.append("—" * 30)
        parts.append("💡 来西安，穿越千年，感受中华文明的璀璨光芒 ✨")
        parts.append("")
        if platform == "小红书":
            parts.append(" ".join([f"#{t}" for t in tags[:5]]) + " #西安旅游 #文化传承 #非遗 #文物")

        body = "\n".join(parts)

        return ContentPiece(
            content_type="文案",
            title=f"探秘千年古都 | {topic}",
            body=body,
            tags=list(set(tags)),
            cultural_elements=[topic],
            target_platform=platform,
            word_count=len(body)
        )

    def _generate_image_prompt(self, topic: str, data: Dict) -> ContentPiece:
        """生成AI图像提示词"""
        prompts = []

        # 根据数据生成不同风格图片提示
        if data["relics"]:
            relic = data["relics"][0]
            prompts.append({
                "style": "写实摄影风",
                "zh": f"西安{relic['name']}，{relic.get('era', '')}古建筑/文物，阳光明媚，蓝天白云，广角镜头，高清摄影，细节清晰，文化氛围",
                "en": f"Xi'an {relic['name']}, {relic.get('era', '')} ancient Chinese architecture/cultural relic, sunny day, blue sky, wide angle lens, high resolution photography, detailed, cultural atmosphere, 8K"
            })

        if data["ich"]:
            ich = data["ich"][0]
            prompts.append({
                "style": "艺术插画风",
                "zh": f"{ich['name']}非遗艺术表演，中国传统风格插画，水墨风格，动态姿态，文化传承，精美细节，暖色调",
                "en": f"{ich['name']} intangible cultural heritage performance, Chinese traditional style illustration, ink wash painting style, dynamic pose, cultural heritage, exquisite details, warm tones"
            })

        if data["tourism"]:
            tourism = data["tourism"][0]
            prompts.append({
                "style": "夜景氛围风",
                "zh": f"{tourism['name']}夜景，华灯初上，唐风建筑，人潮涌动，热闹氛围，长曝光摄影，璀璨灯光",
                "en": f"{tourism['name']} at night, evening lights, Tang Dynasty style architecture, bustling crowd, lively atmosphere, long exposure photography, brilliant lights"
            })

        # 通用提示词
        if not prompts:
            prompts.append({
                "style": "国风插画风",
                "zh": f"西安{topic}，中国传统文化主题，国风插画，精美细节，暖色调，古都韵味，艺术感",
                "en": f"Xi'an {topic}, Chinese traditional culture theme, Chinese style illustration, exquisite details, warm tones, ancient capital charm, artistic"
            })

        body = json.dumps(prompts, ensure_ascii=False, indent=2)

        return ContentPiece(
            content_type="图片描述",
            title=f"AI图像生成提示词 | {topic}",
            body=body,
            tags=[p["style"] for p in prompts],
            cultural_elements=[topic],
            target_platform="AI图像生成工具",
            word_count=len(body)
        )

    def _generate_video_script(self, topic: str, data: Dict) -> ContentPiece:
        """生成视频分镜头脚本"""
        script = []

        # 开场
        script.append({
            "shot": 1,
            "scene": "开场全景",
            "duration": "5s",
            "camera": "航拍推近",
            "visual": "西安城市全景，从钟楼向四周展开，清晨薄雾中古城苏醒",
            "audio": "西安鼓乐前奏，悠远绵长",
            "narration": "这里是西安，一座承载着华夏文明三千年的古都。"
        })

        # 主体内容
        shot_num = 2
        for r in data["relics"][:2]:
            script.append({
                "shot": shot_num,
                "scene": f"文物展示 - {r['name']}",
                "duration": "4s",
                "camera": "中景推进→特写",
                "visual": f"{r['name']}不同角度展示，突出{', '.join(r.get('keywords', [])[:2])}等细节",
                "audio": "背景音乐渐强",
                "narration": f"{r['name']}，{r.get('era', '')}时期的瑰宝，见证了华夏文明的辉煌。"
            })
            shot_num += 1

        for ich in data["ich"][:2]:
            script.append({
                "shot": shot_num,
                "scene": f"非遗展示 - {ich['name']}",
                "duration": "5s",
                "camera": "特写+慢动作",
                "visual": f"{ich['name']}表演/制作过程，传承人手部特写",
                "audio": "融入非遗项目原声",
                "narration": f"{ich['name']}，{ich.get('level', '')}，传承千年的技艺。"
            })
            shot_num += 1

        for tourism in data["tourism"][:2]:
            script.append({
                "shot": shot_num,
                "scene": f"文旅体验 - {tourism['name']}",
                "duration": "4s",
                "camera": "手持跟拍+延时摄影",
                "visual": f"{tourism['name']}人潮涌动，灯火辉煌",
                "audio": "现代与传统融合BGM",
                "narration": f"在{tourism['name']}，感受古老与现代的交融。"
            })
            shot_num += 1

        # 结尾
        script.append({
            "shot": shot_num,
            "scene": "结尾升华",
            "duration": "8s",
            "camera": "升空远退→城市全景",
            "visual": "夜幕降临，西安城墙灯火璀璨，大雁塔在夜色中矗立",
            "audio": "音乐渐弱，余音绕梁",
            "narration": f"西安，每一块砖都有故事，每一种技艺都是传承。{topic}，等你来发现。"
        })

        body = json.dumps(script, ensure_ascii=False, indent=2)
        total_duration = sum(int(s["duration"].replace("s", "")) for s in script)

        return ContentPiece(
            content_type="视频脚本",
            title=f"短视频分镜头脚本 | {topic}",
            body=body,
            tags=["短视频", "分镜头脚本", topic],
            cultural_elements=[topic],
            target_platform="抖音/B站/视频号",
            word_count=len(body)
        )

    def _generate_social(self, topic: str, data: Dict, platform: str) -> ContentPiece:
        """生成社交媒体内容"""
        body = f"🏮 {topic}\n\n"
        body += f"📍 古城西安，藏着说不尽的故事...\n"
        body += f"💫 期待与你一起穿越千年，感受华夏之美\n"
        if platform == "微博":
            body += f"\n#西安# #{topic}# #文化传承# 转发抽三位送西安文创！"
        else:
            body += f"\n#西安 #文化 #旅游 #非遗 #{topic}"

        return ContentPiece(
            content_type="社交媒体",
            title=f"社交媒体内容 | {topic}",
            body=body,
            tags=[topic, "西安", "文化"],
            cultural_elements=[topic],
            target_platform=platform,
            word_count=len(body)
        )

    # ========== 批量生成 ==========

    def batch_generate(self, topics: List[str] = None) -> Dict[str, Any]:
        """批量生成多模态内容"""
        if topics is None:
            # 默认生成所有类型
            topics = [
                "秦始皇兵马俑",
                "大雁塔与丝绸之路",
                "西安城墙",
                "大唐不夜城",
                "西安鼓乐",
                "秦腔艺术",
                "回民街美食",
                "华清宫长恨歌",
            ]

        results = {
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_topics": len(topics),
            "contents": {},
            "statistics": {
                "total_pieces": 0,
                "by_type": {},
                "by_platform": {}
            }
        }

        for topic in topics:
            print(f"  生成: {topic}")
            contents = self.generate_content(topic, content_types=["文案", "图片描述", "视频脚本"])
            results["contents"][topic] = [
                {
                    "type": c.content_type,
                    "title": c.title,
                    "body": c.body,
                    "tags": c.tags,
                    "platform": c.target_platform,
                    "word_count": c.word_count
                }
                for c in contents
            ]
            results["statistics"]["total_pieces"] += len(contents)
            for c in contents:
                results["statistics"]["by_type"][c.content_type] = \
                    results["statistics"]["by_type"].get(c.content_type, 0) + 1

        # 保存
        output_path = os.path.join(OUTPUT_DIR, 'generated_contents.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 批量内容生成完成，共 {results['statistics']['total_pieces']} 条")
        print(f"  保存至: {output_path}")
        return results

    # ========== 合规性检查 ==========

    def compliance_check(self, content: str) -> Dict[str, Any]:
        """内容合规性检查 - 确保符合文博/非遗传播规范"""
        issues = []
        warnings = []

        # 敏感词检查
        sensitive_patterns = ["盗墓", "破坏", "私藏", "走私", "赝品", "假文物"]
        for pattern in sensitive_patterns:
            if pattern in content:
                issues.append(f"包含不当词汇: {pattern}")

        # 历史准确性提示
        historical_checks = {
            "唐朝": ["要注意区分不同时期，唐朝跨度近300年"],
            "兵马俑": ["注意准确描述：兵马俑是陶俑，不是石雕"],
            "丝绸之路": ["注意：丝绸之路是贸易路线网络，不仅是长安"],
        }
        for key, msgs in historical_checks.items():
            if key in content:
                for msg in msgs:
                    warnings.append(msg)

        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0, 100 - len(issues) * 15 - len(warnings) * 5),
            "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ========== 使用示例 ==========

if __name__ == "__main__":
    print("=" * 60)
    print("  西安文化内容创作智能体")
    print("=" * 60)

    agent = CulturalContentAgent()

    # 测试分类与标注
    print("\n[1] 智能分类与标注测试")
    result = agent.classify_and_tag("西安兵马俑是世界第八大奇迹，展示了秦朝的军事力量")
    print(f"  分类: {result.get('category')}")
    print(f"  关键词: {result.get('keywords', [])}")

    # 测试文化要素提取
    print("\n[2] 文化要素提取测试")
    elements = agent.extract_cultural_elements("玄奘法师在大雁塔翻译佛经，为丝绸之路文化交流做出了巨大贡献")
    for elem in elements:
        print(f"  - {elem.element_type}: {elem.name} ({elem.significance[:30]}...)")

    # 测试内容生成
    print("\n[3] 内容生成测试")
    contents = agent.generate_content("大雁塔", content_types=["文案", "图片描述"])
    for c in contents:
        print(f"\n  --- {c.content_type}: {c.title} ---")
        print(f"  字数: {c.word_count}")
        print(f"  标签: {c.tags}")
        # 打印前200字符
        preview = c.body[:200].replace('\n', ' ')
        print(f"  预览: {preview}...")

    # 合规性检查
    print("\n[4] 合规性检查")
    check = agent.compliance_check("兵马俑是秦朝的墓葬雕塑，位于西安临潼区")
    print(f"  合规: {check['is_compliant']}, 评分: {check['score']}")

    print("\n[OK] 智能体测试完成")
