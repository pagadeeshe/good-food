import { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import type { MealType, TodayReportsResponse } from '../../api/types';
import { MEAL_LABELS } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

export function AdminOrdersReportPage() {
  const [report, setReport] = useState<TodayReportsResponse | null>(null);
  const [activeMeal, setActiveMeal] = useState<MealType>('lunch');
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest<TodayReportsResponse>('/api/orders/reports/today/')
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load report'));
  }, []);

  if (error) return <div className="alert error">{error}</div>;
  if (!report) return <LoadingState label="Loading kitchen report…" />;

  const dateLabel = new Date(report.date).toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long',
  });
  const mealReport = report[activeMeal];

  return (
    <div className="admin-page">
      <PageHeader eyebrow="Kitchen" title="Tomorrow's Report" subtitle={dateLabel} icon="👨‍🍳" />

      <div className="meal-tabs">
        {MEALS.map((meal) => (
          <button key={meal} type="button"
            className={`meal-tab ${activeMeal === meal ? 'active' : ''}`}
            onClick={() => setActiveMeal(meal)}>
            <span className="meal-tab-label">{MEAL_LABELS[meal]}</span>
            <span className="meal-tab-deadline">{report[meal].total_orders} orders</span>
          </button>
        ))}
      </div>

      <div className="stats-grid stats-grid-hero">
        <div className="stat stat-1">
          <span className="stat-icon" aria-hidden>📦</span>
          <strong>{mealReport.total_orders}</strong>
          <span>Orders</span>
        </div>
        <div className="stat stat-2">
          <span className="stat-icon" aria-hidden>👥</span>
          <strong>{mealReport.total_users}</strong>
          <span>People</span>
        </div>
        <div className="stat stat-3">
          <span className="stat-icon" aria-hidden>🥡</span>
          <strong>{mealReport.total_items}</strong>
          <span>Total items</span>
        </div>
      </div>

      <div className="card card-elevated table-card">
        {mealReport.items.length === 0 ? (
          <p className="muted empty-inline">No {MEAL_LABELS[activeMeal].toLowerCase()} orders for this menu yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Item</th><th>Category</th><th>Quantity</th></tr>
            </thead>
            <tbody>
              {mealReport.items.map((row) => (
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
