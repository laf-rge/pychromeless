import { Link } from "react-router-dom";
import StoreMap from "../components/StoreMap";

export function StoreMapPage() {
  return (
    <div className="py-8 px-6">
      <div className="mb-6">
        <Link
          to="/"
          className="inline-flex items-center gap-1 font-heading text-sm font-medium text-muted-foreground hover:text-[hsl(var(--pub-ink))] transition-colors"
        >
          &larr; Back to Home
        </Link>
      </div>
      <h1 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-6">
        Store Locations
      </h1>
      <StoreMap />
    </div>
  );
}
