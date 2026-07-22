"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { API } from "@/lib/portal";

interface Ticket {
  id: number;
  category: string;
  description: string;
  status: string;
  created_at: string;
  unit_number: string;
  resident_name: string;
  photo_count: number;
}

const COLUMNS: { key: string; label: string }[] = [
  { key: "new", label: "New" },
  { key: "scheduled", label: "Scheduled" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
];

export default function OfficeMaintenancePage() {
  const [adminKey, setAdminKey] = useState("");
  const [entered, setEntered] = useState(false);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = sessionStorage.getItem("office_admin_key");
    if (stored) {
      setAdminKey(stored);
      setEntered(true);
    }
  }, []);

  const load = useCallback(
    async (key: string) => {
      setError("");
      const res = await fetch(`${API}/api/admin/maintenance`, {
        headers: { "X-Admin-Key": key },
      });
      if (res.status === 401) {
        setError("Invalid admin key.");
        setEntered(false);
        sessionStorage.removeItem("office_admin_key");
        return;
      }
      setTickets(await res.json());
    },
    []
  );

  useEffect(() => {
    if (entered && adminKey) load(adminKey);
  }, [entered, adminKey, load]);

  async function move(id: number, status: string) {
    const res = await fetch(`${API}/api/admin/maintenance/${id}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
      body: JSON.stringify({ status }),
    });
    if (res.ok) load(adminKey);
  }

  if (!entered) {
    return (
      <div className="mx-auto max-w-sm px-4 py-20">
        <h1 className="font-display text-3xl text-pine-800">Office — Maintenance Board</h1>
        <form
          className="mt-6 rounded-2xl border border-cream-dark bg-white p-6"
          onSubmit={(e) => {
            e.preventDefault();
            sessionStorage.setItem("office_admin_key", adminKey);
            setEntered(true);
          }}
        >
          <Label htmlFor="key">Admin key</Label>
          <Input
            id="key"
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            required
          />
          {error && (
            <p className="mt-3 text-sm font-semibold text-red-700" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" className="mt-4 w-full">
            Open board
          </Button>
        </form>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <h1 className="font-display text-3xl text-pine-800">Maintenance Board</h1>
      <p className="mt-1 text-sm text-charcoal-light">
        Every move notifies the resident (alert outbox — delivery lands in Phase 6).
      </p>
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((col) => (
          <section key={col.key} aria-label={col.label} className="rounded-2xl bg-cream-dark/60 p-3">
            <h2 className="px-2 py-1 font-semibold text-pine-800">
              {col.label}{" "}
              <span className="text-sm text-charcoal-light">
                ({tickets.filter((t) => t.status === col.key).length})
              </span>
            </h2>
            <div className="mt-2 space-y-3">
              {tickets
                .filter((t) => t.status === col.key)
                .map((t) => (
                  <article key={t.id} className="rounded-xl border border-cream-dark bg-white p-4">
                    <p className="text-sm font-bold">
                      Unit {t.unit_number} · <span className="capitalize">{t.category}</span>
                    </p>
                    <p className="mt-1 text-xs text-charcoal-light">
                      {t.resident_name} · #{t.id}
                      {t.photo_count > 0 && ` · ${t.photo_count} 📷`}
                    </p>
                    <p className="mt-2 line-clamp-3 text-sm">{t.description}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {COLUMNS.filter((c) => c.key !== t.status).map((c) => (
                        <button
                          key={c.key}
                          onClick={() => move(t.id, c.key)}
                          className="rounded-full bg-pine-100 px-2.5 py-1 text-xs font-semibold text-pine-800 hover:bg-pine-300"
                        >
                          → {c.label}
                        </button>
                      ))}
                    </div>
                  </article>
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
