import { useRef, useEffect, useState } from "react";
import mapboxgl, { Map, LngLatLike, LngLat, Marker } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { storeLocations, CustomGeoJSON } from "./StoreMapData";
import { cn } from "../utils/cn";
// Use absolute path from public/ — dynamic DOM elements can't resolve
// Bun's relative asset paths (they resolve relative to page URL, not module)
const customMarkerImage = "/map-marker-jersey-mikes.png";

mapboxgl.accessToken =
  "pk.eyJ1Ijoid2Fnb25lcm1hbmFnZW1lbnQiLCJhIjoiY2x2aXA1MDJoMWtobjJqbjFqa2lxenhleCJ9.KxOTU9EAcV9lZKE5HBR03g";

export default function StoreMap() {
  const mapcenter: LngLat = new LngLat(-122.7024, 38.3719);
  const defaultzoom = 10;
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [selectedStore, setSelectedStore] = useState<string | null>(null);

  useEffect(() => {
    if (map.current || mapContainer.current == null) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current!,
      style: "mapbox://styles/mapbox/light-v11",
      center: [mapcenter.lng, mapcenter.lat],
      zoom: defaultzoom,
      scrollZoom: false,
      touchZoomRotate: true,
    });

    map.current.on("load", () => {
      if (!map.current) return;
      map.current.addControl(new mapboxgl.NavigationControl(), "top-right");

      // Add HTML markers for each store
      const features = (storeLocations as CustomGeoJSON).features;
      features.forEach((feature) => {
        const el = document.createElement("div");
        el.className = "store-marker";
        el.style.cursor = "pointer";

        const img = document.createElement("img");
        img.src = customMarkerImage;
        img.alt = `${feature.properties.store} location`;
        img.style.width = "32px";
        img.style.height = "auto";
        el.appendChild(img);

        const coords = feature.geometry.coordinates as [number, number];
        const marker = new mapboxgl.Marker({ element: el, anchor: "bottom" })
          .setLngLat(coords)
          .addTo(map.current!);

        el.addEventListener("click", () => {
          setSelectedStore((prev) => {
            if (prev === feature.properties.store) {
              map.current?.flyTo({ center: mapcenter, zoom: defaultzoom });
              return null;
            } else {
              map.current?.flyTo({ center: coords, zoom: 15 });
              return feature.properties.store;
            }
          });
        });

        markersRef.current.push(marker);
      });
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapContainer]);

  const handleCardClick = (storeName: string, coordinates: LngLatLike) => {
    if (selectedStore === storeName) {
      setSelectedStore(null);
      map.current?.flyTo({ center: mapcenter, zoom: defaultzoom });
    } else {
      setSelectedStore(storeName);
      map.current?.flyTo({ center: coordinates, zoom: 15 });
    }
  };

  return (
    <div className="flex flex-col md:flex-row justify-center items-start w-full max-w-6xl mx-auto gap-4">
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-row md:flex-col justify-center items-start w-full flex-wrap gap-4">
          {(storeLocations as CustomGeoJSON).features.map((feature) => (
            <div
              key={feature.properties.store}
              className={cn(
                "min-w-[200px] md:w-full cursor-pointer p-4 rounded-xl border transition-all",
                selectedStore === feature.properties.store
                  ? "bg-[#C8102E]/10 border-[#C8102E] shadow-md"
                  : "bg-white border-[hsl(var(--pub-stone))] shadow-sm hover:shadow-md hover:border-[#C8102E]/40"
              )}
              role="button"
              aria-label={`Store location: ${feature.properties.store} - ${feature.properties.address}, ${feature.properties.city}`}
              aria-pressed={selectedStore === feature.properties.store}
              onClick={() => handleCardClick(feature.properties.store, feature.geometry.coordinates)}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  handleCardClick(feature.properties.store, feature.geometry.coordinates);
                }
              }}
            >
              <div className="font-heading text-base font-bold text-[hsl(var(--pub-ink))]">
                Jersey Mike's Subs
              </div>
              <div className="font-heading text-sm font-semibold text-[hsl(var(--pub-ink))]">
                {feature.properties.store}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {feature.properties.address}
              </div>
              <div className="text-sm text-muted-foreground">
                {feature.properties.city}, {feature.properties.state}{" "}
                {feature.properties.postalCode}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                Open daily {feature.properties.hours}
              </div>
              <div className="mt-2 space-y-1">
                <div>
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href={
                      "https://maps.apple.com/?q=q=Jersey%20Mike's%20Subs%20" +
                      encodeURIComponent(
                        [
                          feature.properties.address,
                          feature.properties.city,
                          feature.properties.state,
                          feature.properties.postalCode,
                        ].join(" ")
                      )
                    }
                    className="text-sm text-[#C8102E] hover:text-[#9B0D23] hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    📍 Directions
                  </a>
                </div>
                <div>
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href={"tel:" + feature.properties.phone}
                    className="text-sm text-[hsl(var(--pub-earth))] hover:text-[hsl(var(--pub-ink))]"
                    onClick={(e) => e.stopPropagation()}
                  >
                    📞 {feature.properties.phoneFormatted}
                  </a>
                </div>
                <div>
                  <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href={feature.properties.url}
                    aria-label={`Order online from ${feature.properties.store} location`}
                    className="text-sm text-[#C8102E] hover:text-[#9B0D23] hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    🛒 Order Now
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div
        ref={mapContainer}
        className="flex-1 md:flex-[3] min-h-[550px] md:min-h-[732px] min-w-[200px] w-full rounded-xl border border-[hsl(var(--pub-stone))] shadow-sm"
        style={{ height: "100%" }}
      />
    </div>
  );
}
