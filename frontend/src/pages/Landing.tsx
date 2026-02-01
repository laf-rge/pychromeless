import { Link } from "react-router-dom";
import { MapPin, ArrowRight, ExternalLink } from "lucide-react";
import { ImagePlaceholder } from "../components/ui/image-placeholder";
import { storeLocations, StoreProperties } from "../components/StoreMapData";

function getStores(): StoreProperties[] {
  if (storeLocations.type === "FeatureCollection") {
    return storeLocations.features.map(
      (f) => f.properties as StoreProperties
    );
  }
  return [];
}

export function LandingPage() {
  const stores = getStores();

  return (
    <div>
      {/* ===== HERO ===== */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-5 min-h-[480px]">
            {/* Text side */}
            <div className="lg:col-span-3 flex flex-col justify-center px-6 py-16 lg:px-12 lg:py-20">
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-4">
                Jersey Mike's Subs
              </p>
              <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] text-[hsl(var(--pub-ink))] mb-6">
                Serving California communities since 2015
              </h1>
              <p className="font-heading text-lg text-muted-foreground max-w-lg mb-8">
                Wagoner Management Corp. proudly operates Jersey Mike's franchise locations,
                bringing fresh, authentic subs to the neighborhoods we call home.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link
                  to="/locations"
                  className="inline-flex items-center gap-2 rounded-lg bg-[#C8102E] px-6 py-3 font-heading text-sm font-semibold text-white shadow-md transition-all hover:bg-[#9B0D23] hover:shadow-lg active:scale-[0.98]"
                >
                  <MapPin className="h-4 w-4" />
                  Find a Location
                </Link>
                <a
                  href="https://www.jerseymikes.com/menu"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-lg border-2 border-[hsl(var(--pub-stone))] px-6 py-3 font-heading text-sm font-semibold text-[hsl(var(--pub-ink))] transition-all hover:border-[#C8102E] hover:text-[#C8102E] active:scale-[0.98]"
                >
                  Order Online
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>
            </div>
            {/* Image side */}
            <div className="lg:col-span-2 relative hidden lg:block">
              <div
                className="absolute inset-0"
                style={{ clipPath: "polygon(12% 0, 100% 0, 100% 100%, 0% 100%)" }}
              >
                <ImagePlaceholder
                  variant="food"
                  className="h-full w-full rounded-none border-0"
                  label="Store photo"
                />
              </div>
            </div>
            {/* Mobile image */}
            <div className="lg:hidden px-6 pb-8">
              <ImagePlaceholder
                variant="food"
                aspectRatio="16/9"
                label="Store photo"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ===== LOCATIONS ===== */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-10">
            <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-2">
              Our Locations
            </p>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-[hsl(var(--pub-ink))]">
              Find us in your neighborhood
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stores.map((store) => (
              <a
                key={store.storeNumber}
                href={store.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative bg-white rounded-xl overflow-hidden shadow-sm border border-[hsl(var(--pub-stone))] transition-all hover:shadow-lg hover:-translate-y-1"
              >
                {/* Red accent bar */}
                <div className="h-[3px] bg-[#C8102E]" />
                <ImagePlaceholder
                  variant="store"
                  aspectRatio="4/3"
                  className="rounded-none border-0 border-b border-[hsl(var(--pub-stone))]"
                  label={store.city}
                />
                <div className="p-4">
                  <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] group-hover:text-[#C8102E] transition-colors">
                    {store.store}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {store.address}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {store.city}, {store.state} {store.postalCode}
                  </p>
                  <p className="text-sm text-[hsl(var(--pub-earth))] mt-2">
                    {store.phoneFormatted}
                  </p>
                </div>
                {/* Hover overlay */}
                <div className="absolute inset-x-0 top-[3px] h-[calc(4/3*100%/(4/3+1))] flex items-center justify-center bg-[#C8102E]/0 group-hover:bg-[#C8102E]/10 transition-colors pointer-events-none">
                  <span className="opacity-0 group-hover:opacity-100 transition-opacity font-heading text-sm font-semibold text-[#C8102E] bg-white/90 backdrop-blur-sm px-4 py-2 rounded-lg shadow">
                    View Store
                  </span>
                </div>
              </a>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link
              to="/locations"
              className="inline-flex items-center gap-2 font-heading text-sm font-semibold text-[#C8102E] hover:text-[#9B0D23] transition-colors"
            >
              View all on map
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ===== ABOUT TEASER ===== */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-3">
                Our Story
              </p>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                Rooted in community, growing across California
              </h2>
              <div className="space-y-4 text-muted-foreground leading-relaxed">
                <p>
                  Wagoner Management Corp. started in 2015 with a single Jersey Mike's
                  location in Long Beach, California. After falling in love with Northern
                  California's wine country, we expanded to Sonoma County in 2022.
                </p>
                <p>
                  Today we operate four locations and counting — each one committed to the
                  same values: fresh ingredients, genuine hospitality, and deep roots in the
                  communities we serve.
                </p>
              </div>
              <Link
                to="/about"
                className="inline-flex items-center gap-2 mt-6 font-heading text-sm font-semibold text-[#C8102E] hover:text-[#9B0D23] transition-colors"
              >
                Learn more about us
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            <ImagePlaceholder
              variant="team"
              aspectRatio="4/3"
              label="Team photo"
            />
          </div>
        </div>
      </section>

      {/* ===== CAREERS ===== */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <ImagePlaceholder
                variant="team"
                aspectRatio="4/3"
                label="Team at work"
              />
            </div>
            <div className="order-1 lg:order-2">
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-3">
                Careers
              </p>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                Join our team
              </h2>
              <div className="space-y-4 text-muted-foreground leading-relaxed mb-8">
                <p>
                  We're always looking for motivated people who care about great food
                  and great service. Whether you're starting your first job or building
                  a career in restaurant management, WMC is a place to grow.
                </p>
                <p>
                  We offer competitive pay, flexible schedules, and a supportive team
                  environment across all our locations.
                </p>
              </div>
              <a
                href="https://form.asana.com/?k=-4SkRX8pl2-0eKzrAvZ-dg&d=1202180131764298"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-[#C8102E] px-8 py-3.5 font-heading text-sm font-semibold text-white shadow-md transition-all hover:bg-[#9B0D23] hover:shadow-lg active:scale-[0.98]"
              >
                Apply Now
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
