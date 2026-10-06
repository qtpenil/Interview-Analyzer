"use client"

import { Progress as ProgressPrimitive } from "@base-ui/react/progress"

import { cn } from "@/lib/utils"

function Progress({
  className,
  children,
  value,
  shimmer = false,
  ...props
}: ProgressPrimitive.Root.Props & { shimmer?: boolean }) {
  return (
    <ProgressPrimitive.Root
      value={value}
      data-slot="progress"
      className={cn("flex flex-wrap gap-3", className)}
      {...props}
    >
      {children}
      <ProgressTrack>
        <ProgressIndicator shimmer={shimmer} />
      </ProgressTrack>
    </ProgressPrimitive.Root>
  )
}

function ProgressTrack({ className, ...props }: ProgressPrimitive.Track.Props) {
  return (
    <ProgressPrimitive.Track
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full bg-muted/50",
        className
      )}
      data-slot="progress-track"
      {...props}
    />
  )
}

function ProgressIndicator({
  className,
  shimmer = false,
  ...props
}: ProgressPrimitive.Indicator.Props & { shimmer?: boolean }) {
  return (
    <ProgressPrimitive.Indicator
      data-slot="progress-indicator"
      className={cn(
        "relative h-full overflow-hidden rounded-full bg-gradient-to-r from-[var(--btn-primary-from)] to-[var(--btn-primary-to)] transition-[width] duration-300 ease-out",
        className
      )}
      {...props}
    >
      {shimmer && (
        <span
          className="pointer-events-none absolute inset-y-0 w-1/3 -translate-x-full skew-x-[-20deg] bg-gradient-to-r from-transparent via-white/40 to-transparent tracker-sheen"
          aria-hidden="true"
        />
      )}
    </ProgressPrimitive.Indicator>
  )
}

function ProgressLabel({ className, ...props }: ProgressPrimitive.Label.Props) {
  return (
    <ProgressPrimitive.Label
      className={cn("text-sm font-medium", className)}
      data-slot="progress-label"
      {...props}
    />
  )
}

function ProgressValue({ className, ...props }: ProgressPrimitive.Value.Props) {
  return (
    <ProgressPrimitive.Value
      className={cn(
        "ml-auto text-sm text-muted-foreground tabular-nums",
        className
      )}
      data-slot="progress-value"
      {...props}
    />
  )
}

export {
  Progress,
  ProgressTrack,
  ProgressIndicator,
  ProgressLabel,
  ProgressValue,
}
