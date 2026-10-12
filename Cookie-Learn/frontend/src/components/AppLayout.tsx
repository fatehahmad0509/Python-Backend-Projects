// Main application layout with sidebar navigation, top stats bar, and theme toggle
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { assetUrl } from "@/lib/api";
import {
  Home, Trophy, Award, User, BarChart3, MessageCircle, Sparkles,
  ShoppingBag, Shield, LogOut, Sun, Moon, Heart, Flame, Zap, Gem, Menu, Languages
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { User as UserT } from "@/types";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Learn", icon: Home, testid: "nav-dashboard" },
  { to: "/languages", label: "Languages", icon: Languages, testid: "nav-languages" },
  { to: "/chat", label: "AI Teacher", icon: Sparkles, testid: "nav-chat" },
  { to: "/practice", label: "Speaking", icon: MessageCircle, testid: "nav-practice" },
  { to: "/leaderboard", label: "League", icon: Trophy, testid: "nav-leaderboard" },
  { to: "/achievements", label: "Achievements", icon: Award, testid: "nav-achievements" },
  { to: "/stats", label: "Stats", icon: BarChart3, testid: "nav-stats" },
  { to: "/shop", label: "Shop", icon: ShoppingBag, testid: "nav-shop" },
  { to: "/profile", label: "Profile", icon: User, testid: "nav-profile" },
];

// Top bar displaying streak, XP, hearts, and gems
function TopStats({ user }: { user: UserT }) {
  return (
    <div className="flex items-center gap-3 sm:gap-4">
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-orange-500/10 text-orange-500" data-testid="stat-streak">
        <Flame className="w-4 h-4 animate-flame" />
        <span className="font-heading font-bold text-sm">{user.streak_days}</span>
      </div>
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent/10 text-accent" data-testid="stat-xp">
        <Zap className="w-4 h-4 fill-accent" />
        <span className="font-heading font-bold text-sm">{user.xp_total}</span>
      </div>
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-destructive/10 text-destructive" data-testid="stat-hearts">
        <Heart className="w-4 h-4 fill-destructive" />
        <span className="font-heading font-bold text-sm">{user.hearts}</span>
      </div>
      <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary/10 text-secondary" data-testid="stat-gems">
        <Gem className="w-4 h-4 fill-secondary" />
        <span className="font-heading font-bold text-sm">{user.gems}</span>
      </div>
    </div>
  );
}

export default function AppLayout() {
  const { user, setUser, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);

  // Refresh user state (hearts, XP, etc.) on mount
  useEffect(() => {
    let mounted = true;
    api.get<UserT>("/progress/state").then(({ data }) => { if (mounted) setUser(data); }).catch(() => {});
    return () => { mounted = false; };
  }, []);

  if (!user) return null;

  // Sidebar component with nav links and logout button
  const Sidebar = ({ onNav }: { onNav?: () => void }) => (
    <nav className="flex flex-col gap-1 p-3">
      {NAV_ITEMS.filter(i => i.to !== "/admin" || user.is_admin).map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          data-testid={item.testid}
          onClick={onNav}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-2xl font-heading font-bold uppercase tracking-wide text-sm transition-colors ${
              isActive ? "bg-primary/15 text-primary" : "hover:bg-muted text-muted-foreground hover:text-foreground"
            }`
          }
        >
          <item.icon className="w-5 h-5" />
          {item.label}
        </NavLink>
      ))}
      {user.is_admin && (
        <NavLink
          to="/admin"
          data-testid="nav-admin"
          onClick={onNav}
          className={({ isActive }) =>
            `flex items-center gap-3 px-4 py-3 rounded-2xl font-heading font-bold uppercase tracking-wide text-sm transition-colors ${
              isActive ? "bg-accent/15 text-accent" : "hover:bg-muted text-muted-foreground hover:text-foreground"
            }`
          }
        >
          <Shield className="w-5 h-5" />
          Admin
        </NavLink>
      )}
      <button
        data-testid="btn-logout"
        onClick={() => { logout(); nav("/"); }}
        className="mt-3 flex items-center gap-3 px-4 py-3 rounded-2xl font-heading font-bold uppercase tracking-wide text-sm text-destructive hover:bg-destructive/10 transition-colors"
      >
        <LogOut className="w-5 h-5" /> Logout
      </button>
    </nav>
  );

  return (
    <div className="min-h-screen">
      {/* Fixed header with menu toggle, brand, stats, and theme/avatar */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-background/80 border-b border-border">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 h-16">
          <div className="flex items-center gap-3">
            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <button className="md:hidden p-2 -ml-2" data-testid="btn-menu-open"><Menu className="w-6 h-6" /></button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 p-0">
                <div className="p-5 border-b border-border">
                  <div className="font-heading font-black text-2xl">🍪 CookieLearn</div>
                </div>
                <Sidebar onNav={() => setOpen(false)} />
              </SheetContent>
            </Sheet>
            <Link to="/dashboard" className="flex items-center gap-2 font-heading font-black text-xl sm:text-2xl" data-testid="brand-link">
              <span className="text-2xl">🍪</span>
              <span className="hidden sm:inline">CookieLearn</span>
            </Link>
          </div>
          <TopStats user={user} />
          <div className="flex items-center gap-2">
            <button onClick={toggle} className="p-2 rounded-xl hover:bg-muted transition-colors" data-testid="btn-theme-toggle" aria-label="Toggle theme">
              {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
            <Link to="/profile" data-testid="link-profile-avatar" className="w-9 h-9 rounded-full bg-primary/20 border-2 border-primary flex items-center justify-center overflow-hidden">
              {user.avatar_url ? (
                <img src={assetUrl(user.avatar_url)} alt="avatar" className="w-full h-full object-cover" />
              ) : (
                <span className="font-heading font-black text-primary">{user.username.slice(0, 1).toUpperCase()}</span>
              )}
            </Link>
          </div>
        </div>
      </header>

      {/* Main layout: sidebar + content area */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6 px-4 sm:px-6 py-6">
        <aside className="hidden md:block sticky top-20 self-start card-surface">
          <Sidebar />
        </aside>
        <main className="min-h-[calc(100vh-6rem)]">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
