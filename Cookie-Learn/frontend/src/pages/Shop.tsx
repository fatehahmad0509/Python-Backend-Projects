// Shop page - purchase in-game items like heart refills
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Gem, Heart, Sparkles } from "lucide-react";

export default function Shop() {
  const { user, setUser } = useAuth();
  async function refill() {
    try {
      const { data } = await api.post("/users/me/refill-hearts");
      setUser(data);
      toast.success("Hearts refilled!");
    } catch (e: any) { toast.error(e?.response?.data?.detail || "Could not purchase"); }
  }
  return (
    <div className="space-y-6">
      <h1 className="font-heading text-3xl font-black" data-testid="shop-title">Shop</h1>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="card-surface p-6" data-testid="shop-refill">
          <Heart className="w-10 h-10 text-destructive fill-destructive" />
          <div className="font-heading text-xl font-black mt-3">Refill Hearts</div>
          <div className="text-sm text-muted-foreground mt-1">Renew all your hearts</div>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-1 text-secondary"><Gem className="w-4 h-4" /> {(user!.max_hearts - user!.hearts) * 10} gems</div>
            <button onClick={refill} className="btn-primary text-sm" data-testid="shop-refill-btn" disabled={user!.hearts >= user!.max_hearts}>Buy</button>
          </div>
        </div>
        <div className="card-surface p-6">
          <Sparkles className="w-10 h-10 text-accent" />
          <div className="font-heading text-xl font-black mt-3">Streak Shield</div>
          <div className="text-sm text-muted-foreground mt-1">Coming soon...</div>
        </div>
        <div className="card-surface p-6">
          <Gem className="w-10 h-10 text-secondary" />
          <div className="font-heading text-xl font-black mt-3">Gem Pack</div>
          <div className="text-sm text-muted-foreground mt-1">Coming soon...</div>
        </div>
      </div>
    </div>
  );
}
