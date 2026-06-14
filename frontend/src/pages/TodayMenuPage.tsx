import { FormEvent, useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import type { MealType, TodayMenusResponse } from '../api/types';
import { MEAL_LABELS, ORDER_DEADLINE } from '../api/types';
import { EmptyState, LoadingState, PageHeader } from '../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

const CATEGORY_EMOJI: Record<string, string> = {
  main: '🍛', side: '🥗', dessert: '🍰', drink: '🥤', snack: '🥪', rice: '🍚', curry: '🍲', beverage: '🥤',
};

function categoryEmoji(category: string) {
  return CATEGORY_EMOJI[category.toLowerCase()] ?? '🍽️';
}

export function TodayMenuPage() {
  const [data, setData] = useState<TodayMenusResponse | null>(null);
  const [activeMeal, setActiveMeal] = useState<MealType>('lunch');
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
      const res = await apiRequest<TodayMenusResponse>('/api/orders/today/');
      setData(res);
      const slot = res[activeMeal];
      const initial: Record<number, number> = {};
      slot.menu?.items.forEach((item) => {
        initial[item.id] = item.quantity || 0;
      });
      setQuantities(initial);
      setNotes(slot.order?.notes ?? '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load menu');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    if (!data) return;
    const slot = data[activeMeal];
    const initial: Record<number, number> = {};
    slot.menu?.items.forEach((item) => {
      initial[item.id] = item.quantity || 0;
    });
    setQuantities(initial);
    setNotes(slot.order?.notes ?? '');
    setError('');
    setMessage('');
  }, [activeMeal, data]);

  function adjustQty(id: number, delta: number, max: number) {
    setQuantities((prev) => ({
      ...prev,
      [id]: Math.max(0, Math.min(max, (prev[id] ?? 0) + delta)),
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const slot = data?.[activeMeal];
    if (!slot?.menu) return;

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
        body: JSON.stringify({ meal_type: activeMeal, items, notes }),
      });
      setMessage(`${MEAL_LABELS[activeMeal]} order placed!`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save order');
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingState label="Loading menus…" />;

  const slot = data?.[activeMeal];
  const menu = slot?.menu;
  const orderingForDate = menu?.date
    ? new Date(menu.date).toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long',
      })
    : new Date(Date.now() + 86400000).toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long',
      });
  const orderingOpen = menu?.is_ordering_open ?? false;
  const userHasOrdered = menu?.user_has_ordered ?? Boolean(slot?.order);
  const totalSelected = Object.values(quantities).reduce((a, b) => a + b, 0);

  function mealTabStatus(meal: MealType) {
    const mealSlot = data?.[meal];
    if (!mealSlot?.menu) return null;
    if (mealSlot.menu.user_has_ordered || mealSlot.order) return 'ordered';
    return mealSlot.menu.is_ordering_open ? 'open' : 'closed';
  }

  return (
    <div className="today-page">
      <PageHeader
        eyebrow="Order"
        title="Order for Tomorrow"
        subtitle={orderingForDate}
        icon="🍽️"
      />

      <div className="meal-tabs">
        {MEALS.map((meal) => {
          const tabStatus = mealTabStatus(meal);
          return (
            <button
              key={meal}
              type="button"
              className={`meal-tab ${activeMeal === meal ? 'active' : ''}`}
              onClick={() => setActiveMeal(meal)}
            >
              <span className="meal-tab-label">{MEAL_LABELS[meal]}</span>
              <span className="meal-tab-deadline">
                {data?.[meal]?.menu?.expires_at_display
                  ? `Before ${data[meal].menu!.expires_at_display}`
                  : `Before ${ORDER_DEADLINE} on menu day`}
              </span>
              {tabStatus && (
                <span className={`meal-tab-status ${tabStatus}`}>
                  {tabStatus === 'open' ? 'Open' : tabStatus === 'ordered' ? 'Ordered' : 'Closed'}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {!menu ? (
        <div className="card card-elevated">
          <EmptyState
            icon="🥘"
            title={`No ${MEAL_LABELS[activeMeal].toLowerCase()} menu`}
            message={`${MEAL_LABELS[activeMeal]} for ${orderingForDate} hasn't been published yet. Admin must publish it for that date.`}
          />
        </div>
      ) : (
        <div className="card card-elevated">
          <div className="meal-deadline-banner">
            <span className="deadline-icon">⏰</span>
            <div>
              <strong>{menu.ordering_deadline_message}</strong>
              <p className="muted">
                {orderingOpen
                  ? (menu.expires_at_display
                    ? `${MEAL_LABELS[activeMeal]} orders close before ${menu.expires_at_display}`
                    : `${MEAL_LABELS[activeMeal]} orders close before ${ORDER_DEADLINE} on the menu date`)
                  : menu.orders_closed_reason}
              </p>
            </div>
            <span className={`status-pill ${orderingOpen ? 'open' : userHasOrdered ? 'ordered' : 'closed'}`}>
              {orderingOpen ? '● Open' : userHasOrdered ? '● Ordered' : '● Closed'}
            </span>
          </div>

          {error && <div className="alert error">{error}</div>}
          {message && <div className="alert success">{message}</div>}

          {userHasOrdered && slot?.order ? (
            <div className="order-placed-summary">
              <p className="alert success">
                Your {MEAL_LABELS[activeMeal].toLowerCase()} order is confirmed. You can order again when the next menu is published.
              </p>
              <ul className="order-items">
                {slot.order.order_items.map((item) => (
                  <li key={item.id}>
                    <span>{item.item_name}</span>
                    <span className="qty-tag">×{item.quantity}</span>
                  </li>
                ))}
              </ul>
              {slot.order.notes && (
                <p className="order-notes"><span>💬</span> {slot.order.notes}</p>
              )}
            </div>
          ) : (
          <form onSubmit={handleSubmit}>
            <div className="menu-grid">
              {menu.items.map((item) => {
                const qty = quantities[item.id] ?? 0;
                return (
                  <article key={item.id} className={`menu-item-card ${qty > 0 ? 'selected' : ''}`}>
                    <div className="menu-item-icon" aria-hidden>{categoryEmoji(item.category)}</div>
                    <div className="menu-item-body">
                      <div className="menu-item-top">
                        <h3>{item.name}</h3>
                        <span className={`badge badge-${item.category}`}>{item.category}</span>
                      </div>
                      <p className="muted">Max {item.max_quantity_per_user} per person</p>
                      <div className="qty-control">
                        <button type="button" className="qty-btn" disabled={!orderingOpen || qty === 0}
                          onClick={() => adjustQty(item.id, -1, item.max_quantity_per_user)}>−</button>
                        <span className="qty-value">{qty}</span>
                        <button type="button" className="qty-btn"
                          disabled={!orderingOpen || qty >= item.max_quantity_per_user}
                          onClick={() => adjustQty(item.id, 1, item.max_quantity_per_user)}>+</button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>

            <div className="order-footer">
              <label className="field">
                <span>Notes <span className="muted">(optional)</span></span>
                <textarea value={notes} disabled={!orderingOpen} onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any allergies or preferences?" rows={2} />
              </label>
              <div className="order-submit-row">
                <div className="order-summary">
                  <span className="muted">Items selected</span>
                  <strong>{totalSelected}</strong>
                </div>
                <button type="submit" className="btn-primary btn-lg" disabled={!orderingOpen || saving}>
                  {saving ? 'Saving…' : `Place ${MEAL_LABELS[activeMeal].toLowerCase()} order →`}
                </button>
              </div>
            </div>
          </form>
          )}
        </div>
      )}
    </div>
  );
}
