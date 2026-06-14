import { Navigate, Route, Routes, useParams } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/Layout';
import { AdminRoute, ProtectedRoute } from './components/ProtectedRoute';
import { LoginPage } from './pages/LoginPage';
import { TodayMenuPage } from './pages/TodayMenuPage';
import { MyOrdersPage } from './pages/MyOrdersPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminWeeklyPage } from './pages/admin/AdminWeeklyPage';
import { AdminDailyPage, AdminDailyEditPage } from './pages/admin/AdminDailyPage';
import { AdminOrdersReportPage } from './pages/admin/AdminOrdersReportPage';
import { AdminAllOrdersPage } from './pages/admin/AdminAllOrdersPage';

function DailyEditRoute() {
  const { mealType = 'lunch', year = '', month = '', day = '' } = useParams();
  return <AdminDailyEditPage mealType={mealType} year={year} month={month} day={day} />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/today" replace />} />
            <Route path="today" element={<TodayMenuPage />} />
            <Route path="orders" element={<MyOrdersPage />} />
            <Route element={<AdminRoute />}>
              <Route path="admin" element={<AdminDashboardPage />} />
              <Route path="admin/weekly" element={<AdminWeeklyPage />} />
              <Route path="admin/daily" element={<Navigate to="/admin/daily/lunch" replace />} />
              <Route path="admin/daily/:mealType" element={<AdminDailyPage />} />
              <Route path="admin/daily/:mealType/:year/:month/:day" element={<DailyEditRoute />} />
              <Route path="admin/reports" element={<AdminOrdersReportPage />} />
              <Route path="admin/orders" element={<AdminAllOrdersPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/today" replace />} />
      </Routes>
    </AuthProvider>
  );
}
