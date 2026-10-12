import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Loader2, Mail, Lock } from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import type { ApiErrorShape } from "../types/api";

export default function LoginPage() {
  const login = useAppStore((s) => s.login);
  const user = useAppStore((s) => s.user);
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: { pathname: string } } };

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  if (user) {
    return <Navigate to={location.state?.from?.pathname || "/"} replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFieldErrors({});
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      const apiErr = err as ApiErrorShape;
      setFormError(apiErr.message);
      setFieldErrors(apiErr.fieldErrors || {});
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-main px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center text-center">
          <img
            src="/logo.jpeg"
            alt="Nova AI logo"
            className="mb-4 h-16 w-16 rounded-2xl object-cover shadow-lg shadow-accent/20"
          />
          <h1 className="text-2xl font-bold text-text-heading">Welcome to Nova AI</h1>
          <p className="mt-1 text-sm text-text-secondary">Sign in to your account to continue</p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          {formError && (
            <div
              role="alert"
              className="rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
            >
              {formError}
            </div>
          )}

          <div>
            <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-text-body">
              Email Address
            </label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
              <input
                id="email"
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={Boolean(fieldErrors.email)}
                aria-describedby={fieldErrors.email ? "email-error" : undefined}
                className="w-full rounded-xl border border-border bg-bg-card py-2.5 pl-10 pr-3 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
                placeholder="example@email.com"
              />
            </div>
            {fieldErrors.email && (
              <p id="email-error" className="mt-1 text-xs text-danger">
                {fieldErrors.email}
              </p>
            )}
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-text-body">
              Password
            </label>
            <div className="relative">
              <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-secondary" />
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={Boolean(fieldErrors.password)}
                aria-describedby={fieldErrors.password ? "password-error" : undefined}
                className="w-full rounded-xl border border-border bg-bg-card py-2.5 pl-10 pr-10 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
                placeholder="••••••••"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-body"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            {fieldErrors.password && (
              <p id="password-error" className="mt-1 text-xs text-danger">
                {fieldErrors.password}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-user-gradient py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Sign In
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-text-secondary">
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-accent-light hover:underline">
            Sign Up
          </Link>
        </p>
      </div>
    </div>
  );
}
