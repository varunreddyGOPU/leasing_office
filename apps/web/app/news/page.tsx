import type { NewsItem } from "@auburn-ridge/shared-types";

import { apiGet } from "@/lib/api";

export const metadata = { title: "Local News | Auburn Ridge Townhomes" };
export const revalidate = 10800; // 3 hours (ISR)

const CATEGORY_LABELS: Record<string, string> = {
  community: "Community",
  roads_transit: "Roads & Transit",
  oakland_university: "Oakland University",
  events: "Events",
  safety: "Safety",
};

export default async function NewsPage() {
  const items = await apiGet<NewsItem[]>("/api/news", 10800);

  const grouped = new Map<string, NewsItem[]>();
  for (const item of items ?? []) {
    const key = CATEGORY_LABELS[item.category] ?? "Community";
    grouped.set(key, [...(grouped.get(key) ?? []), item]);
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-16">
      <h1 className="font-display text-4xl text-pine-800">Around Auburn Hills</h1>
      <p className="mt-3 text-charcoal-light">
        Local headlines for our neighborhood — ZIP codes 48326, 48307, 48309 &amp; 48342. Links
        open the original source.
      </p>

      {!items || items.length === 0 ? (
        <p className="mt-12 rounded-xl bg-cream-dark p-6 text-charcoal-light">
          No local news right now — check back soon.
        </p>
      ) : (
        Array.from(grouped.entries()).map(([category, list]) => (
          <section key={category} className="mt-12">
            <h2 className="border-b-2 border-brass pb-2 font-display text-2xl text-pine-800">
              {category}
            </h2>
            <ul className="mt-4 space-y-4">
              {list.map((item) => (
                <li key={item.id}>
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="group block rounded-xl border border-cream-dark bg-white p-5 transition-shadow hover:shadow-md"
                  >
                    <p className="font-semibold text-charcoal group-hover:text-pine-700">
                      {item.title}
                      <span aria-hidden="true"> ↗</span>
                    </p>
                    <p className="mt-1 text-sm text-charcoal-light">
                      {item.source ?? "Source"}
                      {item.published_at &&
                        ` · ${new Date(item.published_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}`}
                      {" · ZIP "}
                      {item.zip}
                    </p>
                  </a>
                </li>
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  );
}
