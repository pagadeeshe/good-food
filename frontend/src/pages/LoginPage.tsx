import { FormEvent, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (user) {
    return <Navigate to={user.is_portal_admin ? '/admin' : '/today'} replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="login-hero-content">
          <span className="login-badge">Fresh · Daily · Simple</span>
          <h1>Good Food</h1>
          <p>
            Browse today&apos;s menu, place your lunch order in seconds,
            and let the kitchen know exactly what to prepare.
          </p>
          <ul className="login-features">
            <li><span>🍱</span> Daily curated menus</li>
            <li><span>⚡</span> One-tap ordering</li>
            <li><span>👨‍🍳</span> Kitchen-ready reports</li>
          </ul>
        </div>
        <div className="login-hero-orbs" aria-hidden>
          <span className="orb orb-1" />
          <span className="orb orb-2" />
          <span className="orb orb-3" />
        </div>
      </div>

      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-card-head">
          <h2>Welcome back</h2>
          <p className="muted">Sign in with your company email</p>
        </div>
        {error && <div className="alert error">{error}</div>}
        <label className="field">
          <span>Email address</span>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
            autoComplete="email"
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="current-password"
          />
        </label>
        <button type="submit" className="btn-primary btn-lg" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in →'}
        </button>
      </form>
    </div>
  );
}
