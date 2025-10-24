import { useEffect } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

export const LogoutPage = () => {
  const { logout } = useAuth();

  useEffect(() => {
    logout().catch(() => undefined);
  }, [logout]);

  return <Navigate to="/login" replace />;
};
