import { Link, Navigate, Route, Routes } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import IncidentDetailPage from './pages/IncidentDetailPage'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Incident Management System</p>
          <h1>IMS Console</h1>
        </div>
        <nav className="nav-links">
          <Link to="/">Dashboard</Link>
        </nav>
      </header>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/incident/:id" element={<IncidentDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
