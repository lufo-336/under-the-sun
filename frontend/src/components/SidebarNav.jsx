import { NavLink } from 'react-router-dom'

export default function SidebarNav({ items = [], role, variant = 'sidebar', className = '' }) {
  return (
    <nav
      className={`${variant === 'mobile' ? 'fixed inset-x-3 bottom-3 z-40 flex justify-around rounded-2xl border border-border bg-card/95 p-1.5 shadow-soft backdrop-blur lg:hidden' : 'space-y-1'} ${className}`}
      aria-label={`Menu ${role}`}
    >
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${variant === 'mobile' ? 'flex-1 flex-col gap-0.5 py-2 text-[11px]' : ''} ${isActive ? 'bg-sidebar-accent font-semibold text-sidebar-accent-foreground' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}
          end
        >
          <item.icon className={variant === 'mobile' ? 'h-5 w-5' : 'h-4 w-4 shrink-0'} aria-hidden="true" />
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
