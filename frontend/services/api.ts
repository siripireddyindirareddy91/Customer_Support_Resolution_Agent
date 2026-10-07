export type ChatResult = {
  response: string;
  intent: string;
  workflow_status: string;
  order?: Record<string, unknown> | null;
  delivery?: Record<string, unknown> | null;
  resolution?: Record<string, unknown> | null;
  citations: { source: string; excerpt: string }[];
  escalation?: Record<string, string> | null;
  activity: string[];
};

export async function sendMessage(message: string): Promise<ChatResult> {
  const login = await fetch("/api/v1/auth/demo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_id: "CUS-1001" }),
  });
  if (!login.ok) throw new Error("Sign in to continue.");
  const { access_token: token } = await login.json();
  const response = await fetch("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) throw new Error(response.status === 401 ? "Sign in to continue." : "Support is temporarily unavailable.");
  return response.json();
}