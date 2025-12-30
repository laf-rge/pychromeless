import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center space-y-6">
          <h1 className="text-5xl font-bold">Wagoner Management Corp.</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Restaurant operations management and financial integration platform
          </p>
          <div className="flex justify-center gap-4">
            <Button variant="outline" asChild size="lg">
              <Link to="/map">Find a Location</Link>
            </Button>
            <Button variant="outline" asChild size="lg">
              <Link to="/about">Learn More</Link>
            </Button>
            <Button variant="outline" asChild size="lg">
              <a
                href="https://form.asana.com/?k=-4SkRX8pl2-0eKzrAvZ-dg&d=1202180131764298"
                target="_blank"
                rel="noopener noreferrer"
              >
                Join Our Team
              </a>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
