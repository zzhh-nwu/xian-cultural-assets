"""
FastAPI后端主应用
西安文化数字资产平台 API v2.0
提供数据浏览、智能体调用、知识图谱查询、资产登记等功能
"""

import os, sys, json, asyncio
from datetime import datetime
from typing import Optional

# 添加项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'backend'))

from fastapi import FastAPI, HTTPException, Query, Request, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 导入本地模块
from models.schemas import *
from data.collectors.nine_projects import NineProjectsCollector
from database import get_db, init_db
from auth import hash_password, verify_password, create_token, verify_token, get_user_by_id, get_user_by_username

# 尝试导入智能体
try:
    from agent.cultural_agent import CulturalContentAgent
    HAS_AGENT = True
except ImportError:
    HAS_AGENT = False

# 尝试导入知识图谱
try:
    from data.knowledge_graph_builder import KnowledgeGraphBuilder
    HAS_KG = True
except ImportError:
    HAS_KG = False

# ===== 应用初始化 =====
app = FastAPI(
    title='西安文化数字资产平台 API',
    description='陕西文物/非遗/文旅数字资产生成与内容创作 —— 大学生数据要素素质大赛',
    version='2.0.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 加载.env环境变量
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 初始化数据加载器
collector = NineProjectsCollector()
agent = CulturalContentAgent() if HAS_AGENT else None

# 加载知识图谱（如存在）
kg_builder = None
KG_DATA = None
kg_json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'data', '03_kg', 'kg_v2.json')
if os.path.exists(kg_json_path):
    with open(kg_json_path, 'r', encoding='utf-8') as f:
        KG_DATA = json.load(f)


# ===== 首页 =====
@app.get('/')
def root():
    return {
        'app': '西安文化数字资产平台 API v2.0',
        'description': '陕西文物/非遗/文旅数字资产生成与内容创作',
        'status': 'running',
        'capabilities': {
            'data': '9+110+122个文化数字资产',
            'agent': 'DeepSeek AI驱动' if HAS_AGENT else '规则引擎模式',
            'kg': f'{KG_DATA["metadata"]["node_count"]}节点/{KG_DATA["metadata"]["edge_count"]}边' if KG_DATA else '待构建',
            'registry': 'JSON-LD / 西部九省标准',
        },
        'docs': '/docs',
    }


def _normalize_project(p: dict) -> dict:
    """将全国数据集的字段统一转换为前端期望的格式"""
    if 'category_tags' in p:  # 已是西安格式
        return p
    return {
        'asset_id': p.get('asset_id', ''),
        'asset_type': p.get('asset_type', ''),
        'title': p.get('title', ''),
        'title_en': p.get('title_en', ''),
        'description': p.get('description', ''),
        'detailed_description': p.get('detailed_description', p.get('description', '')),
        'category_tags': p.get('keywords', p.get('category_tags', [])),
        'cultural_elements': p.get('cultural_elements', {
            'period': p.get('era', ''),
            'material': '',
            'technique': '',
            'iconography': '',
            'style': '',
            'function': '',
        }),
        'geolocation': p.get('geolocation', {
            'province': p.get('province', ''),
            'city': p.get('city', ''),
            'district': '',
            'site': p.get('title', ''),
            'lat': '',
            'lng': '',
        }),
        'historical_figures': p.get('historical_figures', []),
        'historical_events': p.get('historical_events', []),
        'copyright_holder': p.get('copyright_holder', p.get('source', '')),
        'license': p.get('license', 'CC BY-NC-ND 4.0'),
        'data_provenance': [p.get('source', '')],
        'multimedia': p.get('multimedia', {}),
        'references': p.get('references', []),
        'registration_standard': p.get('registration_standard', '数字资产登记标准 v1.0'),
    }


# ===== 数据API =====
@app.get('/api/data/projects')
def list_projects(asset_type: Optional[str] = None, scope: str = 'all', province: Optional[str] = None):
    """获取项目列表，scope: all(全部) | xian(西安9条) | shaanxi(陕西110条) | national(全国122条) | province(按省筛选)"""
    if scope == 'xian':
        projects = collector.get_all_projects()
    elif scope == 'shaanxi':
        projects = [_normalize_project(p) for p in _load_shaanxi().get('projects', [])] if _load_shaanxi() else []
    elif scope == 'national':
        projects = [_normalize_project(p) for p in _load_national().get('projects', [])] if _load_national() else []
    else:
        projects = collector.get_all_projects()
        if _load_shaanxi():
            projects = projects + [_normalize_project(p) for p in _load_shaanxi().get('projects', [])]
        if _load_national():
            projects = projects + [_normalize_project(p) for p in _load_national().get('projects', [])]

    if province:
        projects = [p for p in projects if (p.get('geolocation',{}).get('province','') == province or p.get('province','') == province)]
    if asset_type:
        projects = [p for p in projects if p.get('asset_type') == asset_type]

    types = {}
    for p in projects:
        types[p['asset_type']] = types.get(p['asset_type'], 0) + 1

    return {'total': len(projects), 'projects': projects, 'types': types, 'scope': scope}


@app.get('/api/data/projects/{asset_id}')
def get_project(asset_id: str):
    """获取单个项目详情，自动搜索西安和全国数据"""
    # 先搜西安
    project = collector.get_project_by_id(asset_id)
    # 再搜全国
    if not project and _load_national():
        for p in _load_national().get('projects', []):
            if p.get('asset_id') == asset_id:
                project = p
                break
    if not project:
        raise HTTPException(404, f'未找到项目: {asset_id}')
    return project


@app.get('/api/data/statistics')
def get_statistics():
    """获取数据统计"""
    return collector.generate_statistics()


@app.get('/api/data/metadata/jsonld')
def get_jsonld_metadata():
    """获取JSON-LD元数据"""
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'data', '02_processed', 'metadata_jsonld.json')
    if not os.path.exists(metadata_path):
        raise HTTPException(404, '元数据文件未生成，请先运行jsonld_schema.py')
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ===== 智能体API =====
@app.post('/api/agent/classify', response_model=ClassificationResponse)
def agent_classify(req: ClassificationRequest):
    """智能分类与标注"""
    if not agent:
        raise HTTPException(503, '智能体不可用')
    result = agent.classify_and_tag(req.text)
    return ClassificationResponse(
        category=result.get('category', ''),
        keywords=result.get('keywords', []),
        era=result.get('era', ''),
        cultural_elements=result.get('cultural_elements', []),
        suggested_tags=result.get('suggested_tags', []),
        compliance=result.get('compliance_check', {}),
        mode_used='ai' if agent.use_ai else 'rule',
    )


@app.post('/api/agent/generate', response_model=ContentGenerationResponse)
def agent_generate(req: ContentGenerationRequest):
    """生成多模态内容"""
    if not agent:
        raise HTTPException(503, '智能体不可用')

    # 如果指定了项目ID，使用项目详细描述作为上下文
    topic = req.topic
    if req.project_id:
        project = collector.get_project_by_id(req.project_id)
        if project:
            topic = f'{req.topic}\n深度资料：{project["description"][:500]}'

    results = agent.generate_content(topic, content_types=req.content_types,
                                     target_platform=req.target_platform)

    contents_out = [
        ContentPieceOut(
            content_type=c.content_type,
            title=c.title,
            body=c.body,
            tags=c.tags,
            cultural_elements=c.cultural_elements,
            target_platform=c.target_platform,
            word_count=c.word_count,
        ) for c in results
    ]

    return ContentGenerationResponse(
        topic=req.topic,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        contents=contents_out,
        total_pieces=len(contents_out),
    )


@app.post('/api/agent/compliance', response_model=ComplianceResponse)
def agent_compliance(req: ComplianceRequest):
    """内容合规性检查"""
    if not agent:
        raise HTTPException(503, '智能体不可用')
    result = agent.compliance_check(req.content)
    return ComplianceResponse(**result)


@app.post('/api/agent/speech')
async def agent_speech(req: SpeechRequest):
    """语音合成 (Edge TTS)"""
    try:
        from data.processors.media_processor import MediaProcessor
        mp = MediaProcessor()
        out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'data', '02_processed', 'audio', f'speech_{hash(req.text) % 10000}.mp3')
        result = await mp.generate_speech(req.text, out_path, req.voice)
        if result:
            return {'status': 'success', 'file': result}
        raise HTTPException(500, '语音合成失败')
    except Exception as e:
        raise HTTPException(500, str(e))


# ===== AI图片+视频生成API =====
from services.jimeng_service import text_to_image, text_to_video, get_video_result, image_recognition


# ===== AI智能对话API（DeepSeek文本 + 豆包图片识别） =====
@app.post('/api/agent/chat')
async def agent_chat(request: Request):
    """智能对话：文字走DeepSeek，带图片走豆包视觉识别"""
    if not agent or not agent.use_ai:
        raise HTTPException(503, '智能体不可用')

    try:
        body = await request.json()
        query = body.get('query', '')
        history = body.get('history', [])
        image_b64 = body.get('image', '')

        # 有图片 → 豆包视觉识别
        if image_b64:
            result = image_recognition(image_b64, query)
            if result.get('success'):
                return {'success': True, 'answer': result['answer'], 'model': 'doubao-vision'}
            return {'success': False, 'error': result.get('error', '识别失败')}

        # 纯文字 → DeepSeek
        messages = [{
            'role': 'system',
            'content': '你是中国文化数字资产平台的AI助手，专注于中国文物、非物质文化遗产、文化旅游领域的知识问答。请用中文回答，提供详细、准确的信息。如果用户询问的文化资产不在你的知识范围内，请如实告知，并建议用户查阅官方文博网站。回答风格专业但亲切，适当使用emoji。'
        }]
        for h in (history or [])[-10:]:
            messages.append({'role': h.get('role', 'user'), 'content': h.get('content', '')})
        messages.append({'role': 'user', 'content': query})

        response = agent.client.chat.completions.create(
            model='deepseek-chat',
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        answer = response.choices[0].message.content
        return {'success': True, 'answer': answer, 'model': 'deepseek-chat'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@app.post('/api/gen/image')
def gen_image(prompt: str = Query(...), width: int = 2048, height: int = 2048):
    """豆包Seedream图片生成"""
    return text_to_image(prompt, width, height)


@app.post('/api/gen/video')
def gen_video(prompt: str = Query(...)):
    """豆包Seedance视频生成（异步）"""
    return text_to_video(prompt)


@app.get('/api/gen/video/{task_id}')
def gen_video_status(task_id: str):
    """查询视频生成状态"""
    return get_video_result(task_id)


# ===== 知识图谱API =====
@app.get('/api/kg/stats')
def kg_stats():
    """知识图谱统计"""
    if not KG_DATA:
        raise HTTPException(404, '知识图谱未构建')
    meta = KG_DATA['metadata']
    nodes = KG_DATA['nodes']
    edges = KG_DATA['edges']

    node_types = {}
    for n in nodes:
        t = n.get('type', '未知')
        node_types[t] = node_types.get(t, 0) + 1

    edge_types = {}
    for e in edges:
        r = e.get('relation', '未知')
        edge_types[r] = edge_types.get(r, 0) + 1

    return {
        'total_nodes': meta['node_count'],
        'total_edges': meta['edge_count'],
        'node_types': node_types,
        'edge_types': edge_types,
        'density': round(meta['edge_count'] / (meta['node_count'] * (meta['node_count'] - 1)), 6) if meta['node_count'] > 1 else 0,
    }


@app.get('/api/kg/query')
def kg_query(entity_name: str = Query(...), max_depth: int = Query(2)):
    """查询知识图谱中的实体"""
    if not KG_DATA:
        raise HTTPException(404, '知识图谱未构建')

    # 简单搜索
    results = []
    for node in KG_DATA['nodes']:
        if entity_name in node.get('name', '') or entity_name in node.get('id', ''):
            node_id = node['id']
            # 查找关联边
            related = []
            for edge in KG_DATA['edges']:
                if edge['source'] == node_id:
                    target = next((n for n in KG_DATA['nodes'] if n['id'] == edge['target']), None)
                    if target:
                        related.append({
                            'target': target['name'],
                            'type': target.get('type', ''),
                            'relation': edge.get('label', edge.get('relation', '')),
                            'direction': 'outgoing'
                        })
                elif edge['target'] == node_id:
                    source = next((n for n in KG_DATA['nodes'] if n['id'] == edge['source']), None)
                    if source:
                        related.append({
                            'target': source['name'],
                            'type': source.get('type', ''),
                            'relation': edge.get('label', edge.get('relation', '')),
                            'direction': 'incoming'
                        })
            results.append({
                'entity': node['name'],
                'node_id': node_id,
                'type': node.get('type', ''),
                'direct_relations': related[:max_depth * 10],
            })

    if not results:
        raise HTTPException(404, f'未找到实体: {entity_name}')
    return {'query': entity_name, 'results': results, 'total_matches': len(results)}


# ===== 联网搜索API =====
def _load_national():
    """每次调用时动态加载全国数据集，确保数据始终最新"""
    path = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'national_projects.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def _load_shaanxi():
    """每次调用时动态加载陕西省数据集"""
    path = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'shaanxi_projects.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


@app.get('/api/search')
def search_assets(q: str = Query(...), scope: str = Query('all')):
    """
    联网搜索文化数字资产
    scope: local(本地数据库) | ai(AI联网检索) | all(全部)
    """
    results = {'query': q, 'scope': scope, 'local': [], 'ai_results': None}

    # 1. 搜索本地数据库（西安9项目 + 全国36项目）
    if scope in ('local', 'all'):
        all_local = []
        # 搜索9项目
        for p in collector.get_all_projects():
            text = json.dumps(p, ensure_ascii=False).lower()
            if q.lower() in text or any(q.lower() in kw.lower() for kw in p.get('category_tags', [])):
                all_local.append({**p, 'source_db': 'Xian 9 Projects'})

        # 搜索陕西省数据集
        if _load_shaanxi():
            for p in _load_shaanxi().get('projects', []):
                text = json.dumps(p, ensure_ascii=False).lower()
                if q.lower() in text or any(q.lower() in kw.lower() for kw in p.get('keywords', [])):
                    all_local.append({**_normalize_project(p), 'source_db': 'Shaanxi 110 Projects'})

        # 搜索全国数据集
        if _load_national():
            for p in _load_national().get('projects', []):
                text = json.dumps(p, ensure_ascii=False).lower()
                if q.lower() in text or any(q.lower() in kw.lower() for kw in p.get('keywords', [])):
                    all_local.append({**_normalize_project(p), 'source_db': 'National 122 Projects'})

        results['local'] = all_local[:20]  # 最多返回20条
        results['local_count'] = len(all_local)

    # 2. AI联网检索
    if scope in ('ai', 'all') and agent and agent.use_ai:
        try:
            ai_response = agent.client.chat.completions.create(
                model=agent.model,
                messages=[{
                    'role': 'system',
                    'content': '你是一个中国文化遗产数字资产的专家。请根据用户查询，提供相关的中国文化数字资产信息。如果查询的是具体的文物、非遗项目或文旅资源，请返回结构化的JSON信息。格式：{"name":"","type":"文物/非遗/文旅","province":"","description":"","digital_status":"","keywords":[],"source":""}。如果查询的是宽泛主题，可以返回多条结果。'
                }, {
                    'role': 'user',
                    'content': f'查询中国文化数字资产：{q}。请返回JSON格式的结构化信息。'
                }],
                temperature=0.3,
                max_tokens=2000
            )
            content = ai_response.choices[0].message.content
            # Try to extract JSON
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            try:
                ai_data = json.loads(content.strip())
                results['ai_results'] = ai_data if isinstance(ai_data, list) else [ai_data]
            except json.JSONDecodeError:
                results['ai_results'] = {'raw': content[:1000]}
        except Exception as e:
            results['ai_results'] = {'error': str(e)}

    results['total'] = len(results['local']) + (len(results['ai_results']) if isinstance(results['ai_results'], list) else 0)
    return results


@app.get('/api/search/national')
def list_national_projects(province: str = None, asset_type: str = None):
    """列出全国数据集项目"""
    if not _load_national():
        raise HTTPException(404, '全国数据集未加载')
    projects = _load_national().get('projects', [])
    if province:
        projects = [p for p in projects if province in p.get('province', '')]
    if asset_type:
        projects = [p for p in projects if p.get('asset_type') == asset_type]
    return {'total': len(projects), 'projects': projects, 'metadata': _load_national().get('metadata', {})}


@app.get('/api/search/stats')
def search_stats():
    """获取数据统计（含全国和陕西数据）"""
    xi_an = collector.generate_statistics()
    shaanxi_count = len(_load_shaanxi().get('projects', [])) if _load_shaanxi() else 0
    national_count = len(_load_national().get('projects', [])) if _load_national() else 0
    return {
        'xian_projects': xi_an['total_projects'],
        'shaanxi_projects': shaanxi_count,
        'national_projects': national_count,
        'total': xi_an['total_projects'] + shaanxi_count + national_count,
        'xian_types': xi_an['by_type'],
    }


# ===== 资产登记API =====
@app.get('/api/registry/certificates/{asset_id}')
def get_rights_certificate(asset_id: str):
    """获取数字权利证书HTML"""
    cert_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'data', '05_registry', f'{asset_id}_rights_certificate.html')
    if not os.path.exists(cert_path):
        raise HTTPException(404, f'证书未生成: {asset_id}')
    with open(cert_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(f.read())


@app.get('/api/registry/manifest')
def get_manifest():
    """获取资产清单"""
    manifest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'data', '05_registry', 'manifest.csv')
    if not os.path.exists(manifest_path):
        raise HTTPException(404, '资产清单未生成')
    return FileResponse(manifest_path, media_type='text/csv',
                       filename='xian_cultural_manifest.csv')


@app.get('/api/registry/asset-package')
def download_asset_package():
    """下载资产包zip"""
    zip_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'data', '04_assets', 'xian_cultural_assets.zip')
    if not os.path.exists(zip_path):
        raise HTTPException(404, '资产包未生成')
    return FileResponse(zip_path, media_type='application/zip',
                       filename='xian_cultural_assets.zip')


# ===== 西文小迈2.0对接方案 =====
@app.get('/api/xwenxiaomai/integration')
def xwenxiaomai_integration():
    """与西文小迈2.0的API对接方案说明"""
    return {
        'integration_plan': {
            'title': '与西文小迈2.0智能体对接方案',
            'roles': {
                '本系统': '文化内容供给侧 —— 负责9项目深度数据采集、JSON-LD元数据生成、多模态内容创作',
                '西文小迈2.0': '登记交易平台 —— 负责数字资产登记确权、交易撮合、合规审核',
            },
            'api_handoff': {
                'step1': '本系统输出标准JSON-LD资产包 →',
                'step2': '西文小迈2.0导入并验证 → ',
                'step3': '完成数字资产登记（五步流程）→',
                'step4': '上架交易 / 授权运营',
            },
            'data_format': 'JSON-LD with @context referencing west9-province standard v1.0',
            'compatibility': '元数据字段完全对标西部九省登记标准',
            'advantages': [
                '填补西文小迈2.0的内容创作空白 —— 本系统提供多模态AI内容生成能力',
                '标准化资产包可直接导入西文小迈的登记交易系统',
                '知识图谱增强跨领域关联搜索，丰富西文小迈的知识库',
            ]
        }
    }


# ===== 用户认证API =====

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ''

class LoginRequest(BaseModel):
    username: str
    password: str


def get_current_user(request: Request) -> dict | None:
    """从请求头提取当前用户（可选认证）"""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        payload = verify_token(token)
        if payload:
            return get_user_by_id(payload['user_id'])
    return None


def require_user(request: Request) -> dict:
    """强制认证（未登录抛401）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, '请先登录')
    return user


def require_admin(request: Request) -> dict:
    """强制管理员认证"""
    user = require_user(request)
    if user.get('role') != 'admin':
        raise HTTPException(403, '需要管理员权限')
    return user


@app.post('/api/auth/register')
def auth_register(req: RegisterRequest):
    """用户注册"""
    if len(req.username) < 2 or len(req.username) > 20:
        raise HTTPException(400, '用户名需2-20个字符')
    if len(req.password) < 6:
        raise HTTPException(400, '密码至少6位')
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE username=?", (req.username,)).fetchone()
    if existing:
        db.close()
        raise HTTPException(400, '用户名已存在')
    hashed = hash_password(req.password)
    db.execute("INSERT INTO users (username, password, email, role) VALUES (?,?,?,?)",
               (req.username, hashed, req.email, 'user'))
    db.commit()
    user = db.execute("SELECT id, username, email, role, avatar, created_at FROM users WHERE username=?",
                      (req.username,)).fetchone()
    db.close()
    user_dict = dict(user)
    token = create_token(user_dict['id'], user_dict['username'], user_dict['role'])
    return {'success': True, 'token': token, 'user': user_dict}


@app.post('/api/auth/login')
def auth_login(req: LoginRequest):
    """用户登录"""
    user = get_user_by_username(req.username)
    if not user or not verify_password(req.password, user['password']):
        raise HTTPException(401, '用户名或密码错误')
    token = create_token(user['id'], user['username'], user['role'])
    return {
        'success': True,
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'avatar': user['avatar'],
            'created_at': user['created_at'],
        }
    }


@app.get('/api/auth/me')
def auth_me(user: dict = Depends(require_user)):
    """获取当前用户信息"""
    return {'success': True, 'user': user}


# ===== 用户上传API =====

@app.post('/api/upload/create')
async def upload_create(
    request: Request,
    asset_name: str = Form(...),
    asset_type: str = Form('cultural_relic'),
    description: str = Form(''),
    city: str = Form(''),
    province: str = Form('陕西'),
    image: UploadFile | None = File(None),
):
    """用户上传资产"""
    user = require_user(request)

    # 保存图片
    image_path = ''
    if image and image.filename:
        upload_dir = os.path.join(BASE_DIR, 'frontend', 'public', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(image.filename)[1] or '.jpg'
        safe_name = f"{user['id']}_{int(datetime.now().timestamp())}_{hash(image.filename) % 10000}{ext}"
        save_path = os.path.join(upload_dir, safe_name)
        content = await image.read()
        if len(content) > 5 * 1024 * 1024:  # 5MB限制
            raise HTTPException(400, '图片大小不能超过5MB')
        with open(save_path, 'wb') as f:
            f.write(content)
        image_path = f'/uploads/{safe_name}'

    db = get_db()
    db.execute(
        "INSERT INTO uploads (user_id, asset_name, asset_type, description, city, province, image_path, status) VALUES (?,?,?,?,?,?,?,?)",
        (user['id'], asset_name, asset_type, description, city, province, image_path, 'pending')
    )
    db.commit()
    upload_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()

    return {'success': True, 'upload_id': upload_id, 'message': '提交成功，等待审核'}


@app.get('/api/upload/my')
def upload_my(request: Request):
    """我的上传列表"""
    user = require_user(request)
    db = get_db()
    rows = db.execute(
        "SELECT * FROM uploads WHERE user_id=? ORDER BY created_at DESC",
        (user['id'],)
    ).fetchall()
    db.close()
    return {'success': True, 'uploads': [dict(r) for r in rows]}


# ===== 管理员审核API =====

@app.get('/api/admin/pending')
def admin_pending(user: dict = Depends(require_admin)):
    """获取待审核列表"""
    db = get_db()
    rows = db.execute(
        """SELECT u.*, us.username as submitter_name
           FROM uploads u JOIN users us ON u.user_id = us.id
           ORDER BY u.created_at DESC"""
    ).fetchall()
    db.close()
    return {'success': True, 'uploads': [dict(r) for r in rows]}


@app.post('/api/admin/review')
async def admin_review(request: Request):
    """审核操作"""
    user = require_admin(request)

    body = await request.json()
    upload_id = body.get('upload_id')
    action = body.get('action')  # 'approve' | 'reject'
    remark = body.get('remark', '')

    if action not in ('approve', 'reject'):
        raise HTTPException(400, '操作只能是 approve 或 reject')

    db = get_db()
    upload = db.execute("SELECT * FROM uploads WHERE id=?", (upload_id,)).fetchone()
    if not upload:
        db.close()
        raise HTTPException(404, '上传记录不存在')

    new_status = 'approved' if action == 'approve' else 'rejected'
    db.execute(
        "UPDATE uploads SET status=?, reject_reason=?, reviewed_at=datetime('now','localtime') WHERE id=?",
        (new_status, remark if action == 'reject' else '', upload_id)
    )
    db.execute(
        "INSERT INTO audit_logs (upload_id, reviewer_id, action, remark) VALUES (?,?,?,?)",
        (upload_id, user['id'], action, remark)
    )

    # 审核通过 → 将资产添加到官网数据
    if action == 'approve':
        asset_id = f"USER-{upload_id:04d}"
        up = dict(upload)  # 转为普通dict
        import json as _json
        shaanxi_path = os.path.join(BASE_DIR, 'data', '01_raw', 'text', 'shaanxi_projects.json')
        if os.path.exists(shaanxi_path):
            with open(shaanxi_path, 'r', encoding='utf-8') as f:
                shaanxi_data = _json.load(f)

            submitter = up.get('submitter_name') or '用户投稿'

            new_project = {
                'asset_id': asset_id,
                'title': up['asset_name'],
                'title_en': '',
                'asset_type': up['asset_type'],
                'description': up['description'] or '',
                'detailed_description': up['description'] or '',
                'keywords': [up['asset_type'], up['city'], '用户投稿'],
                'cultural_elements': {
                    'period': '', 'material': '', 'technique': '',
                    'iconography': '', 'style': '', 'function': ''
                },
                'geolocation': {
                    'province': up['province'] or '陕西',
                    'city': up['city'] or '',
                    'district': '',
                    'site': up['asset_name'],
                    'lat': '', 'lng': ''
                },
                'historical_figures': [],
                'historical_events': [],
                'copyright_holder': submitter,
                'license': 'CC BY-NC-ND 4.0',
                'data_provenance': ['用户投稿，经平台审核'],
                'multimedia': {'images': {'urls': [up['image_path']], 'count': 1, 'description': up['asset_name']}} if up['image_path'] else {},
                'references': [],
                'registration_standard': '数字资产登记标准 v1.0',
                'source': f'用户 {submitter} 投稿，审核通过'
            }

            shaanxi_data['projects'].append(new_project)
            shaanxi_data['metadata']['total'] = len(shaanxi_data['projects'])
            shaanxi_data['metadata']['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(shaanxi_path, 'w', encoding='utf-8') as f:
                _json.dump(shaanxi_data, f, ensure_ascii=False, indent=2)

    db.commit()
    db.close()

    return {'success': True, 'message': '审核完成', 'new_status': new_status}


# ===== 启动入口 =====
if __name__ == '__main__':
    import uvicorn
    print('=' * 60)
    print('  西安文化数字资产平台 API v2.0')
    print('=' * 60)
    print(f'  数据: 9个深度文化项目')
    print(f'  智能体: {"DeepSeek AI" if agent and agent.use_ai else "规则引擎"}')
    print(f'  知识图谱: {"就绪" if KG_DATA else "待构建"}')
    print(f'  API文档: http://localhost:8000/docs')
    uvicorn.run(app, host='0.0.0.0', port=8000)
