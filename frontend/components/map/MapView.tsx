"use client";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import { formatPrice } from "@/lib/utils";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Leaflet varsayılan ikon fix
const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = defaultIcon;

interface Props {
  listings: any[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
}

export default function MapView({ listings, selectedIds, onToggleSelect }: Props) {
  const validListings = listings.filter((l) => l.latitude && l.longitude);

  // Çanakkale merkez
  const center: [number, number] = [40.1553, 26.4142];

  return (
    <MapContainer center={center} zoom={12} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org">OSM</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {validListings.map((listing) => (
        <Marker
          key={listing.id}
          position={[listing.latitude, listing.longitude]}
          eventHandlers={{
            click: () => onToggleSelect(listing.id),
          }}
        >
          <Popup>
            <div className="min-w-[200px]">
              <p className="font-bold text-sm">{listing.title}</p>
              <p className="text-blue-600 font-bold">{formatPrice(listing.price)}</p>
              <p className="text-xs text-gray-500">
                {listing.room_count} · {listing.area_m2}m² · {listing.district}
              </p>
              {listing.motivation_score > 30 && (
                <p className="text-xs text-orange-600 mt-1">Motivasyon: {listing.motivation_score}/100</p>
              )}
              <button
                onClick={() => onToggleSelect(listing.id)}
                className={`mt-2 text-xs px-3 py-1 rounded ${
                  selectedIds.includes(listing.id)
                    ? "bg-red-100 text-red-700"
                    : "bg-blue-100 text-blue-700"
                }`}
              >
                {selectedIds.includes(listing.id) ? "Rotadan Çıkar" : "Rotaya Ekle"}
              </button>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
