import { NavLink } from 'react-router-dom'

function BasketballIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="36" cy="36" r="34" fill="#f7630c"/>
      <path d="M36 2 C36 2 22 18 22 36 C22 54 36 70 36 70" stroke="#1a0800" strokeWidth="2.2" fill="none"/>
      <path d="M36 2 C36 2 50 18 50 36 C50 54 36 70 36 70" stroke="#1a0800" strokeWidth="2.2" fill="none"/>
      <path d="M2 36 C2 36 18 22 36 22 C54 22 70 36 70 36" stroke="#1a0800" strokeWidth="2.2" fill="none"/>
      <path d="M2 36 C2 36 18 50 36 50 C54 50 70 36 70 36" stroke="#1a0800" strokeWidth="2.2" fill="none"/>
    </svg>
  )
}

export default function Nav() {
  return (
    <nav className="topnav">
      <NavLink to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
        <BasketballIcon />
        <span>Positionless<span className="dot"> ●</span> NBA</span>
      </NavLink>
      <div className="nav-links">
        <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Home</NavLink>
        <NavLink to="/explorer" className={({ isActive }) => isActive ? 'active' : ''}>Index Explorer</NavLink>
        <NavLink to="/paper" className={({ isActive }) => isActive ? 'active' : ''}>Paper</NavLink>
      </div>
    </nav>
  )
}