import { Link } from "react-router-dom";
import { MapPin, Phone, ExternalLink } from "lucide-react";
import { storeLocations, StoreProperties } from "../StoreMapData";

const quickLinks = [
  { label: "Our Locations", to: "/locations" },
  { label: "About Us", to: "/about" },
  { label: "Join Our Team", to: "/careers" },
];

const externalLinks = [
  {
    label: "Order Online",
    href: "https://www.jerseymikes.com/menu",
  },
];

function getStores(): StoreProperties[] {
  if (storeLocations.type === "FeatureCollection") {
    return storeLocations.features.map(
      (f) => f.properties as StoreProperties
    );
  }
  return [];
}

export function Footer() {
  const stores = getStores();

  return (
    <footer className="bg-[#2C2416] text-[#F5F0E8]">
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="space-y-3">
            <h3 className="font-heading text-lg font-semibold text-white">
              Wagoner Management Corp.
            </h3>
            <p className="text-sm leading-relaxed text-[#B8AFA0]">
              Proudly operating Jersey Mike's franchise locations across California.
            </p>
          </div>

          {/* Locations */}
          <div className="space-y-3">
            <h4 className="font-heading text-sm font-semibold uppercase tracking-wider text-[#D4A853]">
              Locations
            </h4>
            <ul className="space-y-2">
              {stores.map((store) => (
                <li key={store.store} className="flex items-start gap-2 text-sm text-[#B8AFA0]">
                  <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#D4A853]" />
                  <a
                    href={store.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-white transition-colors"
                  >
                    {store.store}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Quick Links */}
          <div className="space-y-3">
            <h4 className="font-heading text-sm font-semibold uppercase tracking-wider text-[#D4A853]">
              Quick Links
            </h4>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-[#B8AFA0] hover:text-white transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
              {externalLinks.map((link) => (
                <li key={link.href} className="flex items-center gap-1.5">
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-[#B8AFA0] hover:text-white transition-colors"
                  >
                    {link.label}
                  </a>
                  <ExternalLink className="h-3 w-3 text-[#B8AFA0]" />
                </li>
              ))}
            </ul>
          </div>

          {/* Contact */}
          <div className="space-y-3">
            <h4 className="font-heading text-sm font-semibold uppercase tracking-wider text-[#D4A853]">
              Contact
            </h4>
            <ul className="space-y-2">
              {stores.map((store) => (
                <li key={store.store} className="flex items-center gap-2 text-sm text-[#B8AFA0]">
                  <Phone className="h-3.5 w-3.5 shrink-0 text-[#D4A853]" />
                  <a
                    href={`tel:${store.phoneFormatted.replace(/\s/g, "")}`}
                    className="hover:text-white transition-colors"
                  >
                    {store.store}: {store.phoneFormatted}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 border-t border-[#4A3F30] pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-[#8B7355]">
            &copy; {new Date().getFullYear()} Wagoner Management Corp. All rights reserved.
          </p>
          <p className="text-xs text-[#8B7355]">
            Jersey Mike's&reg; is a registered trademark of Jersey Mike's Franchise Systems, Inc.
          </p>
        </div>
      </div>
    </footer>
  );
}
