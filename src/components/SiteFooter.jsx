import { Link } from 'react-router-dom';
import { Compass, Mail, Shield } from 'lucide-react';

export default function SiteFooter() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <Compass className="h-6 w-6 text-primary" />
              <span className="font-heading text-xl font-semibold">RideConnect</span>
            </Link>
            <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
              A trust-first marketplace connecting verified riders with animal owners
              for safe, unforgettable riding experiences.
            </p>
            <div className="flex items-center gap-2 mt-4 text-xs text-muted-foreground">
              <Shield className="h-4 w-4 text-primary" />
              <span>Verified riders &amp; trusted owners</span>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-3">Explore</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/listings" className="hover:text-primary transition-colors">Browse Listings</Link></li>
              <li><Link to="/#how-it-works" className="hover:text-primary transition-colors">How it Works</Link></li>
              <li><Link to="/register" className="hover:text-primary transition-colors">Create Account</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-semibold mb-3">For Owners</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><Link to="/owner/dashboard" className="hover:text-primary transition-colors">Owner Dashboard</Link></li>
              <li><Link to="/owner/listings/new" className="hover:text-primary transition-colors">Create Listing</Link></li>
              <li><Link to="/#how-it-works" className="hover:text-primary transition-colors">Safety &amp; Trust</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} RideConnect. All rights reserved.
          </p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Mail className="h-3.5 w-3.5" />
            <span>Built with trust at the core</span>
          </div>
        </div>
      </div>
    </footer>
  );
}