"""
批量生成全部233项资产的JSON-LD元数据
处理：nine_projects(9) + shaanxi_projects(102) + national_projects(122)
"""
import json, os, hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', '01_raw', 'text')
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', '02_processed')
SINGLE_DIR = os.path.join(OUTPUT_DIR, 'single_assets')
os.makedirs(SINGLE_DIR, exist_ok=True)

JSONLD_CONTEXT = {
    "@context": {
        "schema": "http://schema.org/",
        "dc": "http://purl.org/dc/terms/",
        "x9p": "http://west9-province.org/standard/v1.0#",
        "cultural": "http://cultural-asset.org/ns#",
    }
}

ASSET_TYPE_MAP = {
    'cultural_relic': 'cultural:CulturalRelic',
    'intangible_heritage': 'cultural:IntangibleHeritage',
    'cultural_tourism': 'cultural:CulturalTourism',
}


def sha256_dict(d: dict) -> str:
    return hashlib.sha256(
        json.dumps(d, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()


def build_jsonld(project: dict) -> dict:
    """为单个项目构建JSON-LD，兼容简单格式和深度格式"""
    fingerprint = sha256_dict(project)

    # 地理位置 — 兼容两种格式
    geoloc = project.get('geolocation', {})
    province = project.get('province', '') or geoloc.get('province', '')
    city = project.get('city', '') or geoloc.get('city', '')
    district = geoloc.get('district', '')
    site = geoloc.get('site', '')
    lat = geoloc.get('lat', '')
    lng = geoloc.get('lng', '')

    # 文化要素 — 兼容两种格式
    ce = project.get('cultural_elements', {})
    era = project.get('era', '') or ce.get('period', '')

    record = {
        "@type": ASSET_TYPE_MAP.get(project['asset_type'], 'schema:CreativeWork'),
        "@id": f"urn:sha256:{fingerprint}",
        "schema:identifier": project['asset_id'],
        "schema:name": project['title'],
        "schema:description": project.get('description', ''),
        "schema:keywords": project.get('keywords', []) or project.get('category_tags', []),

        "cultural:culturalElements": {
            "cultural:period": era,
            "cultural:material": ce.get('material', ''),
            "cultural:technique": ce.get('technique', ''),
            "cultural:iconography": ce.get('iconography', ''),
            "cultural:style": ce.get('style', ''),
            "cultural:function": ce.get('function', ''),
        },

        "x9p:geolocation": {
            "schema:addressRegion": province,
            "schema:addressLocality": city,
            "schema:addressDistrict": district,
            "schema:locationName": site,
            "schema:latitude": lat,
            "schema:longitude": lng,
        },

        "cultural:relatedFigures": [
            {"schema:Person": {"schema:name": name}}
            for name in project.get('historical_figures', [])
        ],
        "cultural:relatedEvents": project.get('historical_events', []),

        "schema:copyrightHolder": {
            "schema:Organization": {"schema:name": project.get('copyright_holder', '') or project.get('source', '')}
        },
        "schema:license": project.get('license', 'CC BY-NC-ND 4.0'),
        "schema:citation": project.get('data_provenance', []) or ([project['source']] if project.get('source') else []),

        "x9p:registrationStandard": "数字资产登记标准 v1.0",
        "x9p:certificationHash": f"sha256:{fingerprint}",
        "dcterms:created": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # 深度字段（仅nine_projects有）
    if project.get('title_en'):
        record["schema:alternateName"] = project['title_en']
    if project.get('detailed_description'):
        record["schema:additionalDescription"] = project['detailed_description']
    if project.get('references'):
        record["schema:sameAs"] = project['references']
    if project.get('multimedia'):
        multimedia = {}
        for key, asset in project['multimedia'].items():
            multimedia[key] = {
                "@type": "schema:MediaObject",
                "schema:encodingFormat": asset.get('asset_type', ''),
                "schema:url": asset.get('urls', []),
                "schema:description": asset.get('description', ''),
                "schema:license": asset.get('license_info', ''),
            }
        record["x9p:digitalRepresentation"] = multimedia

    return record


def process_file(filepath: str, label: str) -> list:
    """处理单个JSON文件，返回记录列表"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    for project in data['projects']:
        record = build_jsonld(project)

        # 保存单个文件
        asset_id = project['asset_id']
        single = {**JSONLD_CONTEXT, **record}
        single_path = os.path.join(SINGLE_DIR, f'{asset_id}_metadata.jsonld')
        with open(single_path, 'w', encoding='utf-8') as f:
            json.dump(single, f, ensure_ascii=False, indent=2)

        records.append(record)

    print(f'  ✓ {label}: {len(records)} 条 → {SINGLE_DIR}\\')
    return records


if __name__ == '__main__':
    print('=' * 60)
    print('  批量JSON-LD元数据生成')
    print('=' * 60)

    all_records = []

    # 1. 九大项目
    all_records += process_file(
        os.path.join(DATA_DIR, 'nine_projects.json'), '九大项目'
    )

    # 2. 陕西102项
    all_records += process_file(
        os.path.join(DATA_DIR, 'shaanxi_projects.json'), '陕西全省'
    )

    # 3. 全国122项
    all_records += process_file(
        os.path.join(DATA_DIR, 'national_projects.json'), '全国数据'
    )

    # 汇总输出
    dataset = {
        **JSONLD_CONTEXT,
        "@type": "schema:Dataset",
        "schema:name": "中国文化遗产数字资产包（全量233项）",
        "schema:description": "覆盖陕西102项 + 全国122项 + 西安深度9项的文物/非遗/文旅数字资产，对标数字资产登记标准v1.0",
        "dc:creator": "大学生数据要素素质大赛参赛团队",
        "dc:date": datetime.now().strftime("%Y-%m-%d"),
        "schema:version": "2.0.0",
        "x9p:standardVersion": "数字资产登记标准 v1.0",
        "x9p:totalAssets": len(all_records),
        "schema:hasPart": all_records,
    }

    output_path = os.path.join(OUTPUT_DIR, 'metadata_jsonld.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f'\n{"=" * 60}')
    print(f'  ✅ 全部完成！')
    print(f'  总资产数: {len(all_records)} 项')
    print(f'  单个文件: {SINGLE_DIR}\\ (每个资产一份 .jsonld)')
    print(f'  汇总文件: {output_path}')
    print(f'{"=" * 60}')
