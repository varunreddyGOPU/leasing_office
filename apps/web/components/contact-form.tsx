"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input, Label, Select, Textarea } from "@/components/ui/input";

export function ContactForm() {
  const [status, setStatus] = useState<"idle" | "sending" | "done" | "error">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("sending");
    const form = new FormData(e.currentTarget);
    const date = form.get("tour_date") as string;
    const time = form.get("tour_time") as string;
    try {
      const res = await fetch("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.get("name"),
          email: form.get("email") || null,
          phone: form.get("phone") || null,
          desired_bedrooms: form.get("bedrooms") ? Number(form.get("bedrooms")) : null,
          preferred_tour_at: date ? `${date}T${time || "10:00"}:00` : null,
          notes: form.get("notes") || null,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail?.[0]?.msg ?? body.detail ?? "Request failed");
      setMessage(body.message);
      setStatus("done");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Something went wrong — please call us.");
      setStatus("error");
    }
  }

  if (status === "done") {
    return (
      <div className="rounded-2xl border border-pine-300 bg-pine-100 p-8" role="status">
        <h2 className="font-display text-2xl text-pine-800">Tour request received</h2>
        <p className="mt-2 text-charcoal">{message}</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="rounded-2xl border border-cream-dark bg-white p-8">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label htmlFor="name">Full name *</Label>
          <Input id="name" name="name" required maxLength={120} autoComplete="name" />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" name="email" type="email" autoComplete="email" />
        </div>
        <div>
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" name="phone" type="tel" autoComplete="tel" />
        </div>
        <div>
          <Label htmlFor="tour_date">Preferred date</Label>
          <Input
            id="tour_date"
            name="tour_date"
            type="date"
            min={new Date().toISOString().slice(0, 10)}
          />
        </div>
        <div>
          <Label htmlFor="tour_time">Preferred time (office: 9:30–5, Mon–Fri)</Label>
          <Input id="tour_time" name="tour_time" type="time" min="09:30" max="17:00" />
        </div>
        <div>
          <Label htmlFor="bedrooms">Bedrooms</Label>
          <Select id="bedrooms" name="bedrooms" defaultValue="">
            <option value="">No preference</option>
            <option value="1">1 bedroom</option>
            <option value="2">2 bedrooms</option>
            <option value="3">3 bedrooms</option>
          </Select>
        </div>
        <div className="sm:col-span-2">
          <Label htmlFor="notes">Anything else?</Label>
          <Textarea id="notes" name="notes" maxLength={2000} placeholder="Pets, move-in timing, questions…" />
        </div>
      </div>
      <p className="mt-4 text-xs text-charcoal-light">
        Provide an email or phone number so the office can reach you.
      </p>
      {status === "error" && (
        <p className="mt-3 text-sm font-semibold text-red-700" role="alert">
          {message}
        </p>
      )}
      <Button type="submit" size="lg" className="mt-6" disabled={status === "sending"}>
        {status === "sending" ? "Sending…" : "Request a Tour"}
      </Button>
    </form>
  );
}
