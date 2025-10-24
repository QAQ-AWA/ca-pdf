import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../../contexts/AuthContext";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type ProtectedRouteProps = {
  children: React.ReactElement;
  requiredRoles?: string[];
  redirectTo?: string;
  unauthorizedTo?: string;
};

export const ProtectedRoute = ({
  children,
  requiredRoles,
  redirectTo = "/login",
  unauthorizedTo = "/unauthorized",
}: ProtectedRouteProps) => {
  const location = useLocation();
  const { isAuthenticated, isLoading, hasRole } = useAuth();
  const theme = useTheme();

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: theme.colors.background,
        }}
      >
        <Spinner size={48} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={redirectTo} replace state={{ from: location }} />;
  }

  if (requiredRoles && requiredRoles.length > 0 && !hasRole(...requiredRoles)) {
    return <Navigate to={unauthorizedTo} replace state={{ from: location }} />;
  }

  return children;
};
