import { FormEvent, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import type { MealType, UpcomingDay, UpcomingMenusResponse } from '../../api/types';
import { MEAL_LABELS, ORDER_DEADLINE } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

export function AdminDailyPage() {
  const { mealType } = useParams();
  const activeMeal: MealType = mealType === 'dinner' ? 'dinner' : 'lunch';
  const [days, setDays] = useState<UpcomingDay[]>([]);
  const [orderingForDate, setOrderingForDate] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest<UpcomingMenusResponse>('/api/admin/daily/')
      .then((res) => {
        setDays(res.days);
        setOrderingForDate(res.ordering_for_date);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'));
  }, []);

  if (error) return <div className="alert error">{error}</div>;

  const filtered = days
    .filter((d) => d.meal_type === activeMeal)
    .sort((a, b) => {
      if (a.is_ordering_target) return -1;
      if (b.is_ordering_target) return 1;
      return a.date.localeCompare(b.date);
    });

  const orderingForLabel = orderingForDate
    ? new Date(orderingForDate).toLocaleDateString('en-IN', {
        weekday: 'long', day: 'numeric', month: 'long',
      })
    : '';

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Admin"
        title="Daily Menus"
        subtitle={`Employees are ordering for ${orderingForLabel || 'tomorrow'} — publish that date's menu.`}
        icon="🗓️"
      />

      {orderingForDate && (
        <div className="meal-deadline-banner" style={{ marginBottom: '1rem' }}>
          <span className="deadline-icon">📌</span>
          <div>
            <strong>Active ordering date: {orderingForLabel}</strong>
            <p className="muted">
              Only menus published for this date appear on the order page. Publishing today&apos;s date will not show to employees.
            </p>
          </div>
        </div>
      )}

      <div className="meal-tabs">
        {MEALS.map((meal) => (
          <Link key={meal} to={`/admin/daily/${meal}`}
            className={`meal-tab ${activeMeal === meal ? 'active' : ''}`}>
            <span className="meal-tab-label">{MEAL_LABELS[meal]}</span>
            <span className="meal-tab-deadline">Closes {ORDER_DEADLINE}</span>
          </Link>
        ))}
      </div>

      <div className="card card-elevated table-card">
        {!filtered.length ? (
          <LoadingState label="Loading menus…" />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Day</th>
                <th>Items</th>
                <th>Status</th>
                <th>Source</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((day) => {
                const d = new Date(day.date + 'T12:00:00');
                const path = `/admin/daily/${activeMeal}/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
                return (
                  <tr key={`${day.date}-${day.meal_type}`} className={day.is_ordering_target ? 'row-highlight' : ''}>
                    <td>{d.toLocaleDateString()}</td>
                    <td>
                      {day.day_name}
                      {day.is_ordering_target && (
                        <span className="status-pill open" style={{ marginLeft: '0.5rem' }}>Ordering now</span>
                      )}
                    </td>
                    <td><span className="qty-tag">{day.item_count}</span></td>
                    <td>
                      <span className={`status-pill status-${day.daily_menu?.status ?? 'draft'}`}>
                        {day.daily_menu?.status ?? 'draft'}
                      </span>
                    </td>
                    <td>{day.source}</td>
                    <td><Link to={path} className="table-link">{day.is_ordering_target ? 'Edit & publish →' : 'Edit →'}</Link></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

interface DailyDetail {
  menu_date: string;
  day_name: string;
  meal_type: MealType;
  daily_menu: {
    id: number;
    status: string;
    expires_at_display: string | null;
    ordering_deadline_message: string;
  } | null;
  custom_items: { id: number; name: string; category: string }[];
  standard_items: { name: string; category: string }[];
  using_standard: boolean;
}

export function AdminDailyEditPage({
  mealType, year, month, day,
}: { mealType: string; year: string; month: string; day: string }) {
  const meal: MealType = mealType === 'dinner' ? 'dinner' : 'lunch';
  const [detail, setDetail] = useState<DailyDetail | null>(null);
  const [newItem, setNewItem] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const path = `/api/admin/daily/${year}/${month}/${day}/${meal}/`;

  async function load() {
    const data = await apiRequest<DailyDetail>(path);
    setDetail(data);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'));
  }, [year, month, day, meal]);

  async function action(body: Record<string, unknown>) {
    setError('');
    setMessage('');
    try {
      await apiRequest(path, { method: 'POST', body: JSON.stringify(body) });
      setMessage('Updated.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Action failed');
    }
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!newItem.trim()) return;
    await action({ action: 'add_item', name: newItem.trim() });
    setNewItem('');
  }

  if (error && !detail) return <div className="alert error">{error}</div>;
  if (!detail) return <LoadingState label="Loading menu…" />;

  const dateLabel = new Date(detail.menu_date).toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long',
  });

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow={`${MEAL_LABELS[meal]} menu`}
        title={detail.day_name}
        subtitle={dateLabel}
        icon="✏️"
      >
        <span className={`status-pill status-${detail.daily_menu?.status ?? 'draft'}`}>
          {detail.daily_menu?.status ?? 'not created'}
        </span>
      </PageHeader>

      <div className="meal-deadline-banner">
        <span className="deadline-icon">⏰</span>
        <div>
          <strong>
            {detail.daily_menu?.ordering_deadline_message
              ?? `Orders close at ${ORDER_DEADLINE} on the menu date`}
          </strong>
          <p className="muted">
            Employees order today for this menu date. On Sunday they see Monday&apos;s menu; orders close Monday at 10:00 AM.
          </p>
        </div>
      </div>

      <div className="card card-elevated">
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <div className="actions">
          <button type="button" className="btn-primary" onClick={() => action({ action: 'publish' })}>Publish</button>
          <button type="button" className="btn-secondary" onClick={() => action({ action: 'unpublish' })}>Unpublish</button>
          <button type="button" className="btn-secondary" onClick={() => action({ action: 'reset_to_standard' })}>Reset to standard</button>
        </div>

        <h3 className="section-title">Custom items</h3>
        {detail.custom_items.length === 0 ? (
          <p className="muted">{detail.using_standard ? 'Using standard weekly template.' : 'No custom items.'}</p>
        ) : (
          <ul className="admin-item-list">
            {detail.custom_items.map((item) => (
              <li key={item.id} className="item-row-between">
                <span>{item.name}</span>
                <button type="button" className="btn-danger"
                  onClick={() => action({ action: 'delete_item', item_id: item.id })}>Remove</button>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={handleAdd} className="inline-form">
          <input value={newItem} onChange={(e) => setNewItem(e.target.value)} placeholder="Add item…" />
          <button type="submit" className="btn-primary">Add</button>
        </form>

        {detail.standard_items.length > 0 && (
          <>
            <h3 className="section-title">Standard template</h3>
            <ul className="menu-preview-list">
              {detail.standard_items.map((item) => (
                <li key={item.name}>
                  <span>{item.name}</span>
                  <span className={`badge badge-${item.category}`}>{item.category}</span>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
