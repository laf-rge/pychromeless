import { GeoJSON } from "geojson";
import { LngLatLike } from "mapbox-gl";

export interface CustomGeoJSON {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: {
      type: "Point";
      coordinates: LngLatLike;
    };
    properties: StoreProperties;
  }>;
}

export interface StoreProperties {
  phoneFormatted: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  crossStreet: string;
  postalCode: string;
  state: string;
  url: string;
  store: string;
  storeNumber: string;
  hours: string;
}

export const storeLocations: GeoJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.697541, 38.328981],
      },
      properties: {
        phoneFormatted: "+1 (707) 387-1716",
        phone: "+17073871716",
        address: "640 E Cotati Ave Unit B",
        city: "Cotati",
        country: "United States",
        crossStreet: "at Baytree Court",
        postalCode: "94931",
        state: "CA",
        url: "https://www.jerseymikes.com/20407/cotati-ca",
        store: "Cotati",
        storeNumber: "20407",
        hours: "10am–9pm",
      },
    },
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.712791, 38.412461],
      },
      properties: {
        phoneFormatted: "+1 (707) 230-2324",
        phone: "+17072302324",
        address: "2688 Santa Rosa Ave Unit A",
        city: "Santa Rosa",
        country: "United States",
        crossStreet: "at Yolanda Ave",
        postalCode: "95407",
        state: "CA",
        url: "https://www.jerseymikes.com/20358/santa-rosa-ca",
        store: "Santa Rosa",
        storeNumber: "20358",
        hours: "10am–9pm",
      },
    },
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.736711, 38.480261],
      },
      properties: {
        phoneFormatted: "+1 (707) 324-3233",
        phone: "+17073243233",
        address: "919 Hopper Ave STE C",
        city: "Santa Rosa",
        country: "United States",
        crossStreet: "at Airway Dr",
        postalCode: "95403",
        state: "CA",
        url: "https://www.jerseymikes.com/20400/santa-rosa-ca",
        store: "North Santa Rosa",
        storeNumber: "20400",
        hours: "10am–9pm",
      },
    },
    {
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [-122.625249, 38.249233],
      },
      properties: {
        phoneFormatted: "+1 (707) 238-3220",
        phone: "+17072383220",
        address: "201 S McDowell Blvd STE B",
        city: "Petaluma",
        country: "United States",
        crossStreet: "at E Washington St",
        postalCode: "94954",
        state: "CA",
        url: "https://www.jerseymikes.com/20395/petaluma-ca",
        store: "Petaluma",
        storeNumber: "20395",
        hours: "10am–9pm",
      },
    },
  ],
};
