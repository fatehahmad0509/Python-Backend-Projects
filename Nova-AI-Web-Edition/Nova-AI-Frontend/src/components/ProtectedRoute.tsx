import { Navigate, useLocation } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = useAppStore((s) => s.user);
  const isAuthReady = useAppStore((s) => s.isAuthReady);
  const location = useLocation();

  if (!isAuthReady) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-bg-main">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
