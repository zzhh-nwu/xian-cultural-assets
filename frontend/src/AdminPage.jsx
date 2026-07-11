import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from './AuthContext'

import API from './api'
const pageIn = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.4, ease: [0.25, 0.1, 0.25, 1] },
}

const STATUS_MAP = {
  pending: { label: '待审核', color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  approved: { label: '已通过', color: '#10b981', bg: 'rgba(16,185,129,0.1)' },
  rejected: { label: '已驳回', color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
}

const TYPE_MAP = {
  cultural_relic: '文物',
  intangible_heritage: '非遗',
  cultural_tourism: '文旅',
}

export default function AdminPage() {
  const { token } = useAuth()
  const [uploads, setUploads] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(false)
  const [reviewing, setReviewing] = useState(null)
  const [rejectReason, setRejectReason] = useState('')
  const [showRejectInput, setShowRejectInput] = useState(null)

  const loadUploads = () => {
    if (!token) return
    setLoading(true)
    fetch(`${API}/admin/pending`, {
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

  const doReview = async (uploadId, action, remark = '') => {
    setReviewing(uploadId)
    try {
      const r = await fetch(`${API}/admin/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ upload_id: uploadId, action, remark }),
      })
      const d = await r.json()
      if (d.success) {
        loadUploads()
        setShowRejectInput(null)
        setRejectReason('')
      } else {
        alert(d.detail || '操作失败')
      }
    } catch (e) {
      alert('网络错误')
    }
    setReviewing(null)
  }

  const filtered = filter === 'all'
    ? uploads
    : uploads.filter(u => u.status === filter)

  const pendingCount = uploads.filter(u => u.status === 'pending').length

  return (
    <motion.div {...pageIn} className="py-10">
      <span className="text-sm font-bold text-[#C9A96E] tracking-widest">管理后台</span>
      <h1 className="text-4xl md:text-5xl font-black tracking-tight mt-2 mb-1 text-[#E8E0D5]" style={{ fontFamily: "'Noto Serif SC', serif" }}>
        资产审核
      </h1>
      <p className="text-sm text-[#B8A99A] mb-6">
        🔍 {uploads.length} 条记录 · {pendingCount} 条待审核
      </p>

      {/* 筛选 */}
      <div className="flex gap-1.5 mb-6 flex-wrap">
        {[
          ['all', '全部'],
          ['pending', '待审核'],
          ['approved', '已通过'],
          ['rejected', '已驳回'],
        ].map(([k, v]) => (
          <button
            key={k}
            onClick={() => setFilter(k)}
            className={`px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 ${filter === k ? 'text-[#C9A96E]' : 'text-[#B8A99A] hover:text-[#C9A96E]'}`}
            style={filter === k ? { background: 'rgba(201,169,110,0.15)', border: '1px solid rgba(201,169,110,0.2)' } : { border: '1px solid rgba(201,169,110,0.1)' }}
          >
            {v} ({k === 'all' ? uploads.length : uploads.filter(u => u.status === k).length})
          </button>
        ))}
        <button
          onClick={loadUploads}
          className="ml-auto px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300 text-[#B8A99A] hover:text-[#C9A96E]"
          style={{ border: '1px solid rgba(201,169,110,0.15)' }}
        >
          🔄 刷新
        </button>
      </div>

      {loading ? (
        <div className="text-center py-16" style={{ color: 'rgba(184,169,154,0.3)' }}>加载中…</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 rounded-2xl" style={{ background: 'rgba(37,37,56,0.3)', border: '1px dashed rgba(201,169,110,0.2)' }}>
          <div className="text-5xl mb-3">✅</div>
          <p className="text-[#B8A99A] font-semibold">暂无符合条件的记录</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((u) => {
            const st = STATUS_MAP[u.status] || STATUS_MAP.pending
            return (
              <div
                key={u.id}
                className="rounded-2xl p-5 oriental"
                style={{ background: 'rgba(37,37,56,0.4)', backdropFilter: 'blur(8px)' }}
              >
                <div className="flex flex-col lg:flex-row gap-4 items-start">
                  {/* 缩略图 */}
                  {u.image_path ? (
                    <img
                      src={u.image_path}
                      alt={u.asset_name}
                      className="w-24 h-24 rounded-xl object-cover shrink-0"
                      style={{ border: '1px solid rgba(201,169,110,0.15)' }}
                    />
                  ) : (
                    <div className="w-24 h-24 rounded-xl flex items-center justify-center shrink-0 text-3xl"
                      style={{ background: 'rgba(45,45,66,0.6)' }}>
                      🏛️
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-lg font-bold text-[#E8E0D5]">{u.asset_name}</h3>
                      <span
                        className="text-xs font-bold px-2.5 py-1 rounded-full"
                        style={{ backgroundColor: st.bg, color: st.color }}
                      >
                        {st.label}
                      </span>
                    </div>
                    <p className="text-sm text-[#B8A99A]">
                      {TYPE_MAP[u.asset_type] || u.asset_type} · {u.city || u.province}
                    </p>
                    {u.description && (
                      <p className="text-sm text-[#9B8E82] mt-1 line-clamp-2">{u.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs" style={{ color: 'rgba(155,142,130,0.5)' }}>
                      <span>👤 {u.submitter_name || '未知用户'}</span>
                      <span>📅 {u.created_at}</span>
                      {u.reviewed_at && <span>✅ {u.reviewed_at}</span>}
                    </div>
                    {u.status === 'rejected' && u.reject_reason && (
                      <p className="text-xs text-red-400 mt-1">驳回原因：{u.reject_reason}</p>
                    )}
                  </div>

                  {/* 审核按钮（仅待审核状态） */}
                  {u.status === 'pending' && (
                    <div className="flex items-center gap-2 shrink-0 self-end lg:self-center">
                      {showRejectInput === u.id ? (
                        <div className="flex items-center gap-2">
                          <input
                            value={rejectReason}
                            onChange={e => setRejectReason(e.target.value)}
                            placeholder="驳回原因"
                            className="w-32 rounded-lg px-3 py-1.5 text-xs outline-none bg-transparent text-[#E8E0D5]"
                            style={{ border: '1px solid rgba(239,68,68,0.3)' }}
                          />
                          <button
                            onClick={() => doReview(u.id, 'reject', rejectReason)}
                            disabled={reviewing === u.id}
                            className="bg-red-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-red-600 disabled:opacity-50"
                          >
                            确认
                          </button>
                          <button
                            onClick={() => { setShowRejectInput(null); setRejectReason('') }}
                            className="text-xs text-[#B8A99A] hover:text-[#C9A96E]"
                          >
                            取消
                          </button>
                        </div>
                      ) : (
                        <>
                          <button
                            onClick={() => doReview(u.id, 'approve')}
                            disabled={reviewing === u.id}
                            className="font-bold text-sm px-5 py-2.5 rounded-xl disabled:opacity-50 transition-all duration-300"
                            style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}
                          >
                            {reviewing === u.id ? '…' : '✅ 通过'}
                          </button>
                          <button
                            onClick={() => setShowRejectInput(u.id)}
                            disabled={reviewing === u.id}
                            className="font-bold text-sm px-5 py-2.5 rounded-xl disabled:opacity-50 transition-all duration-300"
                            style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }}
                          >
                            ❌ 驳回
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </motion.div>
  )
}
