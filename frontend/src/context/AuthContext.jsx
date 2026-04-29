import { createContext, useEffect, useState } from 'react'
import { getMe } from '../api/auth'
import { getAuthToken } from '../api/client'

export const AuthContext = createContext(null)

function storeToken(token) {
  localStorage.setItem('jwt_token', token)
  sessionStorage.setItem('jwt_token', token)
}

function clearToken() {
  localStorage.removeItem('jwt_token')
  sessionStorage.removeItem('jwt_token')
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    const token = getAuthToken()
    if (!token) {
      setLoading(false)
      return
    }

    getMe()
      .then(profile => {
        if (alive) setUser(profile)
      })
      .catch(() => {
        clearToken()
      })
      .finally(() => {
        if (alive) setLoading(false)
      })

    return () => {
      alive = false
    }
  }, [])

  const loginWithToken = async (token, profile = null) => {
    storeToken(token)
    if (profile) {
      setUser(profile)
      return profile
    }

    const me = await getMe()
    setUser(me)
    return me
  }

  const logout = () => {
    clearToken()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithToken, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}
