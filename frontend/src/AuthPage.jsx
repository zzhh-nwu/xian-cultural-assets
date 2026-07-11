import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from './AuthContext'

import API from './api'

export default function AuthPage({ onSuccess }) {
  const { login } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!username.trim() || !password.trim()) {
      setError('请填写用户名和密码')
      return
    }
    if (mode === 'register' && password.length < 6) {
      setError('密码至少6位')
      return
    }
    setLoading(true)

    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register'
      const body = mode === 'login'
        ? { username: username.trim(), password }
        : { username: username.trim(), password, email: email.trim() }

      const r = await fetch(`${API}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const d = await r.json()

      if (d.success) {
        login(d.token, d.user)
        if (onSuccess) onSuccess()
      } else {
        setError(d.detail || '操作失败')
      }
    } catch (e) {
      setError('网络错误，请稍后重试')
    }
    setLoading(false)
  }

  const inputClass = "w-full rounded-xl px-4 py-3 text-sm font-medium outline-none bg-transparent text-[#E8E0D5] placeholder:text-[#9B8E82] transition-all duration-300"
  const inputStyle = { border: '1px solid rgba(201,169,110,0.2)' }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="rounded-2xl oriental p-8 w-full max-w-[420px]"
        style={{ background: 'rgba(37,37,56,0.5)', backdropFilter: 'blur(12px)' }}
      >
        <div className="text-center mb-6">
          <div className="text-4xl mb-2">
            {mode === 'login' ? '🔐' : '📝'}
          </div>
          <h2 className="text-2xl font-black text-[#C9A96E]" style={{ fontFamily: "'Noto Serif SC', serif" }}>
            {mode === 'login' ? '用户登录' : '注册账号'}
          </h2>
          <p className="text-sm text-[#B8A99A] mt-1">
            {mode === 'login' ? '登录后上传资产，参与共建' : '加入平台，分享你的文化数字资产'}
          </p>
        </div>

        {error && (
          <div className="rounded-xl px-4 py-3 mb-4 text-sm font-semibold" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#fca5a5' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">用户名</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="请输入用户名"
              className={inputClass}
              style={inputStyle}
            />
          </div>

          {mode === 'register' && (
            <div>
              <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">邮箱（选填）</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                className={inputClass}
                style={inputStyle}
              />
            </div>
          )}

          <div>
            <label className="text-sm font-bold text-[#B8A99A] mb-1.5 block">密码</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder={mode === 'register' ? '至少6位密码' : '请输入密码'}
              className={inputClass}
              style={inputStyle}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full font-semibold text-base py-3.5 rounded-xl transition-all duration-300 disabled:opacity-50 mt-2"
            style={{ background: 'linear-gradient(135deg, #8B3A3A, #C9A96E)', color: '#fff' }}
          >
            {loading ? '处理中…' : mode === 'login' ? '登录' : '注册'}
          </button>
        </form>

        <div className="mt-5 text-center">
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="text-sm font-semibold text-[#C9A96E] hover:underline"
          >
            {mode === 'login' ? '没有账号？立即注册 →' : '已有账号？去登录 →'}
          </button>
        </div>

        {mode === 'login' && (
          <div className="mt-3 text-center text-xs text-[#9B8E82]/40">
            管理员测试：admin / admin123
          </div>
        )}
      </motion.div>
    </div>
  )
}
