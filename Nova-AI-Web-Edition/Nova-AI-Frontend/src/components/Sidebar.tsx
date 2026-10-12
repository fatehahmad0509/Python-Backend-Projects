import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  Menu,
  Plus,
  Search,
  Trash2,
  Settings as SettingsIcon,
  LogOut,
  User,
  X,
  MessageSquare,
} from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import ConfirmModal from "./ConfirmModal";

export default function Sidebar() {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const conversations = useAppStore((s) => s.conversations);
  const fetchConversations = useAppStore((s) => s.fetchConversations);
  const conversationsInitialized = useAppStore((s) => s.conversationsInitialized);
  const deleteConversation = useAppStore((s) => s.deleteConversation);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);
  const user = useAppStore((s) => s.user);
  const logout = useAppStore((s) => s.logout);

  const [search, setSearch] = useState("");
  const [deleteTarget, setDeleteTarget] = useState<{ id: string; title: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [logoutConfirmOpen, setLogoutConfirmOpen] = useState(false);

  useEffect(() => {
    // init()/login() already fetch this in parallel with the auth check —
    // skip the redundant second round trip when that data is already here.
    if (!conversationsInitialized) {
      fetchConversations();
    }
  }, [conversationsInitialized, fetchConversations]);

  const filtered = useMemo(() => {
    if (!search.trim()) return conversations;
    const q = search.toLowerCase();
    return conversations.filter((c) => c.title.toLowerCase().includes(q));
  }, [conversations, search]);

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteConversation(deleteTarget.id);
      if (conversationId === deleteTarget.id) {
        navigate("/");
      }
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <>
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed z-40 flex h-full w-72 shrink-0 flex-col border-r border-border bg-bg-sidebar transition-transform duration-200 lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <img src="/logo.jpeg" alt="Nova AI" className="h-7 w-7 rounded-lg object-cover" />
            <span className="font-semibold text-text-heading">Nova AI</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
            className="rounded-lg p-1.5 text-text-secondary hover:bg-hover lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-3 px-3 pt-3">
          <button
            onClick={() => {
              navigate("/");
              setSidebarOpen(false);
            }}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-accent/40 bg-accent/10 py-2.5 text-sm font-medium text-accent-light transition hover:bg-accent/20"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>

          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search conversations..."
              aria-label="Search conversations"
              className="w-full rounded-xl border border-border bg-bg-card py-2 pl-9 pr-3 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
            />
          </div>
        </div>

        <nav aria-label="Chat history" className="mt-3 flex-1 space-y-1 overflow-y-auto px-3 pb-3">
          {filtered.length === 0 ? (
            <p className="mt-6 text-center text-sm text-text-secondary">
              {search ? "No conversations found." : "No conversations yet. Start now!"}
            </p>
          ) : (
            filtered.map((c) => {
              const isActive = c.id === conversationId;
              return (
                <div
                  key={c.id}
                  className={`group flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
                    isActive ? "bg-hover text-text-heading" : "text-text-body hover:bg-hover"
                  }`}
                >
                  <MessageSquare className="h-4 w-4 shrink-0 text-text-secondary" />
                  <Link
                    to={`/chat/${c.id}`}
                    onClick={() => setSidebarOpen(false)}
                    className="flex-1 truncate"
                    title={c.title}
                  >
                    {c.title || "Untitled chat"}
                  </Link>
                  <button
                    onClick={() => setDeleteTarget({ id: c.id, title: c.title })}
                    aria-label={`Delete ${c.title}`}
                    className="shrink-0 rounded-lg p-1 text-text-secondary opacity-0 transition hover:bg-danger/10 hover:text-danger group-hover:opacity-100 focus-visible:opacity-100"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </nav>

        <div className="border-t border-border p-3">
          <div className="mb-1 flex items-center gap-2 rounded-xl px-2 py-2 text-sm text-text-body">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-user-gradient">
              <User className="h-4 w-4 text-white" />
            </span>
            <span className="truncate">{user?.email}</span>
          </div>
          <Link
            to="/settings"
            onClick={() => setSidebarOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-text-body hover:bg-hover"
          >
            <SettingsIcon className="h-4 w-4" />
            Settings
          </Link>
          <button
            onClick={() => setLogoutConfirmOpen(true)}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-text-body hover:bg-hover"
          >
            <LogOut className="h-4 w-4" />
            Log Out
          </button>
        </div>
      </aside>

      <ConfirmModal
        open={Boolean(deleteTarget)}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Chat"
        description={`"${deleteTarget?.title || "This conversation"}" will be permanently deleted. This action cannot be undone.`}
        confirmLabel="Delete"
        danger
        isLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
      />

      <ConfirmModal
        open={logoutConfirmOpen}
        onOpenChange={setLogoutConfirmOpen}
        title="Log Out"
        description="Are you sure you want to log out of your Nova AI account?"
        confirmLabel="Log Out"
        onConfirm={handleLogout}
      />
    </>
  );
}

export function SidebarToggleButton() {
  const setSidebarOpen = useAppStore((s) => s.setSidebarOpen);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  return (
    <button
      onClick={() => setSidebarOpen(!sidebarOpen)}
      aria-label="Toggle sidebar"
      className="flex h-9 w-9 items-center justify-center rounded-xl text-text-body hover:bg-hover lg:hidden"
    >
      <Menu className="h-5 w-5" />
    </button>
  );
}
