import { create } from "zustand";
import { api, tokenStorage } from "../lib/api";
import type {
  ApiErrorShape,
  ChatResponse,
  ConversationDetailRead,
  ConversationRead,
  MessageRead,
  UsageRead,
  UserRead,
} from "../types/api";

type Theme = "light" | "dark";

interface SendMessageArgs {
  message: string;
  conversationId?: string | null;
  imageBase64?: string | null;
  imageMimeType?: string | null;
}

interface AppState {
  // Auth state
  user: UserRead | null;
  isAuthReady: boolean;
  authError: string | null;
  /** true when the backend reports the account as blocked/suspended (HTTP 403). */
  accountSuspended: boolean;

  // Chat state
  conversations: ConversationRead[];
  /** true once conversations have been fetched at least once — lets the sidebar skip a redundant re-fetch on mount. */
  conversationsInitialized: boolean;
  currentConversation: ConversationDetailRead | null;
  isLoadingConversations: boolean;
  isLoadingConversation: boolean;
  /** Set when fetchConversation fails, so the UI can show a retry option instead of staying blank. */
  conversationError: string | null;
  isSending: boolean;
  isAnalyzingImage: boolean;
  /** Set when sendMessage fails (e.g. daily token limit reached), so the UI can show a banner. */
  sendError: string | null;

  // UI state
  sidebarOpen: boolean;
  theme: Theme;

  // Usage state (for the "today's usage" card on the Settings page)
  usage: UsageRead | null;
  isLoadingUsage: boolean;

  // Actions
  init: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchConversations: () => Promise<void>;
  fetchConversation: (id: string) => Promise<void>;
  sendMessage: (args: SendMessageArgs) => Promise<string>;
  deleteConversation: (id: string) => Promise<void>;
  updateProfileDetails: (details: string) => Promise<void>;
  deleteAccount: (password: string) => Promise<void>;
  fetchUsage: () => Promise<void>;
  clearCurrentConversation: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
  setAccountSuspended: (suspended: boolean) => void;
  clearSendError: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  isAuthReady: false,
  authError: null,
  accountSuspended: false,

  conversations: [],
  conversationsInitialized: false,
  currentConversation: null,
  isLoadingConversations: false,
  isLoadingConversation: false,
  conversationError: null,
  isSending: false,
  isAnalyzingImage: false,
  sendError: null,

  sidebarOpen: false,
  theme: localStorage.getItem("nova_theme") === "light" ? "light" : "dark",

  usage: null,
  isLoadingUsage: false,

  init: async () => {
    const token = tokenStorage.getAccess();
    if (!token) {
      set({ isAuthReady: true });
      return;
    }
    // Fire both requests together instead of waiting for /users/me to finish
    // before even starting /chat/conversations — that sequential waterfall
    // (auth check → THEN conversations) was the main reason the sidebar took
    // a few extra seconds to show up on load, not backend/Redis speed.
    const [userResult, conversationsResult] = await Promise.allSettled([
      api.get<UserRead>("/users/me"),
      api.get<ConversationRead[]>("/chat/conversations"),
    ]);

    if (userResult.status === "fulfilled") {
      set({ user: userResult.value.data, isAuthReady: true });
    } else {
      const normalized = userResult.reason as ApiErrorShape;
      // A blocked account keeps its tokens — the response interceptor already
      // triggers the suspension screen for a 403, so don't sign the user out here.
      if (normalized?.status === 403) {
        set({ isAuthReady: true });
        return;
      }
      tokenStorage.clear();
      set({ user: null, isAuthReady: true });
      return;
    }

    if (conversationsResult.status === "fulfilled") {
      set({ conversations: conversationsResult.value.data, conversationsInitialized: true });
    }
  },

  login: async (email, password) => {
    set({ authError: null });
    try {
      const { data } = await api.post("/auth/login", { email, password });
      tokenStorage.set(data.access_token, data.refresh_token);

      // Same parallelization as init(): fetch the profile and the
      // conversation list together so the sidebar is already populated by
      // the time we navigate into the app, instead of loading it a second
      // time after landing on "/".
      const [userResult, conversationsResult] = await Promise.allSettled([
        api.get<UserRead>("/users/me"),
        api.get<ConversationRead[]>("/chat/conversations"),
      ]);

      if (userResult.status === "fulfilled") {
        set({ user: userResult.value.data });
      } else {
        throw userResult.reason;
      }

      if (conversationsResult.status === "fulfilled") {
        set({ conversations: conversationsResult.value.data, conversationsInitialized: true });
      }
    } catch (err) {
      // `err` here is already the normalized ApiErrorShape produced by the
      // response interceptor (see lib/api.ts) — do NOT run it through
      // normalizeError() again, since it is no longer a raw AxiosError and
      // would just fall back to a generic message.
      const normalized = err as ApiErrorShape;
      set({ authError: normalized.message });
      throw normalized;
    }
  },

  register: async (email, password) => {
    set({ authError: null });
    try {
      await api.post("/auth/register", { email, password });
    } catch (err) {
      const normalized = err as ApiErrorShape;
      set({ authError: normalized.message });
      throw normalized;
    }
  },

  logout: async () => {
    const refresh_token = tokenStorage.getRefresh();
    try {
      if (refresh_token) {
        await api.post("/auth/logout", { refresh_token });
      }
    } catch {
      // Ignore network/errors on logout — clear client state regardless.
    } finally {
      tokenStorage.clear();
      set({
        user: null,
        conversations: [],
        conversationsInitialized: false,
        currentConversation: null,
      });
    }
  },

  fetchConversations: async () => {
    set({ isLoadingConversations: true });
    try {
      const { data } = await api.get<ConversationRead[]>("/chat/conversations");
      set({ conversations: data, conversationsInitialized: true });
    } finally {
      set({ isLoadingConversations: false });
    }
  },

  fetchConversation: async (id: string) => {
    set({ isLoadingConversation: true, currentConversation: null, conversationError: null });
    try {
      const { data } = await api.get<ConversationDetailRead>(`/chat/conversations/${id}`);
      set({ currentConversation: data });
    } catch (err) {
      const normalized = err as ApiErrorShape;
      set({
        conversationError:
          normalized?.message || "Failed to load conversation. Please try again.",
      });
    } finally {
      set({ isLoadingConversation: false });
    }
  },

  sendMessage: async ({ message, conversationId, imageBase64, imageMimeType }) => {
    set({
      isSending: true,
      isAnalyzingImage: Boolean(imageBase64),
      conversationError: null,
      sendError: null,
    });

    // Optimistically render the user's message immediately.
    const optimisticUserMessage: MessageRead = {
      id: `optimistic-${Date.now()}`,
      role: "user",
      content: message,
      image_base64: imageBase64 ?? null,
      image_mime_type: imageMimeType ?? null,
      created_at: new Date().toISOString(),
    };

    const existing = get().currentConversation;
    set({
      currentConversation: existing
        ? { ...existing, messages: [...existing.messages, optimisticUserMessage] }
        : {
            id: "pending",
            title: "New Conversation",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            messages: [optimisticUserMessage],
          },
    });

    try {
      const { data } = await api.post<ChatResponse>("/chat", {
        conversation_id: conversationId ?? null,
        message,
        image_base64: imageBase64 ?? null,
        image_mime_type: imageMimeType ?? null,
      });

      set((state) => {
        const base = state.currentConversation;
        const filteredMessages = (base?.messages ?? []).filter(
          (m) => m.id !== optimisticUserMessage.id
        );
        return {
          currentConversation: {
            id: data.conversation_id,
            title: data.title,
            created_at: base?.created_at ?? new Date().toISOString(),
            updated_at: new Date().toISOString(),
            messages: [
              ...filteredMessages,
              data.user_message,
              { ...data.assistant_message, _isNew: true },
            ],
          },
        };
      });

      // Refresh sidebar conversation list so title/order stays current.
      get().fetchConversations();

      return data.conversation_id;
    } catch (err) {
      // The message was never actually sent — drop the optimistic bubble so
      // the UI doesn't show a user message that the backend never received,
      // and surface an error (e.g. daily token limit reached) so the
      // person knows what happened instead of the request failing silently.
      const normalized = err as ApiErrorShape;
      set((state) => {
        const base = state.currentConversation;
        if (!base) return { sendError: normalized?.message || "Failed to send message." };
        const filteredMessages = base.messages.filter((m) => m.id !== optimisticUserMessage.id);
        return {
          currentConversation:
            filteredMessages.length > 0 ? { ...base, messages: filteredMessages } : null,
          sendError: normalized?.message || "Failed to send message.",
        };
      });
      throw normalized;
    } finally {
      set({ isSending: false, isAnalyzingImage: false });
    }
  },

  deleteConversation: async (id: string) => {
    await api.delete(`/chat/conversations/${id}`);
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversation:
        state.currentConversation?.id === id ? null : state.currentConversation,
    }));
  },

  updateProfileDetails: async (details: string) => {
    const { data } = await api.put<UserRead>("/users/me/details", { details });
    set({ user: data });
  },

  deleteAccount: async (password: string) => {
    await api.delete("/users/me", { data: { password } });
    tokenStorage.clear();
    set({ user: null, conversations: [], currentConversation: null });
  },

  fetchUsage: async () => {
    set({ isLoadingUsage: true });
    try {
      const { data } = await api.get<UsageRead>("/users/me/usage");
      set({ usage: data });
    } finally {
      set({ isLoadingUsage: false });
    }
  },

  clearCurrentConversation: () => set({ currentConversation: null, conversationError: null }),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setTheme: (theme) => {
    localStorage.setItem("nova_theme", theme);
    set({ theme });
  },
  setAccountSuspended: (suspended) => set({ accountSuspended: suspended }),
  clearSendError: () => set({ sendError: null }),
}));
