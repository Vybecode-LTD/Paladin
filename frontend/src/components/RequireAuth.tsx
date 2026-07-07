import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export default function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ padding: 40, color: "#a4abb8" }}>Loading…</div>;
  if (!user) return <Navigate to="/admin/login" replace />;
  return <>{children}</>;
}
