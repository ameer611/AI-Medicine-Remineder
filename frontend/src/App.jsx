import { Navigate, Route, Routes } from 'react-router-dom'
import NavBar from './components/NavBar'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Medicines from './pages/Medicines'
import Schedules from './pages/Schedules'
import Analytics from './pages/Analytics'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main className="page-shell">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/medicines"
            element={
              <ProtectedRoute>
                <Medicines />
              </ProtectedRoute>
            }
          />
          <Route
            path="/schedules"
            element={
              <ProtectedRoute>
                <Schedules />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}
