import { useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import type { AdminOrdersResponse, MealType } from '../../api/types';
import { MEAL_LABELS } from '../../api/types';
import { EmptyState, LoadingState, PageHeader } from '../../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

type FilterMode = 'tomorrow' | 'all';

export function AdminAllOrdersPage() {
  const [data, setData] = useState<AdminOrdersResponse | null>(null);
  const [activeMeal, setActiveMeal] = useState<MealType | 'all'>('all');
  const [filterMode, setFilterMode] = useState<FilterMode>('tomorrow');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError('');
    const params = new URLSearchParams();
    if (filterMode === 'all') {
      params.set('all', '1');
    }
    if (activeMeal !== 'all') {
      params.set('meal', activeMeal);
    }
    const query = params.toString();
    apiRequest<AdminOrdersResponse>(`/api/orders/admin/${query ? `?${query}` : ''}`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load orders'))
      .finally(() => setLoading(false));
  }, [activeMeal, filterMode]);

  if (loading) return <LoadingState label="Loading orders…" />;
  if (error) return <div className="alert error">{error}</div>;

  const menuDateLabel = data?.menu_date
    ? new Date(data.menu_date + 'T12:00:00').toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long',
      })
    : '';

  const orders = data?.orders ?? [];

  return (
    <div className="orders-page admin-page">
      <PageHeader
        eyebrow="Admin"
        title="All Orders"
        subtitle={
          data?.show_all
            ? 'Every active order across all menu dates'
            : `Orders for menu date: ${menuDateLabel}`
        }
        icon="📋"
      />

      <div className="filter-row" style={{ marginBottom: '1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button
          type="button"
          className={filterMode === 'tomorrow' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setFilterMode('tomorrow')}
        >
          Tomorrow&apos;s menu
        </button>
        <button
          type="button"
          className={filterMode === 'all' ? 'btn-primary' : 'btn-secondary'}
          onClick={() => setFilterMode('all')}
        >
          All dates
        </button>
        <span className="muted" style={{ alignSelf: 'center', marginLeft: '0.5rem' }}>
          {orders.length} order{orders.length === 1 ? '' : 's'}
        </span>
      </div>

      <div className="meal-tabs">
        <button
          type="button"
          className={`meal-tab ${activeMeal === 'all' ? 'active' : ''}`}
          onClick={() => setActiveMeal('all')}
        >
          <span className="meal-tab-label">All meals</span>
        </button>
        {MEALS.map((meal) => (
          <button
            key={meal}
            type="button"
            className={`meal-tab ${activeMeal === meal ? 'active' : ''}`}
            onClick={() => setActiveMeal(meal)}
          >
            <span className="meal-tab-label">{MEAL_LABELS[meal]}</span>
          </button>
        ))}
      </div>

      {orders.length === 0 ? (
        <div className="card card-elevated">
          <EmptyState
            icon="📋"
            title="No orders yet"
            message={
              filterMode === 'all'
                ? 'No student orders have been placed.'
                : `No orders for ${menuDateLabel || 'this menu date'} yet.`
            }
          />
        </div>
      ) : (
        <div className="card card-elevated table-card">
          <table className="data-table admin-orders-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Student ID</th>
                <th>Menu date</th>
                <th>Meal</th>
                <th>Items ordered</th>
                <th>Notes</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => (
                <tr key={order.id}>
                  <td><strong>{order.user_name}</strong></td>
                  <td className="muted">{order.student_id}</td>
                  <td>
                    {new Date(order.menu_date + 'T12:00:00').toLocaleDateString('en-IN', {
                      weekday: 'short', day: 'numeric', month: 'short',
                    })}
                  </td>
                  <td>{order.meal_type_display}</td>
                  <td>
                    <ul className="admin-order-items-inline">
                      {order.order_items.map((item) => (
                        <li key={item.id}>
                          <span>{item.item_name}</span>
                          <span className="qty-tag">×{item.quantity}</span>
                        </li>
                      ))}
                    </ul>
                  </td>
                  <td className="muted">{order.notes || '—'}</td>
                  <td>
                    <span className={`status-pill status-${order.status}`}>{order.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

}
