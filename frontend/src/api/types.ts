export type MealType = 'lunch' | 'dinner';

export const MEAL_LABELS: Record<MealType, string> = {
  lunch: 'Lunch',
  dinner: 'Dinner',
};

export const ORDER_DEADLINE = '10:00 AM';

export const MEAL_DEADLINES: Record<MealType, string> = {
  lunch: ORDER_DEADLINE,
  dinner: ORDER_DEADLINE,
};

export interface User {
  id: number;
  student_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_portal_admin: boolean;
}

export interface AuthResponse {
  access?: string;
  refresh?: string;
  user: User;
}

export interface MenuItemRow {
  id: number;
  name: string;
  category: string;
  max_quantity_per_user: number;
  quantity: number;
}

export interface MenuPayload {
  id: number;
  date: string;
  ordering_for_date?: string;
  meal_type: MealType;
  meal_type_display: string;
  published_at?: string | null;
  expires_at?: string | null;
  expires_at_display?: string | null;
  order_deadline_display?: string;
  ordering_deadline_message: string;
  is_ordering_open: boolean;
  user_has_ordered?: boolean;
  orders_closed_reason: string | null;
  status: string;
  items: MenuItemRow[];
}

export interface MealOrderSlot {
  menu: MenuPayload | null;
  order: Order | null;
}

export interface TodayMenusResponse {
  lunch: MealOrderSlot;
  dinner: MealOrderSlot;
}

export interface OrderItem {
  id: number;
  item_name: string;
  item_category: string;
  quantity: number;
}

export interface Order {
  id: number;
  order_date: string;
  meal_type: MealType;
  meal_type_display: string;
  status: string;
  total_items: number;
  notes: string;
  order_items: OrderItem[];
}

export interface AdminOrder extends Order {
  user_name: string;
  student_id: string;
  user_email: string;
  menu_date: string;
}

export interface AdminOrdersResponse {
  menu_date: string | null;
  show_all: boolean;
  count: number;
  orders: AdminOrder[];
}

export interface OrderTotals {
  date?: string;
  meal_type?: MealType | null;
  total_students: number;
  total_orders: number;
  total_items: number;
  items: { item_name: string; item_category: string; total_quantity: number }[];
}

export interface TodayReportsResponse {
  date: string;
  lunch: OrderTotals;
  dinner: OrderTotals;
}

export interface AdminMealSlot {
  daily_menu: { id: number; date: string; status: string; meal_type: MealType } | null;
  items: { name: string; category: string }[];
  source: string;
  order_totals: OrderTotals;
}

export interface AdminDashboard {
  today: string;
  ordering_for_date: string;
  menus: Record<MealType, AdminMealSlot>;
  weekday_count: number;
}

export interface WeeklyTemplateDay {
  weekday: number;
  day_name: string;
  meal_type: MealType;
  template: {
    id: number;
    name: string;
    description: string;
    meal_type: MealType;
    template_items: { id: number; name: string; category: string; sort_order: number }[];
  } | null;
  item_count: number;
  is_locked?: boolean;
}

export interface UpcomingDay {
  date: string;
  day_name: string;
  meal_type: MealType;
  daily_menu: { id: number; date: string; status: string; meal_type: MealType } | null;
  item_count: number;
  source: string;
  is_ordering_target?: boolean;
}

export interface UpcomingMenusResponse {
  ordering_for_date: string;
  days: UpcomingDay[];
}
