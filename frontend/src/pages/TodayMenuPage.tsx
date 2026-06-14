import { FormEvent, useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import type { TodayMenuResponse } from '../api/types';
import { EmptyState, LoadingState, PageHeader } from '../components/PageHeader';

const CATEGORY_EMOJI: Record<string, string> = {
  main: '🍛',
  side: '🥗',
  dessert: '🍰',
  drink: '🥤',
  snack: '🥪',
};

function categoryEmoji(category: string) {
  return CATEGORY_EMOJI[category.toLowerCase()] ?? '🍽️';
}

export function TodayMenuPage() {
  const [data, setData] = useState<TodayMenuResponse | null>(null);
  const [quantities, setQuantities] = useState<Record<number, number>>({});
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const res = await apiRequest<TodayMenuResponse>('/api/orders/today/');
      setData(res);
      const initial: Record<number, number> = {};
      res.menu?.items.forEach((item) => {
        initial[item.id] = item.quantity || 0;
      });
      setQuantities(initial);
      setNotes(res.order?.notes ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load menu');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function adjustQty(id: number, delta: number, max: number) {
    setQuantities((prev) => ({
      ...prev,
      [id]: Math.max(0, Math.min(max, (prev[id] ?? 0) + delta)),
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!data?.menu) return;

    const items = Object.entries(quantities)
      .filter(([, qty]) => qty > 0)
      .map(([menu_item_id, quantity]) => ({
        menu_item_id: Number(menu_item_id),
        quantity,
      }));

    if (items.length === 0) {
      setError('Select at least one item.');
      return;
    }

    setSaving(true);
    setError('');
    setMessage('');
    try {
      await apiRequest('/api/orders/today/', {
        method: 'POST',
        body: JSON.stringify({ items, notes }),
      });
      setMessage('Your order has been saved. Enjoy your meal!');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save order');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState label="Loading today's menu…" />;

  if (!data?.menu) {
    return (
      <div className="card card-elevated">
        <PageHeader
          eyebrow="Lunch"
          title="Today's Menu"
          subtitle="Check back when the kitchen publishes today's offerings."
          icon="🍽️"
        />
        <EmptyState
          icon="🥘"
          title="No menu yet"
          message="Today's menu hasn't been published. Check again soon!"
        />
      </div>
    );
  }

  const { menu } = data;
  const orderingOpen = menu.is_ordering_open;
  const totalSelected = Object.values(quantities).reduce((a, b) => a + b, 0);
  const dateLabel = new Date(menu.date).toLocaleDateString('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <div className="today-page">
      <PageHeader
        eyebrow="Lunch"
        title="Today's Menu"
        subtitle={dateLabel}
        icon="🍽️"
      >
        <span className={`status-pill ${orderingOpen ? 'open' : 'closed'}`}>
          {orderingOpen ? '● Orders open' : '● Orders closed'}
        </span>
      </PageHeader>

      <div className="card card-elevated">
        {!orderingOpen && (
          <div className="alert warning">
            {menu.orders_closed_reason || 'Ordering is closed for today.'}
          </div>
        )}
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <form onSubmit={handleSubmit}>
          <div className="menu-grid">
            {menu.items.map((item) => {
              const qty = quantities[item.id] ?? 0;
              return (
                <article
                  key={item.id}
                  className={`menu-item-card ${qty > 0 ? 'selected' : ''}`}
                >
                  <div className="menu-item-icon" aria-hidden>
                    {categoryEmoji(item.category)}
                  </div>
                  <div className="menu-item-body">
                    <div className="menu-item-top">
                      <h3>{item.name}</h3>
                      <span className={`badge badge-${item.category}`}>{item.category}</span>
                    </div>
                    <p className="muted">Max {item.max_quantity_per_user} per person</p>
                    <div className="qty-control">
                      <button
                        type="button"
                        className="qty-btn"
                        disabled={!orderingOpen || qty === 0}
                        onClick={() => adjustQty(item.id, -1, item.max_quantity_per_user)}
                        aria-label={`Decrease ${item.name}`}
                      >
                        −
                      </button>
                      <span className="qty-value">{qty}</span>
                      <button
                        type="button"
                        className="qty-btn"
                        disabled={!orderingOpen || qty >= item.max_quantity_per_user}
                        onClick={() => adjustQty(item.id, 1, item.max_quantity_per_user)}
                        aria-label={`Increase ${item.name}`}
                      >
                        +
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="order-footer">
            <label className="field">
              <span>Special notes <span className="muted">(optional)</span></span>
              <textarea
                value={notes}
                disabled={!orderingOpen}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Any allergies or preferences?"
                rows={2}
              />
            </label>

            <div className="order-submit-row">
              <div className="order-summary">
                <span className="muted">Items selected</span>
                <strong>{totalSelected}</strong>
              </div>
              <button
                type="submit"
                className="btn-primary btn-lg"
                disabled={!orderingOpen || saving}
              >
                {saving ? 'Saving…' : 'Place order →'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
