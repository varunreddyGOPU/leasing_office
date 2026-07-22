import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

import { ChatWidget } from "@/components/chat-widget";

export const metadata: Metadata = {
  title: "Auburn Ridge Townhomes | Auburn Hills, MI",
  description:
    "1, 2 & 3 bedroom townhomes in Auburn Hills, MI — private entry, in-home washer & dryer, minutes from Oakland University. Call 248-377-2680.",
};

const nav = [
  { href: "/", label: "Home" },
  { href: "/floor-plans", label: "Floor Plans" },
  { href: "/estimate", label: "Instant Estimate" },
  { href: "/news", label: "Local News" },
  { href: "/contact", label: "Contact" },
  { href: "/portal", label: "Resident Portal" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-50 bg-pine-900 text-cream shadow-md">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="font-display text-lg tracking-wide">
              Auburn Ridge Townhomes
            </Link>
            <nav aria-label="Main" className="order-3 -mx-4 w-screen overflow-x-auto px-4 sm:order-2 sm:mx-0 sm:w-auto sm:flex-1">
              <ul className="flex gap-5 whitespace-nowrap text-sm">
                {nav.map((item) => (
                  <li key={item.href}>
                    <Link href={item.href} className="text-cream/85 hover:text-cream">
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <a
              href="tel:248-377-2680"
              className="order-2 ml-auto rounded-full bg-brass px-4 py-1.5 text-sm font-semibold text-charcoal hover:opacity-90 sm:order-3 sm:ml-0"
            >
              248-377-2680
            </a>
          </div>
        </header>
        <main>{children}</main>
        <ChatWidget />
        <footer className="mt-16 bg-pine-900 text-cream">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 text-sm sm:grid-cols-3">
            <div>
              <p className="font-display text-base">Auburn Ridge Townhomes</p>
              <p className="mt-2 text-cream/80">
                2610 Davison Ave
                <br />
                Auburn Hills, MI 48326
              </p>
            </div>
            <div>
              <p className="font-semibold">Leasing Office</p>
              <p className="mt-2 text-cream/80">Mon–Fri 9:30am–5:00pm</p>
              <p className="mt-1">
                <a href="tel:248-377-2680" className="underline">
                  248-377-2680
                </a>
              </p>
              <p className="mt-1">
                <a href="mailto:Auburnridge@633pros.com" className="underline">
                  Auburnridge@633pros.com
                </a>
              </p>
            </div>
            <div className="flex items-start gap-2 text-cream/80">
              <span aria-hidden="true" className="text-2xl leading-none">
                ⌂
              </span>
              <p>
                Equal Housing Opportunity. Pricing shown on this site is sample data and
                estimates only — the leasing office confirms all final pricing.
              </p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
