"""九大文化项目数据加载器 —— 从JSON加载，彻底避免编码问题"""
import json, os, hashlib
from datetime import datetime
from typing import List, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'nine_projects.json')


class NineProjectsCollector:
    """九大文化项目数据采集器 —— 从预定义的JSON数据集加载"""

    def __init__(self, json_path: str = None):
        self.json_path = json_path or JSON_PATH
        self._data = None

    def _load(self) -> dict:
        if self._data is None:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        return self._data

    def get_all_projects(self) -> List[dict]:
        return self._load()['projects']

    def get_metadata(self) -> dict:
        return self._load()['metadata']

    def get_project_by_id(self, asset_id: str) -> Optional[dict]:
        for p in self._load()['projects']:
            if p['asset_id'] == asset_id:
                return p
        return None

    def get_projects_by_type(self, asset_type: str) -> List[dict]:
        return [p for p in self._load()['projects'] if p['asset_type'] == asset_type]

    def compute_asset_fingerprint(self, project: dict) -> str:
        content = json.dumps(project, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def generate_statistics(self) -> dict:
        projects = self._load()['projects']
        stats = {
            'total_projects': len(projects),
            'by_type': {},
            'total_tags': set(),
            'total_historical_figures': set(),
            'total_multimedia_urls': 0,
            'era_coverage': set(),
            'district_coverage': set(),
            'total_description_chars': 0,
        }
        for p in projects:
            stats['by_type'][p['asset_type']] = stats['by_type'].get(p['asset_type'], 0) + 1
            stats['total_tags'].update(p.get('category_tags', []))
            stats['total_historical_figures'].update(p.get('historical_figures', []))
            ce = p.get('cultural_elements', {})
            stats['era_coverage'].add(ce.get('period', '')[:4])
            stats['district_coverage'].add(p.get('geolocation', {}).get('district', ''))
            stats['total_description_chars'] += len(p.get('description', '')) + len(p.get('detailed_description', ''))
            for asset in p.get('multimedia', {}).values():
                stats['total_multimedia_urls'] += len(asset.get('urls', []))
        stats['total_tags'] = len(stats['total_tags'])
        stats['total_historical_figures'] = len(stats['total_historical_figures'])
        stats['era_coverage'] = sorted([e for e in stats['era_coverage'] if e])
        stats['district_coverage'] = sorted([d for d in stats['district_coverage'] if d])
        return stats


if __name__ == '__main__':
    print('=' * 60)
    print('  西安文化数字资产 - 九大项目数据加载器')
    print('=' * 60)
    collector = NineProjectsCollector()
    projects = collector.get_all_projects()
    print(f'加载项目: {len(projects)} 个')
    stats = collector.generate_statistics()
    print(f'类型分布: {stats["by_type"]}')
    print(f'总标签数: {stats["total_tags"]}')
    print(f'历史人物: {stats["total_historical_figures"]}')
    print(f'多媒体URL: {stats["total_multimedia_urls"]}')
    print(f'朝代覆盖: {stats["era_coverage"]}')
    print(f'区域覆盖: {stats["district_coverage"]}')
    print(f'总字数: {stats["total_description_chars"]:,}')
    for p in projects:
        fp = collector.compute_asset_fingerprint(p)[:16]
        print(f'  [{p["asset_id"]}] {p["title"]}  指纹: {fp}...')
    print('\n数据加载成功!')
