import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2, LogIn } from "lucide-react";

export default function Login() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  async function submit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
      toast.success("Hoşgeldin! 🍪");
      nav("/dashboard");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Giriş başarısız");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Link to="/" className="flex items-center justify-center gap-2 font-heading font-black text-2xl mb-8" data-testid="login-brand">
          <span className="text-3xl">🍪</span> CookieLearn
        </Link>
        <div className="card-surface p-8">
          <h1 className="font-heading text-3xl font-black mb-1">Tekrar hoşgeldin</h1>
          <p className="text-muted-foreground mb-6">Öğrenmene kaldığın yerden devam et.</p>
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">E-posta</label>
              <input
                data-testid="login-email"
                type="email" required autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary transition-colors outline-none"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="text-xs font-heading font-bold uppercase tracking-widest text-muted-foreground">Şifre</label>
              <input
                data-testid="login-password"
                type="password" required minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full px-4 py-3 rounded-xl bg-muted border-2 border-transparent focus:border-primary transition-colors outline-none"
                placeholder="••••••••"
              />
            </div>
            <button data-testid="login-submit" disabled={loading} className="btn-primary w-full">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><LogIn className="w-5 h-5" /> Giriş Yap</>}
            </button>
          </form>
          <div className="mt-6 text-sm text-center text-muted-foreground">
            Hesabın yok mu? <Link to="/register" className="text-primary font-heading font-bold" data-testid="login-register-link">Kayıt ol</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
