import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as RadioGroup from "@radix-ui/react-radio-group";
import {
  ArrowLeft,
  Check,
  Eye,
  EyeOff,
  Loader2,
  Rocket,
  Search,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useAppStore } from "../store/useAppStore";
import ConfirmModal from "../components/ConfirmModal";
import { SidebarToggleButton } from "../components/Sidebar";
import Sidebar from "../components/Sidebar";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "Free",
    features: ["30k tokens/day", "1 web search/day"],
  },
  {
    id: "plus",
    name: "Plus",
    emoji: "✨",
    price: "$5.99/mo",
    features: ["60k tokens/day", "5 web searches/day"],
  },
  {
    id: "pro",
    name: "Pro",
    emoji: "🚀",
    price: "$12.99/mo",
    features: ["120k tokens/day", "20 web searches/day"],
  },
];

export default function SettingsPage() {
  const navigate = useNavigate();
  const user = useAppStore((s) => s.user);
  const theme = useAppStore((s) => s.theme);
  const setTheme = useAppStore((s) => s.setTheme);
  const updateProfileDetails = useAppStore((s) => s.updateProfileDetails);
  const deleteAccount = useAppStore((s) => s.deleteAccount);
  const usage = useAppStore((s) => s.usage);
  const isLoadingUsage = useAppStore((s) => s.isLoadingUsage);
  const fetchUsage = useAppStore((s) => s.fetchUsage);

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  // Determine which card shows as "Active" based on the "plan" field from the backend.
  // If it doesn't match one of the three known plans (e.g. "developer" plan),
  // no card is shown as active.
  const activePlanId = (user?.plan || "").trim().toLowerCase();

  const [details, setDetails] = useState(user?.details || "");
  const [isSavingDetails, setIsSavingDetails] = useState(false);
  const [savedNotice, setSavedNotice] = useState(false);

  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleSaveDetails = async () => {
    setIsSavingDetails(true);
    setSavedNotice(false);
    try {
      await updateProfileDetails(details);
      setSavedNotice(true);
      setTimeout(() => setSavedNotice(false), 2500);
    } finally {
      setIsSavingDetails(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!password) {
      setDeleteError("Enter your password to continue.");
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAccount(password);
      navigate("/login", { replace: true });
    } catch (err) {
      const message = (err as { message?: string })?.message || "Could not delete account.";
      setDeleteError(message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="flex h-screen bg-bg-main">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <header className="flex items-center gap-2 border-b border-border px-4 py-3">
          <SidebarToggleButton />
          <button
            onClick={() => navigate(-1)}
            aria-label="Go back"
            className="flex h-9 w-9 items-center justify-center rounded-xl text-text-body hover:bg-hover"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <h1 className="font-semibold text-text-heading">Settings</h1>
        </header>

        <div className="mx-auto w-full max-w-2xl space-y-8 px-4 py-8">
          {/* Today's Usage */}
          <section>
            <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold text-text-heading">
              Today's Usage <Sparkles className="h-4 w-4 text-accent-light" />
            </h2>
            <p className="mb-4 text-sm text-text-secondary">
              Your daily limit resets every night.
            </p>

            {isLoadingUsage && !usage ? (
              <div className="flex items-center gap-2 rounded-2xl border border-border bg-bg-card p-4 text-sm text-text-secondary">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading usage info...
              </div>
            ) : usage ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <UsageMeter
                  icon={<Sparkles className="h-3.5 w-3.5" />}
                  label="Token Usage"
                  used={usage.tokens_used_today}
                  limit={usage.token_limit}
                  formatValue={(n) => n.toLocaleString("en-US")}
                />
                <UsageMeter
                  icon={<Search className="h-3.5 w-3.5" />}
                  label="Web Search"
                  used={usage.searches_used_today}
                  limit={usage.search_limit}
                  formatValue={(n) => n.toLocaleString("en-US")}
                />
              </div>
            ) : (
              <p className="rounded-2xl border border-border bg-bg-card p-4 text-sm text-text-secondary">
                Could not load usage info.
              </p>
            )}
          </section>

          {/* Upgrade Plan */}
          <section>
            <h2 className="mb-1 flex items-center gap-2 text-lg font-semibold text-text-heading">
              Upgrade Your Plan <Rocket className="h-4 w-4 text-accent-light" />
            </h2>
            <p className="mb-4 text-sm text-text-secondary">
              Upgrade for higher limits, more image analysis, and web searches!
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {PLANS.map((plan) => {
                const isCurrent = plan.id === activePlanId;
                return (
                  <div
                    key={plan.id}
                    className={`flex flex-col rounded-2xl border p-4 ${
                      isCurrent ? "border-accent bg-accent/5" : "border-border bg-bg-card"
                    }`}
                  >
                    <div className="mb-1 flex items-center gap-1.5 font-semibold text-text-heading">
                      {plan.name} {plan.emoji}
                    </div>
                    <div className="mb-3 text-sm text-text-secondary">{plan.price}</div>
                    <ul className="mb-4 flex-1 space-y-1.5">
                      {plan.features.map((f) => (
                        <li key={f} className="flex items-center gap-1.5 text-xs text-text-body">
                          <Check className="h-3.5 w-3.5 text-success" />
                          {f}
                        </li>
                      ))}
                    </ul>
                    <button
                      disabled={isCurrent}
                      className={`rounded-xl py-2 text-sm font-medium transition ${
                        isCurrent
                          ? "cursor-default bg-bg-sidebar text-text-secondary"
                          : "bg-user-gradient text-white hover:opacity-90"
                      }`}
                    >
                      {isCurrent ? "Active" : "Upgrade"}
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Theme */}
          <section>
            <h2 className="mb-3 text-lg font-semibold text-text-heading">Theme</h2>
            <RadioGroup.Root
              value={theme}
              onValueChange={(v) => setTheme(v as "light" | "dark")}
              className="flex flex-wrap gap-3"
              aria-label="Theme selection"
            >
              {[
                { value: "light", label: "Light" },
                { value: "dark", label: "Dark" },
              ].map((opt) => (
                <label
                  key={opt.value}
                  className="flex cursor-pointer items-center gap-2 rounded-xl border border-border bg-bg-card px-4 py-2.5 text-sm text-text-body has-[[data-state=checked]]:border-accent has-[[data-state=checked]]:bg-accent/10"
                >
                  <RadioGroup.Item
                    value={opt.value}
                    className="flex h-4 w-4 items-center justify-center rounded-full border border-border data-[state=checked]:border-accent"
                  >
                    <RadioGroup.Indicator className="h-2 w-2 rounded-full bg-accent" />
                  </RadioGroup.Item>
                  {opt.label}
                </label>
              ))}
            </RadioGroup.Root>
          </section>

          {/* Profile Details */}
          <section>
            <h2 className="mb-3 text-lg font-semibold text-text-heading">Profile Details</h2>
            <p className="mb-2 text-sm text-text-secondary">
              Tell us about yourself so Nova can personalize responses.
            </p>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              maxLength={4000}
              rows={4}
              placeholder="E.g., I'm a backend developer..."
              className="w-full resize-none rounded-xl border border-border bg-bg-card p-3 text-sm text-text-body placeholder:text-text-secondary focus:border-accent focus:outline-none"
            />
            <div className="mt-3 flex items-center gap-3">
              <button
                onClick={handleSaveDetails}
                disabled={isSavingDetails}
                className="flex items-center gap-2 rounded-xl bg-user-gradient px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSavingDetails && <Loader2 className="h-4 w-4 animate-spin" />}
                Save Details
              </button>
              {savedNotice && (
                <span className="flex items-center gap-1 text-sm text-success">
                  <Check className="h-4 w-4" /> Saved
                </span>
              )}
            </div>

            <button
              onClick={() => setDeleteModalOpen(true)}
              className="mt-6 flex items-center gap-2 rounded-xl border border-danger/30 px-4 py-2 text-sm font-medium text-danger transition hover:bg-danger/10"
            >
              <Trash2 className="h-4 w-4" />
              Permanently Delete Account
            </button>
          </section>
        </div>
      </div>

      <ConfirmModal
        open={deleteModalOpen}
        onOpenChange={(open) => {
          setDeleteModalOpen(open);
          if (!open) {
            setPassword("");
            setDeleteError(null);
          }
        }}
        title="Delete Account"
        description="Are you sure you want to delete your account? This action cannot be undone."
        confirmLabel="Delete Account"
        danger
        isLoading={isDeleting}
        onConfirm={handleDeleteAccount}
      >
        <div>
          <label htmlFor="delete-password" className="mb-1.5 block text-sm font-medium text-text-body">
            Enter Your Password
          </label>
          <div className="relative">
            <input
              id="delete-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-bg-main py-2 pl-3 pr-10 text-sm text-text-body focus:border-danger focus:outline-none"
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
          {deleteError && <p className="mt-1.5 text-xs text-danger">{deleteError}</p>}
        </div>
      </ConfirmModal>
    </div>
  );
}

interface UsageMeterProps {
  icon: React.ReactNode;
  label: string;
  used: number;
  /** null = unlimited (developer plan) */
  limit: number | null;
  formatValue: (n: number) => string;
}

function UsageMeter({ icon, label, used, limit, formatValue }: UsageMeterProps) {
  const isUnlimited = limit === null;
  const pct = isUnlimited ? 0 : Math.min(100, limit > 0 ? (used / limit) * 100 : 100);
  const isNearLimit = !isUnlimited && pct >= 90;

  return (
    <div className="rounded-2xl border border-border bg-bg-card p-4">
      <div className="mb-2 flex items-center gap-1.5 text-sm font-medium text-text-heading">
        {icon}
        {label}
      </div>
      <div className="mb-2 text-lg font-semibold text-text-heading">
        {formatValue(used)}
        <span className="text-sm font-normal text-text-secondary">
          {" "}
          / {isUnlimited ? "unlimited" : formatValue(limit)}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-sidebar">
          <div
            className={`h-full rounded-full transition-all ${
              isNearLimit ? "bg-danger" : "bg-user-gradient"
            }`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
    </div>
  );
}
