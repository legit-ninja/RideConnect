import { Link } from 'react-router-dom';
import { MapPin, Star } from 'lucide-react';

export default function ListingCard({ listing }) {
  const photo = listing.photos?.[0] || 'https://images.unsplash.com/photo-1553284965-83fd3df1c5ad?w=800&q=80';
  const location = [listing.city, listing.state].filter(Boolean).join(', ');

  return (
    <Link to={`/listings/${listing.slug || listing.id}`} className="group block">
      <div className="card-hover overflow-hidden rounded-lg border border-border bg-card">
        <div className="relative aspect-[4/5] overflow-hidden bg-muted">
          <img
            src={photo}
            alt={listing.title}
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
          <div className="absolute top-3 left-3">
            <span className="inline-flex items-center rounded-full bg-background/90 backdrop-blur px-3 py-1 text-xs font-medium capitalize text-foreground">
              {listing.skill_level_required}
            </span>
          </div>
          <div className="absolute bottom-3 right-3">
            <span className="inline-flex items-center rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground">
              {listing.is_free ? 'Free' : `$${listing.price || 0}`}
            </span>
          </div>
        </div>
        <div className="p-4">
          <h3 className="font-heading text-lg font-semibold leading-tight line-clamp-1 group-hover:text-primary transition-colors">
            {listing.title}
          </h3>
          <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
            {listing.animal_name} &middot; {listing.animal_breed || listing.animal_species}
          </p>
          {location && (
            <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin className="h-3.5 w-3.5" />
              <span>{location}</span>
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}