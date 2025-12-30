import { useRef, useEffect, useState } from "react";
import mapboxgl, { Map, LngLatLike, LngLat } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { storeLocations, CustomGeoJSON, StoreProperties } from "./StoreMapData";
import { Point } from "geojson";
import { cn } from "../utils/cn";
import customMarkerImage from "../assets/map-marker-jersey-mikes.png";

mapboxgl.accessToken =
  "pk.eyJ1Ijoid2Fnb25lcm1hbmFnZW1lbnQiLCJhIjoiY2x2aXA1MDJoMWtobjJqbjFqa2lxenhleCJ9.KxOTU9EAcV9lZKE5HBR03g";

export default function StoreMap() {
  const mapcenter: LngLat = new LngLat(-122.7024, 38.3719);
  const defaultzoom = 10;
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<Map | null>(null);
  const [selectedStore, setSelectedStore] = useState<string | null>(null);

  const handleStyleLoad = () => {
    if (map.current == null) return;

    console.log("Style loaded, loading marker image:", customMarkerImage);

    // Add the marker image to the map
    map.current.loadImage(customMarkerImage, (error, image) => {
      if (error) {
        console.error("Failed to load custom marker image", error);
        // Fallback: add layer with default marker
        if (map.current) {
          map.current.addLayer({
            id: "store-locations",
            type: "symbol",
            source: {
              type: "geojson",
              data: storeLocations,
            },
            layout: {
              "icon-image": "marker-15",
              "icon-allow-overlap": true,
              "icon-anchor": "bottom",
            },
          });
          console.log("Store locations layer added with default marker");
        }
        return;
      }
      if (!map.current) return;
      if (image) {
        map.current.addImage("custom-marker", image);
        console.log("Custom marker image added successfully");
      }

      // Add the layer after the image has been added
      // Use inline source definition like the old code
      map.current.addLayer({
        id: "store-locations",
        type: "symbol",
        source: {
          type: "geojson",
          data: storeLocations,
        },
        layout: {
          "icon-image": "custom-marker",
          "icon-allow-overlap": true,
          "icon-anchor": "bottom",
        },
      });
      console.log("Store locations layer added");
    });
  };

  useEffect(() => {
    if (map.current || mapContainer.current == null) return;

    console.log("Initializing map...");
    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current!,
        style: "mapbox://styles/mapbox/standard",
        center: [mapcenter.lng, mapcenter.lat],
        zoom: defaultzoom,
        scrollZoom: false,
        touchZoomRotate: true,
      });

      console.log("Map created, waiting for style to load...");

      // Wait for the style to load before adding the layer
      map.current.on("style.load", handleStyleLoad);

      // Add navigation control after map is ready
      map.current.on("load", () => {
        console.log("Map fully loaded");
        if (map.current) {
          map.current.addControl(new mapboxgl.NavigationControl(), "top-right");
        }
      });
    } catch (error) {
      console.error("Error initializing map:", error);
    }
    return () => {
      if (map.current) {
        map.current.off("style.load", handleStyleLoad);
        map.current.remove();
        map.current = null;
      }
    };
  }, [mapContainer]);

  useEffect(() => {
    if (!map.current) return;
    map.current.on<"click">("click", "store-locations", (e) => {
      if (e.features) {
        const featureGeometry = e.features[0].geometry as Point;
        const storeProps = e.features[0].properties as StoreProperties;
        const clickedStoreIndex = storeProps.store;
        if (selectedStore === clickedStoreIndex) {
          setSelectedStore(null);
          map.current!.flyTo({ center: mapcenter, zoom: defaultzoom });
        } else {
          setSelectedStore(clickedStoreIndex);
          if (
            "coordinates" in featureGeometry &&
            featureGeometry.coordinates.length >= 2
          ) {
            const coordinates: LngLatLike = [
              featureGeometry.coordinates[0],
              featureGeometry.coordinates[1],
            ] as [number, number];

            map.current!.flyTo({ center: coordinates, zoom: 15 });
          }
        }
      }
    });
    map.current.on("mouseenter", "store-locations", () => {
      map.current!.getCanvas().style.cursor = "pointer";
    });

    map.current.on("mouseleave", "store-locations", () => {
      map.current!.getCanvas().style.cursor = "";
    });
  }, [selectedStore]);

  return (
    <div className="flex flex-col md:flex-row justify-center items-start w-full max-w-6xl mx-auto">
      <div className="flex-1 pr-0 md:pr-4 overflow-y-auto">
        <div className="flex flex-row md:flex-col justify-center items-start w-full flex-wrap">
          {(storeLocations as CustomGeoJSON).features.map((feature) => (
            <div
              key={feature.properties.store}
              className={cn(
                "min-w-[200px] md:w-full mb-4 cursor-pointer p-2 rounded-lg border-2 ml-2",
                selectedStore === feature.properties.store
                  ? "bg-red-200 dark:bg-red-900 border-gray-500"
                  : "bg-gray-100 dark:bg-gray-700 border-gray-500"
              )}
              role="button"
              aria-label={`Store location: ${feature.properties.store} - ${feature.properties.address}, ${feature.properties.city}`}
              aria-pressed={selectedStore === feature.properties.store}
              onClick={() => {
                if (selectedStore === feature.properties.store) {
                  setSelectedStore(null);
                  map.current!.flyTo({
                    center: mapcenter,
                    zoom: defaultzoom,
                  });
                } else {
                  setSelectedStore(feature.properties.store);
                  const coordinates: LngLatLike =
                    feature.geometry.coordinates;
                  map.current!.flyTo({ center: coordinates, zoom: 15 });
                }
              }}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  if (selectedStore === feature.properties.store) {
                    setSelectedStore(null);
                    map.current!.flyTo({
                      center: mapcenter,
                      zoom: defaultzoom,
                    });
                  } else {
                    setSelectedStore(feature.properties.store);
                    const coordinates: LngLatLike =
                      feature.geometry.coordinates;
                    map.current!.flyTo({ center: coordinates, zoom: 15 });
                  }
                }
              }}
            >
              <div className="text-md font-bold" aria-label="Store name">
                Jersey Mike's Subs
              </div>
              <div className="text-sm font-bold" aria-label="Store location">
                {feature.properties.store}
              </div>
              <div className="text-sm" aria-label="Store address">
                {feature.properties.address}
              </div>
              <div className="text-sm">
                {feature.properties.city}, {feature.properties.state}{" "}
                {feature.properties.postalCode}
              </div>
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
                  className="text-primary hover:underline"
                >
                  📍 Directions
                </a>
              </div>
              <div>
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href={"tel:" + feature.properties.phone}
                  className="text-primary hover:underline"
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
                  className="text-primary hover:underline"
                >
                  🛒 Order Now
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div
        ref={mapContainer}
        className="ml-2 md:ml-0 flex-1 md:flex-[3] min-h-[550px] md:min-h-[732px] min-w-[200px] w-[97%] rounded-lg border-2 border-gray-500"
        style={{ height: "100%" }}
      />
    </div>
  );
}
