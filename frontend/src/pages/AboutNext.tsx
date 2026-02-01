import { Link } from "react-router-dom";
import { ArrowRight, Phone } from "lucide-react";
import { ImagePlaceholder } from "../components/ui/image-placeholder";

const milestones = [
  {
    year: "2015",
    title: "Where it started",
    description:
      "Wagoner Management Corp. opened its first Jersey Mike's in Long Beach, California. One store, a small crew, and a commitment to doing things right.",
    imageLabel: "Long Beach location",
    imageVariant: "store" as const,
  },
  {
    year: "2022",
    title: "Heading north",
    description:
      "After falling in love with Northern California's wine country, we opened our first Sonoma County location in Santa Rosa. The community welcomed us immediately.",
    imageLabel: "Santa Rosa opening",
    imageVariant: "team" as const,
  },
  {
    year: "2023",
    title: "Growing across the region",
    description:
      "Petaluma, Cotati, North Santa Rosa — three new stores in quick succession. Each one built on the same foundation: fresh food, great people, real community ties.",
    imageLabel: "Team across stores",
    imageVariant: "store" as const,
  },
  {
    year: "2024–25",
    title: "Four stores and counting",
    description:
      "With four thriving locations and a growing team, we've become a part of the fabric of Sonoma County. And we're just getting started.",
    imageLabel: "Current team",
    imageVariant: "team" as const,
  },
];

const values = [
  {
    title: "Fresh, every time",
    description:
      "We slice our meats and cheese fresh for every sub. It's the Jersey Mike's way, and it's non-negotiable.",
  },
  {
    title: "People first",
    description:
      "We invest in our team with competitive pay, flexible schedules, and real paths to advancement. Many of our managers started behind the counter.",
  },
  {
    title: "Community roots",
    description:
      "We're not just in the neighborhood — we're part of it. From local fundraisers to youth sports sponsorships, we show up for the communities that show up for us.",
  },
  {
    title: "Always growing",
    description:
      "We're expanding to new regions across California, bringing the same values and commitment to every community we enter.",
  },
];

export function AboutNextPage() {
  return (
    <div>
      {/* Hero */}
      <section className="py-16 lg:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-3">
                About WMC
              </p>
              <h1 className="font-display text-4xl sm:text-5xl font-bold text-[hsl(var(--pub-ink))] mb-6 leading-[1.1]">
                Rooted in community, growing across California
              </h1>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Wagoner Management Corp. is a Jersey Mike's franchise operator
                committed to bringing fresh, authentic subs to the communities
                we call home. We believe great food starts with great people
                and genuine connections to the neighborhoods we serve.
              </p>
            </div>
            <ImagePlaceholder
              variant="team"
              aspectRatio="4/3"
              label="Team photo"
            />
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-16">
            <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-2">
              Our Journey
            </p>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-[hsl(var(--pub-ink))]">
              From one store to a growing family
            </h2>
          </div>

          <div className="relative">
            {/* Vertical line — visible on lg only */}
            <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-[#C8102E]/20" />

            <div className="space-y-16 lg:space-y-24">
              {milestones.map((milestone, index) => {
                const isEven = index % 2 === 0;
                return (
                  <div
                    key={milestone.year}
                    className="relative grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-center"
                  >
                    {/* Timeline dot — centered on the line */}
                    <div className="hidden lg:flex absolute left-1/2 -translate-x-1/2 items-center justify-center">
                      <div className="h-10 w-10 rounded-full bg-white border-[3px] border-[#C8102E] flex items-center justify-center shadow-sm">
                        <div className="h-3 w-3 rounded-full bg-[#C8102E]" />
                      </div>
                    </div>

                    {/* Text */}
                    <div
                      className={`${isEven ? "lg:pr-16" : "lg:order-2 lg:pl-16"}`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        {/* Mobile dot */}
                        <div className="lg:hidden h-8 w-8 rounded-full bg-white border-2 border-[#C8102E] flex items-center justify-center shadow-sm flex-shrink-0">
                          <div className="h-2 w-2 rounded-full bg-[#C8102E]" />
                        </div>
                        <span className="font-display text-2xl font-bold text-[#C8102E]">
                          {milestone.year}
                        </span>
                      </div>
                      <h3 className="font-heading text-xl font-semibold text-[hsl(var(--pub-ink))] mb-3">
                        {milestone.title}
                      </h3>
                      <p className="text-muted-foreground leading-relaxed">
                        {milestone.description}
                      </p>
                    </div>

                    {/* Image */}
                    <div
                      className={`${isEven ? "lg:order-2 lg:pl-16" : "lg:pr-16"}`}
                    >
                      <ImagePlaceholder
                        variant={milestone.imageVariant}
                        aspectRatio="16/9"
                        label={milestone.imageLabel}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-16 lg:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-2">
              What Drives Us
            </p>
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-[hsl(var(--pub-ink))]">
              Our values in action
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {values.map((value) => (
              <div
                key={value.title}
                className="bg-white rounded-xl p-6 border border-[hsl(var(--pub-stone))] shadow-sm"
              >
                <div className="h-1 w-12 bg-[#C8102E] rounded-full mb-4" />
                <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] mb-2">
                  {value.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Leadership teaser */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <ImagePlaceholder
                variant="team"
                aspectRatio="4/3"
                label="Leadership team"
              />
            </div>
            <div className="order-1 lg:order-2">
              <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                Built by operators, not investors
              </h2>
              <div className="space-y-4 text-muted-foreground leading-relaxed">
                <p>
                  WMC is owner-operated. Our leadership team is in the stores
                  every week — working alongside crews, talking to customers,
                  and making sure every location lives up to the standard we
                  set from day one.
                </p>
                <p>
                  We're hands-on because that's how you build something worth
                  being proud of.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Contact */}
      <section className="py-16 lg:py-20">
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
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
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
