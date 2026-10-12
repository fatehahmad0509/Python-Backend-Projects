// Types mirroring backend openapi.json schema exactly.

export interface UserRead {
  id: string;
  email: string;
  details: string | null;
  created_at: string;
  /**
   * The subscription plan name returned by the backend (e.g. "free", "plus", "pro",
   * or "developer"). If it is not one of the three known plans (e.g. developer),
   * no plan is marked as "Active" on the Settings page.
   */
  plan?: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

export interface MessageRead {
  id: string;
  role: "user" | "assistant" | string;
  content: string;
  image_base64?: string | null;
  image_mime_type?: string | null;
  sources?: Record<string, unknown>[] | null;
  created_at: string;
  /**
   * Client-side only flag — not part of the backend schema.
   * Used only to mark the assistant message that just arrived from a /chat response,
   * so ChatMessage renders it with a one-time "typing" effect;
   * messages loaded from history do not carry this flag and appear instantly.
   */
  _isNew?: boolean;
}

export interface ConversationRead {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetailRead extends ConversationRead {
  messages: MessageRead[];
}

export interface ChatRequest {
  conversation_id?: string | null;
  message: string;
  image_base64?: string | null;
  image_mime_type?: string | null;
}

export interface ChatResponse {
  conversation_id: string;
  title: string;
  user_message: MessageRead;
  assistant_message: MessageRead;
}

export interface UserDetailsUpdate {
  details: string;
}

export interface UsageRead {
  plan: string;
  tokens_used_today: number;
  /** null = unlimited (developer plan) */
  token_limit: number | null;
  searches_used_today: number;
  /** null = unlimited (developer plan) */
  search_limit: number | null;
}

export interface DeleteAccountRequest {
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface MessageResponse {
  success: boolean;
  message: string;
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface HTTPValidationError {
  detail: ValidationError[];
}

export interface ApiErrorShape {
  status?: number;
  message: string;
  fieldErrors?: Record<string, string>;
}
