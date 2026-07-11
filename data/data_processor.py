"""
西安文化数据集清洗与结构化处理模块
将原始数据转化为符合数字资产登记要求的标准化数据集
"""

import json
import os
import re
from typing import List, Dict, Any
from datetime import datetime

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw')
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')


class DataProcessor:
    """数据清洗与结构化处理器"""

    def __init__(self, dataset_path: str = None):
        os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

        if dataset_path is None:
            dataset_path = os.path.join(RAW_DATA_DIR, 'xian_cultural_dataset.json')

        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)

        self.cleaning_report = []

    def clean_and_structure(self) -> dict:
        """执行完整的数据清洗和结构化流程"""
        print("开始数据清洗与结构化处理...")

        # 1. 文本清洗
        print("  [1/5] 文本清洗...")
        self._clean_text()

        # 2. 去重
        print("  [2/5] 数据去重...")
        self._deduplicate()

        # 3. 标准化
        print("  [3/5] 字段标准化...")
        self._standardize_fields()

        # 4. 质量验证
        print("  [4/5] 质量验证...")
        self._validate_quality()

        # 5. 生成资产化元数据
        print("  [5/5] 生成数字资产元数据...")
        self._generate_asset_metadata()

        return self.dataset

    def _clean_text(self):
        """文本清洗"""
        for category in ["relics", "intangible_cultural_heritage", "tourism"]:
            for record in self.dataset.get(category, []):
                # 清洗name字段
                if "name" in record:
                    record["name"] = record["name"].strip()
                    # 移除多余空格
                    record["name"] = re.sub(r'\s+', '', record["name"].replace('(', '（').replace(')', '）'))

                # 清洗keywords
                if "keywords" in record:
                    record["keywords"] = [kw.strip() for kw in record["keywords"] if kw.strip()]

        self.cleaning_report.append("文本清洗完成：去除多余空格、规范化括号")

    def _deduplicate(self):
        """数据去重"""
        seen_names = set()
        for category in ["relics", "intangible_cultural_heritage", "tourism"]:
            unique_records = []
            for record in self.dataset.get(category, []):
                name = record.get("name", "")
                if name not in seen_names:
                    seen_names.add(name)
                    unique_records.append(record)
                else:
                    self.cleaning_report.append(f"去除重复记录: {name}")
            self.dataset[category] = unique_records

        self.cleaning_report.append(f"去重完成：当前唯一记录数 {len(seen_names)}")

    def _standardize_fields(self):
        """字段标准化 - 以符合数字资产登记要求"""
        # 文物数据标准化
        for record in self.dataset.get("relics", []):
            record["standardized"] = {
                "asset_type": "cultural_relic",
                "asset_level": self._normalize_protection_level(record.get("category", "")),
                "geographic_scope": "西安市",
                "time_period": record.get("era", ""),
                "data_completeness": self._calculate_completeness(record),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "standard_version": "1.0"
            }

        # 非遗数据标准化
        for record in self.dataset.get("intangible_cultural_heritage", []):
            record["standardized"] = {
                "asset_type": "intangible_cultural_heritage",
                "asset_level": self._normalize_ich_level(record.get("level", "")),
                "geographic_scope": record.get("origin", ""),
                "category": record.get("category", ""),
                "data_completeness": self._calculate_completeness(record),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "standard_version": "1.0"
            }

        # 文旅数据标准化
        for record in self.dataset.get("tourism", []):
            record["standardized"] = {
                "asset_type": "cultural_tourism",
                "asset_level": self._normalize_scenic_level(record.get("scenic_type", "")),
                "geographic_scope": f"西安市{record.get('district', '')}",
                "data_completeness": self._calculate_completeness(record),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "standard_version": "1.0"
            }

        self.cleaning_report.append("字段标准化完成：统一数字资产登记格式")

    def _normalize_protection_level(self, category: str) -> str:
        """标准化文物保级"""
        level_map = {
            "世界文化遗产": "国家级",
            "全国重点文物保护单位": "国家级",
            "国家一级博物馆": "国家级",
            "国家二级博物馆": "省级",
            "省级文物保护单位": "省级",
        }
        return level_map.get(category, "市县级")

    def _normalize_ich_level(self, level: str) -> str:
        """标准化非遗级别"""
        level_map = {
            "人类非物质文化遗产代表作名录": "世界级",
            "国家级非物质文化遗产": "国家级",
            "省级非物质文化遗产": "省级",
        }
        return level_map.get(level, "市县级")

    def _normalize_scenic_level(self, scenic_type: str) -> str:
        """标准化景区等级"""
        if "AAAAA" in scenic_type:
            return "5A级"
        elif "AAAA" in scenic_type:
            return "4A级"
        elif "AAA" in scenic_type:
            return "3A级"
        return scenic_type

    def _calculate_completeness(self, record: dict) -> float:
        """计算数据完整度"""
        required_fields = ["name", "id", "type"]
        optional_fields = set(record.keys()) - set(required_fields)
        filled_optional = sum(1 for k in optional_fields if record.get(k) not in [None, "", [], {}])
        total_optional = len(optional_fields)
        completeness = 0.5 + (filled_optional / total_optional * 0.5) if total_optional > 0 else 0.5
        return round(completeness, 2)

    def _validate_quality(self):
        """数据质量验证"""
        total_errors = 0
        for category in ["relics", "intangible_cultural_heritage", "tourism"]:
            for record in self.dataset.get(category, []):
                errors = []

                # 必填字段检查
                if not record.get("name"):
                    errors.append("缺少名称")
                if not record.get("id"):
                    errors.append("缺少ID")

                # 关键词检查
                if not record.get("keywords"):
                    errors.append("缺少关键词标签")

                if errors:
                    total_errors += len(errors)
                    self.cleaning_report.append(f"[{record.get('name', '未知')}] {', '.join(errors)}")

        self.dataset["quality_report"] = {
            "total_records": sum(len(self.dataset.get(c, [])) for c in ["relics", "intangible_cultural_heritage", "tourism"]),
            "errors_found": total_errors,
            "is_qualified": total_errors == 0,
            "validation_date": datetime.now().strftime("%Y-%m-%d")
        }

        self.cleaning_report.append(f"质量验证完成：发现 {total_errors} 个问题")

    def _generate_asset_metadata(self):
        """生成数字资产登记元数据"""
        self.dataset["asset_registration_metadata"] = {
            "standard": "DC-文化数字资产元数据标准 v1.0",
            "fields": {
                "dc:title": "西安文物/非遗/文旅数字资产数据集",
                "dc:creator": "大学生数据要素素质大赛参赛团队",
                "dc:date": datetime.now().strftime("%Y-%m-%d"),
                "dc:type": "Dataset",
                "dc:format": "JSON/CSV/Excel",
                "dc:language": "zh-CN",
                "dc:coverage": "西安市",
                "dc:rights": "仅限大赛使用",
                "dc:description": "面向西安文物、非遗、文旅资源的综合性数字资产数据集",
                "dcterms:spatial": "陕西省西安市",
                "dcterms:temporal": "史前-当代",
                "dcat:theme": ["文物", "非物质文化遗产", "文化旅游"],
                "custom:record_count": self.dataset["dataset_metadata"]["total_records"],
                "custom:categories": self.dataset["dataset_metadata"]["categories"]
            }
        }

    def save_processed_data(self):
        """保存处理后的数据"""
        # JSON格式
        json_path = os.path.join(PROCESSED_DATA_DIR, 'xian_cultural_dataset_processed.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        print(f"✓ 处理后数据集已保存: {json_path}")

        # 清洗报告
        report_path = os.path.join(PROCESSED_DATA_DIR, 'cleaning_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "steps": self.cleaning_report,
                "quality": self.dataset.get("quality_report", {})
            }, f, ensure_ascii=False, indent=2)
        print(f"✓ 清洗报告已保存: {report_path}")


if __name__ == "__main__":
    processor = DataProcessor()
    processor.clean_and_structure()
    processor.save_processed_data()
    print("\n数据清洗与结构化处理完成！")
    print(f"清洗步骤: {len(processor.cleaning_report)} 项")
    print(f"质量报告: {processor.dataset.get('quality_report', {})}")
