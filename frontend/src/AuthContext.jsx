import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

import API from './api'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [ready, setReady] = useState(false)

  // 启动时验证 token 有效性
  useEffect(() => {
    if (!token) { setReady(true); return }
    fetch(`${API}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(d => {
        if (d.success && d.user) {
          setUser(d.user)
        } else {
          logout()
        }
      })
      .catch(() => logout())
      .finally(() => setReady(true))
  }, [])

  const login = (newToken, userData) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    setUser(userData)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken('')
    setUser(null)
  }

  const apiAuth = (url, options = {}) => {
    return fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    })
  }

  return (
    <AuthContext.Provider value={{ user, token, ready, login, logout, apiAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
