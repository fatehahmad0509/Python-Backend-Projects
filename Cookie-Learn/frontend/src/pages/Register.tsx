// Registration page with form for email, username, native language, and password
import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2, UserPlus } from "lucide-react";

export default function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", username: "", password: "", full_name: "", native_language_code: "en" });
  const [loading, setLoading] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await register({ ...form, email: form.email.trim().toLowerCase() });
      toast.success("Your account is ready! 🎉");
      nav("/languages");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 font-heading font-black text-2xl mb-8" data-testid="register-brand">
          <span className="text-3xl">🍪</span> CookieLearn
        </Link>
        <div className="card-surface p-8">
          <h1 className="font-heading text-3xl font-black mb-1">Create account</h1>
          <p className="text-muted-foreground mb-6">Your first lesson is as easy as a cookie bite.</p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Email</label>
              <input data-testid="register-email" type="email" required value={form.email} onChange={(e)=>setForm(f=>({...f,email:e.target.value}))} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Username</label>
                <input data-testid="register-username" required minLength={3} value={form.username} onChange={(e)=>setForm(f=>({...f,username:e.target.value}))} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
              </div>
              <div>
                <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Your Native Language</label>
                <select data-testid="register-native" value={form.native_language_code} onChange={(e)=>setForm(f=>({...f,native_language_code:e.target.value}))} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none">
                  <option value="en">🇬🇧 English</option>
                  <option value="tr">🇹🇷 Turkish</option>
                  <option value="az">🇦🇿 Azərbaycanca</option>
                  <option value="de">🇩🇪 Deutsch</option>
                  <option value="es">🇪🇸 Español</option>
                  <option value="fr">🇫🇷 Français</option>
                  <option value="it">🇮🇹 Italiano</option>
                  <option value="ja">🇯🇵 日本語</option>
                  <option value="ko">🇰🇷 한국어</option>
                  <option value="ru">🇷🇺 Русский</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Password</label>
              <input data-testid="register-password" type="password" required minLength={6} value={form.password} onChange={(e)=>setForm(f=>({...f,password:e.target.value}))} className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary outline-none" />
            </div>
            <button data-testid="register-submit" disabled={loading} className="btn-primary w-full">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><UserPlus className="w-5 h-5" /> Create Account</>}
            </button>
          </form>
          <div className="mt-6 text-sm text-center text-muted-foreground">
            Already have an account? <Link to="/login" className="text-primary font-heading font-bold" data-testid="register-login-link">Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
