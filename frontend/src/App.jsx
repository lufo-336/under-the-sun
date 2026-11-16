import { Navigate, Route, Routes } from 'react-router-dom'
import { BrowserRouter } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import AdminAssembleePage from './pages/admin/AdminAssembleePage'
import AdminKpiPage from './pages/admin/AdminKpiPage'
import OperatoreImpiantiPage from './pages/operatore/OperatoreImpiantiPage'
import OperatoreSegnalazioniPage from './pages/operatore/OperatoreSegnalazioniPage'
import SocioDashboardPage from './pages/socio/SocioDashboardPage'
import SocioSegnalazioniPage from './pages/socio/SocioSegnalazioniPage'
import SocioSimulatorePage from './pages/socio/SocioSimulatorePage'
import './App.css'

const navItemsByRole = {
  socio: [
    { to: '/socio/dashboard', label: 'Dashboard', icon: '▣' },
    { to: '/socio/simulatore', label: 'Simulatore', icon: '↗' },
    { to: '/socio/segnalazioni', label: 'Segnalazioni', icon: '✦' }
  ],
  operatore: [
    { to: '/operatore/impianti', label: 'Impianti', icon: '▣' },
    { to: '/operatore/segnalazioni', label: 'Segnalazioni', icon: '✦' }
  ],
  admin: [
    { to: '/admin/kpi', label: 'KPI', icon: '▣' },
    { to: '/admin/assemblee', label: 'Assemblee', icon: '☰' }
  ],
  login: []
}

const AppRoutes = () => {
  const routesConfig = [
    { path: '/socio/dashboard', role: 'socio', element: <SocioDashboardPage /> },
    { path: '/socio/simulatore', role: 'socio', element: <SocioSimulatorePage /> },
    { path: '/socio/segnalazioni', role: 'socio', element: <SocioSegnalazioniPage /> },
    { path: '/operatore/impianti', role: 'operatore', element: <OperatoreImpiantiPage /> },
    { path: '/operatore/segnalazioni', role: 'operatore', element: <OperatoreSegnalazioniPage /> },
    { path: '/admin/kpi', role: 'admin', element: <AdminKpiPage /> },
    { path: '/admin/assemblee', role: 'admin', element: <AdminAssembleePage /> },
    { path: '/', element: <Navigate to="/login" replace /> },
    { path: '*', element: <Navigate to="/login" replace /> }
  ]
  return (
    <Routes>
      {routesConfig.map(({ path, role, element }) => (
        <Route key={path} path={path} element={<AppLayout role={role} navItems={navItemsByRole[role]}>{element}</AppLayout>} />
      ))}
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}

export default App
