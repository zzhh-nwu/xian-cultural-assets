import { useState, useEffect, useRef, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import * as echarts from 'echarts'

// 本地加载中国地图GeoJSON（不再依赖外部CDN）
const CHINA_URL = '/china_geo.json'
// 陕西省市级GeoJSON
const SHAANXI_URL = '/shaanxi_geo.json'

const NAME_MAP = {
  '黑龙江省':'黑龙江','吉林省':'吉林','辽宁省':'辽宁',
  '内蒙古自治区':'内蒙古','北京市':'北京','天津市':'天津','河北省':'河北',
  '山东省':'山东','山西省':'山西','河南省':'河南','陕西省':'陕西',
  '宁夏回族自治区':'宁夏','甘肃省':'甘肃','青海省':'青海','新疆维吾尔自治区':'新疆',
  '西藏自治区':'西藏','四川省':'四川','重庆市':'重庆','贵州省':'贵州',
  '云南省':'云南','广西壮族自治区':'广西','广东省':'广东','福建省':'福建',
  '浙江省':'浙江','江苏省':'江苏','安徽省':'安徽','湖北省':'湖北',
  '湖南省':'湖南','江西省':'江西','上海市':'上海','海南省':'海南','台湾省':'台湾',
  '香港特别行政区':'香港','澳门特别行政区':'澳门',
}

const CITY_SHORT = {
  '西安市':'西安','铜川市':'铜川','宝鸡市':'宝鸡','咸阳市':'咸阳',
  '渭南市':'渭南','延安市':'延安','汉中市':'汉中','榆林市':'榆林',
  '安康市':'安康','商洛市':'商洛',
}

// 全称→简称
function shortName(full){ return NAME_MAP[full]||full }
function shortCity(full){ return CITY_SHORT[full]||full }

function getProvinceData(projects) {
  const map = {}
  projects.forEach(p => {
    const raw = p.geolocation?.province || p.province || ''
    for(const [full, short] of Object.entries(NAME_MAP)) {
      if(raw===full || raw===short || raw.includes(short) || short.includes(raw.replace('省','').replace('市','').replace('自治区',''))){
        const key = full
        if(!map[key]) map[key] = {count:0,items:[]}
        map[key].count++
        if(!map[key].items.includes(p.title)) map[key].items.push(p.title)
        break
      }
    }
  })
  return map
}

function getShaanxiCityData(projects) {
  const map = {}
  projects.forEach(p => {
    const raw = p.geolocation?.province || p.province || ''
    const city = p.geolocation?.city || p.city || ''
    if (!raw.includes('陕西') && raw !== '陕西') return
    for (const [full, short] of Object.entries(CITY_SHORT)) {
      if (city === full || city === short || city.includes(short.replace('市','')) || short.includes(city.replace('市',''))) {
        if (!map[full]) map[full] = { count: 0, items: [] }
        map[full].count++
        if (!map[full].items.includes(p.title)) map[full].items.push(p.title)
        break
      }
    }
  })
  return map
}

export default function ChinaMap({ projects, onEnter, inline }) {
  const chartRef = useRef(null)
  const chartInst = useRef(null)
  const [mapsReady, setMapsReady] = useState(false)
  const [drillProvince, setDrillProvince] = useState(null) // null=全国, '陕西省'=陕西
  const [hoveredRegion, setHoveredRegion] = useState(null)
  const [tooltipData, setTooltipData] = useState({show:false,x:0,y:0})

  const provData = useMemo(()=>getProvinceData(projects),[projects])
  const cityData = useMemo(()=>getShaanxiCityData(projects),[projects])
  const maxCount = Math.max(1,...Object.values(provData).map(d=>d.count),10)
  const maxCityCount = Math.max(1,...Object.values(cityData).map(d=>d.count),10)

  const totalProvinces = Object.keys(provData).length

  const containerClass = inline
    ? 'relative w-full rounded-2xl overflow-hidden oriental'
    : 'fixed inset-0 z-50 overflow-hidden flex flex-col'
  const mapHeight = inline ? 'h-[720px]' : 'flex-1'
  const bgStyle = inline ? {background:'#1A1A2E'} : {background:'#0a1628',fontFamily:'Inter,system-ui,sans-serif'}

  // 加载两份GeoJSON
  useEffect(() => {
    Promise.all([
      fetch(CHINA_URL).then(r=>r.json()),
      fetch(SHAANXI_URL).then(r=>r.json())
    ]).then(([chinaGeo, shaanxiGeo]) => {
      echarts.registerMap('china', chinaGeo)
      echarts.registerMap('shaanxi', shaanxiGeo)
      setMapsReady(true)
    }).catch(() => {
      // 备用：尝试旧格式路径
      fetch('/china_geo.json').then(r=>r.json()).then(geo=>{
        echarts.registerMap('china', geo)
        setMapsReady(true)
      }).catch(() => console.warn('中国地图GeoJSON加载失败'))
    })
  }, [])

  // 当前数据：全国 vs 陕西
  const isDrill = drillProvince === '陕西省'
  const currentData = isDrill ? cityData : provData
  const currentMax = isDrill ? maxCityCount : maxCount

  useEffect(() => {
    if(!mapsReady || !chartRef.current) return
    if(chartInst.current) chartInst.current.dispose()

    const chart = echarts.init(chartRef.current, null, {renderer:'svg'})
    chartInst.current = chart

    // 动画：下钻时放大过渡
    const animDuration = isDrill ? 600 : 400

    const baseOption = {
      backgroundColor: inline ? '#1A1A2E' : '#0a1628',
      tooltip: {show:false},
      animation: true,
      animationDuration: animDuration,
      animationDurationUpdate: 500,
      animationEasing: 'cubicInOut',
    }

    if (isDrill && inline) {
      // ===== 陕西省市级地图（暗色暖金） =====
      chart.setOption({
        ...baseOption,
        visualMap: {
          show:true, top:'12%', right:10, left:'auto', orient:'vertical',
          min:0, max:currentMax,
          inRange:{color:['#2D2D42','#6B2A2A','#8B3A3A','#C9A96E','#D4A574']},
          text:['多','少'], textStyle:{color:'#B8A99A',fontSize:11},
          itemWidth:16, itemHeight:140,
        },
        series:[{
          type:'map', map:'shaanxi',
          roam:false,
          top:'6%', bottom:'6%',
          aspectScale:0.9,
          label:{show:true,color:'#9B8E82',fontSize:11,fontWeight:'700'},
          emphasis:{
            label:{show:true,color:'#C9A96E',fontSize:15,fontWeight:'bold'},
            itemStyle:{areaColor:'#C9A96E',borderColor:'#D4A574',borderWidth:2,shadowBlur:16,shadowColor:'rgba(201,169,110,0.3)'}
          },
          itemStyle:{borderColor:'rgba(201,169,110,0.15)',borderWidth:1,areaColor:'#252538'},
          data: Object.entries(cityData).map(([k,v])=>({
            name:k, value:v.count,
            itemStyle: k==='西安市' ? {areaColor:'#8B3A3A',borderColor:'#C9A96E',borderWidth:2.5} : undefined,
            label: k==='西安市' ? {color:'#C9A96E',fontSize:12,fontWeight:'bold'} : undefined,
          })),
        }]
      })

      chart.off('click')
      chart.off('mouseover')
      chart.off('mousemove')
      chart.off('mouseout')

      chart.on('mouseover', (params) => {
        if(params.name && cityData[params.name]){
          setHoveredRegion(params.name)
          setTooltipData({show:true,x:params.event.event.clientX,y:params.event.event.clientY})
        }
      })
      chart.on('mousemove', (params) => {
        if(hoveredRegion){
          setTooltipData(t=>({...t,x:params.event.event.clientX,y:params.event.event.clientY}))
        }
      })
      chart.on('mouseout', () => {setHoveredRegion(null);setTooltipData(t=>({...t,show:false}))})

      chart.on('click', (params) => {
        if(params.name && cityData[params.name]){
          onEnter(params.name) // 传递城市名过滤
        }
      })

    } else if (inline) {
      // ===== 全国地图（暗色暖金） =====
      chart.setOption({
        ...baseOption,
        visualMap: {
          show:true, top:'28%', right:10, left:'auto', orient:'vertical',
          min:0, max:currentMax,
          inRange:{color:['#252538','#3D2A2A','#6B2A2A','#8B3A3A','#C9A96E']},
          text:['多','少'], textStyle:{color:'#B8A99A',fontSize:11},
          itemWidth:16, itemHeight:140,
        },
        series:[{
          type:'map', map:'china',
          roam:false, zoom:1.6,
          top:'28%', bottom:'-5%',
          aspectScale:0.85,
          label:{show:true,color:'#9B8E82',fontSize:9,fontWeight:'600'},
          emphasis:{
            label:{show:true,color:'#C9A96E',fontSize:13,fontWeight:'bold'},
            itemStyle:{areaColor:'#C9A96E',borderColor:'#D4A574',borderWidth:2,shadowBlur:16,shadowColor:'rgba(201,169,110,0.3)'}
          },
          itemStyle:{borderColor:'rgba(201,169,110,0.1)',borderWidth:1,areaColor:'#2D2D42'},
          data: Object.entries(provData).map(([k,v])=>({
            name:k, value:v.count,
            itemStyle: k==='陕西省' ? {areaColor:'#8B3A3A',borderColor:'#C9A96E',borderWidth:2.5} : undefined,
            label: k==='陕西省' ? {color:'#C9A96E',fontSize:11,fontWeight:'bold'} : undefined,
          })),
        }]
      })

      chart.off('click')
      chart.off('mouseover')
      chart.off('mousemove')
      chart.off('mouseout')

      chart.on('mouseover', (params) => {
        if(params.name && provData[params.name]){
          setHoveredRegion(params.name)
          setTooltipData({show:true,x:params.event.event.clientX,y:params.event.event.clientY})
        }
      })
      chart.on('mousemove', (params) => {
        if(hoveredRegion){
          setTooltipData(t=>({...t,x:params.event.event.clientX,y:params.event.event.clientY}))
        }
      })
      chart.on('mouseout', () => {setHoveredRegion(null);setTooltipData(t=>({...t,show:false}))})

      chart.on('click', (params) => {
        if(params.name === '陕西省'){
          setDrillProvince('陕西省') // 内联下钻
        } else if(params.name && provData[params.name]){
          onEnter(shortName(params.name))
        }
      })

    } else {
      // ===== 全屏暗色（保留） =====
      chart.setOption({
        ...baseOption,
        animationDuration: 400,
        visualMap: {
          show:true, top:'28%', right:40, left:'auto', orient:'vertical',
          min:0, max:currentMax,
          inRange:{color:['#1a2a45','#1e4d8c','#2563eb','#3b82f6','#60a5fa']},
          text:['多','少'], textStyle:{color:'#8899aa',fontSize:14},
          itemWidth:24, itemHeight:180,
        },
        series:[{
          type:'map', map:'china',
          roam:false, zoom:1.5,
          top:'18%', bottom:'14%',
          aspectScale:0.85,
          label:{show:true,color:'#8899aa',fontSize:9,fontWeight:'500'},
          emphasis:{
            label:{show:true,color:'#fff',fontSize:13,fontWeight:'bold'},
            itemStyle:{areaColor:'#3b82f6',borderColor:'#60a5fa',borderWidth:2,shadowBlur:20,shadowColor:'rgba(59,130,246,0.5)'}
          },
          itemStyle:{borderColor:'#1e2d4a',borderWidth:1.2,areaColor:'#1a2a45'},
          data: Object.entries(provData).map(([k,v])=>({
            name:k, value:v.count,
            itemStyle: k==='陕西省' ? {areaColor:'#dc2626',borderColor:'#ef4444',borderWidth:2} : undefined,
            label: k==='陕西省' ? {color:'#fff',fontSize:11,fontWeight:'bold'} : undefined,
          })),
        }]
      })

      chart.off('click')
      chart.off('mouseover')
      chart.off('mousemove')
      chart.off('mouseout')

      chart.on('mouseover', (params) => {
        if(params.name && provData[params.name]){
          setHoveredRegion(params.name)
          setTooltipData({show:true,x:params.event.event.clientX,y:params.event.event.clientY})
        }
      })
      chart.on('mousemove', (params) => {
        if(hoveredRegion){
          setTooltipData(t=>({...t,x:params.event.event.clientX,y:params.event.event.clientY}))
        }
      })
      chart.on('mouseout', () => {setHoveredRegion(null);setTooltipData(t=>({...t,show:false}))})

      chart.on('click', (params) => {
        if(params.name && provData[params.name]){
          onEnter(shortName(params.name))
        }
      })
    }

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)
    return () => {window.removeEventListener('resize',handleResize);chart.dispose()}
  }, [mapsReady, projects, drillProvince])

  // tooltip 显示名称
  const tooltipName = isDrill ? (CITY_SHORT[hoveredRegion] || hoveredRegion) : shortName(hoveredRegion)
  const tooltipCount = hoveredRegion ? (currentData[hoveredRegion]?.count || 0) : 0
  const tooltipItems = hoveredRegion ? (currentData[hoveredRegion]?.items || []) : []

  return (
    <motion.div exit={inline?undefined:{opacity:0}} transition={{duration:0.4}}
      className={containerClass}
      style={bgStyle}>

      {/* 标题 — 全屏模式显示 */}
      {!inline && (
        <div className="text-center pt-14 pb-0 pointer-events-none">
          <h1 className="text-3xl md:text-5xl font-black text-white tracking-wider mb-1">中国文化数字资产地图</h1>
          <p className="text-sm md:text-base font-semibold text-blue-400/70 tracking-widest uppercase">
            China Cultural Digital Asset Map · {projects.length} 个项目 · {totalProvinces} 省份
          </p>
        </div>
      )}

      {/* 下钻返回按钮 */}
      <AnimatePresence>
        {isDrill && inline && (
          <motion.button
            initial={{opacity:0,x:-12}} animate={{opacity:1,x:0}} exit={{opacity:0,x:-12}} transition={{duration:0.25}}
            whileHover={{scale:1.03}} whileTap={{scale:0.97}}
            onClick={() => setDrillProvince(null)}
            className="absolute top-4 left-4 z-10 font-semibold text-sm px-5 py-2.5 rounded-xl transition-all duration-300 hover:opacity-90"
            style={{background:'rgba(37,37,56,0.7)',color:'#C9A96E',border:'1px solid rgba(201,169,110,0.2)',backdropFilter:'blur(8px)'}}>
            ← 返回全国
          </motion.button>
        )}
      </AnimatePresence>

      {/* 地图 */}
      <div className={mapHeight + ' w-full'} ref={chartRef} />

      {/* Tooltip */}
      {hoveredRegion && currentData[hoveredRegion] && (
        <div className="fixed z-50 pointer-events-none"
          style={{left:tooltipData.x+18,top:tooltipData.y-10,transform:'translateY(-100%)'}}>
          <div className="rounded-xl px-5 py-4 shadow-2xl min-w-[180px] max-w-[280px]"
            style={inline
              ? {background:'rgba(37,37,56,0.95)',border:'1px solid rgba(201,169,110,0.25)',color:'#E8E0D5',backdropFilter:'blur(12px)',boxShadow:'0 8px 32px rgba(0,0,0,0.5)'}
              : {background:'#0a1628',border:'1px solid rgba(201,169,110,0.3)',color:'#fff',boxShadow:'0 8px 32px rgba(0,0,0,0.5), 0 0 1px rgba(201,169,110,0.4)'}}>
            <div className="flex items-center justify-between mb-2.5">
              <span className="font-bold text-base">{tooltipName}</span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full font-bold text-white"
                style={{background:'linear-gradient(135deg, #8B3A3A, #C9A96E)'}}>
                {tooltipCount} 项资产
              </span>
            </div>
            <div className="space-y-0.5 max-h-[160px] overflow-y-auto">
              {tooltipItems.map((t,i)=>(
                <div key={i} className="text-xs leading-relaxed text-[#B8A99A]">· {t}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 提示标签 */}
      {inline && !isDrill && (
        <div className="absolute bottom-3 right-4 z-10">
          <span className="text-[10px] font-bold px-2 py-1 rounded" style={{background:'rgba(37,37,56,0.6)',color:'#9B8E82'}}>点击省份查看详情 · 赭红为陕西省</span>
        </div>
      )}
      {inline && isDrill && (
        <div className="absolute bottom-3 right-4 z-10">
          <span className="text-[10px] font-bold px-2 py-1 rounded" style={{background:'rgba(37,37,56,0.6)',color:'#9B8E82'}}>点击城市查看资产 · 赭红为西安市</span>
        </div>
      )}

      {/* 进入按钮 — 全屏模式显示 */}
      {!inline && (
        <motion.button whileHover={{scale:1.05}} whileTap={{scale:0.97}}
          onClick={()=>onEnter()}
          className="absolute top-6 right-6 z-10 bg-blue-600 text-white text-lg font-bold px-10 py-5 rounded-xl hover:bg-blue-500 transition-colors shadow-xl shadow-blue-500/30 tracking-wider">
          进入平台 →
        </motion.button>
      )}
    </motion.div>
  )
}
