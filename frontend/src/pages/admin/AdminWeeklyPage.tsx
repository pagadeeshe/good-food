import { FormEvent, useEffect, useState } from 'react';
import { apiRequest } from '../../api/client';
import type { MealType, WeeklyTemplateDay } from '../../api/types';
import { MEAL_LABELS, ORDER_DEADLINE } from '../../api/types';
import { LoadingState, PageHeader } from '../../components/PageHeader';

const MEALS: MealType[] = ['lunch', 'dinner'];

export function AdminWeeklyPage() {
  const [days, setDays] = useState<WeeklyTemplateDay[]>([]);
  const [activeMeal, setActiveMeal] = useState<MealType>('lunch');
  const [selected, setSelected] = useState<number | null>(null);
  const [newItem, setNewItem] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    const data = await apiRequest<WeeklyTemplateDay[]>('/api/admin/weekly/');
    setDays(data);
    const mealDays = data.filter((d) => d.meal_type === activeMeal);
    if (selected === null && mealDays.length > 0) setSelected(mealDays[0].weekday);
  }

  useEffect(() => {
    load().catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'));
  }, []);

  useEffect(() => {
    const mealDays = days.filter((d) => d.meal_type === activeMeal);
    if (mealDays.length > 0) setSelected(mealDays[0].weekday);
  }, [activeMeal, days]);

  const mealDays = days.filter((d) => d.meal_type === activeMeal);
  const current = mealDays.find((d) => d.weekday === selected);

  async function postAction(body: Record<string, unknown>) {
    if (selected === null) return;
    setError('');
    setMessage('');
    try {
      await apiRequest(`/api/admin/weekly/${selected}/${activeMeal}/`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      setMessage('Updated.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    }
  }

  async function handleAdd(e: FormEvent) {
    e.preventDefault();
    if (!newItem.trim()) return;
    await postAction({ action: 'add_item', name: newItem.trim() });
    setNewItem('');
  }

  return (
    <div className="admin-page">
      <PageHeader
        eyebrow="Admin"
        title="Weekly Templates"
        subtitle="Set standard lunch and dinner menus for each weekday."
        icon="📅"
      />

      <div className="meal-tabs">
        {MEALS.map((meal) => (
          <button key={meal} type="button"
            className={`meal-tab ${activeMeal === meal ? 'active' : ''}`}
            onClick={() => setActiveMeal(meal)}>
            <span className="meal-tab-label">{MEAL_LABELS[meal]}</span>
            <span className="meal-tab-deadline">Closes {ORDER_DEADLINE} on menu day</span>
          </button>
        ))}
      </div>

      <div className="card card-elevated">
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        {!days.length ? (
          <LoadingState label="Loading templates…" />
        ) : (
          <>
            <div className="weekday-tabs">
              {mealDays.map((day) => (
                <button key={day.weekday} type="button"
                  className={selected === day.weekday ? 'tab active' : 'tab'}
                  onClick={() => setSelected(day.weekday)}>
                  {day.day_name.slice(0, 3)}
                </button>
              ))}
            </div>

            {current?.template && (
              <>
                <p className="muted">{current.template.description || 'No description yet.'}</p>
                <ul className="admin-item-list">
                  {current.template.template_items.map((item) => (
                    <li key={item.id} className="item-row-between">
                      <span>{item.name} <span className={`badge badge-${item.category}`}>{item.category}</span></span>
                      <button type="button" className="btn-danger"
                        onClick={() => postAction({ action: 'delete_item', item_id: item.id })}>Remove</button>
                    </li>
                  ))}
                </ul>
                <form onSubmit={handleAdd} className="inline-form">
                  <input value={newItem} onChange={(e) => setNewItem(e.target.value)} placeholder="Add new item…" />
                  <button type="submit" className="btn-primary">Add item</button>
                </form>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
