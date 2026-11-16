import DemoRoleSwitcher from './DemoRoleSwitcher'
import SidebarNav from './SidebarNav'

export default function AppLayout({ role, navItems, title, subtitle, children }) {
  const showSidebar = role !== 'login'

  return (
    <div className="app-shell">
      <DemoRoleSwitcher currentRole={role} />

      <div className="app-body">
        {showSidebar && (
          <aside className="sidebar">
            <div className="brand-box">
              <div className="brand-mark">☀</div>
              <div>
                <div className="brand-kicker">CER</div>
                <div className="brand-name">UnderTheSun</div>
              </div>
            </div>
            <SidebarNav items={navItems} role={role} />
          </aside>
        )}

        <main className="main-pane">
          {title && (
            <header className="page-header">
              <div>
                <p className="section-kicker">Wireframe interattivo</p>
                <h1>{title}</h1>
              </div>
              {subtitle && <span className="page-subtitle">{subtitle}</span>}
            </header>
          )}
          <div className="page-content">{children}</div>
        </main>
      </div>
    </div>
  )
}
