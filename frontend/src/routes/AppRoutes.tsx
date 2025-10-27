import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../components/router/ProtectedRoute";
import { DashboardShell } from "../components/shell/DashboardShell";
import { OverviewPage } from "../pages/dashboard/OverviewPage";
import { SigningWorkspacePage } from "../pages/dashboard/SigningWorkspacePage";
import { SettingsPage } from "../pages/dashboard/SettingsPage";
import { AdminPage } from "../pages/dashboard/AdminPage";
import { LoginPage } from "../pages/LoginPage";
import { LogoutPage } from "../pages/LogoutPage";
import { UnauthorizedPage } from "../pages/UnauthorizedPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/logout" element={<LogoutPage />} />
    <Route path="/unauthorized" element={<UnauthorizedPage />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <DashboardShell />
        </ProtectedRoute>
      }
    >
      <Route index element={<OverviewPage />} />
      <Route path="signing" element={<SigningWorkspacePage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route
        path="admin"
        element={
          <ProtectedRoute requiredRoles={["admin"]}>
            <AdminPage />
          </ProtectedRoute>
        }
      />
    </Route>
    <Route path="*" element={<NotFoundPage />} />
  </Routes>
);
