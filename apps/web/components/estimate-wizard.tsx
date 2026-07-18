"use client";

import { useState } from "react";
import type { EstimateResponse, FloorPlan, LeaseTermMonths } from "@auburn-ridge/shared-types";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Input, Label, Select } from "@/components/ui/input";
import { cn, usd } from "@/lib/utils";

const STEPS = ["Floor plan", "Move-in & term", "Options", "Your details"] as const;
const TERMS: LeaseTermMonths[] = [6, 9, 12, 15];

const SAVINGS = [
  { item: "In-home washer & dryer", value: "saves ~$50/mo vs. laundromat" },
  { item: "FREE assigned carport", value: "covered parking, $0" },
  { item: "24-hr fitness center", value: "replaces a ~$30/mo gym" },
  { item: "Seasonal pool & sundeck", value: "included" },
  { item: "Private entry & patio/balcony", value: "included" },
];

interface FormState {
  planId?: number;
  moveIn: string;
  term: LeaseTermMonths;
  petType: "none" | "cat" | "dog";
  petCount: number;
  carports: number;
  furnished: boolean;
  name: string;
  email: string;
  phone: string;
}

export function EstimateWizard({
  plans,
  initialPlanId,
}: {
  plans: FloorPlan[];
  initialPlanId?: number;
}) {
  const validInitial = plans.some((p) => p.id === initialPlanId) ? initialPlanId : undefined;
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<FormState>({
    planId: validInitial,
    moveIn: "",
    term: 12,
    petType: "none",
    petCount: 1,
    carports: 1,
    furnished: false,
    name: "",
    email: "",
    phone: "",
  });
  const [result, setResult] = useState<EstimateResponse | null>(null);
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);

  const patch = (p: Partial<FormState>) => setForm((f) => ({ ...f, ...p }));
  const today = new Date().toISOString().slice(0, 10);

  const stepValid =
    (step === 0 && form.planId !== undefined) ||
    (step === 1 && form.moveIn >= today) ||
    step === 2 ||
    (step === 3 && /.+@.+\..+/.test(form.email));

  async function submit() {
    setSending(true);
    setError("");
    try {
      const res = await fetch("/api/estimate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          floor_plan_id: form.planId,
          move_in_date: form.moveIn,
          lease_term_months: form.term,
          pets:
            form.petType === "none" ? [] : [{ type: form.petType, count: form.petCount }],
          carports: form.carports,
          furnished: form.furnished,
          email: form.email,
          name: form.name || null,
          phone: form.phone || null,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : body.detail?.[0]?.msg ?? "Could not compute your estimate."
        );
      }
      setResult(body as EstimateResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong — please call us.");
    } finally {
      setSending(false);
    }
  }

  if (result) {
    return <Results result={result} onRestart={() => { setResult(null); setStep(0); }} />;
  }

  return (
    <div className="mt-10 max-w-3xl">
      {/* Step indicator */}
      <ol className="flex flex-wrap gap-2" aria-label="Estimate steps">
        {STEPS.map((label, i) => (
          <li
            key={label}
            aria-current={i === step ? "step" : undefined}
            className={cn(
              "rounded-full px-4 py-1.5 text-sm",
              i === step
                ? "bg-pine-700 font-semibold text-cream"
                : i < step
                  ? "bg-pine-100 text-pine-800"
                  : "bg-cream-dark text-charcoal-light"
            )}
          >
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      <Card className="mt-6">
        <CardContent className="pt-6">
          {step === 0 && (
            <fieldset>
              <legend className="font-display text-2xl text-pine-800">
                Which floor plan fits?
              </legend>
              <div className="mt-5 grid gap-4 sm:grid-cols-3">
                {plans.map((plan) => (
                  <button
                    key={plan.id}
                    type="button"
                    onClick={() => patch({ planId: plan.id })}
                    aria-pressed={form.planId === plan.id}
                    className={cn(
                      "rounded-xl border-2 p-4 text-left transition-colors",
                      form.planId === plan.id
                        ? "border-pine-700 bg-pine-100"
                        : "border-cream-dark bg-white hover:border-pine-300"
                    )}
                  >
                    <p className="font-display text-lg text-pine-800">{plan.name}</p>
                    <p className="mt-1 text-sm text-charcoal">
                      {plan.bedrooms} bed · {plan.bathrooms} bath · ~{plan.sqft} sqft
                    </p>
                    <p className="mt-2 font-semibold text-charcoal">
                      from {usd.format(plan.current_asking_rent ?? plan.base_rent)}/mo
                    </p>
                  </button>
                ))}
              </div>
            </fieldset>
          )}

          {step === 1 && (
            <div>
              <h2 className="font-display text-2xl text-pine-800">When and for how long?</h2>
              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <div>
                  <Label htmlFor="moveIn">Move-in date *</Label>
                  <Input
                    id="moveIn"
                    type="date"
                    min={today}
                    value={form.moveIn}
                    onChange={(e) => patch({ moveIn: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="term">Lease term</Label>
                  <Select
                    id="term"
                    value={form.term}
                    onChange={(e) => patch({ term: Number(e.target.value) as LeaseTermMonths })}
                  >
                    {TERMS.map((t) => (
                      <option key={t} value={t}>
                        {t} months{t === 12 ? " (standard)" : ""}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="font-display text-2xl text-pine-800">A few options</h2>
              <div className="mt-5 grid gap-5 sm:grid-cols-3">
                <div>
                  <Label htmlFor="petType">Pets</Label>
                  <Select
                    id="petType"
                    value={form.petType}
                    onChange={(e) =>
                      patch({ petType: e.target.value as FormState["petType"] })
                    }
                  >
                    <option value="none">No pets</option>
                    <option value="cat">Cat(s)</option>
                    <option value="dog">Dog(s)</option>
                  </Select>
                </div>
                {form.petType !== "none" && (
                  <div>
                    <Label htmlFor="petCount">How many? (max 2)</Label>
                    <Select
                      id="petCount"
                      value={form.petCount}
                      onChange={(e) => patch({ petCount: Number(e.target.value) })}
                    >
                      <option value={1}>1</option>
                      <option value={2}>2</option>
                    </Select>
                  </div>
                )}
                <div>
                  <Label htmlFor="carports">Carports (first one FREE)</Label>
                  <Select
                    id="carports"
                    value={form.carports}
                    onChange={(e) => patch({ carports: Number(e.target.value) })}
                  >
                    <option value={1}>1 — included</option>
                    <option value={2}>2</option>
                    <option value={0}>None</option>
                  </Select>
                </div>
              </div>
              <label className="mt-6 flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={form.furnished}
                  onChange={(e) => patch({ furnished: e.target.checked })}
                  className="h-5 w-5 accent-pine-700"
                />
                <span>
                  Furnished / corporate rental{" "}
                  <span className="text-sm text-charcoal-light">(+$300/mo sample premium)</span>
                </span>
              </label>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="font-display text-2xl text-pine-800">
                Where should we send your breakdown?
              </h2>
              <p className="mt-2 text-sm text-charcoal-light">
                Email required to view the full itemized estimate. The office may follow up
                about availability.
              </p>
              <div className="mt-5 grid gap-5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <Label htmlFor="est-email">Email *</Label>
                  <Input
                    id="est-email"
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => patch({ email: e.target.value })}
                    autoComplete="email"
                  />
                </div>
                <div>
                  <Label htmlFor="est-name">Name</Label>
                  <Input
                    id="est-name"
                    value={form.name}
                    onChange={(e) => patch({ name: e.target.value })}
                    autoComplete="name"
                  />
                </div>
                <div>
                  <Label htmlFor="est-phone">Phone</Label>
                  <Input
                    id="est-phone"
                    type="tel"
                    value={form.phone}
                    onChange={(e) => patch({ phone: e.target.value })}
                    autoComplete="tel"
                  />
                </div>
              </div>
            </div>
          )}

          {error && (
            <p className="mt-5 text-sm font-semibold text-red-700" role="alert">
              {error}
            </p>
          )}

          <div className="mt-8 flex justify-between">
            <Button
              variant="ghost"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
            >
              ← Back
            </Button>
            {step < STEPS.length - 1 ? (
              <Button onClick={() => setStep((s) => s + 1)} disabled={!stepValid}>
                Continue →
              </Button>
            ) : (
              <Button variant="brass" onClick={submit} disabled={!stepValid || sending}>
                {sending ? "Calculating…" : "Show my estimate"}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Results({ result, onRestart }: { result: EstimateResponse; onRestart: () => void }) {
  return (
    <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_340px]">
      <div>
        <Card>
          <CardContent className="pt-6">
            <CardTitle className="text-2xl">
              {result.floor_plan_name} — your estimate
            </CardTitle>
            <p className="mt-4 text-4xl font-bold text-pine-800">
              {usd.format(result.monthly_estimate)}
              <span className="text-base font-normal text-charcoal-light">/month</span>
            </p>

            <h3 className="mt-8 font-semibold text-charcoal">Monthly breakdown</h3>
            <table className="mt-2 w-full text-sm">
              <tbody>
                {result.monthly_breakdown.map((line) => (
                  <tr key={line.label} className="border-b border-cream-dark">
                    <td className="py-2 pr-4">{line.label}</td>
                    <td className="py-2 text-right font-semibold">
                      {line.amount === 0 ? "FREE" : usd.format(line.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h3 className="mt-8 font-semibold text-charcoal">
              Total move-in cost: {usd.format(result.move_in_total)}
            </h3>
            <table className="mt-2 w-full text-sm">
              <tbody>
                {result.move_in_breakdown.map((line) => (
                  <tr key={line.label} className="border-b border-cream-dark">
                    <td className="py-2 pr-4">{line.label}</td>
                    <td className="py-2 text-right font-semibold">{usd.format(line.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="mt-6 rounded-lg bg-cream p-4 text-sm text-charcoal-light">
              {result.disclaimer}
            </p>
            <p className="mt-3 text-sm font-semibold text-pine-700" role="status">
              Saved — the office will follow up.
            </p>

            <div className="mt-6 flex gap-3">
              <Button variant="outline" onClick={onRestart}>
                Start over
              </Button>
              <a
                href="/contact"
                className="inline-flex items-center rounded-full bg-pine-700 px-6 py-2.5 text-sm font-semibold text-cream hover:bg-pine-800"
              >
                Schedule a tour
              </a>
            </div>
          </CardContent>
        </Card>
      </div>

      <aside className="rounded-2xl bg-pine-800 p-6 text-cream lg:sticky lg:top-24 lg:self-start">
        <h3 className="font-display text-xl">What&apos;s included — and what it saves you</h3>
        <ul className="mt-4 space-y-3 text-sm">
          {SAVINGS.map((s) => (
            <li key={s.item} className="flex justify-between gap-3 border-b border-cream/15 pb-2">
              <span>{s.item}</span>
              <span className="text-right text-brass">{s.value}</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-xs text-cream/70">
          Estimated $80+/mo of built-in value compared to renting these separately.
        </p>
      </aside>
    </div>
  );
}
