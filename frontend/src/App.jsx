import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { BrowserRouter } from 'react-router-dom'
import { AlertTriangle, BarChart3, Calculator, FileText, Gauge, LayoutDashboard, MessageSquare } from 'lucide-react'
import AppLayout from './components/AppLayout'
import LoginPage from './pages/auth/LoginPage'
import AdminAssembleePage from './pages/admin/AdminAssembleePage'
import AdminKpiPage from './pages/admin/AdminKpiPage'
import OperatoreImpiantiPage from './pages/operatore/OperatoreImpiantiPage'
import OperatoreSegnalazioniPage from './pages/operatore/OperatoreSegnalazioniPage'
import SocioDashboardPage from './pages/socio/SocioDashboardPage'
import SocioSegnalazioniPage from './pages/socio/SocioSegnalazioniPage'
import SocioSimulatorePage from './pages/socio/SocioSimulatorePage'

const navItemsByRole = {
  socio: [
    { to: '/socio/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/socio/simulatore', label: 'Simulatore', icon: Calculator },
    { to: '/socio/segnalazioni', label: 'Segnalazioni', icon: MessageSquare }
  ],
  operatore: [
    { to: '/operatore/impianti', label: 'Impianti', icon: Gauge },
    { to: '/operatore/segnalazioni', label: 'Segnalazioni', icon: AlertTriangle }
  ],
  admin: [
    { to: '/admin/kpi', label: 'KPI', icon: BarChart3 },
    { to: '/admin/assemblee', label: 'Assemblee', icon: FileText }
  ],
  login: []
}

function AppRoutes() {
  const location = useLocation()
  const currentRole = location.pathname.startsWith('/admin')
    ? 'admin'
    : location.pathname.startsWith('/operatore')
      ? 'operatore'
      : location.pathname.startsWith('/socio')
        ? 'socio'
        : 'login'

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/socio/dashboard" replace />} />
      <Route
        path="/login"
        element={
          <AppLayout role="login" navItems={navItemsByRole.login}>
            <LoginPage />
          </AppLayout>
        }
      />
      <Route
        path="/socio/dashboard"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.socio} title="Dashboard socio" subtitle="Riepilogo consumi e prestazioni comunitarie">
            <SocioDashboardPage />
          </AppLayout>
        }
      />
      <Route
        path="/socio/simulatore"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.socio} title="Simulatore CER" subtitle="Scenario di condivisione e incentivo">
            <SocioSimulatorePage />
          </AppLayout>
        }
      />
      <Route
        path="/socio/segnalazioni"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.socio} title="Segnalazioni socio" subtitle="Comunicazioni e richieste del membro">
            <SocioSegnalazioniPage />
          </AppLayout>
        }
      />
      <Route
        path="/operatore/impianti"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.operatore} title="Impianti" subtitle="Monitoraggio produzione e anomalie">
            <OperatoreImpiantiPage />
          </AppLayout>
        }
      />
      <Route
        path="/operatore/segnalazioni"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.operatore} title="Segnalazioni operatore" subtitle="Coda prioritaria e classificazione LLM">
            <OperatoreSegnalazioniPage />
          </AppLayout>
        }
      />
      <Route
        path="/admin/kpi"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.admin} title="KPI comunità" subtitle="Indicatore aggregato del portale CER">
            <AdminKpiPage />
          </AppLayout>
        }
      />
      <Route
        path="/admin/assemblee"
        element={
          <AppLayout role={currentRole} navItems={navItemsByRole.admin} title="Verbali assemblee" subtitle="Sintesi e dettaglio decisioni della comunità">
            <AdminAssembleePage />
          </AppLayout>
        }
      />
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
