// Root app component with route definitions
import { Routes, Route, Navigate } from "react-router-dom";
import "@/App.css";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import LanguageSelect from "@/pages/LanguageSelect";
import LessonPlayer from "@/pages/LessonPlayer";
import TestSession from "@/pages/TestSession";
import AIChat from "@/pages/AIChat";
import Practice from "@/pages/Practice";
import Profile from "@/pages/Profile";
import Stats from "@/pages/Stats";
import Leaderboard from "@/pages/Leaderboard";
import Achievements from "@/pages/Achievements";
import Shop from "@/pages/Shop";
import Admin from "@/pages/Admin";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppLayout from "@/components/AppLayout";
import { useAuth } from "@/contexts/AuthContext";

function AppInner() {
  const { user } = useAuth();
  return (
    <Routes>
      {/* Public routes - redirect to dashboard if already logged in */}
      <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes wrapped in AppLayout (sidebar nav + header) */}
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/languages" element={<LanguageSelect />} />
        <Route path="/test" element={<TestSession />} />
        <Route path="/lesson/:lessonId" element={<LessonPlayer />} />
        <Route path="/ai-lesson" element={<LessonPlayer />} />
        <Route path="/chat" element={<AIChat />} />
        <Route path="/practice" element={<Practice />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/stats" element={<Stats />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/achievements" element={<Achievements />} />
        <Route path="/shop" element={<Shop />} />
        <Route path="/admin" element={<Admin />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <div className="App font-body">
      <AppInner />
    </div>
  );
}
