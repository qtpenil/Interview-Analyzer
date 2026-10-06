import { ShieldCheck, Zap, FileText, Lock, LayoutDashboard } from "lucide-react";
import Reveal from "./Reveal";

const trustItems = [
  { icon: ShieldCheck, label: "AI Powered" },
  { icon: Lock, label: "Secure Processing" },
  { icon: Zap, label: "Fast Analysis" },
  { icon: FileText, label: "PDF Reports" },
  { icon: LayoutDashboard, label: "Modern Dashboard" },
];

export default function TrustBar() {
  return (
    <section className="border-y border-default bg-surface/40">
      <div className="mx-auto max-w-7xl px-5 sm:px-8 py-6">
        <Reveal>
          <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-12">
            {trustItems.map(({ icon: Icon, label }) => (
              <li
                key={label}
                className="flex items-center gap-2.5 text-sm font-semibold text-secondary"
              >
                <Icon className="h-5 w-5 text-secondary" />
                {label}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
