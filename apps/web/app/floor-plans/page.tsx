import Link from "next/link";
import type { FloorPlan } from "@auburn-ridge/shared-types";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api";
import { usd } from "@/lib/utils";

export const metadata = { title: "Floor Plans | Auburn Ridge Townhomes" };
export const revalidate = 300;

export default async function FloorPlansPage() {
  const plans = await apiGet<FloorPlan[]>("/api/floor-plans", 300);

  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <h1 className="font-display text-4xl text-pine-800">Floor Plans</h1>
      <p className="mt-3 max-w-2xl text-charcoal-light">
        Every home includes private entry, in-home washer &amp; dryer, patio or balcony, and an
        electric fireplace. Pricing below is <strong>sample data</strong> — editable by the
        office and always confirmed before you sign.
      </p>

      {!plans ? (
        <p className="mt-12 rounded-xl bg-cream-dark p-6 text-charcoal-light">
          Floor plans are temporarily unavailable — please call the office at{" "}
          <a className="underline" href="tel:248-377-2680">
            248-377-2680
          </a>
          .
        </p>
      ) : (
        <div className="mt-10 grid gap-8 md:grid-cols-3">
          {plans.map((plan) => (
            <Card key={plan.id} className="flex flex-col">
              <div
                aria-hidden="true"
                className="h-44 rounded-t-2xl bg-gradient-to-br from-pine-300 via-pine-100 to-cream-dark"
              />
              <CardContent className="flex flex-1 flex-col pt-5">
                <div className="flex items-center justify-between">
                  <CardTitle>{plan.name}</CardTitle>
                  {plan.available_units > 0 ? (
                    <Badge variant="available">
                      {plan.available_units} available
                    </Badge>
                  ) : (
                    <Badge variant="waitlist">Join waitlist</Badge>
                  )}
                </div>
                <p className="mt-2 text-sm font-semibold text-charcoal">
                  {plan.bedrooms} bed · {plan.bathrooms} bath · ~{plan.sqft.toLocaleString()} sqft
                </p>
                <p className="mt-3 flex-1 text-sm text-charcoal-light">{plan.description}</p>
                <p className="mt-5 text-2xl font-bold text-pine-800">
                  from {usd.format(plan.current_asking_rent ?? plan.base_rent)}
                  <span className="text-sm font-normal text-charcoal-light">/mo</span>
                </p>
                <Link
                  href={`/estimate?plan=${plan.id}`}
                  className={buttonVariants({ variant: "primary", size: "md" }) + " mt-5"}
                >
                  Estimate this unit
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
