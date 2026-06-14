import { Link, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const USER_NAV = [
  { to: '/today', label: "Today's Menu", icon: '🍽️' },
  { to: '/orders', label: 'My Orders', icon: '📋' },
] as const;

const ADMIN_ITEMS = [
  { to: '/admin', label: 'Dashboard', icon: '📊' },
  { to: '/admin/weekly', label: 'Weekly', icon: '📅' },
  { to: '/admin/daily', label: 'Daily', icon: '🗓️' },
  { to: '/admin/orders', label: 'All Orders', icon: '📋' },
  { to: '/admin/reports', label: 'Kitchen', icon: '👨‍🍳' },
] as const;

export function Layout() {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const initial = user?.full_name?.charAt(0)?.toUpperCase() ?? '?';

  const navLink = (to: string, label: string, icon: string) => {
    const active = location.pathname === to
      || (to !== '/admin' && location.pathname.startsWith(to));
    return (
      <Link
        key={to}
        to={to}
        className={active ? 'nav-link active' : 'nav-link'}
      >
        <span className="nav-icon" aria-hidden>{icon}</span>
        {label}
      </Link>
    );
  };

  return (
    <div className="app-shell">
      <div className="app-bg" aria-hidden />
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden>🥗</span>
          <div>
            <span className="brand-name">Good Food</span>
            <span className="brand-tag">Office lunch, simplified</span>
          </div>
        </div>
        <nav className="nav">
          {(isAdmin ? USER_NAV.filter((item) => item.to !== '/orders') : USER_NAV)
            .map(({ to, label, icon }) => navLink(to, label, icon))}
          {isAdmin && ADMIN_ITEMS.map(({ to, label, icon }) => navLink(to, label, icon))}
        </nav>
        <div className="user-bar">
          <div className="user-chip">
            <span className="avatar">{initial}</span>
            <div className="user-meta">
              <span className="user-name">{user?.full_name}</span>
              <span className="user-role">{isAdmin ? 'Admin' : 'Student'}</span>
            </div>
          </div>
          <button type="button" className="btn-ghost" onClick={() => logout()}>
            Logout
          </button>
        </div>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}
