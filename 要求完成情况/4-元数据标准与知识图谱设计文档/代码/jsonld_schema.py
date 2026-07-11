"""
JSON-LD数字资产元数据生成器
对标数字资产登记标准 v1.0，输出符合JSON-LD规范的元数据文件
"""

import json, os, hashlib
from datetime import datetime
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data', '01_raw', 'text')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', '02_processed')


class JSONLDMetadataGenerator:
    """JSON-LD元数据生成器 —— 对标数字资产登记标准"""

    JSONLD_CONTEXT = {
        "@context": {
            "schema": "http://schema.org/",
            "dc": "http://purl.org/dc/terms/",
            "dcterms": "http://purl.org/dc/terms/",
            "x9p": "http://west9-province.org/standard/v1.0#",
            "cultural": "http://cultural-asset.org/ns#",
            "owl": "http://www.w3.org/2002/07/owl#",
        }
    }

    def __init__(self, projects_path: str = None):
        if projects_path is None:
            projects_path = os.path.join(DATA_DIR, 'nine_projects.json')
        with open(projects_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def generate_all_metadata(self) -> Dict[str, Any]:
        """为全部9个项目生成JSON-LD元数据"""
        records = []
        for project in self.data['projects']:
            record = self.generate_single_metadata(project)
            records.append(record)

        dataset = {
            **self.JSONLD_CONTEXT,
            "@type": "schema:Dataset",
            "schema:name": self.data['metadata']['title'],
            "schema:description": self.data['metadata']['description'],
            "dc:creator": "大学生数据要素素质大赛参赛团队",
            "dc:date": datetime.now().strftime("%Y-%m-%d"),
            "schema:version": self.data['metadata']['version'],
            "x9p:standardVersion": "数字资产登记标准 v1.0",
            "x9p:totalAssets": len(records),
            "x9p:assetCategories": self.data['metadata']['project_types'],
            "schema:hasPart": records,
        }
        return dataset

    def generate_single_metadata(self, project: dict) -> dict:
        """为单个项目生成JSON-LD元数据"""
        fingerprint = self._compute_fingerprint(project)
        geoloc = project.get('geolocation', {})

        return {
            "@type": self._get_asset_type(project['asset_type']),
            "@id": f"urn:sha256:{fingerprint}",
            "schema:identifier": project['asset_id'],
            "schema:name": project['title'],
            "schema:alternateName": project.get('title_en', ''),
            "schema:description": project.get('description', ''),
            "schema:additionalDescription": project.get('detailed_description', ''),
            "schema:keywords": project.get('category_tags', []),

            "cultural:culturalElements": {
                "cultural:period": project.get('cultural_elements', {}).get('period', ''),
                "cultural:material": project.get('cultural_elements', {}).get('material', ''),
                "cultural:technique": project.get('cultural_elements', {}).get('technique', ''),
                "cultural:iconography": project.get('cultural_elements', {}).get('iconography', ''),
                "cultural:style": project.get('cultural_elements', {}).get('style', ''),
                "cultural:function": project.get('cultural_elements', {}).get('function', ''),
            },

            "x9p:geolocation": {
                "schema:addressRegion": geoloc.get('province', '陕西省'),
                "schema:addressLocality": geoloc.get('city', '西安市'),
                "schema:addressDistrict": geoloc.get('district', ''),
                "schema:locationName": geoloc.get('site', ''),
                "schema:latitude": geoloc.get('lat', ''),
                "schema:longitude": geoloc.get('lng', ''),
            },

            "cultural:relatedFigures": [
                {"schema:Person": {"schema:name": name}}
                for name in project.get('historical_figures', [])
            ],

            "cultural:relatedEvents": project.get('historical_events', []),

            "schema:copyrightHolder": {
                "schema:Organization": {"schema:name": project.get('copyright_holder', '')}
            },
            "schema:license": project.get('license', 'CC BY-NC-ND 4.0'),

            "schema:citation": project.get('data_provenance', []),
            "schema:sameAs": project.get('references', []),

            "x9p:digitalRepresentation": self._format_multimedia(project.get('multimedia', {})),

            "x9p:registrationStandard": project.get('registration_standard', '数字资产登记标准 v1.0'),
            "x9p:certificationHash": f"sha256:{fingerprint}",
            "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "x9p:dataProvenance": project.get('data_provenance', []),
        }

    def _get_asset_type(self, asset_type: str) -> str:
        mapping = {
            'cultural_relic': 'cultural:CulturalRelic',
            'intangible_heritage': 'cultural:IntangibleHeritage',
            'cultural_tourism': 'cultural:CulturalTourism',
        }
        return mapping.get(asset_type, 'schema:CreativeWork')

    def _format_multimedia(self, multimedia: dict) -> dict:
        result = {}
        for key, asset in multimedia.items():
            result[key] = {
                "@type": "schema:MediaObject",
                "schema:encodingFormat": asset.get('asset_type', ''),
                "schema:url": asset.get('urls', []),
                "schema:description": asset.get('description', ''),
                "schema:license": asset.get('license_info', ''),
            }
        return result

    def _compute_fingerprint(self, project: dict) -> str:
        content = json.dumps(project, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def export_jsonld(self, output_path: str = None) -> str:
        dataset = self.generate_all_metadata()
        if output_path is None:
            output_path = os.path.join(OUTPUT_DIR, 'metadata_jsonld.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f'JSON-LD元数据已导出: {output_path}')
        return output_path

    def export_single_jsonld(self, asset_id: str, output_dir: str = None) -> str:
        for project in self.data['projects']:
            if project['asset_id'] == asset_id:
                record = self.generate_single_metadata(project)
                record.update(self.JSONLD_CONTEXT)
                if output_dir is None:
                    output_dir = os.path.join(OUTPUT_DIR, 'single_assets')
                os.makedirs(output_dir, exist_ok=True)
                path = os.path.join(output_dir, f'{asset_id}_metadata.jsonld')
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)
                print(f'单个资产元数据已导出: {path}')
                return path
        return ''


if __name__ == '__main__':
    print('=' * 60)
    print('  JSON-LD元数据生成器')
    print('=' * 60)
    gen = JSONLDMetadataGenerator()
    gen.export_jsonld()
    print(f'已生成 {len(gen.data["projects"])} 个资产的JSON-LD元数据')
    # 测试单个导出
    gen.export_single_jsonld('XA-REL-001')
    print('完成！')
