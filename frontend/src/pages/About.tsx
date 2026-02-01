import { Link } from "react-router-dom";
import { ArrowRight, Phone } from "lucide-react";
import { ImagePlaceholder } from "../components/ui/image-placeholder";

export function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-3">
                About WMC
              </p>
              <h1 className="font-display text-4xl sm:text-5xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                Rooted in community, growing across California
              </h1>
              <div className="space-y-4 text-muted-foreground leading-relaxed">
                <p>
                  Wagoner Management Corp. is a Jersey Mike's franchise operator
                  committed to bringing fresh, authentic subs to the communities
                  we call home. We believe great food starts with great people
                  and genuine connections to the neighborhoods we serve.
                </p>
              </div>
            </div>
            <ImagePlaceholder
              variant="team"
              aspectRatio="4/3"
              label="Team photo"
            />
          </div>
        </div>
      </section>

      {/* Our Story */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))]">
              Our Story
            </h2>
          </div>
          <div className="max-w-3xl mx-auto space-y-6 text-muted-foreground leading-relaxed">
            <p>
              We started in 2015 with a single Jersey Mike's location in Long
              Beach, California. From day one, the goal was simple: run a great
              restaurant, take care of our team, and be a real part of the
              community.
            </p>
            <p>
              After falling in love with Northern California's wine country, we
              expanded to Sonoma County in 2022 with our first Santa Rosa
              location. The response was incredible, and we quickly grew to
              four stores across the region.
            </p>
            <p>
              Today, every location reflects the same values we started with —
              fresh ingredients, genuine hospitality, and a commitment to the
              people who walk through our doors, whether they're customers or
              crew members.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <ImagePlaceholder
                variant="store"
                aspectRatio="4/3"
                label="Store interior"
              />
            </div>
            <div className="order-1 lg:order-2">
              <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                What drives us
              </h2>
              <div className="space-y-5">
                <div>
                  <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] mb-1">
                    Fresh, every time
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    We slice our meats and cheese fresh for every sub. It's the
                    Jersey Mike's way, and it's non-negotiable.
                  </p>
                </div>
                <div>
                  <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] mb-1">
                    People first
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    We invest in our team with competitive pay, flexible
                    schedules, and real paths to advancement. Many of our
                    managers started behind the counter.
                  </p>
                </div>
                <div>
                  <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] mb-1">
                    Community roots
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    We're not just in the neighborhood — we're part of it.
                    From local fundraisers to youth sports sponsorships, we show
                    up for the communities that show up for us.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-4">
            Get in touch
          </h2>
          <p className="text-lg text-muted-foreground mb-6">
            For general inquiries, catering, or partnership opportunities,
            reach our corporate office.
          </p>
          <a
            href="tel:+15623802210"
            className="inline-flex items-center gap-2 font-heading text-lg font-semibold text-[hsl(var(--pub-ink))] hover:text-[#C8102E] transition-colors"
          >
            <Phone className="h-5 w-5 text-[hsl(var(--pub-earth))]" />
            (562) 380-2210
          </a>
          <p className="text-sm text-muted-foreground mt-2">
            For store-specific questions, please contact{" "}
            <Link to="/locations" className="text-[#C8102E] hover:text-[#9B0D23] hover:underline">
              your nearest location
            </Link>{" "}
            directly.
          </p>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-4">
            Want to be part of the team?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            We're always looking for great people. Check out our open positions
            and apply today.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="https://form.asana.com/?k=-4SkRX8pl2-0eKzrAvZ-dg&d=1202180131764298"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg bg-[#C8102E] px-8 py-3.5 font-heading text-sm font-semibold text-white shadow-md transition-all hover:bg-[#9B0D23] hover:shadow-lg active:scale-[0.98]"
            >
              Apply Now
              <ArrowRight className="h-4 w-4" />
            </a>
            <Link
              to="/locations"
              className="inline-flex items-center gap-2 rounded-lg border-2 border-[hsl(var(--pub-stone))] px-8 py-3.5 font-heading text-sm font-semibold text-[hsl(var(--pub-ink))] transition-all hover:border-[#C8102E] hover:text-[#C8102E] active:scale-[0.98]"
            >
              Find a Location
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
