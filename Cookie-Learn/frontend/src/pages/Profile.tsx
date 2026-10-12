// Profile page - edit personal info, upload avatar, change password
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { api, assetUrl } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Camera, Save } from "lucide-react";

export default function Profile() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ full_name: "", username: "", bio: "", native_language_code: "en", level_code: "A1", daily_goal_xp: 30 });
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (user) setForm({
      full_name: user.full_name || "",
      username: user.username,
      bio: user.bio || "",
      native_language_code: user.native_language_code,
      level_code: user.level_code,
      daily_goal_xp: user.daily_goal_xp,
    });
  }, [user]);

  // Save profile changes
  async function save() {
    try {
      const { data } = await api.patch("/users/me", form);
      setUser(data);
      toast.success("Profile updated");
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Could not save"); }
  }

  // Change password
  async function changePw() {
    if (pw.new_password.length < 6) return toast.error("New password must be at least 6 characters");
    try {
      await api.post("/auth/change-password", pw);
      toast.success("Password changed");
      setPw({ current_password: "", new_password: "" });
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Could not change"); }
  }

  // Upload avatar image
  async function uploadAvatar(file: File) {
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const { data } = await api.post("/users/me/avatar", fd, { headers: { "Content-Type": "multipart/form-data" } });
      setUser(data);
      toast.success("Avatar uploaded");
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Could not upload"); }
    finally { setUploading(false); }
  }

  if (!user) return null;
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="font-heading text-3xl font-black" data-testid="profile-title">Profile</h1>
      {/* Avatar section */}
      <div className="card-surface p-6 flex items-center gap-6 flex-wrap">
        <div className="relative w-24 h-24 rounded-full bg-primary/20 border-4 border-primary overflow-hidden flex items-center justify-center">
          {user.avatar_url ? (
            <img src={assetUrl(user.avatar_url)} alt="avatar" className="w-full h-full object-cover" />
          ) : (
            <span className="font-heading font-black text-3xl text-primary">{user.username.slice(0, 2).toUpperCase()}</span>
          )}
          <label className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 hover:opacity-100 cursor-pointer transition-opacity" data-testid="avatar-label">
            <Camera className="w-6 h-6 text-white" />
            <input data-testid="avatar-input" type="file" accept="image/*" className="hidden" disabled={uploading} onChange={(e) => e.target.files?.[0] && uploadAvatar(e.target.files[0])} />
          </label>
        </div>
        <div>
          <div className="font-heading text-2xl font-black">{user.full_name || user.username}</div>
          <div className="text-muted-foreground">@{user.username}</div>
          <div className="text-xs text-muted-foreground mt-1">{user.email}</div>
        </div>
      </div>

      {/* Edit profile form */}
      <div className="card-surface p-6 space-y-4">
        <h2 className="font-heading text-xl font-black">Information</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} testid="profile-fullname" />
          <Input label="Username" value={form.username} onChange={(v) => setForm({ ...form, username: v })} testid="profile-username" />
          <Select label="My Native Language" value={form.native_language_code} onChange={(v) => setForm({ ...form, native_language_code: v })} testid="profile-native"
            options={[["en", "🇬🇧 English"], ["tr", "🇹🇷 Turkish"], ["az", "🇦🇿 Azərbaycan"], ["de", "🇩🇪 Deutsch"], ["es", "🇪🇸 Español"], ["fr", "🇫🇷 Français"], ["it", "🇮🇹 Italiano"], ["ja", "🇯🇵 日本語"], ["ko", "🇰🇷 한국어"], ["ru", "🇷🇺 Русский"]]} />
          <Select label="My Level" value={form.level_code} onChange={(v) => setForm({ ...form, level_code: v })} testid="profile-level"
            options={[["A1","A1"],["A2","A2"],["B1","B1"],["B2","B2"],["C1","C1"],["C2","C2"]]} />
          <div className="sm:col-span-2">
            <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Daily Goal ({form.daily_goal_xp} XP)</label>
            <input type="range" min={10} max={100} step={10} value={form.daily_goal_xp} onChange={(e) => setForm({ ...form, daily_goal_xp: Number(e.target.value) })} className="w-full mt-2" data-testid="profile-daily-goal" />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Biography</label>
            <textarea value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none min-h-[80px]" data-testid="profile-bio" />
          </div>
        </div>
        <button onClick={save} className="btn-primary" data-testid="profile-save"><Save className="w-4 h-4" /> Save</button>
      </div>

      {/* Change password section */}
      <div className="card-surface p-6 space-y-4">
        <h2 className="font-heading text-xl font-black">Change Password</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <Input label="Current password" type="password" value={pw.current_password} onChange={(v) => setPw({ ...pw, current_password: v })} testid="pw-current" />
          <Input label="New password" type="password" value={pw.new_password} onChange={(v) => setPw({ ...pw, new_password: v })} testid="pw-new" />
        </div>
        <button onClick={changePw} className="btn-outline" data-testid="pw-submit">Change Password</button>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, type = "text", testid }: any) {
  return (
    <div>
      <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">{label}</label>
      <input data-testid={testid} type={type} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
    </div>
  );
}
function Select({ label, value, onChange, options, testid }: any) {
  return (
    <div>
      <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">{label}</label>
      <select data-testid={testid} value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none">
        {options.map(([v, l]: any) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}
