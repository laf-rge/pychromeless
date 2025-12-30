import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";

export function AboutPage() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="container mx-auto max-w-3xl space-y-6">
        <div className="mb-6">
          <Button variant="outline" asChild>
            <Link to="/">← Back to Home</Link>
          </Button>
        </div>
        <h1 className="text-4xl font-bold text-center">About Us</h1>
        <div className="space-y-4 text-lg text-muted-foreground">
          <p>
            Wagoner Management Corp. started in 2015 operating a single Jersey
            Mike's location in Long Beach, California.
          </p>
          <p>
            After visiting Sonoma County, our founders fell in love with the
            area and in April of 2022 we opened our first Northern California
            location in Santa Rosa.
          </p>
          <p>
            We currently operate 4 locations in Sonoma County, bringing fresh,
            authentic Jersey Mike's subs to the communities we serve.
          </p>
        </div>
      </div>
    </div>
  );
}
