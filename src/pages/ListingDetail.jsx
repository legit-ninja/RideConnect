import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { MapPin, Calendar, ArrowLeft, Shield, MessageCircle, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import StarRating from '@/components/StarRating';
import EmptyState from '@/components/EmptyState';
import { base44 } from '@/api/base44Client';

export default function ListingDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activePhoto, setActivePhoto] = useState(0);
  const [user, setUser] = useState(null);
  const [showBooking, setShowBooking] = useState(false);
  const [bookingData, setBookingData] = useState({ date: '', time: '', message: '' });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    base44.entities.Listing.filter({ slug })
      .then(async (data) => {
        if (data.length > 0) {
          const l = data[0];
          setListing(l);
          const revs = await base44.entities.Review.filter({ listing_id: l.id });
          setReviews(revs);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));

    base44.auth.isAuthenticated().then(async (authed) => {
      if (authed) setUser(await base44.auth.me());
    });
  }, [slug]);

  const avgRating = reviews.length > 0 ? reviews.reduce((a, r) => a + r.rating, 0) / reviews.length : 0;

  const handleBooking = async (e) => {
    e.preventDefault();
    if (!user) { navigate('/login'); return; }
    if (!user.riding_skill_level || user.riding_skill_level === 'none') {
      navigate('/profile/setup'); return;
    }
    setSubmitting(true);
    try {
      await base44.entities.Booking.create({
        listing_id: listing.id,
        listing_title: listing.title,
        owner_id: listing.created_by_id,
        rider_id: user.id,
        rider_name: user.full_name || user.email,
        rider_skill_level: user.riding_skill_level,
        requested_date: bookingData.date,
        requested_time: bookingData.time,
        rider_message: bookingData.message,
        status: 'pending',
      });
      navigate('/dashboard');
    } catch (err) {
      // error handled by toast
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!listing) {
    return (
      <div className="pt-20">
        <EmptyState title="Listing not found" description="This listing may have been removed or is no longer available." />
      </div>
    );
  }

  const photos = listing.photos?.length > 0
    ? listing.photos
    : ['https://images.unsplash.com/photo-1553284965-83fd3df1c5ad?w=1200&q=80'];
  const location = [listing.city, listing.state].filter(Boolean).join(', ');

  return (
    <div className="pt-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/listings" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary mb-6">
          <ArrowLeft className="h-4 w-4" /> Back to listings
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          {/* Gallery + Info */}
          <div className="lg:col-span-3">
            <div className="rounded-lg overflow-hidden border border-border bg-card">
              <div className="aspect-[16/10] bg-muted">
                <img src={photos[activePhoto]} alt={listing.title} className="h-full w-full object-cover" />
              </div>
              {photos.length > 1 && (
                <div className="flex gap-2 p-3 overflow-x-auto">
                  {photos.map((photo, i) => (
                    <button
                      key={i}
                      onClick={() => setActivePhoto(i)}
                      className={`flex-shrink-0 h-16 w-20 rounded-md overflow-hidden border-2 transition-colors ${i === activePhoto ? 'border-primary' : 'border-transparent'}`}
                    >
                      <img src={photo} alt="" className="h-full w-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-8">
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary" className="capitalize">{listing.skill_level_required}</Badge>
                    <Badge variant="outline" className="capitalize">{listing.discipline}</Badge>
                  </div>
                  <h1 className="font-heading text-3xl sm:text-4xl font-semibold">{listing.title}</h1>
                  {location && (
                    <p className="mt-2 flex items-center gap-1 text-sm text-muted-foreground">
                      <MapPin className="h-4 w-4" /> {location}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-2xl font-semibold text-primary">
                    {listing.is_free ? 'Free' : `$${listing.price || 0}`}
                  </p>
                </div>
              </div>

              {reviews.length > 0 && (
                <div className="mt-4 flex items-center gap-2">
                  <StarRating rating={Math.round(avgRating)} size={18} />
                  <span className="text-sm text-muted-foreground">{avgRating.toFixed(1)} ({reviews.length} reviews)</span>
                </div>
              )}

              <div className="mt-8 p-6 rounded-lg border border-border bg-card">
                <h3 className="font-heading text-lg font-semibold mb-2">{listing.animal_name}</h3>
                <p className="text-sm text-muted-foreground">
                  {listing.animal_breed ? `${listing.animal_breed} ` : ''}
                  <span className="capitalize">{listing.animal_species}</span>
                </p>
                <p className="mt-4 text-sm leading-relaxed text-foreground/80">
                  {listing.description || 'No description provided.'}
                </p>
              </div>
            </div>
          </div>

          {/* Booking sidebar */}
          <div className="lg:col-span-2">
            <div className="sticky top-24 rounded-lg border border-border bg-card p-6">
              <h3 className="font-heading text-xl font-semibold">Request a Booking</h3>
              <p className="mt-1 text-sm text-muted-foreground">Connect with the owner to schedule your ride.</p>

              {!user ? (
                <div className="mt-6 space-y-3">
                  <p className="text-sm text-muted-foreground">Sign in to request a booking or message the owner.</p>
                  <Button asChild className="w-full h-11">
                    <Link to="/login">Sign In to Continue</Link>
                  </Button>
                  <Button asChild variant="outline" className="w-full h-11">
                    <Link to="/register">Create Account</Link>
                  </Button>
                </div>
              ) : (!user.riding_skill_level || user.riding_skill_level === 'none') ? (
                <div className="mt-6 space-y-3">
                  <p className="text-sm text-muted-foreground">Complete your profile with your riding skill level to book.</p>
                  <Button asChild className="w-full h-11">
                    <Link to="/profile/setup">Set Up Profile</Link>
                  </Button>
                </div>
              ) : showBooking ? (
                <form onSubmit={handleBooking} className="mt-6 space-y-4">
                  <div>
                    <Label htmlFor="date">Preferred Date</Label>
                    <Input id="date" type="date" required value={bookingData.date}
                      onChange={(e) => setBookingData({ ...bookingData, date: e.target.value })}
                      className="mt-1.5 h-11" />
                  </div>
                  <div>
                    <Label htmlFor="time">Preferred Time</Label>
                    <Input id="time" type="time" required value={bookingData.time}
                      onChange={(e) => setBookingData({ ...bookingData, time: e.target.value })}
                      className="mt-1.5 h-11" />
                  </div>
                  <div>
                    <Label htmlFor="message">Message to Owner</Label>
                    <Textarea id="message" rows={3} placeholder="Tell the owner about your experience..."
                      value={bookingData.message}
                      onChange={(e) => setBookingData({ ...bookingData, message: e.target.value })}
                      className="mt-1.5" />
                  </div>
                  <Button type="submit" disabled={submitting} className="w-full h-11">
                    {submitting ? 'Sending...' : 'Send Request'}
                  </Button>
                </form>
              ) : (
                <div className="mt-6 space-y-3">
                  <Button onClick={() => setShowBooking(true)} className="w-full h-11">
                    <Calendar className="mr-2 h-4 w-4" /> Request Booking
                  </Button>
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-border space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Shield className="h-4 w-4 text-primary" /> Verified owner
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MessageCircle className="h-4 w-4 text-primary" /> Direct messaging
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Reviews */}
        <section className="mt-16">
          <h2 className="font-heading text-2xl font-semibold mb-6">Reviews</h2>
          {reviews.length === 0 ? (
            <p className="text-sm text-muted-foreground">No reviews yet. Be the first to ride and review!</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reviews.map((review) => (
                <div key={review.id} className="p-5 rounded-lg border border-border bg-card">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-sm">{review.rider_name || 'Anonymous Rider'}</span>
                    <StarRating rating={review.rating} size={14} />
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed">{review.content}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}