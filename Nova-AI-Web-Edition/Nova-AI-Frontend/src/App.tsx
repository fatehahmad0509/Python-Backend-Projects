import { useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { useAppStore } from "./store/useAppStore";
import { registerSessionExpiredHandler, registerAccountSuspendedHandler, api } from "./lib/api";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ChatPage from "./pages/ChatPage";
import SettingsPage from "./pages/SettingsPage";
import SuspendedAccountPage from "./pages/SuspendedAccountPage";

export default function App() {
  const init = useAppStore((s) => s.init);
  const theme = useAppStore((s) => s.theme);
  const accountSuspended = useAppStore((s) => s.accountSuspended);
  const setAccountSuspended = useAppStore((s) => s.setAccountSuspended);
  const navigate = useNavigate();

  useEffect(() => {
    // App Initializer: liveness check (section 7, /health) + auth bootstrap.
    api.get("/health").catch(() => {
      // Non-fatal — backend may be cold-starting on Render's free tier.
    });
    init();
  }, [init]);

  useEffect(() => {
    registerSessionExpiredHandler(() => {
      navigate("/login", { replace: true });
    });
    registerAccountSuspendedHandler(() => {
      setAccountSuspended(true);
    });
  }, [navigate, setAccountSuspended]);

  // Only "light" and "dark" exist now — dark is the default, .light overrides
  // the CSS variables defined in index.css.
  useEffect(() => {
    document.documentElement.classList.toggle("light", theme === "light");
  }, [theme]);

  // A blocked/suspended account always sees this screen, regardless of route
  // or auth state — the account is never force-logged-out.
  if (accountSuspended) {
    return <SuspendedAccountPage />;
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat/:conversationId"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
