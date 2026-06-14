export interface User {
  id: number;
  employee_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_portal_admin: boolean;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface MenuItemRow {
  id: number;
  name: string;
  category: string;
  max_quantity_per_user: number;
  quantity: number;
}

export interface TodayMenuResponse {
  menu: {
    id: number;
    date: string;
    is_ordering_open: boolean;
    orders_closed_reason: string | null;
    items: MenuItemRow[];
  } | null;
  order: Order | null;
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
  status: string;
  total_items: number;
  notes: string;
  order_items: OrderItem[];
}

export interface OrderTotals {
  date: string;
  total_users: number;
  total_orders: number;
  total_items: number;
  items: { item_name: string; item_category: string; total_quantity: number }[];
}

export interface AdminDashboard {
  today: string;
  today_menu: { id: number; date: string; status: string } | null;
  today_items: { name: string; category: string }[];
  today_source: string;
  order_totals: OrderTotals;
  weekday_count: number;
}

export interface WeeklyTemplateDay {
  weekday: number;
  day_name: string;
  template: {
    id: number;
    name: string;
    description: string;
    template_items: { id: number; name: string; category: string; sort_order: number }[];
  } | null;
  item_count: number;
}

export interface UpcomingDay {
  date: string;
  day_name: string;
  daily_menu: { id: number; date: string; status: string } | null;
  item_count: number;
  source: string;
}
