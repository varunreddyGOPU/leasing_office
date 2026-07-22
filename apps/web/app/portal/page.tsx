"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input, Label, Select, Textarea } from "@/components/ui/input";
import { portalFetch, portalJson } from "@/lib/portal";
import { usd } from "@/lib/utils";

interface LeaseInfo {
  id: number;
  start_date: string;
  end_date: string;
  days_to_end: number;
  monthly_rent: number;
  renewal_status: string;
  renewal_offer_rent: number | null;
  unit: {
    unit_number: string;
    floor_plan_name: string;
    bedrooms: number;
    bathrooms: number;
    sqft: number;
  };
}

interface MeLease {
  resident: { id: number; name: string; email: string };
  lease: LeaseInfo | null;
  upcoming_lease: LeaseInfo | null;
}

interface Ticket {
  id: number;
  category: string;
  description: string;
  status: string;
  created_at: string;
  photo_count: number;
}

const STATUS_LABEL: Record<string, string> = {
  new: "New",
  scheduled: "Scheduled",
  in_progress: "In progress",
  resolved: "Resolved",
};

export default function PortalPage() {
  const router = useRouter();
  const [data, setData] = useState<MeLease | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [error, setError] = useState("");
  const [renewBusy, setRenewBusy] = useState(false);
  const [ticketBusy, setTicketBusy] = useState(false);
  const [ticketMsg, setTicketMsg] = useState("");

  const load = useCallback(async () => {
    try {
      const me = await portalJson<MeLease>("/api/me/lease");
      setData(me);
      setTickets(await portalJson<Ticket[]>("/api/me/maintenance"));
    } catch (err) {
      const status = (err as Error & { status?: number }).status;
      if (status === 401) router.push("/portal/login");
      else setError(err instanceof Error ? err.message : "Failed to load.");
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  async function renew(action: "accept" | "decline") {
    if (action === "decline" && !confirm("Decline the renewal offer? The office will be notified and your home will be listed for its next lease.")) return;
    setRenewBusy(true);
    try {
      setData(
        await portalJson<MeLease>("/api/me/renewal", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ action }),
        })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Renewal action failed.");
    } finally {
      setRenewBusy(false);
    }
  }

  async function submitTicket(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setTicketBusy(true);
    setTicketMsg("");
    const formEl = e.currentTarget;
    try {
      const res = await portalFetch("/api/me/maintenance", {
        method: "POST",
        body: new FormData(formEl),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(typeof body.detail === "string" ? body.detail : "Submit failed");
      formEl.reset();
      setTicketMsg("Request received — the office will schedule it shortly.");
      setTickets(await portalJson<Ticket[]>("/api/me/maintenance"));
    } catch (err) {
      setTicketMsg(err instanceof Error ? err.message : "Submit failed.");
    } finally {
      setTicketBusy(false);
    }
  }

  async function signOut() {
    await portalFetch("/api/auth/logout", { method: "POST" });
    router.push("/portal/login");
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-charcoal-light">
        {error || "Loading your home…"}
      </div>
    );
  }

  const { lease, upcoming_lease: upcoming } = data;

  return (
    <div className="mx-auto max-w-4xl px-4 py-14">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl text-pine-800">Welcome, {data.resident.name.split(" ")[0]}</h1>
          <p className="mt-1 text-charcoal-light">{data.resident.email}</p>
        </div>
        <Button variant="ghost" onClick={signOut}>
          Sign out
        </Button>
      </div>

      {error && (
        <p className="mt-4 text-sm font-semibold text-red-700" role="alert">
          {error}
        </p>
      )}

      {/* Lease */}
      {lease ? (
        <Card className="mt-8">
          <CardContent className="pt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle>
                {lease.unit.floor_plan_name} · Unit {lease.unit.unit_number}
              </CardTitle>
              <Badge variant="brass">{lease.days_to_end} days left on lease</Badge>
            </div>
            <dl className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-charcoal-light">Monthly rent</dt>
                <dd className="mt-1 text-lg font-bold text-pine-800">{usd.format(lease.monthly_rent)}</dd>
              </div>
              <div>
                <dt className="text-charcoal-light">Lease term</dt>
                <dd className="mt-1 font-semibold">
                  {lease.start_date} → {lease.end_date}
                </dd>
              </div>
              <div>
                <dt className="text-charcoal-light">Home</dt>
                <dd className="mt-1 font-semibold">
                  {lease.unit.bedrooms} bed · {lease.unit.bathrooms} bath · {lease.unit.sqft} sqft
                </dd>
              </div>
              <div>
                <dt className="text-charcoal-light">Renewal</dt>
                <dd className="mt-1 font-semibold capitalize">{lease.renewal_status}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      ) : (
        <p className="mt-8 rounded-xl bg-cream-dark p-6">No active lease on file — contact the office at 248-377-2680.</p>
      )}

      {/* Renewal offer */}
      {lease?.renewal_status === "offered" && lease.renewal_offer_rent != null && (
        <Card className="mt-6 border-2 border-brass">
          <CardContent className="pt-6">
            <CardTitle>Your renewal offer</CardTitle>
            <p className="mt-2 text-sm text-charcoal-light">
              Renew for 12 months starting the day after your current lease ends. One click — no paperwork.
            </p>
            <div className="mt-5 flex flex-wrap items-end gap-8">
              <div>
                <p className="text-sm text-charcoal-light">Current rent</p>
                <p className="text-2xl font-bold text-charcoal">{usd.format(lease.monthly_rent)}</p>
              </div>
              <div aria-hidden="true" className="pb-1 text-2xl text-charcoal-light">→</div>
              <div>
                <p className="text-sm text-charcoal-light">Renewal rent</p>
                <p className="text-3xl font-bold text-pine-800">{usd.format(lease.renewal_offer_rent)}</p>
              </div>
            </div>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button variant="brass" size="lg" onClick={() => renew("accept")} disabled={renewBusy}>
                {renewBusy ? "Working…" : "Accept renewal"}
              </Button>
              <Button variant="outline" size="lg" onClick={() => renew("decline")} disabled={renewBusy}>
                Decline
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {lease?.renewal_status === "accepted" && upcoming && (
        <div className="mt-6 rounded-2xl border border-pine-300 bg-pine-100 p-6" role="status">
          <p className="font-display text-xl text-pine-800">Renewal confirmed 🎉</p>
          <p className="mt-2 text-sm text-charcoal">
            Your next lease runs {upcoming.start_date} → {upcoming.end_date} at{" "}
            <strong>{usd.format(upcoming.monthly_rent)}/mo</strong>. A confirmation is on its way to your inbox.
          </p>
        </div>
      )}

      {lease?.renewal_status === "declined" && (
        <div className="mt-6 rounded-2xl bg-cream-dark p-6 text-sm text-charcoal">
          You declined this renewal — the office has been notified. If you change your mind, call 248-377-2680.
        </div>
      )}

      {/* Maintenance */}
      <h2 className="mt-12 font-display text-2xl text-pine-800">Maintenance requests</h2>
      <div className="mt-4 grid gap-8 lg:grid-cols-[1fr_1fr]">
        <form onSubmit={submitTicket} className="rounded-2xl border border-cream-dark bg-white p-6">
          <Label htmlFor="category">Category</Label>
          <Select id="category" name="category" required defaultValue="plumbing">
            <option value="plumbing">Plumbing</option>
            <option value="electrical">Electrical</option>
            <option value="appliance">Appliance</option>
            <option value="hvac">Heating / cooling</option>
            <option value="pest">Pest control</option>
            <option value="other">Other</option>
          </Select>
          <div className="mt-4">
            <Label htmlFor="description">What&apos;s wrong?</Label>
            <Textarea id="description" name="description" required minLength={5} maxLength={4000} />
          </div>
          <div className="mt-4">
            <Label htmlFor="photos">Photos (up to 5, optional)</Label>
            <input
              id="photos"
              name="photos"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              multiple
              className="w-full text-sm"
            />
          </div>
          {ticketMsg && (
            <p className="mt-4 text-sm font-semibold text-pine-700" role="status">
              {ticketMsg}
            </p>
          )}
          <Button type="submit" className="mt-5" disabled={ticketBusy}>
            {ticketBusy ? "Submitting…" : "Submit request"}
          </Button>
        </form>

        <div className="space-y-3">
          {tickets.length === 0 && <p className="text-sm text-charcoal-light">No requests yet.</p>}
          {tickets.map((t) => (
            <div key={t.id} className="rounded-xl border border-cream-dark bg-white p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="font-semibold capitalize">{t.category}</p>
                <Badge variant={t.status === "resolved" ? "available" : "waitlist"}>
                  {STATUS_LABEL[t.status] ?? t.status}
                </Badge>
              </div>
              <p className="mt-1 text-sm text-charcoal-light">{t.description}</p>
              <p className="mt-2 text-xs text-charcoal-light">
                #{t.id} · {new Date(t.created_at).toLocaleDateString()}
                {t.photo_count > 0 && ` · ${t.photo_count} photo${t.photo_count > 1 ? "s" : ""}`}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
