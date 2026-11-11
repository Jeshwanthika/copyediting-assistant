import { BRAND } from "@/lib/brand";

export default function BrandLogo({ className = "" }: { className?: string }) {
  return (
    <div className={`brand ${className}`}>
      <div className="brand-mark">{BRAND.mark}</div>
      <div className="brand-copy">
        <span className="brand-title">
          <span className="brand-accent">{BRAND.accent}</span>
          {BRAND.rest}
        </span>
        <span className="brand-version">{BRAND.tagline}</span>
      </div>
    </div>
  );
}
