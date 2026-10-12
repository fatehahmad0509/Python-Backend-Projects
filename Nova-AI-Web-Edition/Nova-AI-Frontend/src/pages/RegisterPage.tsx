import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Loader2, Mail, Lock, CheckCircle2 } from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import type { ApiErrorShape } from "../types/api";

export default function RegisterPage() {
  const register = useAppStore((s) => s.register);
  const user = useAppStore((s) => s.user);
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [success, setSuccess] = useState(false);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFieldErrors({});

    if (password.length < 8) {
      setFieldErrors({ password: "Password must be at least 8 characters." });
      return;
    }

    setIsSubmitting(true);
    try {
      await register(email, password);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
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
          <h1 className="text-2xl font-bold text-text-heading">Join Nova AI</h1>
          <p className="mt-1 text-sm text-text-secondary">Create your free account</p>
        </div>

        {success ? (
          <div className="flex flex-col items-center gap-3 rounded-xl border border-success/30 bg-success/10 px-4 py-8 text-center">
            <CheckCircle2 className="h-8 w-8 text-success" />
            <p className="text-sm text-text-body">
              Your account has been created! Redirecting to login...
            </p>
          </div>
        ) : (
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
                  className="w-full rounded-xl border border-border bg-bg-card py-2.5 pl-10 pr-3 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
                  placeholder="example@email.com"
                />
              </div>
              {fieldErrors.email && <p className="mt-1 text-xs text-danger">{fieldErrors.email}</p>}
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
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={Boolean(fieldErrors.password)}
                  className="w-full rounded-xl border border-border bg-bg-card py-2.5 pl-10 pr-10 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
                  placeholder="At least 8 characters"
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
              {fieldErrors.password ? (
                <p className="mt-1 text-xs text-danger">{fieldErrors.password}</p>
              ) : (
                <p className="mt-1 text-xs text-text-secondary">Use at least 8 characters.</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-user-gradient py-2.5 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
              Sign Up
            </button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-text-secondary">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-accent-light hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
}
