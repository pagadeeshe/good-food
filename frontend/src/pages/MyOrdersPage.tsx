import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import type { Order } from '../api/types';
import { EmptyState, LoadingState, PageHeader } from '../components/PageHeader';

interface PaginatedOrders {
  results: Order[];
}

export function MyOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<PaginatedOrders | Order[]>('/api/orders/my/')
      .then((data) => {
        setOrders(Array.isArray(data) ? data : data.results);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load orders'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Loading your orders…" />;
  if (error) return <div className="alert error">{error}</div>;

  return (
    <div className="orders-page">
      <PageHeader
        eyebrow="History"
        title="My Orders"
        subtitle="Your past lunch orders at a glance."
        icon="📋"
      />

      {orders.length === 0 ? (
        <div className="card card-elevated">
          <EmptyState
            icon="🍽️"
            title="No orders yet"
            message="Head to Today's Menu and place your first order!"
          />
        </div>
      ) : (
        <div className="order-list">
          {orders.map((order) => (
            <article key={order.id} className="order-card">
              <header>
                <div>
                  <time>
                    {new Date(order.order_date).toLocaleDateString('en-IN', {
                      weekday: 'short',
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
                  </time>
                  <span className="order-meta">{order.total_items} items</span>
                </div>
                <span className={`status-pill status-${order.status}`}>{order.status}</span>
              </header>
              <ul className="order-items">
                {order.order_items.map((item) => (
                  <li key={item.id}>
                    <span>{item.item_name}</span>
                    <span className="qty-tag">×{item.quantity}</span>
                  </li>
                ))}
              </ul>
              {order.notes && (
                <p className="order-notes">
                  <span>💬</span> {order.notes}
                </p>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
