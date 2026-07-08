import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Calendar, Clock, CheckCircle, XCircle, Compass, Pencil, Trash2, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import EmptyState from '@/components/EmptyState';
import ListingCard from '@/components/ListingCard';
import BookingsCalendar from '@/components/BookingsCalendar';
import { base44 } from '@/api/base44Client';

export default function OwnerDashboard() {
  const [listings, setListings] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [shareLink, setShareLink] = useState(null);

  useEffect(() => {
    base44.auth.isAuthenticated().then(async (authed) => {
      if (!authed) return;
      const u = await base44.auth.me();
      setUser(u);
      const [lst, bkg] = await Promise.all([
        base44.entities.Listing.filter({ created_by_id: u.id }, '-created_date', 50),
        base44.entities.Booking.filter({ owner_id: u.id }, '-created_date', 50),
      ]);
      setListings(lst);
      setBookings(bkg);
      setLoading(false);
    });
  }, []);

  const handleApprove = async (booking) => {
    await base44.entities.Booking.update(booking.id, { status: 'approved', owner_response: 'Booking approved! Looking forward to meeting you.' });
    setBookings(bookings.map(b => b.id === booking.id ? { ...b, status: 'approved', owner_response: 'Booking approved! Looking forward to meeting you.' } : b));
  };

  const handleDecline = async (booking) => {
    await base44.entities.Booking.update(booking.id, { status: 'declined' });
    setBookings(bookings.map(b => b.id === booking.id ? { ...b, status: 'declined' } : b));
  };

  const handleDelete = async (listingId) => {
    await base44.entities.Listing.update(listingId, { status: 'archived' });
    setListings(listings.filter(l => l.id !== listingId));
  };

  const handleShare = async (listing) => {
    const token = Math.random().toString(36).substring(2, 12);
    await base44.entities.InviteToken.create({
      token,
      listing_id: listing.id,
      type: 'public',
    });
    setShareLink(`${window.location.origin}/i/${token}`);
  };

  const pendingBookings = bookings.filter(b => b.status === 'pending');
  const otherBookings = bookings.filter(b => b.status !== 'pending');

  if (!user) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="pt-20 min-h-screen px-4 sm:px-6 lg:px-8 py-12">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
          <div>
            <h1 className="font-heading text-3xl sm:text-4xl font-semibold">Owner Dashboard</h1>
            <p className="mt-2 text-muted-foreground">Manage your listings and booking requests.</p>
          </div>
          <Button asChild>
            <Link to="/owner/listings/new"><Plus className="mr-2 h-4 w-4" /> New Listing</Link>
          </Button>
        </div>

        {shareLink && (
          <div className="mb-6 p-4 rounded-lg border border-primary/30 bg-primary/5 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium">Share link created!</p>
              <p className="text-sm text-muted-foreground truncate">{shareLink}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => { navigator.clipboard.writeText(shareLink); }}>Copy</Button>
          </div>
        )}

        {loading ? (
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
        ) : (
          <Tabs defaultValue="listings">
            <TabsList className="mb-6">
              <TabsTrigger value="listings">My Listings ({listings.length})</TabsTrigger>
              <TabsTrigger value="bookings">Booking Requests ({pendingBookings.length})</TabsTrigger>
              <TabsTrigger value="calendar">Calendar</TabsTrigger>
            </TabsList>

            <TabsContent value="listings">
              {listings.length === 0 ? (
                <EmptyState
                  icon={Compass}
                  title="No listings yet"
                  description="Create your first listing to start receiving booking requests."
                  action={<Button asChild><Link to="/owner/listings/new"><Plus className="mr-2 h-4 w-4" /> Create Listing</Link></Button>}
                />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  {listings.map((listing) => (
                    <div key={listing.id} className="group relative">
                      <ListingCard listing={listing} />
                      <div className="mt-3 flex items-center gap-2">
                        <Button asChild variant="outline" size="sm" className="flex-1">
                          <Link to={`/owner/listings/${listing.id}/edit`}><Pencil className="mr-1 h-3.5 w-3.5" /> Edit</Link>
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleShare(listing)}>
                          <Share2 className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => handleDelete(listing.id)}>
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="bookings">
              {pendingBookings.length === 0 && otherBookings.length === 0 ? (
                <EmptyState icon={Calendar} title="No booking requests" description="When riders request bookings, they'll appear here for you to review." />
              ) : (
                <div className="space-y-6">
                  {pendingBookings.length > 0 && (
                    <div>
                      <h3 className="font-heading text-lg font-semibold mb-3">Pending Requests</h3>
                      <div className="space-y-3">
                        {pendingBookings.map((booking) => (
                          <BookingRow key={booking.id} booking={booking} onApprove={handleApprove} onDecline={handleDecline} />
                        ))}
                      </div>
                    </div>
                  )}
                  {otherBookings.length > 0 && (
                    <div>
                      <h3 className="font-heading text-lg font-semibold mb-3">All Bookings</h3>
                      <div className="space-y-3">
                        {otherBookings.map((booking) => (
                          <BookingRow key={booking.id} booking={booking} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </TabsContent>

            <TabsContent value="calendar">
              {bookings.length === 0 ? (
                <EmptyState icon={Calendar} title="No bookings to display" description="When riders request bookings, their ride dates will appear on this calendar." />
              ) : (
                <BookingsCalendar bookings={bookings} />
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}

function BookingRow({ booking, onApprove, onDecline }) {
  const config = {
    pending: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-500',
    approved: 'bg-green-500/10 text-green-600 dark:text-green-500',
    declined: 'bg-red-500/10 text-red-600 dark:text-red-500',
    completed: 'bg-primary/10 text-primary',
    cancelled: 'bg-muted text-muted-foreground',
  };
  return (
    <div className="p-5 rounded-lg border border-border bg-card">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link to={`/listings/${booking.listing_id}`} className="font-heading text-lg font-semibold hover:text-primary">
            {booking.listing_title}
          </Link>
          <p className="text-sm text-muted-foreground mt-1">From {booking.rider_name}</p>
          {booking.rider_skill_level && (
            <Badge variant="secondary" className="mt-2 capitalize">{booking.rider_skill_level} rider</Badge>
          )}
          <div className="mt-3 flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5" /> {booking.requested_date}</span>
            {booking.requested_time && <span className="flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> {booking.requested_time}</span>}
          </div>
          {booking.rider_message && <p className="mt-3 text-sm text-muted-foreground italic">"{booking.rider_message}"</p>}
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge className={config[booking.status]}><span className="capitalize">{booking.status}</span></Badge>
          {booking.status === 'pending' && onApprove && (
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onApprove(booking)}><CheckCircle className="mr-1 h-3.5 w-3.5" /> Approve</Button>
              <Button size="sm" variant="outline" onClick={() => onDecline(booking)}><XCircle className="mr-1 h-3.5 w-3.5" /> Decline</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}