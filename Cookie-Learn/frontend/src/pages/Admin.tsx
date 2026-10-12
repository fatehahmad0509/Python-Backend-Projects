// Admin panel - manage languages and users (admin-only access)
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Language, User } from "@/types";
import { Plus, Trash2 } from "lucide-react";
import { Navigate } from "react-router-dom";

export default function Admin() {
  const { user } = useAuth();
  const [langs, setLangs] = useState<Language[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [newLang, setNewLang] = useState({ code: "", name: "", native_name: "", flag_emoji: "", order_index: 10 });

  useEffect(() => {
    if (!user?.is_admin) return;
    api.get<Language[]>("/languages").then(({ data }) => setLangs(data));
    api.get<User[]>("/admin/users").then(({ data }) => setUsers(data));
  }, [user]);

  if (!user) return null;
  if (!user.is_admin) return <Navigate to="/dashboard" replace />;

  async function addLang() {
    try {
      await api.post("/admin/languages", newLang);
      const { data } = await api.get<Language[]>("/languages");
      setLangs(data);
      setNewLang({ code: "", name: "", native_name: "", flag_emoji: "", order_index: 10 });
      toast.success("Language added");
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Error"); }
  }
  async function delLang(id: string) {
    if (!confirm("Delete? All related curriculum will be deleted.")) return;
    await api.delete(`/admin/languages/${id}`);
    setLangs((l) => l.filter((x) => x.id !== id));
  }
  async function toggleAdmin(u: User) {
    const { data } = await api.patch<User>(`/admin/users/${u.id}`, { is_admin: !u.is_admin });
    setUsers((prev) => prev.map((x) => (x.id === u.id ? data : x)));
  }

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-3xl font-black" data-testid="admin-title">Admin Panel</h1>
      <Tabs defaultValue="languages">
        <TabsList data-testid="admin-tabs">
          <TabsTrigger value="languages" data-testid="tab-languages">Languages</TabsTrigger>
          <TabsTrigger value="users" data-testid="tab-users">Users</TabsTrigger>
        </TabsList>

        {/* Languages tab */}
        <TabsContent value="languages" className="space-y-4">
          <div className="card-surface p-6 space-y-4" data-testid="admin-new-lang">
            <h2 className="font-heading text-xl font-black">New Language</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <input placeholder="Code (en)" data-testid="new-lang-code" value={newLang.code} onChange={(e) => setNewLang({ ...newLang, code: e.target.value })} className="px-3 py-2 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
              <input placeholder="Name" data-testid="new-lang-name" value={newLang.name} onChange={(e) => setNewLang({ ...newLang, name: e.target.value })} className="px-3 py-2 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
              <input placeholder="Native Name" data-testid="new-lang-native" value={newLang.native_name} onChange={(e) => setNewLang({ ...newLang, native_name: e.target.value })} className="px-3 py-2 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
              <input placeholder="🇺🇸" data-testid="new-lang-flag" value={newLang.flag_emoji} onChange={(e) => setNewLang({ ...newLang, flag_emoji: e.target.value })} className="px-3 py-2 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
              <button onClick={addLang} className="btn-primary" data-testid="new-lang-submit"><Plus className="w-4 h-4" /> Add</button>
            </div>
          </div>
          <div className="card-surface divide-y divide-border" data-testid="admin-langs-list">
            {langs.map((l) => (
              <div key={l.id} className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <div className="text-2xl">{l.flag_emoji}</div>
                  <div>
                    <div className="font-heading font-bold">{l.native_name} <span className="text-muted-foreground text-xs">({l.code})</span></div>
                    <div className="text-xs text-muted-foreground">{l.name}</div>
                  </div>
                </div>
                <button onClick={() => delLang(l.id)} className="p-2 rounded-xl text-destructive hover:bg-destructive/10" data-testid={`del-lang-${l.code}`}><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
          </div>
        </TabsContent>

        {/* Users tab */}
        <TabsContent value="users" className="space-y-4">
          <div className="card-surface divide-y divide-border" data-testid="admin-users-list">
            {users.map((u) => (
              <div key={u.id} className="flex items-center justify-between p-4">
                <div>
                  <div className="font-heading font-bold">{u.username} {u.is_admin && <span className="text-xs text-accent">(admin)</span>}</div>
                  <div className="text-xs text-muted-foreground">{u.email}</div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-sm text-muted-foreground">{u.xp_total} XP · {u.streak_days} day</div>
                  <button onClick={() => toggleAdmin(u)} className="btn-outline text-xs" data-testid={`toggle-admin-${u.id}`}>
                    {u.is_admin ? "Remove Admin" : "Make Admin"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
