import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const amenities = [
  { title: "Private Entry", body: "Every townhome has its own front door — no shared hallways." },
  { title: "In-Home Washer & Dryer", body: "Full-size laundry in every home. No laundromat trips." },
  { title: "Patio or Balcony", body: "Private outdoor space with every floor plan." },
  { title: "Electric Fireplace", body: "A warm centerpiece in every living room." },
  { title: "Seasonal Pool & Sundeck", body: "Resort-style summers, steps from your door." },
  { title: "24-Hour Fitness Center", body: "Newly renovated and always open." },
  { title: "FREE Assigned Carports", body: "Covered parking included with every home." },
  { title: "Pet Friendly", body: "Cats and dogs welcome — bring the whole family." },
];

const proximity = [
  { place: "Oakland University", time: "5 min" },
  { place: "Village of Rochester Hills", time: "10 min" },
  { place: "Trader Joe's & Whole Foods", time: "<10 min" },
  { place: "Chrysler · UWM · GM · Troy", time: "easy commute" },
  { place: "Top Golf", time: "nearby" },
  { place: "Paint Creek Trail", time: "nearby" },
  { place: "Meadowbrook Theater", time: "nearby" },
  { place: "Great Lakes Crossing", time: "nearby" },
  { place: "Pine Knob", time: "nearby" },
];

const testimonials = [
  {
    quote:
      "The private entry and in-home laundry sold us instantly. It feels like a house, not an apartment.",
    name: "Current resident",
  },
  {
    quote:
      "Five minutes to campus and a quiet street to come home to. Best decision of my grad program.",
    name: "OU graduate student",
  },
  {
    quote:
      "The free carport got me through a Michigan winter without ever scraping ice. Worth it alone.",
    name: "Two-year resident",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-pine-800 text-cream">
        <div
          aria-hidden="true"
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(176,141,63,0.25),transparent_55%)]"
        />
        <div className="relative mx-auto max-w-6xl px-4 py-28 text-center">
          <p className="text-sm uppercase tracking-[0.3em] text-brass">
            Auburn Hills, Michigan
          </p>
          <h1 className="mt-4 font-display text-5xl tracking-wide sm:text-6xl">Welcome Home</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-cream/90">
            1, 2 &amp; 3 bedroom townhomes in a quiet, tree-lined community — private entry,
            in-home washer &amp; dryer, and five minutes from Oakland University.
          </p>
          <div className="mt-10 flex flex-wrap justify-center gap-4">
            <Link href="/estimate" className={buttonVariants({ variant: "brass", size: "lg" })}>
              Get an Instant Estimate
            </Link>
            <Link
              href="/floor-plans"
              className={cn(
                buttonVariants({ variant: "outline", size: "lg" }),
                "border-cream text-cream hover:bg-cream hover:text-pine-800"
              )}
            >
              View Floor Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Location proximity strip */}
      <section aria-label="Nearby places" className="border-b border-cream-dark bg-white">
        <div className="mx-auto max-w-6xl overflow-x-auto px-4">
          <ul className="flex gap-3 whitespace-nowrap py-4">
            {proximity.map((p) => (
              <li
                key={p.place}
                className="rounded-full border border-cream-dark bg-cream px-4 py-1.5 text-sm"
              >
                <span className="font-semibold text-pine-800">{p.place}</span>
                <span className="text-charcoal-light"> · {p.time}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Amenities */}
      <section className="mx-auto max-w-6xl px-4 py-20">
        <h2 className="font-display text-3xl text-pine-800 sm:text-4xl">Life at Auburn Ridge</h2>
        <p className="mt-3 max-w-2xl text-charcoal-light">
          Townhome living with the comforts of a house and the ease of a community.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {amenities.map((a) => (
            <Card key={a.title}>
              <CardContent className="pt-6">
                <div
                  aria-hidden="true"
                  className="mb-4 h-24 rounded-xl bg-gradient-to-br from-pine-100 to-pine-300"
                />
                <CardTitle className="text-lg">{a.title}</CardTitle>
                <p className="mt-2 text-sm text-charcoal-light">{a.body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-pine-700 text-cream">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="font-display text-3xl">What residents say</h2>
          <p className="mt-1 text-sm text-cream/60">(sample quotes — replace with real resident testimonials)</p>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {testimonials.map((t) => (
              <blockquote key={t.quote} className="rounded-2xl bg-pine-800/60 p-6">
                <p className="text-cream/95">“{t.quote}”</p>
                <footer className="mt-4 text-sm text-brass">— {t.name}</footer>
              </blockquote>
            ))}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="mx-auto max-w-6xl px-4 py-20 text-center">
        <h2 className="font-display text-3xl text-pine-800">
          See what your monthly rent would look like
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-charcoal-light">
          Pick a floor plan, move-in date, and lease term — get an itemized estimate in under a
          minute.
        </p>
        <Link
          href="/estimate"
          className={cn(buttonVariants({ variant: "primary", size: "lg" }), "mt-8")}
        >
          Get an Instant Estimate
        </Link>
      </section>
    </>
  );
}
