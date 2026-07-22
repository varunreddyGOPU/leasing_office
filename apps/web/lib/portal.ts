// All browser calls are same-origin relative URLs, proxied to FastAPI by the
// Next.js rewrite — one public origin, so tunnels/deploys just work and the
// session cookie stays first-party. Set NEXT_PUBLIC_API_URL only to bypass
// the proxy in unusual setups.
export const API = process.env.NEXT_PUBLIC_API_URL ?? "";

export async function portalFetch(path: string, init?: RequestInit): Promise<Response> {
  return fetch(`${API}${path}`, { credentials: "include", ...init });
}

export async function portalJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await portalFetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`;
    const err = new Error(detail) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json() as Promise<T>;
}
