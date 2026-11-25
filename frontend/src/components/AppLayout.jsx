import { Sun } from 'lucide-react'
import SidebarNav from './SidebarNav'
import UserBar from './UserBar'

function Logo() {
  return (
    <div className="flex min-w-0 items-center gap-2.5">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-gradient-sun text-primary-foreground shadow-glow">
        <Sun className="h-5 w-5" aria-hidden="true" />
      </span>
      <span className="min-w-0 leading-tight">
        <span className="block truncate text-base font-extrabold tracking-tight text-foreground">UnderTheSun</span>
        <span className="block truncate text-[11px] font-semibold uppercase tracking-wider text-primary">CER Buby Green</span>
      </span>
    </div>
  )
}

export default function AppLayout({ role, navItems, title, subtitle, children }) {
  const showSidebar = role !== 'login'
  return (
    <div className="min-h-screen bg-page">
      <UserBar role={role} />

      <div className="mx-auto flex max-w-7xl gap-6 px-4 pb-28 pt-6 lg:pb-10">
        {showSidebar && (
          <aside className="sticky top-16 hidden h-fit w-60 shrink-0 rounded-2xl border border-border bg-sidebar p-4 shadow-soft lg:block">
            <Logo />
            <p className="mb-2 mt-6 px-3 text-[11px] font-bold uppercase tracking-wider text-muted-foreground">Area {role}</p>
            <SidebarNav items={navItems} role={role} />
          </aside>
        )}

        <main className="min-w-0 flex-1">
          {showSidebar && <div className="mb-5 lg:hidden"><Logo /></div>}
          {title && (
            <header className="mb-6">
              <h1 className="text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">{title}</h1>
              {subtitle && <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>}
            </header>
          )}
          {children}
        </main>
      </div>
      {showSidebar && <SidebarNav items={navItems} role={role} variant="mobile" />}
    </div>
  )
}
