import { Lock, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/useAppStore";

export default function SuspendedAccountPage() {
  const logout = useAppStore((s) => s.logout);
  const setAccountSuspended = useAppStore((s) => s.setAccountSuspended);
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    setAccountSuspended(false);
    navigate("/login", { replace: true });
  };

  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center px-6 py-12 text-center"
      style={{
        background:
          "radial-gradient(circle at 50% 32%, #2c1015 0%, #1a0c11 45%, #0b0a12 100%)",
      }}
    >
      <div className="mb-8 flex h-28 w-28 items-center justify-center rounded-full bg-[#3a1a20]">
        <Lock className="h-12 w-12 text-[#f2b8ad]" strokeWidth={1.75} />
      </div>

      <h1 className="mb-8 max-w-xs text-3xl font-extrabold leading-tight text-[#f2b8ad]">
        Your Nova AI Account Has Been Suspended!
      </h1>

      <div className="mb-10 max-w-md rounded-2xl bg-[#211f33]/80 px-6 py-6">
        <p className="text-[15px] leading-relaxed text-[#c9c6da]">
          Unusual activity has been detected on your account. Your account
          has been temporarily suspended to ensure the security of our platform
          and prevent misuse. This does not mean your account has been closed;
          it is only under review for security purposes. For more
          information,{" "}
          <a href="mailto:support@nova.ai" className="underline">
            support@nova.ai
          </a>{" "}
          email us
        </p>
      </div>

      <button
        onClick={handleLogout}
        className="flex w-full max-w-md items-center justify-center gap-2 rounded-2xl bg-[#f2b8ad] py-4 text-base font-bold text-[#6b1d1d] transition hover:opacity-90"
      >
        <LogOut className="h-5 w-5" />
        Log Out
      </button>
    </div>
  );
}
