import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from './LoadingSpinner'

export default function ProtectedRoute({ children }) {
  const auth = useAuth()

  if (auth?.loading) return <LoadingSpinner label="Loading your profile..." />
  if (!auth?.user) return <Navigate to="/login" replace />
  return children
}
