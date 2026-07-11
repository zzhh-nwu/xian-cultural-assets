import { useState, useEffect, useRef, useMemo } from 'react'
import { motion } from 'framer-motion'
import * as echarts from 'echarts'

// 本地加载陕西省市级GeoJSON（不再依赖外部CDN）
const MAP_URL = '/shaanxi_geo.json'

const CITY_SHORT = {
  '西安市':'西安','铜川市':'铜川','宝鸡市':'宝鸡','咸阳市':'咸阳',
  '渭南市':'渭南','延安市':'延安','汉中市':'汉中','榆林市':'榆林',
  '安康市':'安康','商洛市':'商洛',
}

function getCityData(projects) {
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

export default function ShaanxiMap({ projects, onBack, onEnterCity }) {
  const chartRef = useRef(null)
  const chartInst = useRef(null)
  const [mapLoaded, setMapLoaded] = useState(false)
  const [hoveredCity, setHoveredCity] = useState(null)
  const [tooltipData, setTooltipData] = useState({ show: false, x: 0, y: 0 })

  const cityData = useMemo(() => getCityData(projects), [projects])
  const maxCount = Math.max(1, ...Object.values(cityData).map(d => d.count), 10)

  useEffect(() => {
    fetch(MAP_URL).then(r => r.json()).then(geo => {
      echarts.registerMap('shaanxi', geo)
      setMapLoaded(true)
    }).catch(() => console.warn('陕西GeoJSON加载失败'))
  }, [])

  useEffect(() => {
    if (!mapLoaded || !chartRef.current) return
    if (chartInst.current) chartInst.current.dispose()

    const chart = echarts.init(chartRef.current, null, { renderer: 'svg' })
    chartInst.current = chart

    const option = {
      backgroundColor: '#1A1A2E',
      tooltip: { show: false },
      visualMap: {
        show: true, top: '20%', right: 30, left: 'auto', orient: 'vertical',
        min: 0, max: maxCount,
        inRange: { color: ['#252538', '#3D2A2A', '#6B2A2A', '#8B3A3A', '#C9A96E'] },
        text: ['多', '少'], textStyle: { color: '#B8A99A', fontSize: 13 },
        itemWidth: 22, itemHeight: 160,
      },
      series: [{
        type: 'map', map: 'shaanxi',
        roam: false,
        top: '10%', bottom: '10%',
        aspectScale: 0.9,
        label: { show: true, color: '#9B8E82', fontSize: 10, fontWeight: '600' },
        emphasis: {
          label: { show: true, color: '#C9A96E', fontSize: 14, fontWeight: 'bold' },
          itemStyle: { areaColor: '#C9A96E', borderColor: '#D4A574', borderWidth: 2, shadowBlur: 20, shadowColor: 'rgba(201,169,110,0.4)' }
        },
        itemStyle: { borderColor: 'rgba(201,169,110,0.12)', borderWidth: 1.2, areaColor: '#252538' },
        data: Object.entries(cityData).map(([k, v]) => ({ name: k, value: v.count })),
      }]
    }

    chart.setOption(option)

    chart.on('mouseover', (params) => {
      if (params.name && cityData[params.name]) {
        setHoveredCity(params.name)
        setTooltipData({ show: true, x: params.event.event.clientX, y: params.event.event.clientY })
      }
    })
    chart.on('mousemove', (params) => {
      if (hoveredCity) setTooltipData(t => ({ ...t, x: params.event.event.clientX, y: params.event.event.clientY }))
    })
    chart.on('mouseout', () => { setHoveredCity(null); setTooltipData(t => ({ ...t, show: false })) })

    chart.on('click', (params) => {
      if (params.name && cityData[params.name]) {
        onEnterCity(params.name)
      }
    })

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)
    return () => { window.removeEventListener('resize', handleResize); chart.dispose() }
  }, [mapLoaded, projects])

  const totalCities = Object.keys(cityData).length
  const totalProjects = Object.values(cityData).reduce((s, d) => s + d.count, 0)

  return (
    <motion.div exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
      className="fixed inset-0 z-50 overflow-hidden flex flex-col"
      style={{ background: '#1A1A2E', fontFamily: 'Inter,system-ui,sans-serif' }}>

      {/* 标题 */}
      <div className="text-center pt-12 pb-0 pointer-events-none">
        <h1 className="text-3xl md:text-5xl font-black text-[#E8E0D5] tracking-wider mb-1" style={{fontFamily:"'Noto Serif SC',serif"}}>陕西省文化数字资产地图</h1>
        <p className="text-sm md:text-base font-semibold tracking-widest uppercase" style={{color:'rgba(201,169,110,0.7)'}}>
          Shaanxi Cultural Digital Asset Map · {totalProjects} 个项目 · {totalCities} 个城市
        </p>
      </div>

      {/* 地图 */}
      <div className="flex-1 w-full" ref={chartRef} />

      {/* Tooltip */}
      {hoveredCity && cityData[hoveredCity] && (
        <div className="fixed z-50 pointer-events-none"
          style={{ left: tooltipData.x + 18, top: tooltipData.y - 10, transform: 'translateY(-100%)' }}>
          <div className="rounded-xl px-5 py-4 shadow-2xl min-w-[180px] max-w-[300px]"
            style={{ background:'rgba(37,37,56,0.95)', border:'1px solid rgba(201,169,110,0.25)', color:'#E8E0D5', backdropFilter:'blur(12px)', boxShadow:'0 8px 32px rgba(0,0,0,0.5)' }}>
            <div className="flex items-center justify-between mb-2.5">
              <span className="font-bold text-base" style={{color:'#E8E0D5'}}>{CITY_SHORT[hoveredCity] || hoveredCity}</span>
              <span className="text-[11px] px-2.5 py-0.5 rounded-full font-bold text-white"
                style={{background:'linear-gradient(135deg, #8B3A3A, #C9A96E)'}}>
                {cityData[hoveredCity].count} 项资产
              </span>
            </div>
            <div className="space-y-0.5 max-h-[160px] overflow-y-auto">
              {(cityData[hoveredCity].items || []).map((t, i) => (
                <div key={i} className="text-[#B8A99A] text-xs leading-relaxed">· {t}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 返回按钮 */}
      <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.97 }}
        onClick={onBack}
        className="absolute top-6 left-6 z-10 text-base font-semibold px-8 py-3.5 rounded-xl transition-all duration-300 tracking-wider"
        style={{background:'rgba(37,37,56,0.7)',color:'#C9A96E',border:'1px solid rgba(201,169,110,0.2)',backdropFilter:'blur(8px)'}}>
        ← 返回全国地图
      </motion.button>

      {/* 各市统计面板 */}
      <div className="absolute bottom-6 left-6 right-6 z-10">
        <div className="flex flex-wrap gap-2 justify-center">
          {Object.entries(cityData).sort((a, b) => b[1].count - a[1].count).map(([city, data]) => (
            <div key={city}
              className="rounded-xl px-4 py-2 text-center min-w-[80px]"
              style={{background:'rgba(37,37,56,0.5)',border:'1px solid rgba(201,169,110,0.15)',backdropFilter:'blur(8px)'}}>
              <div className="text-[#E8E0D5] font-bold text-sm">{CITY_SHORT[city] || city}</div>
              <div className="text-[#C9A96E] font-mono text-xs font-bold">{data.count}</div>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
