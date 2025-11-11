import { Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "../components/router/ProtectedRoute";
import { DashboardShell } from "../components/shell/DashboardShell";
import { OverviewPage } from "../pages/dashboard/OverviewPage";
import { SigningWorkspacePage } from "../pages/dashboard/SigningWorkspacePage";
import { SettingsPage } from "../pages/dashboard/SettingsPage";
import { AdminPage } from "../pages/dashboard/AdminPage";
import { VerificationPage } from "../pages/dashboard/VerificationPage";
import { AuditLogPage } from "../pages/dashboard/AuditLogPage";
import { UsersManagementPage } from "../pages/dashboard/UsersManagementPage";
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
      <Route path="verification" element={<VerificationPage />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route
        path="audit-logs"
        element={
          <ProtectedRoute requiredRoles={["admin"]}>
            <AuditLogPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="admin"
        element={
          <ProtectedRoute requiredRoles={["admin"]}>
            <AdminPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="users"
        element={
          <ProtectedRoute requiredRoles={["admin"]}>
            <UsersManagementPage />
          </ProtectedRoute>
        }
      />
    </Route>
    <Route path="*" element={<NotFoundPage />} />
  </Routes>
);
