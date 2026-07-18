// Server-side fetch helper. In Docker the API is reached via the internal
// hostname (API_URL); browser calls go through the Next.js /api rewrite.
const API_URL = process.env.API_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string, revalidateSeconds = 300): Promise<T | null> {
  try {
    const res = await fetch(`${API_URL}${path}`, {
      next: { revalidate: revalidateSeconds },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
