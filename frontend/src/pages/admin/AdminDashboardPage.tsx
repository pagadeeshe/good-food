import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import type { AdminDashboard, MealType } from '../../api/types';
import { MEAL_LABELS, ORDER_DEADLINE } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

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

  const orderingForLabel = new Date(data.ordering_for_date).toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long',
  });
  const orderingParts = data.ordering_for_date.split('-').map(Number);
  const orderingPathDate = orderingParts.length === 3
    ? { year: orderingParts[0], month: orderingParts[1], day: orderingParts[2] }
    : null;

  return (
    <div className="admin-page">
      <PageHeader eyebrow="Admin" title="Dashboard" subtitle={`Ordering for ${orderingForLabel}`} icon="📊" />

      <div className="meal-dashboard-grid">
        {MEALS.map((meal) => {
          const slot = data.menus[meal];
          const status = slot.daily_menu?.status ?? 'draft';
          const editPath = orderingPathDate
            ? `/admin/daily/${meal}/${orderingPathDate.year}/${orderingPathDate.month}/${orderingPathDate.day}`
            : `/admin/daily/${meal}`;
          return (
            <div key={meal} className="card card-elevated">
              <div className="card-section-head">
                <h3>{MEAL_LABELS[meal]}</h3>
                <span className={`status-pill status-${status}`}>{status}</span>
              </div>
              <div className="card-section-head" style={{ marginTop: '-0.5rem' }}>
                <span className="deadline-badge">⏰ Closes {ORDER_DEADLINE}</span>
              </div>
              <div className="mini-stats-row">
                <div className="stat-mini">
                  <strong>{slot.order_totals.total_orders}</strong>
                  <span>Orders</span>
                </div>
                <div className="stat-mini">
                  <strong>{slot.order_totals.total_students}</strong>
                  <span>Students</span>
                </div>
                <div className="stat-mini">
                  <strong>{slot.order_totals.total_items}</strong>
                  <span>Items</span>
                </div>
              </div>
              {status !== 'published' && (
                <p className="alert error" style={{ marginBottom: '0.75rem' }}>
                  Not visible to students — publish {MEAL_LABELS[meal].toLowerCase()} for {orderingForLabel}.
                </p>
              )}
              {slot.items.length === 0 ? (
                <p className="muted">No items for tomorrow.</p>
              ) : (
                <ul className="menu-preview-list">
                  {slot.items.map((item) => (
                    <li key={item.name}>
                      <span>{item.name}</span>
                      <span className={`badge badge-${item.category}`}>{item.category}</span>
                    </li>
                  ))}
                </ul>
              )}
              <div className="actions">
                <Link to={editPath} className="btn-primary">
                  {status === 'published' ? 'Edit menu' : 'Publish for tomorrow →'}
                </Link>
              </div>
            </div>
          );
        })}
      </div>

      <div className="actions" style={{ marginTop: '1rem' }}>
        <Link to="/admin/reports" className="btn-primary">Kitchen report →</Link>
      </div>
    </div>
  );
}
