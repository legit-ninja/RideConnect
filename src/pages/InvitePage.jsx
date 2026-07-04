import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { base44 } from '@/api/base44Client';

export default function InvitePage() {
  const { token } = useParams();
  const [invite, setInvite] = useState(null);
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    base44.entities.InviteToken.filter({ token })
      .then(async (data) => {
        if (data.length > 0) {
          const inv = data[0];
          setInvite(inv);
          if (inv.listing_id) {
            const listings = await base44.entities.Listing.filter({ id: inv.listing_id });
            if (listings.length > 0) setListing(listings[0]);
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  const photo = listing?.photos?.[0] || 'https://images.unsplash.com/photo-1553284965-83fd3df1c5ad?w=1200&q=80';

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20">
      <div className="max-w-2xl w-full">
        <div className="rounded-2xl overflow-hidden border border-border bg-card shadow-xl">
          <div className="relative h-64 overflow-hidden">
            <img src={photo} alt="" className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent" />
            <div className="absolute bottom-0 left-0 right-0 p-6">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/20 border border-primary/40 text-primary text-xs font-medium mb-2">
                <Sparkles className="h-3 w-3" /> You've been invited
              </span>
              <h1 className="font-heading text-3xl font-semibold text-white">{listing?.title || 'Riding Experience'}</h1>
            </div>
          </div>
          <div className="p-6 sm:p-8">
            {invite?.invitee_email && (
              <p className="text-sm text-muted-foreground mb-4">
                This invite was sent to <span className="text-foreground font-medium">{invite.invitee_email}</span>
              </p>
            )}
            <p className="text-foreground/80 leading-relaxed">
              {listing?.description || 'A trusted owner has invited you to explore a verified riding experience. Join RideConnect to connect with the owner and book your ride.'}
            </p>
            {listing && (
              <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground">
                <Shield className="h-4 w-4 text-primary" /> Verified by a trusted RideConnect owner
              </div>
            )}
            <div className="mt-8 flex flex-col sm:flex-row gap-3">
              <Button asChild size="lg" className="h-12">
                <Link to="/register">Accept Invite <ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              {listing && (
                <Button asChild variant="outline" size="lg" className="h-12">
                  <Link to={`/listings/${listing.slug || listing.id}`}>View Listing</Link>
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}