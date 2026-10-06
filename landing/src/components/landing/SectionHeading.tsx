import type { ReactNode } from "react";
import Reveal from "./Reveal";

type SectionHeadingProps = {
  eyebrow: string;
  title: ReactNode;
  description?: ReactNode;
  align?: "center" | "left";
  className?: string;
};

export default function SectionHeading({
  eyebrow,
  title,
  description,
  align = "center",
  className = "",
}: SectionHeadingProps) {
  const alignment =
    align === "center"
      ? "mx-auto text-center items-center"
      : "items-start text-left";

  return (
    <Reveal className={`flex max-w-2xl flex-col ${alignment} ${className}`}>
      <span className="inline-flex items-center gap-2 rounded-full border border-accent-soft-border bg-accent-soft px-3 py-1 text-xs font-bold uppercase tracking-widest text-secondary">
        {eyebrow}
      </span>
      <h2 className="mt-5 text-3xl font-extrabold tracking-tight text-primary sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base leading-7 text-secondary">{description}</p>
      )}
    </Reveal>
  );
}
