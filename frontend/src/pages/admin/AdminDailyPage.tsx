import { FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiRequest } from '../../api/client';
import type { UpcomingDay } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

export function AdminDailyPage() {
  const [days, setDays] = useState<UpcomingDay[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    apiRequest<UpcomingDay[]>('/api/admin/daily/')
      .then(setDays)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'));
  }, []);

  if (error) return <div className="alert error">{error}</div>;

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Admin"
        title="Daily Menus"
        subtitle="Upcoming menus for the next two weeks."
        icon="🗓️"
      />

      <div className="card card-elevated table-card">
        {!days.length ? (
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
              {days.map((day) => {
                const d = new Date(day.date);
                const path = `/admin/daily/${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
                return (
                  <tr key={day.date}>
                    <td>{d.toLocaleDateString()}</td>
                    <td>{day.day_name}</td>
                    <td><span className="qty-tag">{day.item_count}</span></td>
                    <td>
                      <span className={`status-pill status-${day.daily_menu?.status ?? 'draft'}`}>
                        {day.daily_menu?.status ?? 'draft'}
                      </span>
                    </td>
                    <td>{day.source}</td>
                    <td><Link to={path} className="table-link">Edit →</Link></td>
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
  daily_menu: { id: number; status: string } | null;
  custom_items: { id: number; name: string; category: string }[];
  standard_items: { name: string; category: string }[];
  using_standard: boolean;
}

export function AdminDailyEditPage({ year, month, day }: { year: string; month: string; day: string }) {
  const [detail, setDetail] = useState<DailyDetail | null>(null);
  const [newItem, setNewItem] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const path = `/api/admin/daily/${year}/${month}/${day}/`;

  async function load() {
    const data = await apiRequest<DailyDetail>(path);
    setDetail(data);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'));
  }, [year, month, day]);

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
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Edit menu"
        title={detail.day_name}
        subtitle={dateLabel}
        icon="✏️"
      >
        <span className={`status-pill status-${detail.daily_menu?.status ?? 'draft'}`}>
          {detail.daily_menu?.status ?? 'not created'}
        </span>
      </PageHeader>

      <div className="card card-elevated">
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <div className="actions">
          <button type="button" className="btn-primary" onClick={() => action({ action: 'publish' })}>
            Publish
          </button>
          <button type="button" className="btn-secondary" onClick={() => action({ action: 'unpublish' })}>
            Unpublish
          </button>
          <button type="button" className="btn-secondary" onClick={() => action({ action: 'reset_to_standard' })}>
            Reset to standard
          </button>
        </div>

        <h3 className="section-title">Custom items</h3>
        {detail.custom_items.length === 0 ? (
          <p className="muted">{detail.using_standard ? 'Using standard weekly template.' : 'No custom items.'}</p>
        ) : (
          <ul className="admin-item-list">
            {detail.custom_items.map((item) => (
              <li key={item.id} className="item-row-between">
                <span>{item.name}</span>
                <button
                  type="button"
                  className="btn-danger"
                  onClick={() => action({ action: 'delete_item', item_id: item.id })}
                >
                  Remove
                </button>
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
