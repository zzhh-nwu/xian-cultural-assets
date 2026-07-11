import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from './AuthContext'

import API from './api'
const pageIn = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] },
}

const TYPE_OPTIONS = [
  ['cultural_relic', '文物'],
  ['intangible_heritage', '非遗'],
  ['cultural_tourism', '文旅'],
]

const STATUS_MAP = {
  pending: { label: '审核中', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  approved: { label: '已通过', color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  rejected: { label: '已驳回', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
}

export default function UserCenter() {
  const { user, token } = useAuth()
  const [tab, setTab] = useState('list') // 'list' | 'upload'
  const [uploads, setUploads] = useState([])
  const [loading, setLoading] = useState(false)

  // 上传表单
  const [assetName, setAssetName] = useState('')
  const [assetType, setAssetType] = useState('cultural_relic')
  const [description, setDescription] = useState('')
  const [city, setCity] = useState('西安')
  const [image, setImage] = useState(null)
  const [preview, setPreview] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [msg, setMsg] = useState('')

  const loadUploads = () => {
    if (!token) return
    setLoading(true)
    fetch(`${API}/upload/my`, {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) setUploads(d.uploads || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadUploads() }, [token])

  const handleImage = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      setMsg('图片大小不能超过5MB')
      return
    }
    setImage(file)
    setPreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!assetName.trim()) { setMsg('请填写资产名称'); return }
    setSubmitting(true)
    setMsg('')

    try {
      const formData = new FormData()
      formData.append('asset_name', assetName.trim())
      formData.append('asset_type', assetType)
      formData.append('description', description.trim())
      formData.append('city', city.trim())
      if (image) formData.append('image', image)

      const r = await fetch(`${API}/upload/create`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      })
      const d = await r.json()
      if (d.success) {
        setMsg('✅ 提交成功！等待管理员审核')
        setAssetName('')
        setDescription('')
        setImage(null)
        setPreview('')
        loadUploads()
        setTimeout(() => { setTab('list'); setMsg('') }, 1500)
      } else {
        setMsg('❌ ' + (d.detail || '提交失败'))
      }
    } catch (e) {
      setMsg('❌ 网络错误')
    }
    setSubmitting(false)
  }

  const inputClass = "w-full rounded-xl px-4 py-3 text-sm font-medium outline-none bg-transparent text-[#E8E0D5] placeholder:text-[#9B8E82] transition-all duration-300"
  const inputStyle = { border: '1px solid rgba(201,169,110,0.2)' }
  const selectStyle = { ...inputStyle, background: 'rgba(37,37,56,0.6)', color: '#E8E0D5' }

  return (
    <motion.div {...pageIn} className="py-10">
      <span className="text-sm font-bold text-[#C9A96E] tracking-widest">用户中心</span>
      <h1 className="text-4xl md:text-5xl font-black tracking-tight mt-2 mb-1 text-[#E8E0D5]" style={{ fontFamily: "'Noto Serif SC', serif" }}>
        我的资产
      </h1>
      <p className="text-sm text-[#B8A99A] mb-6">
        👤 {user?.username} · {user?.email || '未绑定邮箱'}
      </p>

      {/* Tab切换 */}
      <div className="flex gap-1.5 mb-6">
        <button
          onClick={() => setTab('list')}
          className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${tab === 'list' ? 'text-[#C9A96E]' : 'text-[#B8A99A] hover:text-[#C9A96E]'}`}
          style={tab === 'list' ? { background: 'rgba(201,169,110,0.15)', border: '1px solid rgba(201,169,110,0.2)' } : { border: '1px solid rgba(201,169,110,0.1)' }}
        >
          📋 我的上传记录 ({uploads.length})
        </button>
        <button
          onClick={() => setTab('upload')}
          className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${tab === 'upload' ? 'text-[#C9A96E]' : 'text-[#B8A99A] hover:text-[#C9A96E]'}`}
          style={tab === 'upload' ? { background: 'rgba(201,169,110,0.15)', border: '1px solid rgba(201,169,110,0.2)' } : { border: '1px solid rgba(201,169,110,0.1)' }}
        >
          ➕ 上传新资产
        </button>
      </div>

      {msg && (
        <div className="text-sm rounded-xl px-4 py-3 mb-4 font-bold"
          style={msg.startsWith('✅') ? { background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#6ee7b7' } : { background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5' }}>
          {msg}
        </div>
      )}

      {/* 上传记录列表 */}
      {tab === 'list' && (
        <div>
          {loading ? (
            <div className="text-center py-12" style={{ color: 'rgba(184,169,154,0.3)' }}>加载中…</div>
          ) : uploads.length === 0 ? (
            <div className="text-center py-16 rounded-2xl" style={{ background: 'rgba(37,37,56,0.3)', border: '1px dashed rgba(201,169,110,0.2)' }}>
              <div className="text-5xl mb-3">📭</div>
              <p className="text-[#B8A99A] font-semibold">暂无上传记录</p>
              <button
                onClick={() => setTab('upload')}
                className="mt-3 text-sm font-semibold px-5 py-2.5 rounded-xl transition-all duration-300"
                style={{ background: 'linear-gradient(135deg, #8B3A3A, #C9A96E)', color: '#fff' }}
              >
                去上传 →
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {uploads.map((u) => {
                const st = STATUS_MAP[u.status] || STATUS_MAP.pending
                return (
                  <div
                    key={u.id}
                    className="rounded-2xl p-5 flex flex-col sm:flex-row gap-4 items-start oriental"
                    style={{ background: 'rgba(37,37,56,0.4)', backdropFilter: 'blur(8px)' }}
                  >
                    {/* 缩略图 */}
                    {u.image_path ? (
                      <img
                        src={u.image_path}
                        alt={u.asset_name}
                        className="w-20 h-20 rounded-xl object-cover shrink-0"
                        style={{ border: '1px solid rgba(201,169,110,0.15)' }}
                      />
                    ) : (
                      <div className="w-20 h-20 rounded-xl flex items-center justify-center shrink-0 text-2xl"
                        style={{ background: 'rgba(45,45,66,0.6)' }}>
                        🏛️
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      <h3 className="text-base font-bold text-[#E8E0D5] truncate">{u.asset_name}</h3>
                      <p className="text-sm text-[#B8A99A] mt-0.5">
                        {u.asset_type === 'cultural_relic' ? '文物' : u.asset_type === 'intangible_heritage' ? '非遗' : '文旅'}
                        {' · '}{u.city || u.province || '陕西'}
                      </p>
                      {u.description && (
                        <p className="text-xs text-[#9B8E82] mt-1 line-clamp-2">{u.description}</p>
                      )}
                      <p className="text-xs mt-1.5" style={{ color: 'rgba(155,142,130,0.5)' }}>
                        提交于 {u.created_at}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span
                        className="text-xs font-bold px-3 py-1.5 rounded-full"
                        style={{ backgroundColor: st.bg, color: st.color }}
                      >
                        {st.label}
                      </span>
                      {u.status === 'rejected' && u.reject_reason && (
                        <span className="text-xs text-red-400 max-w-[120px] truncate" title={u.reject_reason}>
                          {u.reject_reason}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* 上传表单 */}
      {tab === 'upload' && (
        <div className="rounded-2xl oriental p-6 md:p-8" style={{ background: 'rgba(37,37,56,0.4)', backdropFilter: 'blur(8px)' }}>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">
                资产名称 <span className="text-red-400">*</span>
              </label>
              <input
                value={assetName}
                onChange={e => setAssetName(e.target.value)}
                placeholder="如：西安城墙永宁门、华阴老腔…"
                className={inputClass}
                style={inputStyle}
              />
            </div>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">资产类型</label>
                <div className="flex gap-2">
                  {TYPE_OPTIONS.map(([k, v]) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setAssetType(k)}
                      className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${assetType === k ? 'text-[#C9A96E]' : 'text-[#B8A99A] hover:text-[#C9A96E]'}`}
                      style={assetType === k ? { background: 'rgba(201,169,110,0.15)', border: '1px solid rgba(201,169,110,0.3)' } : { border: '1px solid rgba(201,169,110,0.1)' }}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">所属城市</label>
                <select
                  value={city}
                  onChange={e => setCity(e.target.value)}
                  className="w-full rounded-xl px-4 py-3 text-sm font-medium outline-none transition-all duration-300"
                  style={selectStyle}
                >
                  {[
                    '西安', '铜川', '宝鸡', '咸阳', '渭南',
                    '延安', '汉中', '榆林', '安康', '商洛',
                    '其他',
                  ].map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">资产描述</label>
              <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={4}
                placeholder="描述这个文化资产的历史背景、文化价值、数字化现状…"
                className={`${inputClass} resize-none`}
                style={inputStyle}
              />
            </div>

            <div>
              <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">资产图片（选填，≤5MB）</label>
              <div className="flex items-center gap-4">
                <label className="rounded-xl px-6 py-4 text-sm font-semibold cursor-pointer transition-all duration-300"
                  style={{ background: 'rgba(45,45,66,0.5)', border: '1px dashed rgba(201,169,110,0.25)', color: '#B8A99A' }}>
                  📁 选择图片
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImage}
                    className="hidden"
                  />
                </label>
                {preview && (
                  <div className="relative">
                    <img
                      src={preview}
                      alt="预览"
                      className="w-24 h-24 rounded-xl object-cover"
                      style={{ border: '1px solid rgba(201,169,110,0.2)' }}
                    />
                    <button
                      type="button"
                      onClick={() => { setImage(null); setPreview('') }}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs font-bold"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || !assetName.trim()}
              className="w-full font-semibold text-base py-3.5 rounded-xl transition-all duration-300 disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #8B3A3A, #C9A96E)', color: '#fff' }}
            >
              {submitting ? '提交中…' : '🚀 提交审核'}
            </button>
          </form>
        </div>
      )}
    </motion.div>
  )
}
