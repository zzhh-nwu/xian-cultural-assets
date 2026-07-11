import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ChinaMap from './ChinaMap'
import { AuthProvider, useAuth } from './AuthContext'
import AuthPage from './AuthPage'
import UserCenter from './UserCenter'
import AdminPage from './AdminPage'

import API from './api'
const fadeIn = { initial:{opacity:0,y:20}, whileInView:{opacity:1,y:0}, viewport:{once:true,margin:'0px'}, transition:{duration:0.5,ease:'easeOut'} }
const pageIn = { initial:{opacity:0,y:16}, animate:{opacity:1,y:0}, transition:{duration:0.5,ease:[0.22,0.61,0.36,1]} }
const cardIn = (i) => ({ initial:{opacity:0,y:20}, whileInView:{opacity:1,y:0}, viewport:{once:true,margin:'0px'}, transition:{duration:0.4,delay:Math.min(i*0.04,0.2),ease:'easeOut'} })

function AppInner() {
  const { user, ready } = useAuth()
  const [page, setPage] = useState('dashboard')
  const [projects, setProjects] = useState([])
  const [kgStats, setKgStats] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [provinceFilter, setProvinceFilter] = useState(null)
  const [chatQuery, setChatQuery] = useState('')
  const [aiOpen, setAiOpen] = useState(false)
  const [showCover, setShowCover] = useState(true)

  const loadData = () => {
    setLoaded(false)
    fetch(`${API}/data/projects`).then(r=>r.json()).then(d=>{setProjects(d.projects||[]);setLoaded(true)})
    fetch(`${API}/kg/stats`).then(r=>r.json()).then(setKgStats).catch(()=>{})
  }

  useEffect(() => { loadData() }, [])
  useEffect(() => { window.scrollTo({top:0,behavior:'instant'}) }, [page])

  const enterApp = (province) => {
    setProvinceFilter(province||null)
    if(province) setPage('projects')
  }

  if (!ready) {
    return <div className="min-h-screen flex items-center justify-center" style={{background:'#1A1A2E'}}>
      <div className="text-sm gold-shimmer" style={{color:'rgba(201,169,110,0.5)'}}>加载中…</div>
    </div>
  }

  // ===== 封面页 =====
  if (showCover) {
    return (
      <motion.div
        initial={{opacity:0}} animate={{opacity:1}} transition={{duration:0.4}}
        onClick={() => setShowCover(false)}
        className="fixed inset-0 z-50 cursor-pointer overflow-hidden"
        style={{background:'linear-gradient(90deg, #f7ead4 0%, #d8a880 50%, #d79968 100%)'}}>
        <img src="/images/cover_raw.png" alt="封面"
          className="absolute inset-0 m-auto max-w-full max-h-full object-contain" />
      </motion.div>
    )
  }

  return (
    <motion.div key="app" initial={{opacity:0}} animate={{opacity:1}} transition={{duration:0.6}}
      className="min-h-screen relative" style={{background:'#1A1A2E'}}>
      <Nav page={page} setPage={setPage} onOpenAI={()=>setAiOpen(true)} />
      {page==='login' && <AuthPage onSuccess={()=>setPage('dashboard')} />}

      {page==='dashboard' && (
        <Dashboard projects={projects} kgStats={kgStats} setPage={setPage} onEnterProvince={enterApp} />
      )}

      {page!=='dashboard' && page!=='login' && (
        <main className="max-w-[1440px] mx-auto px-4 md:px-10 lg:px-20">
          <button
            onClick={() => setPage(page==='detail' ? 'projects' : 'dashboard')}
            className="mt-6 mb-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 flex items-center gap-2 btn-ghost">
            ← 返回{page==='detail'?'资产列表':'总览'}
          </button>
          {!loaded && page!=='detail' && <div className="text-center py-20 gold-shimmer" style={{color:'rgba(201,169,110,0.4)'}}>加载中…</div>}
          {page==='projects' && <Projects projects={projects} setPage={setPage} loaded={loaded} reload={loadData} provinceFilter={provinceFilter} setChatQuery={setChatQuery} />}
          {page==='detail' && <DetailPage projects={projects} setPage={setPage} setChatQuery={setChatQuery} />}
          {page==='kg' && <KnowledgeGraph kgStats={kgStats} />}
          {page==='chat' && <ChatPage initialQuery={chatQuery} />}
          {page==='user' && user && <UserCenter />}
          {page==='admin' && user?.role==='admin' && <AdminPage />}
          {page==='user' && !user && <AuthPage onSuccess={()=>setPage('user')} />}
        </main>
      )}
      <AIFloat projects={projects} open={aiOpen} setOpen={setAiOpen} />
    </motion.div>
  )
}

export default function App() {
  return <AuthProvider><AppInner /></AuthProvider>
}

// ==================== NAV ====================
function Nav({ page, setPage, onOpenAI }) {
  const { user, logout } = useAuth()
  const items = [['dashboard','01. 总览'],['projects','02. 资产'],['kg','03. 图谱'],['chat','04. 智能体查询']]
  return (
    <nav className="sticky top-0 z-40" style={{background:'rgba(26,26,46,0.88)',backdropFilter:'blur(24px)',WebkitBackdropFilter:'blur(24px)',borderBottom:'1px solid rgba(201,169,110,0.1)'}}>
      <div className="max-w-[1440px] mx-auto px-4 md:px-10 lg:px-20 flex items-center h-16">
        <button onClick={()=>setPage('dashboard')} className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center oriental-gold"
            style={{background:'linear-gradient(135deg, #8B3A3A, #6B2A2A)'}}>
            <span className="text-[#C9A96E] font-black text-lg" style={{fontFamily:"'Noto Serif SC',serif"}}>文</span>
          </div>
          <span className="text-base font-bold text-[#C9A96E] hidden md:inline tracking-wider" style={{fontFamily:"'Noto Serif SC',serif"}}>文化数字资产</span>
        </button>

        <div className="flex gap-1 ml-auto md:ml-0">
          {items.map(([k,v])=>(
            <button key={k} onClick={()=>setPage(k)}
              className={`px-5 md:px-7 py-2 text-sm font-semibold rounded-xl transition-all duration-300 ${
                page===k ? 'text-[#C9A96E]' : 'text-[#B8A99A] hover:text-[#C9A96E]'
              }`}
              style={page===k ? {background:'rgba(201,169,110,0.08)',border:'1px solid rgba(201,169,110,0.15)'} : {border:'1px solid transparent'}}>
              {v}
            </button>
          ))}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button onClick={onOpenAI} className="px-4 py-2 text-sm font-semibold rounded-xl btn-gold">
            🎨 AI 创作
          </button>
          {user ? (<>
            {user.role==='admin' && <button onClick={()=>setPage('admin')} className={`px-3 py-2 text-sm font-semibold rounded-xl transition-all ${page==='admin'?'text-[#C9A96E] glass-light':'text-[#B8A99A] hover:text-[#C9A96E]'}`}>⚙️</button>}
            <button onClick={()=>setPage('user')} className={`px-3 py-2 text-sm font-semibold rounded-xl transition-all ${page==='user'?'text-[#C9A96E] glass-light':'text-[#B8A99A] hover:text-[#C9A96E]'}`}>👤 {user.username}</button>
            <button onClick={()=>{logout();setPage('dashboard')}} className="text-xs text-[#9B8E82] hover:text-red-400 px-2 py-1 transition-colors">退出</button>
          </>) : (
            <button onClick={()=>setPage('login')} className="px-5 py-2 text-sm font-semibold rounded-xl btn-primary">🔐 登录</button>
          )}
        </div>
      </div>
    </nav>
  )
}

// ==================== DASHBOARD ====================
function Dashboard({ projects, kgStats, setPage, onEnterProvince }) {
  const imageMap = useImageMap()
  const tc = projects.reduce((a,p)=>({...a,[p.asset_type]:(a[p.asset_type]||0)+1}),{})
  const [bgIndex, setBgIndex] = useState(0)
  const [bgImages, setBgImages] = useState([])

  useEffect(() => {
    if (!imageMap) return
    const shuffled = [...Object.values(imageMap)]
    for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]] }
    setBgImages(shuffled.slice(0, 20))
  }, [imageMap])

  useEffect(() => {
    if (bgImages.length <= 1) return
    const timer = setInterval(() => setBgIndex(i => (i + 1) % bgImages.length), 6000)
    return () => clearInterval(timer)
  }, [bgImages])

  const heroSearch = () => {
    const v = document.getElementById('hero-search')?.value
    setPage('projects'); setTimeout(()=>{ window._heroSearch=v; window.dispatchEvent(new Event('heroSearch')) },100)
  }

  return (
    <div>
      {/* ===== Hero 首屏 — 全屏沉浸式 ===== */}
      <section className="relative h-screen flex flex-col items-center justify-center overflow-hidden">
        {/* 轮播背景 */}
        <AnimatePresence initial={false}>
          {bgImages.length > 0 ? (
            <motion.div key={bgIndex}
              initial={{x:'100%',opacity:0}} animate={{x:0,opacity:1}} exit={{x:'-100%',opacity:0}}
              transition={{duration:0.8,ease:[0.22,0.61,0.36,1]}}
              className="absolute inset-0 bg-cover bg-center"
              style={{backgroundImage:`url(${bgImages[bgIndex]}), linear-gradient(135deg, #1a0a0a 0%, #2d1810 30%, #1A1A2E 70%, #0a1628 100%)`}} />
          ) : (
            <div className="absolute inset-0" style={{background:'linear-gradient(135deg, #1a0a0a 0%, #2d1810 30%, #1A1A2E 70%, #0a1628 100%)'}} />
          )}
        </AnimatePresence>

        {/* 暗色叠层 — 博物馆暗展厅氛围 */}
        <div className="absolute inset-0" style={{background:'linear-gradient(to bottom, rgba(0,0,0,0.5) 0%, rgba(26,26,46,0.3) 40%, rgba(26,26,46,0.85) 85%, #1A1A2E 100%)'}} />

        {/* 金光线 — 展柜射灯感 */}
        <div className="absolute top-[15%] left-1/2 -translate-x-1/2 w-[60%] h-[1px] opacity-20"
          style={{background:'linear-gradient(90deg, transparent, #C9A96E, transparent)'}} />

        {/* 标题区 */}
        <motion.div initial={{opacity:0,y:30}} animate={{opacity:1,y:0}} transition={{duration:0.9,ease:'easeOut'}}
          className="relative z-10 text-center px-6 max-w-4xl -mt-24">
          <h1 className="text-[clamp(2rem,5.5vw,6rem)] text-[#E8E0D5] tracking-[0.03em] leading-[1.08] mb-3 whitespace-nowrap"
            style={{fontFamily:"'Noto Serif SC','Ma Shan Zheng',serif",textShadow:'0 4px 80px rgba(139,58,58,0.3)'}}>
            文物 / 非遗 / 文旅
          </h1>
          <h2 className="text-[clamp(2rem,5.5vw,6rem)] text-[#E8E0D5] tracking-[0.03em] leading-[1.08] mb-6"
            style={{fontFamily:"'Noto Serif SC','Ma Shan Zheng',serif",textShadow:'0 4px 80px rgba(139,58,58,0.3)'}}>
            数字资产平台
          </h2>
          <p className="text-lg md:text-xl text-[#B8A99A] mb-10 tracking-wide">
            让每一件文物都有数字身份，让每一项非遗都有数字传承
          </p>

          {/* 搜索栏 */}
          <div className="max-w-[560px] mx-auto">
            <div className="flex items-center rounded-2xl overflow-hidden" style={{background:'rgba(37,37,56,0.6)',backdropFilter:'blur(16px)',border:'1px solid rgba(201,169,110,0.2)',boxShadow:'0 8px 48px rgba(0,0,0,0.4)'}}>
              <input id="hero-search" type="text" placeholder="搜索文物、非遗、文旅…"
                onKeyDown={e => e.key==='Enter' && heroSearch()}
                className="flex-1 px-6 py-4 text-base font-medium bg-transparent outline-none text-[#E8E0D5] placeholder:text-[#9B8E82]" />
              <button onClick={heroSearch}
                className="font-semibold text-sm px-8 py-4 m-1.5 rounded-xl btn-gold">搜索</button>
            </div>
          </div>
        </motion.div>

        {/* 向下滚动提示 */}
        <motion.div animate={{opacity:[0.3,0.8,0.3],y:[0,6,0]}} transition={{duration:3,repeat:Infinity}}
          className="absolute bottom-8 z-10 text-[#9B8E82] text-xs tracking-widest">
          ↓ 向下浏览
        </motion.div>
      </section>

      {/* ===== 统计面板 — 展柜风格 ===== */}
      <section className="max-w-[1440px] mx-auto px-4 md:px-10 lg:px-20 -mt-16 relative z-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
          <StatExhibit label="文物资产" value={tc.cultural_relic||0} icon="🏺" color="#8B3A3A" />
          <StatExhibit label="非遗资产" value={tc.intangible_heritage||0} icon="🎭" color="#C9A96E" />
          <StatExhibit label="文旅资产" value={tc.cultural_tourism||0} icon="🏯" color="#D4A574" />
          <StatExhibit label="知识图谱节点" value={kgStats?.total_nodes||'…'} icon="🔮" color="#A78BFA" />
        </div>
      </section>

      {/* ===== 地图 ===== */}
      <section className="max-w-[1440px] mx-auto px-4 md:px-10 lg:px-20 py-16">
        <div className="text-center mb-8">
          <span className="text-xs font-bold tracking-[0.25em] text-[#C9A96E] uppercase">Cultural Digital Asset Map</span>
          <h2 className="text-3xl md:text-4xl font-black text-[#E8E0D5] mt-3 mb-2" style={{fontFamily:"'Noto Serif SC',serif"}}>中国文化数字资产地图</h2>
          <p className="text-sm text-[#B8A99A]">{projects.length} 个项目 · {Object.keys(projects.reduce((a,p)=>{const r=p.geolocation?.province||p.province||'';if(r)a[r]=(a[r]||0)+1;return a},{})).length} 省份</p>
        </div>
        <ChinaMap projects={projects} onEnter={onEnterProvince} inline />
      </section>
    </div>
  )
}

function StatExhibit({ label, value, icon, color }) {
  return (
    <motion.div {...fadeIn} className="glass p-5 md:p-6 text-center group cursor-default transition-all duration-500 hover:border-[#C9A96E]/30"
      style={{border:'1px solid rgba(201,169,110,0.12)'}}>
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-3xl md:text-4xl font-black mb-1" style={{color,fontFamily:"'JetBrains Mono',monospace"}}>{value}</div>
      <div className="text-xs md:text-sm font-semibold text-[#B8A99A] tracking-wider">{label}</div>
    </motion.div>
  )
}

// ===== 图片映射 =====
let _imageMap = null; let _imageMapLoading = false
function useImageMap() {
  const [map, setMap] = useState(_imageMap)
  useEffect(() => {
    if (_imageMap) return
    if (_imageMapLoading) { const check = setInterval(() => { if (_imageMap) { setMap(_imageMap); clearInterval(check) } }, 100); return () => clearInterval(check) }
    _imageMapLoading = true
    fetch('/image_map.json').then(r=>r.json()).then(d=>{_imageMap=d;setMap(d)}).catch(()=>{_imageMap={};setMap({})})
  }, [])
  return map
}

// ==================== MUSEUM ASSET CARD ====================
function AssetCard({ project }) {
  const imageMap = useImageMap()
  const tl = {cultural_relic:'文物',intangible_heritage:'非遗',cultural_tourism:'文旅'}
  const tc = {cultural_relic:'#8B3A3A',intangible_heritage:'#C9A96E',cultural_tourism:'#D4A574'}
  const imgSrc = imageMap?.[project.asset_id] || ''

  return (
    <div className="museum-card cursor-pointer group h-full flex flex-col">
      {/* 图片区 — 展品橱窗 */}
      <div className="relative h-60 sm:h-72 overflow-hidden">
        {imgSrc ? (
          <img src={imgSrc} alt={project.title} className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-5xl" style={{background:'rgba(45,45,66,0.6)'}}>🏛️</div>
        )}
        {/* 底部渐变 + 标签 */}
        <div className="absolute inset-x-0 bottom-0 p-4" style={{background:'linear-gradient(to top, rgba(26,26,46,0.95), transparent)'}}>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-white px-2.5 py-1 rounded-md" style={{background:tc[project.asset_type]}}>{tl[project.asset_type]}</span>
            <span className="text-[10px] font-mono text-white/50">{project.asset_id}</span>
          </div>
          <h3 className="text-sm font-bold text-white mt-1.5 line-clamp-1">{project.title}</h3>
        </div>

        {/* 悬停面板 — 展品信息 */}
        <motion.div initial={{y:'100%'}} whileHover={{y:0}} transition={{duration:0.4,ease:[0.22,0.61,0.36,1]}}
          className="absolute inset-0 flex flex-col justify-end p-5"
          style={{background:'linear-gradient(to top, rgba(26,26,46,0.98) 0%, rgba(26,26,46,0.85) 60%, rgba(37,37,56,0.7) 100%)',backdropFilter:'blur(4px)',pointerEvents:'none'}}>
          <div className="w-8 h-[2px] mb-3" style={{background:'#C9A96E'}} />
          <p className="text-xs text-[#B8A99A] leading-relaxed line-clamp-3 mb-3">{project.description}</p>
          <div className="flex items-center gap-2 text-[10px] text-[#9B8E82] mb-3">
            <span>📍 {(project.geolocation?.province||'')} {(project.geolocation?.city||'')}</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {(project.category_tags||[]).slice(0,3).map(t=>(
              <span key={t} className="text-[10px] font-medium px-2.5 py-1 rounded-full" style={{background:'rgba(201,169,110,0.1)',color:'#C9A96E'}}>{t}</span>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

// ==================== PROJECTS ====================
function Projects({ projects, setPage, loaded, reload, provinceFilter, setChatQuery }) {
  const [filter, setFilter] = useState(provinceFilter?'all':'all')
  const [q, setQ] = useState(provinceFilter||'')
  const [aiR, setAiR] = useState(null)
  const [loading, setLoading] = useState(false)
  const tl = {cultural_relic:'文物',intangible_heritage:'非遗',cultural_tourism:'文旅'}

  useEffect(() => {
    const handler = () => { if(window._heroSearch){ setQ(window._heroSearch); window._heroSearch='' } }
    window.addEventListener('heroSearch', handler); return () => window.removeEventListener('heroSearch', handler)
  }, [])

  if(!loaded || projects.length===0) return (
    <div className="py-20 text-center">
      <h1 className="text-4xl font-black text-[#E8E0D5] mb-4" style={{fontFamily:"'Noto Serif SC',serif"}}>数字资产浏览</h1>
      <p className="text-[#B8A99A] mb-6">数据加载中…</p>
      <button onClick={reload} className="px-6 py-3 rounded-xl btn-primary">重新加载</button>
    </div>
  )

  let filtered = filter==='all' ? projects : projects.filter(p=>p.asset_type===filter)
  if(q.trim()){ const ql=q.toLowerCase(); filtered=filtered.filter(p=>p.title?.toLowerCase().includes(ql)||p.description?.toLowerCase().includes(ql)||(p.category_tags||[]).some(t=>t.toLowerCase().includes(ql))||(p.geolocation?.province||'').includes(q)||(p.geolocation?.city||'').includes(q)) }

  const doAI = async () => { if(!q.trim())return; setLoading(true); try{const r=await fetch(`${API}/search?q=${encodeURIComponent(q)}&scope=ai`);setAiR(await r.json())}catch(e){}; setLoading(false) }

  return (
    <motion.div {...pageIn} className="py-12">
      <div className="text-center mb-10">
        <span className="text-xs font-bold tracking-[0.25em] text-[#C9A96E] uppercase">Asset Gallery</span>
        <h1 className="text-4xl md:text-5xl font-black text-[#E8E0D5] mt-3 mb-2" style={{fontFamily:"'Noto Serif SC',serif"}}>数字资产浏览</h1>
        <p className="text-sm text-[#B8A99A]">{filtered.length} / {projects.length} 个项目</p>
      </div>

      {/* 搜索 + AI */}
      <div className="max-w-[640px] mx-auto mb-4">
        <div className="flex rounded-2xl overflow-hidden glass">
          <input value={q} onChange={e=>setQ(e.target.value)} placeholder="搜索文物、非遗、文旅…"
            className="flex-1 px-5 py-3.5 text-sm font-medium outline-none bg-transparent text-[#E8E0D5] placeholder:text-[#9B8E82]" />
          <button onClick={doAI} disabled={loading} className="text-[#1A1A2E] text-xs font-semibold px-6 btn-gold rounded-none">{loading?'检索中':'AI 搜索'}</button>
        </div>
      </div>

      {/* 快捷标签 */}
      <div className="flex flex-wrap justify-center gap-1.5 mb-4">
        {['敦煌','云冈','故宫','长城','三星堆','昆曲','良渚','布达拉宫'].map(t=>(
          <button key={t} onClick={()=>setQ(t)} className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-300 ${q===t?'text-[#C9A96E] bg-[#C9A96E]/10 border-[#C9A96E]/30':'text-[#B8A99A] border-transparent hover:text-[#C9A96E]'} border`}>{t}</button>
        ))}
        {q&&<button onClick={()=>{setQ('');setAiR(null)}} className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-[#C9A96E]/30 text-[#C9A96E] btn-ghost">✕ 清除</button>}
      </div>

      {/* 类型筛选 */}
      <div className="flex justify-center gap-2 mb-10 flex-wrap">
        {[['all','全部'],...Object.entries(tl)].map(([k,v])=>(
          <button key={k} onClick={()=>setFilter(k)} className={`px-5 py-2 rounded-xl text-xs font-semibold border transition-all duration-300 ${filter===k?'text-[#C9A96E] border-[#C9A96E]/30':'text-[#B8A99A] border-transparent hover:text-[#C9A96E]'}`}
            style={filter===k?{background:'rgba(201,169,110,0.08)'}:{}}>
            {v}（{k==='all'?projects.length:projects.filter(p=>p.asset_type===k).length}）
          </button>
        ))}
      </div>

      {/* 展品网格 */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
        {filtered.map((p,i)=>(
          <motion.div key={p.asset_id} {...cardIn(i)} onClick={()=>{window._selProject=p.asset_id;setPage('detail')}}
            className="cursor-pointer h-full">
            <AssetCard project={p} />
          </motion.div>
        ))}
        {filtered.length===0 && q.trim() && (
          <motion.div {...cardIn(0)} onClick={()=>{setChatQuery(q);setPage('chat')}}
            className="col-span-full glass p-12 cursor-pointer hover:border-[#C9A96E]/30 transition-all group flex flex-col items-center text-center"
            style={{border:'1px dashed rgba(201,169,110,0.25)'}}>
            <div className="text-5xl mb-4">🤖</div>
            <h3 className="text-lg font-bold text-[#E8E0D5] mb-2">暂时无详细信息</h3>
            <p className="text-sm text-[#B8A99A] mb-5">数据库中未找到 "{q}" 的相关资产</p>
            <span className="px-6 py-3 rounded-xl btn-gold text-sm">点击 AI 智能查询 →</span>
          </motion.div>
        )}
      </div>

      {/* AI 搜索结果 */}
      {aiR?.ai_results && (
        <div className="mt-14">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-[2px]" style={{background:'#C9A96E'}} />
            <h3 className="text-lg font-black text-[#C9A96E]">🤖 AI 搜索结果：「{q}」</h3>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {(Array.isArray(aiR.ai_results)?aiR.ai_results:[aiR.ai_results]).map((r,i)=>(
              <div key={i} className="glass p-5">
                <h4 className="text-sm font-bold text-[#E8E0D5] mb-2">{r.name||r.title||'—'}</h4>
                <span className="text-xs font-semibold px-2 py-1 rounded-md" style={{background:'rgba(201,169,110,0.1)',color:'#C9A96E'}}>{r.type||'未知'}</span>
                {r.province&&<p className="text-xs text-[#B8A99A] mt-2">{r.province}</p>}
                <p className="text-xs text-[#9B8E82] mt-1 line-clamp-3">{r.description?.substring(0,150)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}

// ==================== CHAT PAGE ====================
function ChatPage({ initialQuery }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState(initialQuery || '')
  const [loading, setLoading] = useState(false)
  const [img, setImg] = useState(null)
  const chatEndRef = useRef(null)
  const fileRef = useRef(null)

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const pickImage = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    if (f.size > 10*1024*1024) { alert('图片不超过10MB'); return }
    const r = new FileReader()
    r.onload = () => setImg({ b64: r.result.split(',')[1], url: r.result })
    r.readAsDataURL(f)
    e.target.value = ''
  }

  const sendMessage = async (text) => {
    const q = text || input.trim()
    if ((!q && !img) || loading) return
    const imgUrl = img?.url || ''
    setMessages(m => [...m, { role: 'user', content: q || '请识别这张图片', image: imgUrl }])
    setInput(''); setImg(null); setLoading(true)
    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }))
      const body = { query: q, history }
      if (imgUrl) body.image = img?.b64 || ''
      const r = await fetch(`${API}/agent/chat`, { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) })
      const d = await r.json()
      setMessages(m => [...m, { role:'assistant', content: d.success ? d.answer : ('抱歉：'+(d.error||'未知错误')) }])
    } catch(e) { setMessages(m => [...m, { role:'assistant', content:'网络请求失败' }]) }
    setLoading(false)
  }

  return (
    <motion.div {...pageIn} className="py-12 max-w-3xl mx-auto">
      <div className="text-center mb-8">
        <span className="text-xs font-bold tracking-[0.25em] text-[#C9A96E] uppercase">AI Intelligence</span>
        <h1 className="text-3xl md:text-4xl font-black text-[#E8E0D5] mt-3 mb-2" style={{fontFamily:"'Noto Serif SC',serif"}}>DeepSeek + 豆包视觉</h1>
        <p className="text-sm text-[#B8A99A]">文字问答走 DeepSeek · 上传图片走豆包视觉识别</p>
      </div>

      <div className="glass overflow-hidden mb-4" style={{minHeight:'520px'}}>
        <div className="h-[480px] overflow-y-auto p-6 space-y-4">
          {messages.length===0 && (
            <div className="text-center py-24">
              <div className="text-5xl mb-5 gold-shimmer">🤖</div>
              <p className="text-sm text-[#9B8E82]">输入问题，或上传图片让AI识别文化内容</p>
            </div>
          )}
          {messages.map((m,i)=>(
            <motion.div key={i} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}
              className={`flex ${m.role==='user'?'justify-end':'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 ${m.role==='user'?'rounded-br-md':'rounded-bl-md'}`}
                style={m.role==='user'
                  ? {background:'linear-gradient(135deg, #8B3A3A, #6B2A2A)',color:'#fff',boxShadow:'0 4px 16px rgba(139,58,58,0.2)'}
                  : {background:'rgba(45,45,66,0.7)',border:'1px solid rgba(201,169,110,0.1)',color:'#E8E0D5'}}>
                {m.image && <img src={m.image} className="max-w-[200px] max-h-[200px] rounded-xl mb-2 object-cover" />}
                <div className="text-sm leading-relaxed whitespace-pre-wrap">{m.content}</div>
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md px-5 py-3.5" style={{background:'rgba(45,45,66,0.7)',border:'1px solid rgba(201,169,110,0.1)'}}>
                <div className="flex items-center gap-2 text-sm">
                  <span className="w-2 h-2 rounded-full animate-bounce" style={{background:'#C9A96E'}} />
                  <span className="w-2 h-2 rounded-full animate-bounce" style={{background:'#C9A96E',animationDelay:'0.1s'}} />
                  <span className="w-2 h-2 rounded-full animate-bounce" style={{background:'#C9A96E',animationDelay:'0.2s'}} />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* 图片预览 */}
        {img && (
          <div className="px-4 pt-2 flex items-center gap-2">
            <div className="relative inline-block">
              <img src={img.url} className="w-16 h-16 rounded-xl object-cover" style={{border:'2px solid #C9A96E'}} />
              <button onClick={()=>setImg(null)} className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center">×</button>
            </div>
            <span className="text-xs text-[#B8A99A]">图片已就绪</span>
          </div>
        )}

        {/* 输入区 */}
        <div className="p-4 flex gap-3 items-center" style={{borderTop:'1px solid rgba(201,169,110,0.1)'}}>
          <input ref={fileRef} type="file" accept="image/*" onChange={pickImage} className="hidden" />
          <button onClick={()=>fileRef.current?.click()} disabled={loading}
            className={`shrink-0 w-11 h-11 rounded-xl font-bold text-lg flex items-center justify-center transition-all ${img ? 'btn-gold' : 'btn-ghost'}`}
            title="上传图片识别">🖼️</button>
          <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&sendMessage()}
            placeholder={img ? '描述你想了解的内容（可留空）…' : '输入问题，或上传图片识别…'}
            className="flex-1 px-4 py-3 rounded-xl text-sm font-medium outline-none bg-transparent text-[#E8E0D5] placeholder:text-[#9B8E82]"
            style={{border:'1px solid rgba(201,169,110,0.15)'}} />
          <button onClick={()=>sendMessage()} disabled={loading||(!input.trim()&&!img)}
            className="font-semibold text-sm px-6 py-3 rounded-xl btn-primary disabled:opacity-40">发送</button>
        </div>
      </div>
    </motion.div>
  )
}

// ==================== DETAIL PAGE ====================
function DetailPage({ projects, setPage, setChatQuery }) {
  const imageMap = useImageMap()
  const [selId, setSelId] = useState(window._selProject||'XA-REL-001')
  const p = projects.find(x=>x.asset_id===selId) || projects[0]
  const tl = {cultural_relic:'文物',intangible_heritage:'非遗',cultural_tourism:'文旅'}
  const tc = {cultural_relic:'#8B3A3A',intangible_heritage:'#C9A96E',cultural_tourism:'#D4A574'}
  const heroImg = imageMap?.[p?.asset_id] || ''

  return (
    <motion.div {...pageIn} className="py-10 max-w-[1200px] mx-auto">
      {/* 缩略导航 */}
      <div className="flex gap-1.5 mb-10 overflow-x-auto pb-2">
        {projects.map(proj=>(
          <button key={proj.asset_id} onClick={()=>setSelId(proj.asset_id)}
            className={`shrink-0 px-4 py-2 text-xs font-semibold rounded-full border transition-all duration-300 ${
              selId===proj.asset_id ? 'text-[#C9A96E] border-[#C9A96E]/40' : 'text-[#B8A99A] border-transparent hover:text-[#C9A96E]'
            }`}
            style={selId===proj.asset_id?{background:'rgba(201,169,110,0.1)'}:{}}>
            {proj.title}
          </button>
        ))}
      </div>

      {p && (
        <article>
          {/* Hero 大图 — 博物馆展品主图 */}
          <div className="relative rounded-3xl overflow-hidden mb-12" style={{height:'55vh',minHeight:'420px'}}>
            {heroImg ? (
              <img src={heroImg} alt={p.title} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-8xl" style={{background:'rgba(45,45,66,0.6)'}}>🏛️</div>
            )}
            {/* 顶光效果 */}
            <div className="absolute inset-0" style={{background:'radial-gradient(ellipse at 50% 0%, transparent 40%, rgba(26,26,46,0.6) 100%)'}} />
            {/* 底栏 */}
            <div className="absolute inset-x-0 bottom-0 p-8 md:p-12" style={{background:'linear-gradient(to top, rgba(26,26,46,0.95) 0%, transparent 100%)'}}>
              <div className="flex items-center gap-3 mb-3">
                <span className="text-sm font-bold text-white px-3 py-1 rounded-lg" style={{background:tc[p.asset_type]}}>{tl[p.asset_type]}</span>
                <span className="text-sm font-mono text-white/40">{p.asset_id}</span>
              </div>
              <h1 className="text-3xl md:text-5xl lg:text-6xl font-black text-white tracking-tight" style={{fontFamily:"'Noto Serif SC',serif"}}>{p.title}</h1>
            </div>
          </div>

          {/* 位置 + 关键信息行 */}
          <div className="mb-12">
            <p className="text-lg text-[#B8A99A] mb-8">📍 {p.geolocation?.province||''} · {p.geolocation?.city||''}{p.geolocation?.site?' · '+p.geolocation.site:''}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {[
                ['朝代', p.cultural_elements?.period],
                ['材质', p.cultural_elements?.material],
                ['技艺', p.cultural_elements?.technique],
                ['风格', p.cultural_elements?.style||p.cultural_elements?.iconography],
              ].map(([label,value])=>(
                <div key={label} className="group cursor-default">
                  <div className="text-xs font-bold text-[#9B8E82] uppercase tracking-[0.2em] mb-2">{label}</div>
                  <div className="text-xl font-black text-[#E8E0D5] group-hover:text-[#C9A96E] transition-colors">{value||'—'}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 正文 + 侧栏 */}
          <div className="grid md:grid-cols-[7fr_4fr] gap-12 md:gap-16">
            <div>
              <h2 className="text-2xl md:text-3xl font-black text-[#E8E0D5] mb-6" style={{fontFamily:"'Noto Serif SC',serif"}}>📖 资产介绍</h2>
              <p className="text-xl text-[#B8A99A] leading-relaxed mb-6">{p.description}</p>
              {p.detailed_description && p.detailed_description !== p.description && (
                <p className="text-lg text-[#9B8E82] leading-relaxed pt-6" style={{borderTop:'1px solid rgba(201,169,110,0.1)'}}>{p.detailed_description}</p>
              )}
              <div className="mt-8 pt-6 flex flex-wrap gap-2" style={{borderTop:'1px solid rgba(201,169,110,0.1)'}}>
                {(p.category_tags||[]).map(t=>(
                  <span key={t} className="text-sm font-medium px-4 py-2 rounded-full" style={{background:'rgba(201,169,110,0.08)',color:'#C9A96E'}}>#{t}</span>
                ))}
              </div>
            </div>

            {/* 侧栏 */}
            <div className="glass p-6 md:p-8 space-y-6 h-fit">
              <div>
                <div className="text-xs font-bold text-[#9B8E82] uppercase tracking-[0.2em] mb-3">地理位置</div>
                <div className="text-2xl font-black text-[#E8E0D5] mb-1">{p.geolocation?.city||p.geolocation?.province||'—'}</div>
                <div className="text-sm text-[#B8A99A]">{p.geolocation?.province||''}{p.geolocation?.site?' · '+p.geolocation.site:''}</div>
              </div>
              <hr className="hr-gold" />
              <div>
                <div className="text-xs font-bold text-[#9B8E82] uppercase tracking-[0.2em] mb-3">版权信息</div>
                <div className="text-base font-bold text-[#E8E0D5] mb-1">{p.copyright_holder||'—'}</div>
                <div className="text-sm text-[#9B8E82]">{p.license||''}</div>
              </div>
              {p.historical_figures?.length>0 && (<>
                <hr className="hr-gold" />
                <div>
                  <div className="text-xs font-bold text-[#9B8E82] uppercase tracking-[0.2em] mb-3">相关人物</div>
                  <div className="flex flex-wrap gap-2">
                    {p.historical_figures.map((f,i)=>(<span key={i} className="text-sm font-bold px-4 py-2 rounded-full" style={{background:'rgba(201,169,110,0.12)',color:'#C9A96E'}}>{f}</span>))}
                  </div>
                </div>
              </>)}
              {p.historical_events?.length>0 && (<>
                <hr className="hr-gold" />
                <div>
                  <div className="text-xs font-bold text-[#9B8E82] uppercase tracking-[0.2em] mb-3">历史事件</div>
                  <div className="flex flex-wrap gap-2">
                    {p.historical_events.map((e,i)=>(<span key={i} className="text-sm font-bold px-4 py-2 rounded-full" style={{background:'rgba(139,58,58,0.12)',color:'#D4A574'}}>{e}</span>))}
                  </div>
                </div>
              </>)}
            </div>
          </div>

          {/* AI 查询横幅 */}
          <div className="mt-14 rounded-3xl p-8 md:p-10 flex flex-col sm:flex-row items-center justify-between gap-4"
            style={{background:'linear-gradient(135deg, rgba(139,58,58,0.15), rgba(201,169,110,0.08))',border:'1px solid rgba(201,169,110,0.15)'}}>
            <div>
              <h3 className="text-xl font-black text-[#E8E0D5] mb-1">🤖 想了解更多？</h3>
              <p className="text-base text-[#B8A99A]">使用 AI 智能体搜索「{p.title}」的更多深度信息</p>
            </div>
            <button onClick={()=>{setChatQuery(p.title);setPage('chat')}}
              className="shrink-0 px-8 py-3.5 rounded-xl btn-gold text-base">查询智能体 →</button>
          </div>

          {/* 底栏 */}
          <div className="mt-8 flex justify-between items-center text-sm text-[#9B8E82]">
            <span>{p.registration_standard}</span>
            <span className="flex items-center gap-1.5 font-bold" style={{color:'#C9A96E'}}>
              <span className="w-2 h-2 rounded-full" style={{background:'#C9A96E'}}/> 已验证资产
            </span>
          </div>
        </article>
      )}
    </motion.div>
  )
}

// ==================== KNOWLEDGE GRAPH ====================
function KnowledgeGraph({ kgStats }) {
  const containerRef = useRef(null)
  const networkRef = useRef(null)
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [searchText, setSearchText] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState(null)

  // 加载全量数据
  useEffect(() => {
    fetch(`${API}/kg/full`)
      .then(r => r.json())
      .then(d => { setGraphData(d); setLoading(false) })
      .catch(e => { console.error('KG load error:', e); setError('知识图谱数据加载失败'); setLoading(false) })
  }, [])

  // 初始化 vis-network
  useEffect(() => {
    if (!graphData || !containerRef.current || networkRef.current) return
    if (typeof vis === 'undefined' || !vis.Network) {
      setError('vis-network 库未加载，请刷新页面重试')
      setLoading(false)
      return
    }
    try {
    const nodes = new vis.DataSet(graphData.nodes.map(n => ({
      id: n.id,
      label: n.label,
      group: n.group,
      title: `<b>${n.label}</b><br/>类型: ${n.type_cn}<br/>${n.tags?.slice(0,3).join(' / ')||''}`,
      color: n.color,
      font: { size: 11, face: 'Microsoft YaHei, sans-serif' },
    })))
    const edges = new vis.DataSet(graphData.edges.map(e => ({
      id: e.from + '__' + e.to,
      from: e.from,
      to: e.to,
      label: e.label,
      font: { size: 8, color: '#888' },
      arrows: { to: { enabled: true, scaleFactor: 0.5 } },
      color: { color: 'rgba(201,169,110,0.25)', highlight: '#C9A96E', hover: '#C9A96E' },
      width: 0.6,
    })))
    const options = {
      nodes: {
        shape: 'dot',
        size: 14,
        borderWidth: 1.5,
        borderWidthSelected: 3,
        color: { border: '#1A1A2E', background: '#8B3A3A' },
        font: { color: '#E8E0D5', strokeWidth: 0 },
      },
      edges: {
        smooth: { type: 'continuous' },
        hoverWidth: 1.5,
        selectionWidth: 1,
      },
      physics: {
        enabled: true,
        solver: 'barnesHut',
        barnesHut: { gravitationalConstant: -1800, centralGravity: 0.2, springLength: 120, springConstant: 0.02 },
        stabilization: { iterations: 200, updateInterval: 10 },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
        navigationButtons: false,
      },
      groups: graphData.type_colors ? {} : undefined,
    }
    // 设置分组颜色
    if (graphData.type_colors) {
      for (const [g, c] of Object.entries(graphData.type_colors)) {
        options.groups[g] = { color: { background: c, border: c, highlight: { background: c, border: '#fff' } } }
      }
    }
    const network = new vis.Network(containerRef.current, { nodes, edges }, options)
    networkRef.current = network

    // 点击节点
    network.on('click', function (params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0]
        const node = graphData.nodes.find(n => n.id === nodeId)
        setSelectedNode(node)
        // 高亮：关联节点和边彩色，其余变暗
        const connected = new Set(network.getConnectedNodes(nodeId))
        connected.add(nodeId)
        const connectedEdges = new Set(network.getConnectedEdges(nodeId))
        nodes.update(graphData.nodes.map(n => ({
          id: n.id,
          color: connected.has(n.id) ? n.color : 'rgba(100,100,100,0.15)',
          font: { color: connected.has(n.id) ? '#E8E0D5' : 'rgba(150,150,150,0.2)' },
        })))
        edges.update(graphData.edges.map(e => ({
          id: e.from + '__' + e.to,
          color: connectedEdges.has(e.from + '__' + e.to)
            ? { color: '#C9A96E', highlight: '#fff' }
            : { color: 'rgba(100,100,100,0.04)' },
          width: connectedEdges.has(e.from + '__' + e.to) ? 1.2 : 0.3,
        })))
      } else {
        setSelectedNode(null)
        // 恢复全部
        nodes.update(graphData.nodes.map(n => ({ id: n.id, color: n.color, font: { color: '#E8E0D5' } })))
        edges.update(graphData.edges.map(e => ({
          id: e.from + '__' + e.to,
          color: { color: 'rgba(201,169,110,0.25)', highlight: '#C9A96E', hover: '#C9A96E' },
          width: 0.6,
        })))
      }
    })

    // 双击重置视图
    network.on('doubleClick', () => {
      setSelectedNode(null)
      nodes.update(graphData.nodes.map(n => ({ id: n.id, color: n.color, font: { color: '#E8E0D5' } })))
      edges.update(graphData.edges.map(e => ({
        id: e.from + '__' + e.to,
        color: { color: 'rgba(201,169,110,0.25)', highlight: '#C9A96E', hover: '#C9A96E' },
        width: 0.6,
      })))
      network.fit({ animation: { duration: 800, easingFunction: 'easeInOutQuad' } })
    })
    } catch(e) {
      console.error('vis-network init error:', e)
      setError('图谱渲染失败: ' + (e.message || '未知错误'))
      setLoading(false)
    }
  }, [graphData])

  // 搜索
  const doSearch = async () => {
    if (!searchText.trim()) return
    setSearching(true); setSearchResult(null)
    try {
      const r = await fetch(`${API}/kg/query?entity_name=${encodeURIComponent(searchText)}&max_depth=2`)
      if (!r.ok) { setSearchResult({ error: `未找到与"${searchText}"相关的实体` }); setSearching(false); return }
      const d = await r.json()
      setSearchResult(d)
      // 在图里定位第一个结果
      if (d.results?.[0] && networkRef.current) {
        networkRef.current.selectNodes([d.results[0].node_id])
        networkRef.current.focus(d.results[0].node_id, { animation: true, scale: 1.5 })
      }
    } catch (e) { setSearchResult({ error: '搜索失败' }) }
    setSearching(false)
  }

  const nt = kgStats?.node_types || {}
  const et = kgStats?.edge_types || {}
  const cnNames = {related_to:'相关人物',uses_technique:'使用技艺',created_in:'创作时期',located_in:'位于',participates_in:'参与事件',derived_digital_asset:'衍生数字资产',cultural_link:'文化关联',contains:'层级包含'}
  const ntCn = {cultural_relic:'文物',cultural_tourism:'文旅',intangible_heritage:'非遗','传承人/历史人物':'传承人/人物','工艺技术':'工艺技术','时间时期':'时间时期','地理区位':'地理区位','展览活动/历史事件':'展览/事件','数字资产':'数字资产'}
  const maxV = Math.max(1,...Object.values(et))

  return (
    <div className="py-12">
      <div className="text-center mb-8">
        <span className="text-xs font-bold tracking-[0.25em] text-[#C9A96E] uppercase">Knowledge Graph</span>
        <h1 className="text-4xl md:text-5xl font-black text-[#E8E0D5] mt-3 mb-2" style={{fontFamily:"'Noto Serif SC',serif"}}>知识图谱 <span className="text-xs font-mono text-[#C9A96E]/60 align-top">v2</span></h1>
        <p className="text-sm text-[#B8A99A]">{kgStats?.total_nodes||"…"} 节点 · {kgStats?.total_edges||"…"} 条边 · {Object.keys(nt).length||"…"} 种实体 · {Object.keys(et).length||"…"} 种关系</p>
      </div>

      {/* 统计卡片 */}
      {kgStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            ['🔵','节点总数',kgStats.total_nodes,'#C9A96E'],
            ['🔗','边总数',kgStats.total_edges,'#8B3A3A'],
            ['📦','实体类型',Object.keys(nt).length,'#D4A574'],
            ['🔀','关系类型',Object.keys(et).length,'#A78BFA'],
          ].map(([icon,label,value,color])=>(
            <div key={label} className="glass p-5 md:p-6 text-center transition-all duration-500 hover:border-[#C9A96E]/30">
              <div className="text-2xl mb-2">{icon}</div>
              <div className="text-3xl font-black mb-1" style={{color,fontFamily:"'JetBrains Mono',monospace"}}>{value}</div>
              <div className="text-xs font-semibold text-[#B8A99A] tracking-wider">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* 搜索栏 */}
      <div className="glass p-4 mb-6 flex items-center gap-3">
        <input
          type="text" value={searchText} onChange={e=>setSearchText(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&doSearch()}
          placeholder="搜索实体名称，如「兵马俑」「西安鼓乐」…"
          className="flex-1 bg-transparent border border-[#C9A96E]/20 rounded-lg px-4 py-2.5 text-sm text-[#E8E0D5] placeholder-[#B8A99A]/50 outline-none focus:border-[#C9A96E]/50 transition-colors"
        />
        <button onClick={doSearch} disabled={searching}
          className="px-5 py-2.5 rounded-lg text-sm font-bold transition-all duration-300"
          style={{background:'linear-gradient(135deg,#8B3A3A,#C9A96E)',color:'#1A1A2E'}}>
          {searching ? '搜索中…' : '🔍 搜索'}
        </button>
        <span className="text-xs text-[#B8A99A]/60">双击图谱空白处可重置视图</span>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* 图谱主区域 */}
        <div className="lg:col-span-2 glass overflow-hidden relative" style={{minHeight:'600px'}}>
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#1A1A2E]/80">
              <div className="text-center"><div className="text-3xl mb-3 animate-bounce">🔮</div><p className="text-[#C9A96E] text-sm">知识图谱加载中…</p></div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center z-10 bg-[#1A1A2E]/80">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
          <div ref={containerRef} style={{width:'100%',height:'600px'}} />
        </div>

        {/* 右侧面板 */}
        <div className="space-y-4">
          {/* 选中节点详情 */}
          {selectedNode ? (
            <div className="glass p-5 animate-in">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-bold text-[#C9A96E] uppercase tracking-wider">节点详情</h3>
                <button onClick={()=>setSelectedNode(null)} className="text-xs text-[#B8A99A] hover:text-[#E8E0D5]">✕ 关闭</button>
              </div>
              <div className="w-3 h-3 rounded-full mb-3" style={{backgroundColor:selectedNode.color}} />
              <p className="text-lg font-black text-[#E8E0D5] mb-1">{selectedNode.label}</p>
              <p className="text-xs text-[#B8A99A] mb-3">{selectedNode.type_cn} · {selectedNode.id}</p>
              {selectedNode.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.tags.map(t=><span key={t} className="text-xs px-2 py-0.5 rounded-full border border-[#C9A96E]/20 text-[#B8A99A]">{t}</span>)}
                </div>
              )}
              <p className="text-xs text-[#B8A99A]/50 mt-4">点击图谱节点查看关联 · 双击空白重置</p>
            </div>
          ) : (
            <div className="glass p-5 text-center">
              <p className="text-sm text-[#B8A99A]">👆 点击图谱中的节点<br/>查看详细信息</p>
            </div>
          )}

          {/* 搜索结果 */}
          {searchResult && (
            <div className="glass p-5 animate-in max-h-80 overflow-y-auto">
              <h3 className="text-sm font-bold text-[#C9A96E] mb-3 uppercase tracking-wider">
                搜索结果 {searchResult.total_matches ? `(${searchResult.total_matches})` : ''}
              </h3>
              {searchResult.error ? (
                <p className="text-xs text-red-400">{searchResult.error}</p>
              ) : (
                searchResult.results?.map((r,i)=>(
                  <div key={i} className="mb-3 pb-3 border-b border-[#C9A96E]/10 last:border-0 last:pb-0 last:mb-0">
                    <p className="text-sm font-bold text-[#E8E0D5] mb-1">{r.entity}</p>
                    <p className="text-xs text-[#B8A99A] mb-2">{r.type} · {r.direct_relations?.length||0} 条关联</p>
                    {r.direct_relations?.slice(0,5).map((rel,j)=>(
                      <div key={j} className="text-xs flex items-center gap-1.5 mb-0.5">
                        <span className="text-[#8B3A3A]">{rel.direction==='outgoing' ? '→' : '←'}</span>
                        <span className="text-[#C9A96E]">{rel.relation}</span>
                        <span className="text-[#B8A99A]">{rel.target}</span>
                      </div>
                    ))}
                  </div>
                ))
              )}
            </div>
          )}

          {/* 图例 */}
          <div className="glass p-5">
            <h3 className="text-sm font-bold text-[#C9A96E] mb-3 uppercase tracking-wider">图例</h3>
            <div className="grid grid-cols-2 gap-2">
              {[
                ['文物','#8B3A3A'],['非遗','#C9A96E'],['文旅','#D4A574'],
                ['传承人/人物','#f59e0b'],['工艺技术','#A78BFA'],['时间时期','#6366f1'],
                ['地理区位','#14b8a6'],['展览/事件','#f97316'],['数字资产','#8b5cf6'],
              ].map(([label,color])=>(
                <div key={label} className="flex items-center gap-2 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{backgroundColor:color}} />
                  <span className="text-[#B8A99A] truncate">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ==================== AI 浮动创作面板 ====================
function AIFloat({ projects, open, setOpen }) {
  const [view, setView] = useState('form')
  const [topic, setTopic] = useState('')
  const [platform, setPlatform] = useState('小红书')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressText, setProgressText] = useState('')

  const gen = async () => {
    if(!topic.trim()) return; setLoading(true); setResult(null); setProgress(0)
    const types = ['文案','图片描述','视频脚本']; const allResults = []
    try {
      for(let i=0;i<types.length;i++){
        setProgressText(`正在生成${types[i]}… (${i+1}/${types.length})`)
        const r = await fetch(`${API}/agent/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic,content_types:[types[i]],target_platform:platform})})
        const d = await r.json()
        if(d.contents) allResults.push(...d.contents)
        setProgress(Math.round(((i+1)/types.length)*100))
      }
      setResult({contents:allResults}); setProgress(100); setProgressText('生成完成！')
      setTimeout(()=>setView('results'),400)
    } catch(e) { alert('生成失败') }
    setLoading(false)
  }

  return (<>
    <AnimatePresence>
      {open && (
        <motion.div initial={{opacity:0,x:320}} animate={{opacity:1,x:0}} exit={{opacity:0,x:320}} transition={{duration:0.35}}
          className="fixed right-0 top-0 bottom-0 z-40 w-[88vw] max-w-4xl overflow-y-auto"
          style={{background:'rgba(22,22,40,0.96)',backdropFilter:'blur(28px)',borderLeft:'1px solid rgba(201,169,110,0.12)',boxShadow:'-8px 0 48px rgba(0,0,0,0.6)'}}>
          {view==='form' ? (
            <div className="p-8 pt-16 h-full flex flex-col">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-2xl font-black text-[#C9A96E]" style={{fontFamily:"'Noto Serif SC',serif"}}>🤖 AI 创作助手</h2>
                <button onClick={()=>setOpen(false)} className="text-[#B8A99A] hover:text-[#C9A96E] text-2xl rounded-full w-10 h-10 flex items-center justify-center transition-colors glass-light">✕</button>
              </div>
              <div className="flex-1 flex flex-col gap-6">
                <div>
                  <label className="text-sm font-bold text-[#B8A99A] mb-2 block">创作主题</label>
                  <input value={topic} onChange={e=>setTopic(e.target.value)} placeholder="输入主题，如：兵马俑、敦煌莫高窟…"
                    className="w-full rounded-xl px-5 py-3.5 text-base font-semibold outline-none bg-transparent text-[#E8E0D5] placeholder:text-[#9B8E82]"
                    style={{border:'1px solid rgba(201,169,110,0.2)'}} />
                </div>
                <div>
                  <label className="text-sm font-bold text-[#B8A99A] mb-2 block">快捷选题</label>
                  <div className="grid grid-cols-4 gap-2">
                    {projects.slice(0,40).map(p=>(
                      <button key={p.asset_id} onClick={()=>setTopic(p.title)}
                        className={`text-xs font-semibold px-3 py-2 rounded-lg border transition-all duration-300 truncate ${topic===p.title?'text-[#C9A96E] border-[#C9A96E]/40':'border-[#C9A96E]/10 text-[#B8A99A] hover:text-[#C9A96E]'}`}
                        style={topic===p.title?{background:'rgba(201,169,110,0.1)'}:{}}>{p.title}</button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-sm font-bold text-[#B8A99A] mb-2 block">目标平台</label>
                  <div className="flex gap-2">
                    {['小红书','抖音','微信','微博','B站'].map(x=>(
                      <button key={x} onClick={()=>setPlatform(x)}
                        className={`text-sm font-semibold px-5 py-2.5 rounded-lg border transition-all duration-300 ${platform===x?'text-[#C9A96E] border-[#C9A96E]/40':'border-[#C9A96E]/10 text-[#B8A99A] hover:text-[#C9A96E]'}`}
                        style={platform===x?{background:'rgba(201,169,110,0.1)'}:{}}>{x}</button>
                    ))}
                  </div>
                </div>
                {loading ? (
                  <div className="glass p-6 mt-auto">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-8 h-8 rounded-full animate-spin" style={{border:'3px solid rgba(201,169,110,0.2)',borderTopColor:'#C9A96E'}} />
                      <div>
                        <p className="font-bold text-[#C9A96E]">AI 创作中</p>
                        <p className="text-xs text-[#B8A99A]">主题：{topic} · 平台：{platform}</p>
                      </div>
                      <span className="ml-auto text-lg font-black text-[#C9A96E]">{progress}%</span>
                    </div>
                    <div className="h-3 rounded-full overflow-hidden" style={{background:'rgba(201,169,110,0.08)'}}>
                      <div className="h-full rounded-full transition-all duration-500" style={{width:`${progress}%`,background:'linear-gradient(90deg, #8B3A3A, #C9A96E)'}} />
                    </div>
                    <p className="text-xs text-[#B8A99A] mt-2 text-center">{progressText}</p>
                  </div>
                ) : (
                  <button onClick={gen} className="w-full py-4 rounded-xl btn-gold text-lg mt-auto">🚀 生成内容</button>
                )}
              </div>
            </div>
          ) : <ResultsView topic={topic} platform={platform} result={result} onBack={()=>setView('form')} />}
        </motion.div>
      )}
    </AnimatePresence>
    {open && <div className="fixed inset-0 z-30 bg-black/40" onClick={()=>setOpen(false)} />}
  </>)
}

function ResultsView({ topic, platform, result, onBack }) {
  const [tab, setTab] = useState(0)
  const [genImg, setGenImg] = useState(false)
  const [genVid, setGenVid] = useState(false)
  const [imgResult, setImgResult] = useState(null)
  const [vidResult, setVidResult] = useState(null)
  const types = ['文案','图片描述','视频脚本']; const icons = ['📝','🎨','🎬']
  const items = result?.contents || []

  const generateImage = async () => {
    const imgItem = items.find(c=>c.content_type==='图片描述')
    if(!imgItem) return; setGenImg(true)
    try {
      const imgPrompt = imgItem.body?.split('\n').find(l=>l.includes('en:'))?.replace('en:','')?.trim() || imgItem.body?.substring(0,400)
      const r = await fetch(`${API}/gen/image?prompt=${encodeURIComponent(imgPrompt)}`,{method:'POST'})
      setImgResult(await r.json())
    } catch(e) { setImgResult({error:'请求失败'}) }
    setGenImg(false)
  }

  const generateVideo = async () => {
    const vidItem = items.find(c=>c.content_type==='视频脚本')
    if(!vidItem) { alert('请先生成内容（需包含"视频脚本"），再点击生成视频'); return }
    setGenVid(true)
    try {
      const prompt = vidItem.body?.substring(0,500) || `西安文化：${topic}`
      const r = await fetch(`${API}/gen/video?prompt=${encodeURIComponent(prompt)}`,{method:'POST'})
      const d = await r.json()
      if(!d.success){ setVidResult({success:false,error:d.detail||'生成失败'}); setGenVid(false); return }
      if(d.task_id){
        let pollCount=0
        const poll=setInterval(async()=>{
          const sr=await fetch(`${API}/gen/video/${d.task_id}`); const sd=await sr.json(); pollCount++
          if(sd.status==='succeeded'||pollCount>30){clearInterval(poll);setVidResult(sd);setGenVid(false)}
        },5000)
        setVidResult({...d,status:'processing'})
      } else { setVidResult(d); setGenVid(false) }
    } catch(e) { setVidResult({success:false,error:'请求失败'}); setGenVid(false) }
  }

  return (
    <div className="p-8 pt-16 h-full flex flex-col">
      <button onClick={onBack} className="text-sm font-bold text-[#B8A99A] hover:text-[#C9A96E] mb-4 flex items-center gap-1">← 返回创作</button>
      <h2 className="text-xl font-black text-[#C9A96E] mb-1">生成结果</h2>
      <p className="text-base text-[#B8A99A] mb-6">主题：{topic} · 平台：{platform}</p>

      <div className="flex gap-2 mb-4">
        {types.map((t,i)=>(
          <button key={t} onClick={()=>setTab(i)}
            className={`flex-1 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${tab===i?'text-[#C9A96E]':'text-[#B8A99A] hover:text-[#C9A96E]'}`}
            style={tab===i?{background:'rgba(201,169,110,0.1)',border:'1px solid rgba(201,169,110,0.2)'}:{border:'1px solid transparent'}}>
            {icons[i]} {t}
          </button>
        ))}
      </div>

      {tab===1 && (
        <div className="mb-4">
          <button onClick={generateImage} disabled={genImg} className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 disabled:opacity-40" style={{border:'1px solid rgba(201,169,110,0.3)',color:'#C9A96E'}}>
            {genImg?'🎨 生成中…':'🎨 点击生成图片'}
          </button>
          {imgResult && (
            <div className="mt-3 p-4 rounded-xl" style={imgResult.success?{background:'rgba(16,185,129,0.1)',border:'1px solid rgba(16,185,129,0.3)'}:{background:'rgba(239,68,68,0.1)',border:'1px solid rgba(239,68,68,0.3)'}}>
              {imgResult.success
                ? <div><p className='text-sm font-bold text-green-400 mb-2'>图片已生成</p>{imgResult.image_urls?.map((url,j)=>(<img key={j} src={url} alt="AI生成" className="rounded-lg w-full" />))}</div>
                : <p className='text-sm text-red-400'>❌ {imgResult.error||'生成失败'}</p>}
            </div>
          )}
        </div>
      )}

      {tab===2 && (
        <div className="mb-4">
          <button onClick={generateVideo} disabled={genVid} className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 disabled:opacity-40" style={{border:'1px solid rgba(167,139,250,0.3)',color:'#A78BFA'}}>
            {genVid?'🎬 生成中…':'🎬 点击生成视频'}
          </button>
          {vidResult && (
            <div className="mt-3 p-4 rounded-xl" style={vidResult.success===false?{background:'rgba(239,68,68,0.1)',border:'1px solid rgba(239,68,68,0.3)'}:{background:'rgba(16,185,129,0.1)',border:'1px solid rgba(16,185,129,0.3)'}}>
              {vidResult.video_url
                ? <div><p className='text-sm font-bold text-green-400 mb-2'>视频已生成</p><video src={vidResult.video_url} controls playsInline preload="metadata" className='rounded-lg w-full min-h-[240px] bg-black' style={{position:'relative',zIndex:1}} /></div>
                : vidResult.status==='processing' ? <p className='text-sm text-[#C9A96E]'>⏳ 生成中…</p>
                : vidResult.status==='submitted' ? <p className='text-sm text-[#C9A96E]'>📤 已提交…</p>
                : <p className='text-sm text-red-400'>❌ {vidResult.error||'生成失败'}</p>}
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {items.filter(c=>c.content_type===types[tab]).map((c,i)=>(
          <motion.div key={i} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{delay:0.05}}
            className="rounded-2xl p-6 mb-4" style={{background:'rgba(45,45,66,0.5)',border:'1px solid rgba(201,169,110,0.1)'}}>
            <h3 className="text-lg font-bold text-[#E8E0D5] mb-3">{c.title}</h3>
            <div className="flex flex-wrap gap-1.5 mb-4">
              {c.tags?.map(t=>(<span key={t} className="text-xs px-2.5 py-1 rounded-lg" style={{background:'rgba(201,169,110,0.1)',color:'#C9A96E'}}>{t}</span>))}
            </div>
            <div className="text-base leading-relaxed whitespace-pre-wrap rounded-xl p-5" style={{background:'rgba(37,37,56,0.6)',color:'#B8A99A'}}>{c.body}</div>
          </motion.div>
        ))}
        {items.filter(c=>c.content_type===types[tab]).length===0 && (
          <div className="text-center py-12 text-sm" style={{color:'rgba(184,169,154,0.3)'}}>该类型暂无内容</div>
        )}
      </div>
    </div>
  )
}
