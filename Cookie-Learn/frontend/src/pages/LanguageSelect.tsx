// Language selection page - user picks a language to start learning
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Check, Loader2 } from "lucide-react";
import type { Language, User } from "@/types";

export default function LanguageSelect() {
  const { user, setUser } = useAuth();
  const nav = useNavigate();
  const [langs, setLangs] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Language[]>("/languages").then(({ data }) => setLangs(data)).finally(() => setLoading(false));
  }, []);

  async function pick(code: string) {
    try {
      const { data } = await api.post<User>(`/users/me/active-language?code=${code}`);
      setUser(data);
      toast.success(`Active language: ${langs.find(l => l.code === code)?.native_name}`);
      nav("/dashboard");
    } catch {
      toast.error("Something went wrong");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-heading text-3xl sm:text-4xl font-black" data-testid="langselect-title">What do you want to learn?</h1>
        <p className="text-muted-foreground mt-1">Pick a language and start your journey. You can switch anytime.</p>
      </div>
      {loading ? (
        <div className="flex items-center justify-center py-20"><Loader2 className="w-10 h-10 animate-spin text-primary" /></div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="langselect-grid">
          {langs.map((l) => (
            <button
              key={l.code}
              onClick={() => pick(l.code)}
              data-testid={`lang-${l.code}`}
              className={`card-surface p-6 flex flex-col items-center gap-3 hover:border-primary transition-colors relative ${
                user?.active_language_code === l.code ? "border-primary" : ""
              }`}
            >
              <div className="text-5xl">{l.flag_emoji}</div>
              <div className="font-heading font-black text-lg">{l.native_name}</div>
              <div className="text-xs text-muted-foreground uppercase tracking-widest">{l.name}</div>
              {user?.active_language_code === l.code && (
                <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
                  <Check className="w-4 h-4" />
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
