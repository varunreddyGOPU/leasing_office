import * as React from "react";

import { cn } from "@/lib/utils";

const variants = {
  available: "bg-pine-100 text-pine-800",
  waitlist: "bg-cream-dark text-charcoal-light",
  brass: "bg-brass/15 text-brass",
} as const;

export function Badge({
  variant = "available",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
