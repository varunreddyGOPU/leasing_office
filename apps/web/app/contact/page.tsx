import { ContactForm } from "@/components/contact-form";

export const metadata = { title: "Contact & Tours | Auburn Ridge Townhomes" };

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16">
      <h1 className="font-display text-4xl text-pine-800">Schedule a Tour</h1>
      <p className="mt-3 max-w-2xl text-charcoal-light">
        Come see Auburn Ridge in person. Tell us when works and the office will confirm your
        tour.
      </p>

      <div className="mt-10 grid gap-10 lg:grid-cols-[1fr_360px]">
        <ContactForm />

        <aside className="space-y-6">
          <div className="rounded-2xl bg-pine-800 p-6 text-cream">
            <h2 className="font-display text-xl">Leasing Office</h2>
            <p className="mt-3 text-sm text-cream/85">
              2610 Davison Ave
              <br />
              Auburn Hills, MI 48326
            </p>
            <p className="mt-3 text-sm text-cream/85">Mon–Fri 9:30am–5:00pm</p>
            <p className="mt-3 text-sm">
              <a href="tel:248-377-2680" className="font-semibold text-brass">
                248-377-2680
              </a>
              <br />
              <a href="mailto:Auburnridge@633pros.com" className="underline text-cream/85">
                Auburnridge@633pros.com
              </a>
            </p>
          </div>
          <div
            aria-hidden="true"
            className="flex h-56 items-center justify-center rounded-2xl bg-gradient-to-br from-pine-100 to-pine-300 text-sm text-pine-800"
          >
            Map placeholder — 2610 Davison Ave
          </div>
        </aside>
      </div>
    </div>
  );
}
