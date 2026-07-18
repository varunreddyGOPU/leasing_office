import type { FloorPlan } from "@auburn-ridge/shared-types";

import { EstimateWizard } from "@/components/estimate-wizard";
import { apiGet } from "@/lib/api";

export const metadata = { title: "Instant Estimate | Auburn Ridge Townhomes" };
export const revalidate = 300;

export default async function EstimatePage({
  searchParams,
}: {
  searchParams: { plan?: string };
}) {
  const plans = await apiGet<FloorPlan[]>("/api/floor-plans", 300);

  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <h1 className="font-display text-4xl text-pine-800">Instant Estimate</h1>
      <p className="mt-3 max-w-2xl text-charcoal-light">
        Four quick steps to an itemized monthly estimate and total move-in cost. Estimates use
        current sample pricing — the office confirms final numbers.
      </p>

      {!plans ? (
        <p className="mt-12 rounded-xl bg-cream-dark p-6 text-charcoal-light">
          The estimate tool is temporarily unavailable — please call{" "}
          <a className="underline" href="tel:248-377-2680">
            248-377-2680
          </a>
          .
        </p>
      ) : (
        <EstimateWizard
          plans={plans}
          initialPlanId={searchParams.plan ? Number(searchParams.plan) : undefined}
        />
      )}
    </div>
  );
}
