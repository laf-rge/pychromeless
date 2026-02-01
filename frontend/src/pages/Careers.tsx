import { ArrowRight, Clock, DollarSign, Users, TrendingUp } from "lucide-react";
import { ImagePlaceholder } from "../components/ui/image-placeholder";

const perks = [
  {
    icon: DollarSign,
    title: "Competitive Pay",
    description: "Fair wages that reflect your contribution and experience.",
  },
  {
    icon: Clock,
    title: "Flexible Schedules",
    description: "We work with you to find hours that fit your life.",
  },
  {
    icon: Users,
    title: "Team Culture",
    description: "Supportive environment where everyone helps each other succeed.",
  },
  {
    icon: TrendingUp,
    title: "Growth Opportunities",
    description: "From crew member to management — we promote from within.",
  },
];

export function CareersPage() {
  return (
    <div>
      {/* Hero */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="font-heading text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--pub-warm))] mb-3">
                Careers at WMC
              </p>
              <h1 className="font-display text-4xl sm:text-5xl font-bold text-[hsl(var(--pub-ink))] mb-6">
                Build your career with us
              </h1>
              <p className="text-lg text-muted-foreground leading-relaxed mb-8">
                Whether you're looking for your first job, a flexible part-time role,
                or a path into restaurant management, Wagoner Management Corp. is a
                great place to start. We operate multiple Jersey Mike's locations across
                California and we're growing.
              </p>
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
            <ImagePlaceholder
              variant="team"
              aspectRatio="4/3"
              label="Team photo"
            />
          </div>
        </div>
      </section>

      {/* Perks */}
      <section className="bg-[hsl(var(--pub-cream))] py-16 lg:py-20">
        <div className="mx-auto max-w-7xl px-6">
          <div className="text-center mb-12">
            <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))]">
              Why work with us
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {perks.map((perk) => (
              <div
                key={perk.title}
                className="bg-white rounded-xl p-6 border border-[hsl(var(--pub-stone))] shadow-sm"
              >
                <div className="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-[#C8102E]/10 text-[#C8102E] mb-4">
                  <perk.icon className="h-5 w-5" />
                </div>
                <h3 className="font-heading text-base font-semibold text-[hsl(var(--pub-ink))] mb-2">
                  {perk.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {perk.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 lg:py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-3xl font-bold text-[hsl(var(--pub-ink))] mb-4">
            Ready to get started?
          </h2>
          <p className="text-lg text-muted-foreground mb-8">
            We'd love to hear from you. Apply today and someone from our team
            will be in touch.
          </p>
          <a
            href="https://form.asana.com/?k=-4SkRX8pl2-0eKzrAvZ-dg&d=1202180131764298"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[#C8102E] px-10 py-4 font-heading text-base font-semibold text-white shadow-md transition-all hover:bg-[#9B0D23] hover:shadow-lg active:scale-[0.98]"
          >
            Apply Now
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </section>
    </div>
  );
}
