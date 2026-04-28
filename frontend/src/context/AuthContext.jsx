import { createContext, useEffect, useState } from 'react'
import { getMe } from '../api/auth'

export const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    const token = localStorage.getItem('jwt_token')
    if (!token) {
      setLoading(false)
      return
    }

    getMe()
      .then(profile => {
        if (alive) setUser(profile)
      })
      .catch(() => {
        localStorage.removeItem('jwt_token')
      })
      .finally(() => {
        if (alive) setLoading(false)
      })

    return () => {
      alive = false
    }
  }, [])

  const loginWithToken = async token => {
    localStorage.setItem('jwt_token', token)
    const profile = await getMe()
    setUser(profile)
  }

  const logout = () => {
    localStorage.removeItem('jwt_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginWithToken, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}
