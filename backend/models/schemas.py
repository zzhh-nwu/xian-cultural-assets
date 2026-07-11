"""Pydantic数据模型 —— API请求/响应结构"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ===== 数字资产模型 =====
class CulturalElementOut(BaseModel):
    period: str = ''
    material: str = ''
    technique: str = ''
    iconography: str = ''
    style: str = ''
    function: str = ''

class GeolocationOut(BaseModel):
    province: str = '陕西省'
    city: str = '西安市'
    district: str = ''
    site: str = ''
    lat: str = ''
    lng: str = ''

class MultimediaAssetOut(BaseModel):
    asset_type: str
    urls: List[str] = []
    description: str = ''
    license_info: str = ''

class ProjectOut(BaseModel):
    asset_id: str
    asset_type: str
    title: str
    title_en: str = ''
    description: str = ''
    detailed_description: str = ''
    category_tags: List[str] = []
    cultural_elements: CulturalElementOut = CulturalElementOut()
    geolocation: GeolocationOut = GeolocationOut()
    historical_figures: List[str] = []
    historical_events: List[str] = []
    copyright_holder: str = ''
    license: str = 'CC BY-NC-ND 4.0'
    data_provenance: List[str] = []
    multimedia: Dict[str, MultimediaAssetOut] = {}
    references: List[str] = []
    registration_standard: str = ''

class ProjectsListOut(BaseModel):
    total: int
    projects: List[ProjectOut]
    types: Dict[str, int]

# ===== 智能体模型 =====
class ClassificationRequest(BaseModel):
    text: str
    mode: str = 'auto'  # auto / ai / rule

class ClassificationResponse(BaseModel):
    category: str
    keywords: List[str]
    era: str = ''
    cultural_elements: List[Dict[str, Any]] = []
    suggested_tags: List[str] = []
    compliance: Dict[str, Any] = {}
    mode_used: str

class ContentGenerationRequest(BaseModel):
    topic: str
    content_types: List[str] = ['文案', '图片描述', '视频脚本']
    target_platform: str = '小红书'
    project_id: Optional[str] = None  # 可指定具体项目获取深度数据

class ContentPieceOut(BaseModel):
    content_type: str
    title: str
    body: str
    tags: List[str]
    cultural_elements: List[str]
    target_platform: str
    word_count: int

class ContentGenerationResponse(BaseModel):
    topic: str
    generated_at: str
    contents: List[ContentPieceOut]
    total_pieces: int

class ComplianceRequest(BaseModel):
    content: str

class ComplianceResponse(BaseModel):
    is_compliant: bool
    score: int
    issues: List[str]
    warnings: List[str]

class SpeechRequest(BaseModel):
    text: str
    voice: str = 'zh-CN-XiaoxiaoNeural'

# ===== 知识图谱模型 =====
class KGQueryRequest(BaseModel):
    entity_name: str
    max_depth: int = 2

class KGNodeOut(BaseModel):
    id: str
    name: str
    type: str
    attributes: Dict[str, Any] = {}

class KGEdgeOut(BaseModel):
    source: str
    target: str
    relation: str
    label: str = ''

class KGQueryResponse(BaseModel):
    entity: str
    direct_relations: List[Dict[str, Any]]
    statistics: Dict[str, Any] = {}

class KGStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    node_types: Dict[str, int]
    edge_types: Dict[str, int]
    density: float

# ===== 资产登记模型 =====
class RegistrationInfo(BaseModel):
    asset_name: str
    asset_type: str
    creator: str
    rights: str
    asset_id: Optional[str] = None

class RegistrationResponse(BaseModel):
    registration_number: str
    metadata_jsonld: Dict[str, Any]
    rights_certificate_url: str
    fingerprint: str
    registered_at: str
