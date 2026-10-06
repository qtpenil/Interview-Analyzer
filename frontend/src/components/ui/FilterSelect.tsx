"use client";

import * as React from "react";
import { Select } from "@base-ui/react/select";
import { ChevronDown, Check } from "lucide-react";

interface FilterOption {
  value: string;
  label: string;
}

interface FilterSelectProps {
  id?: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  options: FilterOption[];
  placeholder?: string;
}

export default function FilterSelect({
  id,
  label,
  value,
  onChange,
  options,
  placeholder = "Select...",
}: FilterSelectProps) {
  return (
    <div>
      {label && (
        <label
          id={id ? `${id}-label` : undefined}
          className="block text-xs font-semibold uppercase tracking-wider text-muted mb-2"
        >
          {label}
        </label>
      )}
      <Select.Root
        value={value}
        onValueChange={(v) => onChange(v as string)}
        items={options}
      >
        <Select.Trigger
          aria-labelledby={id ? `${id}-label` : undefined}
          className="flex w-full items-center justify-between gap-2 rounded-xl border border-input-border bg-input-bg px-4 py-2.5 text-sm text-input-text outline-none transition select-none cursor-pointer focus:border-accent focus:ring-4 focus:ring-[var(--ring)] data-disabled:opacity-50"
        >
          <Select.Value
            placeholder={placeholder}
            className="data-placeholder:text-input-placeholder"
          />
          <Select.Icon className="text-input-placeholder shrink-0">
            <ChevronDown className="h-4 w-4" />
          </Select.Icon>
        </Select.Trigger>
        <Select.Portal>
          <Select.Positioner className="outline-none z-50" sideOffset={4} align="start">
            <Select.Popup className="group min-w-[var(--anchor-width)] origin-[var(--transform-origin)] rounded-xl border border-default bg-popover p-1 text-popover-foreground shadow-[var(--shadow)] outline-none transition-[scale,opacity] duration-100 ease-out data-ending-style:scale-[0.98] data-ending-style:opacity-0 data-starting-style:scale-[0.98] data-starting-style:opacity-0">
              <Select.List className="py-1 overflow-y-auto max-h-[var(--available-height)] outline-none">
                {options.map((opt) => (
                  <Select.Item
                    key={opt.value}
                    value={opt.value}
                    className="grid cursor-default grid-cols-[1rem_1fr] items-center gap-2 py-1.5 pr-4 pl-2.5 text-sm outline-none select-none rounded-md data-highlighted:bg-accent data-highlighted:text-accent-foreground data-selected:font-semibold"
                  >
                    <Select.ItemIndicator className="col-start-1 flex items-center">
                      <Check className="h-3.5 w-3.5" />
                    </Select.ItemIndicator>
                    <Select.ItemText className="col-start-2">{opt.label}</Select.ItemText>
                  </Select.Item>
                ))}
              </Select.List>
            </Select.Popup>
          </Select.Positioner>
        </Select.Portal>
      </Select.Root>
    </div>
  );
}
