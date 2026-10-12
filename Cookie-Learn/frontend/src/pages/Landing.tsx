// Landing page - marketing site for CookieLearn with features, language strip, and CTA
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, Zap, MessageCircle, Trophy, Sun, Moon, Bot, BookOpen, Globe2 } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";

const LANGS = [
  { code: "en", name: "English", flag: "🇬🇧" },
  { code: "de", name: "Deutsch", flag: "🇩🇪" },
  { code: "es", name: "Español", flag: "🇪🇸" },
  { code: "fr", name: "Français", flag: "🇫🇷" },
  { code: "it", name: "Italiano", flag: "🇮🇹" },
  { code: "ja", name: "日本語", flag: "🇯🇵" },
  { code: "ko", name: "한국어", flag: "🇰🇷" },
  { code: "ru", name: "Русский", flag: "🇷🇺" },
  { code: "az", name: "Azərbaycanca", flag: "🇦🇿" },
  { code: "tr", name: "Turkish", flag: "🇹🇷" },
];

const FEATURES = [
  { icon: Bot, title: "Your AI Teacher", desc: "Every answer at your fingertips with Cookie, your personal AI language tutor.", color: "primary" },
  { icon: Sparkles, title: "Dynamic Lessons", desc: "Fresh questions generated on the fly by Gemini 3.1, personalized to your level.", color: "accent" },
  { icon: Zap, title: "XP & Streaks", desc: "Stay motivated with XP, streaks, and daily goals.", color: "success" },
  { icon: Trophy, title: "Leagues", desc: "Compete in weekly leagues and climb from Bronze to Master.", color: "secondary" },
  { icon: MessageCircle, title: "Speaking Practice", desc: "Practice conversations with AI and get real-time corrections.", color: "primary" },
  { icon: Globe2, title: "10 Languages", desc: "Learn English, Turkish, German, French, Spanish, Italian, Japanese, Korean, Russian, Azerbaijani.", color: "secondary" },
];

export default function Landing() {
  const { theme, toggle } = useTheme();
  const nav = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="max-w-7xl mx-auto flex items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2 font-heading font-black text-2xl" data-testid="landing-brand">
          <span className="text-3xl">🍪</span>
          <span>CookieLearn</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={toggle} className="p-2 rounded-xl hover:bg-muted transition-colors" data-testid="landing-theme-toggle">
            {theme === "dark" ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <Link to="/login" className="btn-ghost" data-testid="landing-login-link">Login</Link>
          <Link to="/register" className="btn-primary" data-testid="landing-register-link">Start Free</Link>
        </div>
      </header>

      {/* Hero section */}
      <section className="max-w-7xl mx-auto px-6 pt-8 sm:pt-16 pb-24 grid lg:grid-cols-2 gap-12 items-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="text-left">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary font-heading font-bold uppercase tracking-widest text-xs mb-6" data-testid="landing-badge">
            <Sparkles className="w-4 h-4" /> AI-powered, your personal language master
          </div>
          <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-black leading-[0.95] mb-6">
            Learning should be <span className="text-primary">sweet</span>. <br />
            <span className="text-accent">In small bites</span>, every day.
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground max-w-xl mb-8">
            CookieLearn is a modern, Duolingo-like language learning platform powered by Google Gemini 3.1 Flash Lite. Practice speaking, learn vocabulary, and master grammar with interactive lessons.
          </p>
          <div className="flex flex-wrap gap-4">
            <button onClick={() => nav("/register")} className="btn-primary text-base" data-testid="landing-cta-primary">
              <Sparkles className="w-5 h-5" /> Start Now
            </button>
            <button onClick={() => nav("/login")} className="btn-outline text-base" data-testid="landing-cta-secondary">
              <BookOpen className="w-5 h-5" /> Already a Learner?
            </button>
          </div>
          <div className="mt-8 flex flex-wrap gap-2" data-testid="landing-lang-strip">
            {LANGS.map((l) => (
              <span key={l.code} className="px-3 py-1.5 rounded-full bg-card border-2 border-border font-heading font-bold text-sm flex items-center gap-1.5">
                <span className="text-lg">{l.flag}</span> {l.name}
              </span>
            ))}
          </div>
        </motion.div>

        {/* AI chat demo preview */}
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6, delay: 0.15 }} className="relative">
          <div className="absolute -inset-6 bg-primary/20 blur-3xl rounded-full" />
          <div className="relative card-surface p-6 sm:p-8 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-primary/20 border-2 border-primary flex items-center justify-center text-2xl">🍪</div>
              <div>
                <div className="font-heading font-black">Cookie</div>
                <div className="text-xs text-muted-foreground">AI Teacher · Gemini 3.1</div>
              </div>
            </div>
            <div className="bg-muted rounded-2xl rounded-tl-sm p-4 text-sm">
              "How are you?" → A greeting question 👋 <br /> "I'm fine, thanks!" — A typical reply
            </div>
            <div className="bg-primary/10 border border-primary/30 rounded-2xl rounded-tr-sm p-4 text-sm">
              How do I say "I'm fine, and you?"
            </div>
            <div className="bg-muted rounded-2xl rounded-tl-sm p-4 text-sm">
              💡 Casual: <b>"I'm good, and you?"</b> · Formal: <b>"I am well, thank you. And yourself?"</b>
            </div>
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2 text-orange-500">
                <Sparkles className="w-4 h-4 animate-pulse-soft" />
                <span className="font-heading font-bold text-sm uppercase tracking-widest">Live Demo</span>
              </div>
              <div className="text-xs text-muted-foreground">1.2M+ learners</div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features grid */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="card-surface p-6 hover:border-primary transition-colors"
              data-testid={`landing-feature-${i}`}
            >
              <div className={`w-12 h-12 rounded-2xl bg-${f.color}/15 text-${f.color} flex items-center justify-center mb-4`}>
                <f.icon className="w-6 h-6" />
              </div>
              <h3 className="font-heading text-xl font-bold mb-2">{f.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA section */}
      <section className="max-w-7xl mx-auto px-6 pb-24">
        <div className="card-surface p-10 text-center bg-primary/5 border-primary/30">
          <h2 className="font-heading text-3xl sm:text-4xl font-black mb-3">Take your first bite today 🍪</h2>
          <p className="text-muted-foreground mb-6 max-w-2xl mx-auto">
            Start your language learning journey today. No credit card required. All features are free while this portfolio project is active.
          </p>
          <button onClick={() => nav("/register")} className="btn-primary text-base" data-testid="landing-cta-bottom">
            <Sparkles className="w-5 h-5" /> Create Free Account
          </button>
        </div>
      </section>

      <footer className="border-t border-border py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-muted-foreground">
          <div>© 2026 CookieLearn · Portfolio project</div>
          <div className="flex items-center gap-4">
            <a href="https://ai.google.dev/" target="_blank" rel="noreferrer" className="hover:text-foreground">Powered by Gemini 3.1</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
