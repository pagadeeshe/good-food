import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import type { AdminDashboard } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

const STAT_ICONS = ['📦', '👥', '🥡', '📅'] as const;

export function AdminDashboardPage() {
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest<AdminDashboard>('/api/admin/dashboard/')
      .then(setData)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Failed to load dashboard'));
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!data) return <LoadingState label="Loading dashboard…" />;

  const stats = [
    { label: 'Orders today', value: data.order_totals.total_orders },
    { label: 'People ordering', value: data.order_totals.total_users },
    { label: 'Items ordered', value: data.order_totals.total_items },
    { label: 'Weekly templates', value: data.weekday_count },
  ];

  const dateLabel = new Date(data.today).toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Admin"
        title="Dashboard"
        subtitle={dateLabel}
        icon="📊"
      />

      <div className="stats-grid stats-grid-hero">
        {stats.map((stat, i) => (
          <div key={stat.label} className={`stat stat-${i + 1}`}>
            <span className="stat-icon" aria-hidden>{STAT_ICONS[i]}</span>
            <strong>{stat.value}</strong>
            <span>{stat.label}</span>
          </div>
        ))}
      </div>

      <div className="card card-elevated">
        <div className="card-section-head">
          <h3>Today&apos;s menu</h3>
          <span className="badge">{data.today_source}</span>
        </div>
        {data.today_items.length === 0 ? (
          <p className="muted">No items scheduled for today.</p>
        ) : (
          <ul className="menu-preview-list">
            {data.today_items.map((item: { name: string; category: string }) => (
              <li key={item.name}>
                <span>{item.name}</span>
                <span className={`badge badge-${item.category}`}>{item.category}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="actions">
          <Link to="/admin/daily" className="btn-secondary">Manage daily menus</Link>
          <Link to="/admin/reports" className="btn-primary">Kitchen report →</Link>
        </div>
      </div>
    </div>
  );
}
