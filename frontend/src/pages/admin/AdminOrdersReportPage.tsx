import { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import type { OrderTotals } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

export function AdminOrdersReportPage() {
  const [report, setReport] = useState<OrderTotals | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest<OrderTotals>('/api/orders/reports/today/')
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load report'));
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!report) return <LoadingState label="Loading kitchen report…" />;

  const dateLabel = new Date(report.date).toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Kitchen"
        title="Today's Report"
        subtitle={dateLabel}
        icon="👨‍🍳"
      />

      <div className="stats-grid stats-grid-hero">
        <div className="stat stat-1">
          <span className="stat-icon" aria-hidden>📦</span>
          <strong>{report.total_orders}</strong>
          <span>Orders</span>
        </div>
        <div className="stat stat-2">
          <span className="stat-icon" aria-hidden>👥</span>
          <strong>{report.total_users}</strong>
          <span>People</span>
        </div>
        <div className="stat stat-3">
          <span className="stat-icon" aria-hidden>🥡</span>
          <strong>{report.total_items}</strong>
          <span>Total items</span>
        </div>
      </div>

      <div className="card card-elevated table-card">
        {report.items.length === 0 ? (
          <p className="muted empty-inline">No orders yet today — check back at lunch time.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Item</th>
                <th>Category</th>
                <th>Quantity</th>
              </tr>
            </thead>
            <tbody>
              {report.items.map((row) => (
                <tr key={row.item_name}>
                  <td><strong>{row.item_name}</strong></td>
                  <td><span className={`badge badge-${row.item_category}`}>{row.item_category}</span></td>
                  <td><span className="qty-tag qty-tag-lg">{row.total_quantity}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
