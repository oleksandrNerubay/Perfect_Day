import { useState, useRef, useEffect } from 'react'
import './TopMenu.css'

// Menu items config — add/rename/reorder here; no component changes needed
const MENU_ITEMS = [
  { id: 'profile',       label: 'Profile',        onPress: () => console.log('Profile') },
  { id: 'settings',      label: 'Settings',        onPress: () => console.log('Settings') },
  { id: 'history',       label: 'History',         onPress: () => console.log('History') },
  { id: 'notifications', label: 'Notifications',   onPress: () => console.log('Notifications') },
  { id: 'help',          label: 'Help & Feedback',  onPress: () => console.log('Help & Feedback') },
  { id: 'signout',       label: 'Sign Out',         onPress: () => console.log('Sign Out'), danger: true },
]

export default function TopMenu() {
  const [open, setOpen]  = useState(false)
  const menuRef          = useRef(null)

  // Close on outside click
  useEffect(() => {
    if (!open) return
    const handle = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [open])

  return (
    <div className="top-menu" ref={menuRef}>
      <button
        className={`hamburger ${open ? 'hamburger--open' : ''}`}
        onClick={() => setOpen(v => !v)}
        aria-label={open ? 'Close menu' : 'Open menu'}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span className="bar" />
        <span className="bar" />
        <span className="bar" />
      </button>

      {open && (
        <div className="menu-panel" role="menu">
          {MENU_ITEMS.map(item => (
            <button
              key={item.id}
              className={`menu-row ${item.danger ? 'menu-row--danger' : ''}`}
              role="menuitem"
              onClick={() => { item.onPress(); setOpen(false) }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
