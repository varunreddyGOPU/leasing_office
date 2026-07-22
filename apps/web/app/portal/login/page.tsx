"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { portalJson } from "@/lib/portal";

export default function PortalLoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(e.currentTarget);
    try {
      await portalJson("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      router.push("/portal");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-20">
      <h1 className="font-display text-4xl text-pine-800">Resident Portal</h1>
      <p className="mt-2 text-charcoal-light">Sign in to view your lease, renew, or request maintenance.</p>

      <form onSubmit={onSubmit} className="mt-8 rounded-2xl border border-cream-dark bg-white p-8">
        <Label htmlFor="email">Email</Label>
        <Input id="email" name="email" type="email" required autoComplete="email" />
        <div className="mt-4">
          <Label htmlFor="password">Password</Label>
          <Input id="password" name="password" type="password" required autoComplete="current-password" />
        </div>
        {error && (
          <p className="mt-4 text-sm font-semibold text-red-700" role="alert">
            {error}
          </p>
        )}
        <Button type="submit" size="lg" className="mt-6 w-full" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
        <p className="mt-4 rounded-lg bg-cream p-3 text-xs text-charcoal-light">
          Demo (sample data): <strong>resident1@example.com</strong> / <strong>auburn-demo</strong>
        </p>
      </form>
    </div>
  );
}
