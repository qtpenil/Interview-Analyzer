import Link from "next/link";
import type { ReactNode } from "react";
import {
  TrendingDown,
  TrendingUp,
  Trophy,
  type LucideIcon,
} from "lucide-react";
import { GlassCard } from "@/components/landing/MockPanels";
import { ScoreRing } from "@/components/common/ScoreRing";

export type TopicHighlightVariant = "strongest" | "weakest" | "best";

interface TopicHighlightCardProps {
  topic: string;
  averageScore: string | null;
  question: string | null;
  variant: TopicHighlightVariant;
  href: string;
  scoreLabel?: string;
  ringSize?: number;
  ringStroke?: number;
  action?: ReactNode;
  children?: ReactNode;
}

const VARIANT_STYLES: Record<
  TopicHighlightVariant,
  {
    label: string;
    badgeClassName: string;
    hoverClassName: string;
    trackColor: string;
    zoneClassName: string;
    dividerClassName: string;
    scoreValueClassName?: string;
    scoreStrokeColor?: string;
    Icon: LucideIcon;
  }
> = {
  strongest: {
    label: "Strongest Topic",
    badgeClassName: "border border-success-border bg-success-soft text-success",
    hoverClassName: "hover:border-accent-soft-border",
    trackColor: "var(--text-muted)",
    zoneClassName: "bg-accent",
    dividerClassName: "bg-white/70",
    scoreValueClassName: "text-white",
    scoreStrokeColor: "white",
    Icon: TrendingUp,
  },
  weakest: {
    label: "Needs Focus",
    badgeClassName: "border border-warning-border bg-warning-soft text-warning",
    hoverClassName: "hover:border-warning-border/50",
    trackColor: "var(--text-muted)",
    zoneClassName: "bg-accent",
    dividerClassName: "bg-white/70",
    scoreValueClassName: "text-white",
    scoreStrokeColor: "white",
    Icon: TrendingDown,
  },
  best: {
    label: "Best Overall Interview",
    badgeClassName:
      "border border-accent-soft-border bg-accent-soft text-secondary",
    hoverClassName: "hover:border-accent-soft-border",
    trackColor: "var(--text-muted)",
    zoneClassName: "",
    dividerClassName: "bg-accent",
    scoreStrokeColor: "var(--accent)",
    Icon: Trophy,
  },
};

export function TopicHighlightCard({
  topic,
  averageScore,
  question,
  variant,
  href,
  scoreLabel,
  ringSize = 76,
  ringStroke = 6,
  action,
  children,
}: TopicHighlightCardProps) {
  const {
    label,
    badgeClassName,
    hoverClassName,
    trackColor,
    zoneClassName,
    dividerClassName,
    scoreValueClassName,
    scoreStrokeColor,
    Icon,
  } = VARIANT_STYLES[variant];

  return (
    <Link
      href={href}
      className="group block focus:outline-none focus-visible:ring-4 focus-visible:ring-[var(--ring)] rounded-3xl"
    >
      <GlassCard
        className={`overflow-hidden transition-all duration-200 border-default ${hoverClassName} hover:shadow-[0_0_25px_-5px_var(--shadow-glow)] h-full`}
      >
        <div className="flex h-full flex-col items-stretch md:flex-row">
          {/* Left: title + badge, description, extra content */}
          <div className="min-w-0 flex-1 px-4 py-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <h2 className="text-xl sm:text-2xl font-bold text-primary group-hover:text-secondary transition-colors leading-tight">
                {topic}
              </h2>
              <span
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${badgeClassName}`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </span>
            </div>
            {question && (
              <p className="mt-4 line-clamp-2 overflow-hidden text-sm leading-snug text-secondary/70">
                {question}
              </p>
            )}
            {children}
          </div>
          {/* Right: square-ish score zone. The divider is inset by a
              percentage of the zone height, so its margin scales with the
              card size and feels identical on every card. */}
          <div className={`relative flex shrink-0 flex-col items-center justify-center gap-3 border-t border-accent px-5 py-4 md:aspect-square md:min-h-[92px] md:border-t-0 md:py-0 md:pl-4 md:pr-5 ${zoneClassName}`}>
            <span
              aria-hidden="true"
              className={`absolute bottom-[10%] left-0 top-[10%] hidden w-px md:block ${dividerClassName}`}
            />
            <ScoreRing
              value={parseFloat(averageScore || "0")}
              size={ringSize}
              stroke={ringStroke}
              label={scoreLabel}
              strokeColor={scoreStrokeColor || "var(--accent)"}
              trackColor={trackColor}
              trackOpacity={0.3}
              valueClassName={scoreValueClassName}
            />
            {action}
          </div>
        </div>
      </GlassCard>
    </Link>
  );
}
