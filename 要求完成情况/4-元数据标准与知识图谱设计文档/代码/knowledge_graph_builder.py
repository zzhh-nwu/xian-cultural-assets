"""
西安文化知识图谱构建模块
构建文物、非遗、文旅三大领域的知识图谱
支持实体关系、层级结构、多维度关联
"""

import json
import os
import networkx as nx
from typing import List, Dict, Any, Tuple
from datetime import datetime

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'processed')
KG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'knowledge_graph')


class KnowledgeGraphBuilder:
    """西安文化知识图谱构建器"""

    # 文化关系类型定义
    RELATION_TYPES = {
        "same_era": "同时代",
        "same_category": "同类别",
        "same_location": "同区域",
        "cultural_link": "文化关联",
        "derived_from": "源于",
        "part_of": "属于",
        "influences": "影响",
        "related_to": "相关",
        "historical_figure": "历史人物关联",
        "dynasty": "朝代关联",
        "technique": "技艺关联",
        "tourism_route": "文旅线路",
    }

    def __init__(self, dataset_path: str = None):
        os.makedirs(KG_DIR, exist_ok=True)

        if dataset_path is None:
            dataset_path = os.path.join(PROCESSED_DATA_DIR, 'xian_cultural_dataset_processed.json')

        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)

        self.graph = nx.MultiDiGraph()
        self.node_index = {}  # name -> node_id 索引

    def build(self) -> nx.MultiDiGraph:
        """构建完整知识图谱"""
        print("开始构建知识图谱...")

        # 1. 添加实体节点
        print("  [1/5] 添加实体节点...")
        self._add_relic_nodes()
        self._add_ich_nodes()
        self._add_tourism_nodes()
        self._add_concept_nodes()

        # 2. 添加层级关系
        print("  [2/5] 构建层级关系...")
        self._build_hierarchical_relations()

        # 3. 添加跨域关系
        print("  [3/5] 构建跨域关联...")
        self._build_cross_domain_relations()

        # 4. 添加时序关系
        print("  [4/5] 构建时序关系...")
        self._build_temporal_relations()

        # 5. 添加空间关系
        print("  [5/5] 构建空间关系...")
        self._build_spatial_relations()

        print(f"知识图谱构建完成：{self.graph.number_of_nodes()} 节点，{self.graph.number_of_edges()} 边")
        return self.graph

    def _add_relic_nodes(self):
        """添加文物节点"""
        for relic in self.dataset.get("relics", []):
            node_id = relic["id"]
            self.graph.add_node(node_id,
                name=relic["name"],
                type="文物",
                category=relic.get("category", ""),
                era=relic.get("era", ""),
                keywords=relic.get("keywords", []),
                label=f"🏛️ {relic['name']}"
            )
            self.node_index[relic["name"]] = node_id

    def _add_ich_nodes(self):
        """添加非遗节点"""
        for ich in self.dataset.get("intangible_cultural_heritage", []):
            node_id = ich["id"]
            self.graph.add_node(node_id,
                name=ich["name"],
                type="非遗",
                category=ich.get("category", ""),
                level=ich.get("level", ""),
                origin=ich.get("origin", ""),
                keywords=ich.get("keywords", []),
                label=f"🎭 {ich['name']}"
            )
            self.node_index[ich["name"]] = node_id

    def _add_tourism_nodes(self):
        """添加文旅节点"""
        for tourism in self.dataset.get("tourism", []):
            node_id = tourism["id"]
            self.graph.add_node(node_id,
                name=tourism["name"],
                type="文旅",
                scenic_type=tourism.get("scenic_type", ""),
                district=tourism.get("district", ""),
                keywords=tourism.get("keywords", []),
                label=f"🏯 {tourism['name']}"
            )
            self.node_index[tourism["name"]] = node_id

    def _add_concept_nodes(self):
        """添加概念节点（朝代、区域、类别等）"""
        # 朝代节点
        dynasties = set()
        for relic in self.dataset.get("relics", []):
            era = relic.get("era", "")
            if era:
                dynasties.add(era)

        for dynasty in dynasties:
            node_id = f"DYNASTY_{dynasty}"
            self.graph.add_node(node_id,
                name=dynasty,
                type="朝代",
                label=f"📜 {dynasty}"
            )

        # 非遗类别节点
        ich_categories = set()
        for ich in self.dataset.get("intangible_cultural_heritage", []):
            cat = ich.get("category", "")
            if cat:
                ich_categories.add(cat)

        for cat in ich_categories:
            node_id = f"ICH_CAT_{cat}"
            self.graph.add_node(node_id,
                name=cat,
                type="非遗类别",
                label=f"🎨 {cat}"
            )

        # 区域节点
        districts = set()
        for tourism in self.dataset.get("tourism", []):
            d = tourism.get("district", "")
            if d:
                districts.add(d)

        for district in districts:
            node_id = f"DISTRICT_{district}"
            self.graph.add_node(node_id,
                name=district,
                type="区域",
                label=f"📍 {district}"
            )

    def _build_hierarchical_relations(self):
        """构建层级关系"""
        # 朝代层级：朝代 -> 该朝代文物
        for relic in self.dataset.get("relics", []):
            era = relic.get("era", "")
            if era and relic["id"] in self.graph:
                dynasty_node = f"DYNASTY_{era}"
                if dynasty_node in self.graph:
                    self.graph.add_edge(dynasty_node, relic["id"],
                        relation="contains",
                        label="包含"
                    )

        # 非遗类别层级：类别 -> 该类别非遗
        for ich in self.dataset.get("intangible_cultural_heritage", []):
            cat = ich.get("category", "")
            if cat and ich["id"] in self.graph:
                cat_node = f"ICH_CAT_{cat}"
                if cat_node in self.graph:
                    self.graph.add_edge(cat_node, ich["id"],
                        relation="contains",
                        label="包含"
                    )

        # 区域层级：区县 -> 该区县文旅资源
        for tourism in self.dataset.get("tourism", []):
            district = tourism.get("district", "")
            if district and tourism["id"] in self.graph:
                district_node = f"DISTRICT_{district}"
                if district_node in self.graph:
                    self.graph.add_edge(district_node, tourism["id"],
                        relation="contains",
                        label="位于"
                    )

    def _build_cross_domain_relations(self):
        """构建跨域关联"""
        # 关键词匹配关联
        all_nodes = list(self.graph.nodes(data=True))
        for i, (nid1, ndata1) in enumerate(all_nodes):
            kw1 = set(ndata1.get("keywords", []))
            for nid2, ndata2 in all_nodes[i+1:]:
                if ndata1.get("type") != ndata2.get("type"):
                    kw2 = set(ndata2.get("keywords", []))
                    common = kw1 & kw2
                    if common:
                        self.graph.add_edge(nid1, nid2,
                            relation="cultural_link",
                            label=f"文化关联({','.join(list(common)[:2])})",
                            weight=len(common)
                        )

    def _build_temporal_relations(self):
        """构建时序关系"""
        dynasty_order = [
            "新石器时代", "商", "周", "秦", "汉",
            "三国", "晋", "南北朝", "隋", "唐",
            "五代十国", "宋", "元", "明", "清"
        ]

        # 朝代先后关系
        dynasty_nodes = [f"DYNASTY_{d}" for d in dynasty_order if f"DYNASTY_{d}" in self.graph]
        for i in range(len(dynasty_nodes) - 1):
            if dynasty_nodes[i] in self.graph and dynasty_nodes[i+1] in self.graph:
                self.graph.add_edge(dynasty_nodes[i], dynasty_nodes[i+1],
                    relation="precedes",
                    label="早于"
                )

    def _build_spatial_relations(self):
        """构建空间关系"""
        # 临近区域关系
        adjacent_districts = [
            ("雁塔区", "碑林区"), ("雁塔区", "长安区"), ("雁塔区", "莲湖区"),
            ("碑林区", "莲湖区"), ("碑林区", "新城区"), ("莲湖区", "新城区"),
            ("新城区", "灞桥区"), ("长安区", "灞桥区"),
        ]
        for d1, d2 in adjacent_districts:
            n1 = f"DISTRICT_{d1}"
            n2 = f"DISTRICT_{d2}"
            if n1 in self.graph and n2 in self.graph:
                self.graph.add_edge(n1, n2,
                    relation="adjacent",
                    label="毗邻"
                )

    def export_formats(self):
        """导出多种格式"""
        # JSON格式
        kg_json = self._export_json()
        json_path = os.path.join(KG_DIR, 'knowledge_graph.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(kg_json, f, ensure_ascii=False, indent=2)
        print(f"✓ 知识图谱JSON已保存: {json_path}")

        # GraphML格式 - 转换list属性为字符串
        graphml_path = os.path.join(KG_DIR, 'knowledge_graph.graphml')
        graph_copy = self.graph.copy()
        for nid, ndata in graph_copy.nodes(data=True):
            for k, v in list(ndata.items()):
                if isinstance(v, list):
                    ndata[k] = ', '.join(str(x) for x in v)
        nx.write_graphml(graph_copy, graphml_path)
        print(f"✓ 知识图谱GraphML已保存: {graphml_path}")

        # RDF/Turtle格式
        self._export_rdf()

        # HTML可视化
        self._export_html()

    def _export_json(self) -> dict:
        """导出为JSON"""
        nodes = []
        for nid, ndata in self.graph.nodes(data=True):
            nodes.append({
                "id": nid,
                "name": ndata.get("name", ""),
                "type": ndata.get("type", ""),
                "attributes": {k: v for k, v in ndata.items() if k not in ["name", "type", "label"]}
            })

        edges = []
        for u, v, edata in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": edata.get("relation", ""),
                "label": edata.get("label", "")
            })

        return {
            "metadata": {
                "title": "西安文化知识图谱",
                "description": "西安文物、非遗、文旅资源知识图谱，涵盖实体间层级、时序、空间和文化关联",
                "node_count": len(nodes),
                "edge_count": len(edges),
                "created": datetime.now().strftime("%Y-%m-%d"),
                "version": "1.0.0"
            },
            "nodes": nodes,
            "edges": edges
        }

    def _export_rdf(self):
        """导出为RDF/Turtle格式"""
        rdf_path = os.path.join(KG_DIR, 'knowledge_graph.ttl')
        with open(rdf_path, 'w', encoding='utf-8') as f:
            f.write('@prefix xa: <http://xian.culture/kg#> .\n')
            f.write('@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n')
            f.write('@prefix owl: <http://www.w3.org/2002/07/owl#> .\n')
            f.write('\n')

            # 输出节点
            for nid, ndata in self.graph.nodes(data=True):
                name = ndata.get("name", nid)
                ntype = ndata.get("type", "Entity")
                f.write(f'xa:{nid} a xa:{ntype} ;\n')
                f.write(f'    rdfs:label "{name}"@zh .\n\n')

            # 输出边
            for u, v, edata in self.graph.edges(data=True):
                relation = edata.get("relation", "related_to")
                f.write(f'xa:{u} xa:{relation} xa:{v} .\n')

        print(f"✓ 知识图谱RDF已保存: {rdf_path}")

    def _export_html(self):
        """导出HTML交互式可视化"""
        try:
            from pyvis.network import Network

            net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="#333333")

            # 颜色映射
            color_map = {
                "文物": "#e74c3c",
                "非遗": "#f39c12",
                "文旅": "#2ecc71",
                "朝代": "#9b59b6",
                "非遗类别": "#3498db",
                "区域": "#1abc9c"
            }

            for nid, ndata in self.graph.nodes(data=True):
                ntype = ndata.get("type", "")
                color = color_map.get(ntype, "#95a5a6")
                label = ndata.get("label", nid)
                net.add_node(nid, label=label, color=color, title=f"{ndata.get('name', nid)}\n类型: {ntype}")

            for u, v, edata in self.graph.edges(data=True):
                net.add_edge(u, v, title=edata.get("label", ""), label=edata.get("label", ""))

            net.set_options("""
            var options = {
              "nodes": {
                "font": {"size": 14}
              },
              "edges": {
                "font": {"size": 10, "align": "middle"},
                "arrows": {"to": {"enabled": true}}
              },
              "physics": {
                "barnesHut": {"gravitationalConstant": -3000, "centralGravity": 0.3, "springLength": 200},
                "minVelocity": 0.75
              }
            }
            """)

            html_path = os.path.join(KG_DIR, 'knowledge_graph.html')
            net.save_graph(html_path)
            print(f"✓ 知识图谱HTML可视化已保存: {html_path}")
        except ImportError:
            print("⚠ pyvis未安装，跳过HTML可视化")

    def query_related(self, entity_name: str, max_depth: int = 2) -> dict:
        """查询与某个实体相关的所有节点"""
        if entity_name not in self.node_index:
            return {"error": f"未找到实体: {entity_name}"}

        start_node = self.node_index[entity_name]
        result = {
            "entity": entity_name,
            "node_id": start_node,
            "direct_relations": [],
            "extended_relations": []
        }

        # 直接关系
        for neighbor in self.graph.neighbors(start_node):
            edge_data = self.graph.get_edge_data(start_node, neighbor)
            for key, data in edge_data.items():
                neighbor_data = self.graph.nodes[neighbor]
                result["direct_relations"].append({
                    "target": neighbor_data.get("name", neighbor),
                    "type": neighbor_data.get("type", ""),
                    "relation": data.get("label", data.get("relation", "")),
                    "depth": 1
                })

        # 入边关系
        for predecessor in self.graph.predecessors(start_node):
            edge_data = self.graph.get_edge_data(predecessor, start_node)
            for key, data in edge_data.items():
                pred_data = self.graph.nodes[predecessor]
                result["direct_relations"].append({
                    "target": pred_data.get("name", predecessor),
                    "type": pred_data.get("type", ""),
                    "relation": data.get("label", data.get("relation", "")),
                    "direction": "incoming",
                    "depth": 1
                })

        return result

    def get_statistics(self) -> dict:
        """获取知识图谱统计信息"""
        node_types = {}
        for nid, ndata in self.graph.nodes(data=True):
            ntype = ndata.get("type", "Unknown")
            node_types[ntype] = node_types.get(ntype, 0) + 1

        edge_types = {}
        for u, v, edata in self.graph.edges(data=True):
            etype = edata.get("relation", "Unknown")
            edge_types[etype] = edge_types.get(etype, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": node_types,
            "edge_types": edge_types,
            "density": round(nx.density(self.graph), 4),
            "is_connected": nx.is_weakly_connected(self.graph),
            "average_degree": round(sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(), 2) if self.graph.number_of_nodes() > 0 else 0
        }


if __name__ == "__main__":
    print("=" * 60)
    print("  西安文化知识图谱构建工具")
    print("=" * 60)
    builder = KnowledgeGraphBuilder()
    builder.build()
    builder.export_formats()

    stats = builder.get_statistics()
    print(f"\n知识图谱统计:")
    print(f"  节点总数: {stats['total_nodes']}")
    print(f"  边总数: {stats['total_edges']}")
    print(f"  图密度: {stats['density']}")
    print(f"  连通性: {'连通' if stats['is_connected'] else '非全连通'}")
    print(f"  平均度: {stats['average_degree']}")
    print(f"  节点类型: {stats['node_types']}")
    print(f"  边类型: {stats['edge_types']}")
