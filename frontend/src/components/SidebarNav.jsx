import { NavLink } from 'react-router-dom'

export default function SidebarNav({ items = [], role }) {
  return (
    <nav className="sidebar-nav" aria-label={`Menu ${role}`}>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          <span className="nav-icon">{item.icon}</span>
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
