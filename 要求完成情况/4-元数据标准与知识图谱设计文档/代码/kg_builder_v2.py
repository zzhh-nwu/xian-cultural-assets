"""
知识图谱v2 —— 基于9大项目扩展
新增实体：传承人、工艺技术、展览活动
新增关系：创作于、由…传承、衍生出数字资产
支持 Neo4j Cypher 导出
"""

import json, os, sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE_DIR, 'data', 'collectors'))
from nine_projects import NineProjectsCollector

OUT_DIR = os.path.join(BASE_DIR, 'data', '03_kg')
os.makedirs(OUT_DIR, exist_ok=True)


class KGBuilderV2:
    """知识图谱构建器 v2"""

    def __init__(self):
        self.collector = NineProjectsCollector()
        self.projects = self.collector.get_all_projects()
        # 加载全国项目
        national_path = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'national_projects.json')
        if os.path.exists(national_path):
            with open(national_path, 'r', encoding='utf-8') as f:
                national = json.load(f)
            for p in national.get('projects', []):
                # 标准化字段名
                norm = {
                    'asset_id': p.get('asset_id',''),
                    'asset_type': p.get('asset_type',''),
                    'title': p.get('title',''),
                    'category_tags': p.get('keywords',[]),
                    'cultural_elements': {
                        'period': p.get('era',''),
                        'material': '',
                        'technique': '',
                        'iconography': '',
                        'style': '',
                        'function': '',
                    },
                    'geolocation': {
                        'province': p.get('province',''),
                        'city': p.get('city',''),
                        'site': p.get('title',''),
                    },
                    'historical_figures': [],
                    'historical_events': [],
                    'copyright_holder': p.get('source',''),
                }
                self.projects.append(norm)
        self.nodes = []
        self.edges = []

    def build(self) -> dict:
        """构建完整知识图谱 v2"""
        self._add_project_nodes()
        self._add_figure_nodes()
        self._add_technique_nodes()
        self._add_period_nodes()
        self._add_location_nodes()
        self._add_event_nodes()
        self._add_digital_asset_nodes()
        self._build_relations()
        return self._to_output()

    def _add_project_nodes(self):
        for p in self.projects:
            self.nodes.append({
                'id': p['asset_id'],
                'name': p['title'],
                'type': p['asset_type'],
                'label': self._type_label(p['asset_type']) + ' ' + p['title'],
                'tags': p.get('category_tags', []),
            })

    def _add_figure_nodes(self):
        seen = set()
        for p in self.projects:
            for f in p.get('historical_figures', []):
                name = f.split('（')[0].split('(')[0].strip()
                if name and name not in seen:
                    seen.add(name)
                    fid = f'FIG_{hash(name) % 10000:04d}'
                    self.nodes.append({'id': fid, 'name': name, 'type': '传承人/历史人物',
                                       'label': '👤 ' + name})
                    self.edges.append({'source': p['asset_id'], 'target': fid,
                                       'relation': 'related_to', 'label': '相关人物'})

    def _add_technique_nodes(self):
        seen = set()
        for p in self.projects:
            tech = p.get('cultural_elements', {}).get('technique', '')
            if tech and tech not in seen:
                seen.add(tech)
                tid = f'TECH_{hash(tech) % 10000:04d}'
                self.nodes.append({'id': tid, 'name': tech[:50], 'type': '工艺技术',
                                   'label': '🔧 ' + tech[:30]})
                self.edges.append({'source': p['asset_id'], 'target': tid,
                                   'relation': 'uses_technique', 'label': '使用技艺'})

    def _add_period_nodes(self):
        seen = set()
        for p in self.projects:
            period = p.get('cultural_elements', {}).get('period', '')
            simple = period[:8].replace('（', '').replace('(', '')
            if simple and simple not in seen:
                seen.add(simple)
                pid = f'PERIOD_{hash(simple) % 10000:04d}'
                self.nodes.append({'id': pid, 'name': simple, 'type': '时间时期',
                                   'label': '📜 ' + simple})
                self.edges.append({'source': p['asset_id'], 'target': pid,
                                   'relation': 'created_in', 'label': '创作于'})

    def _add_location_nodes(self):
        seen = set()
        for p in self.projects:
            site = p.get('geolocation', {}).get('site', '')
            if site and site not in seen:
                seen.add(site)
                lid = f'LOC_{hash(site) % 10000:04d}'
                self.nodes.append({'id': lid, 'name': site, 'type': '地理区位',
                                   'label': '📍 ' + site})
                self.edges.append({'source': p['asset_id'], 'target': lid,
                                   'relation': 'located_in', 'label': '位于'})

    def _add_event_nodes(self):
        seen = set()
        for p in self.projects:
            for ev in p.get('historical_events', [])[:2]:
                name = ev[:40]
                if name not in seen:
                    seen.add(name)
                    eid = f'EVT_{hash(name) % 10000:04d}'
                    self.nodes.append({'id': eid, 'name': name, 'type': '展览活动/历史事件',
                                       'label': '🎪 ' + name})
                    self.edges.append({'source': p['asset_id'], 'target': eid,
                                       'relation': 'participates_in', 'label': '关联事件'})

    def _add_digital_asset_nodes(self):
        for p in self.projects:
            did = f'DA_{p["asset_id"]}'
            self.nodes.append({'id': did, 'name': p['title'] + ' 数字资产包',
                               'type': '数字资产', 'label': '💾 ' + p['title'] + ' 资产包'})
            self.edges.append({'source': p['asset_id'], 'target': did,
                               'relation': 'derived_digital_asset', 'label': '衍生出数字资产'})

    def _build_relations(self):
        # 跨域关联：相同朝代的项目
        for i, p1 in enumerate(self.projects):
            for j, p2 in enumerate(self.projects):
                if j <= i: continue
                p1_tags = set(p1.get('category_tags', []))
                p2_tags = set(p2.get('category_tags', []))
                common = p1_tags & p2_tags
                if common and p1['asset_type'] != p2['asset_type']:
                    self.edges.append({
                        'source': p1['asset_id'], 'target': p2['asset_id'],
                        'relation': 'cultural_link', 'label': f'文化关联({",".join(list(common)[:2])})'
                    })

    def _type_label(self, t):
        return {'cultural_relic': '🏛️', 'intangible_heritage': '🎭', 'cultural_tourism': '🏯'}.get(t, '')

    def _to_output(self) -> dict:
        node_types = {}
        edge_types = {}
        for n in self.nodes:
            node_types[n['type']] = node_types.get(n['type'], 0) + 1
        for e in self.edges:
            edge_types[e['relation']] = edge_types.get(e['relation'], 0) + 1

        return {
            'metadata': {
                'title': '西安文化知识图谱 v2.0',
                'description': '基于9大项目的扩展知识图谱，含7种实体和7种关系',
                'node_count': len(self.nodes),
                'edge_count': len(self.edges),
                'created': datetime.now().strftime('%Y-%m-%d'),
                'version': '2.0.0',
            },
            'nodes': self.nodes,
            'edges': self.edges,
            'statistics': {
                'node_types': node_types,
                'edge_types': edge_types,
                'density': round(len(self.edges) / max(1, len(self.nodes) * (len(self.nodes)-1)), 6),
            }
        }

    def export_all(self):
        kg = self.build()
        # JSON
        with open(os.path.join(OUT_DIR, 'kg_v2.json'), 'w', encoding='utf-8') as f:
            json.dump(kg, f, ensure_ascii=False, indent=2)
        print(f'✅ KGv2 JSON: {kg["metadata"]["node_count"]}节点/{kg["metadata"]["edge_count"]}边')
        # 统计
        stats = kg['statistics']
        print(f'   节点类型: {stats["node_types"]}')
        print(f'   关系类型: {stats["edge_types"]}')
        # Cypher导出
        self._export_cypher(kg)
        return kg

    def _export_cypher(self, kg):
        """生成Neo4j Cypher导入脚本"""
        lines = ['// Neo4j Cypher 导入脚本 —— 西安文化知识图谱 v2.0', '']
        lines.append('// 1. 创建节点')
        for n in kg['nodes']:
            safe_name = n['name'].replace("'", "\\'")
            lines.append(f"CREATE (:{n['type'].replace(' ', '_').replace('/', '_')} {{id: '{n['id']}', name: '{safe_name}', type: '{n['type']}'}});")
        lines.append('')
        lines.append('// 2. 创建关系')
        for e in kg['edges']:
            lines.append(f"MATCH (a {{id: '{e['source']}'}}), (b {{id: '{e['target']}'}}) CREATE (a)-[:{e['relation'].upper()} {{label: '{e.get('label','')}'}}]->(b);")
        lines.append('')
        lines.append(f'// 总计: {len(kg["nodes"])} 节点, {len(kg["edges"])} 边')
        path = os.path.join(OUT_DIR, 'kg_v2_neo4j.cypher')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f'✅ KGv2 Cypher: {path}')


if __name__ == '__main__':
    print('=' * 60)
    print('  西安文化知识图谱 v2.0 构建器')
    print('=' * 60)
    builder = KGBuilderV2()
    kg = builder.export_all()
    print('\n知识图谱v2构建完成！')
