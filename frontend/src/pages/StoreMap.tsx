import { Link } from "react-router-dom";
import StoreMap from "../components/StoreMap";
import { Button } from "../components/ui/button";

export function StoreMapPage() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mb-6">
        <Button variant="outline" asChild>
          <Link to="/">← Back to Home</Link>
        </Button>
      </div>
      <h1 className="text-3xl font-bold mb-4">Store Locations</h1>
      <StoreMap />
    </div>
  );
}
