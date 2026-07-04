import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, CheckCircle, XCircle, Compass, MessageCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import EmptyState from '@/components/EmptyState';
import { base44 } from '@/api/base44Client';

const statusConfig = {
  pending: { icon: Clock, label: 'Pending', className: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-500' },
  approved: { icon: CheckCircle, label: 'Approved', className: 'bg-green-500/10 text-green-600 dark:text-green-500' },
  declined: { icon: XCircle, label: 'Declined', className: 'bg-red-500/10 text-red-600 dark:text-red-500' },
  completed: { icon: CheckCircle, label: 'Completed', className: 'bg-primary/10 text-primary' },
  cancelled: { icon: XCircle, label: 'Cancelled', className: 'bg-muted text-muted-foreground' },
};

export default function RiderDashboard() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    base44.auth.isAuthenticated().then(async (authed) => {
      if (!authed) return;
      const u = await base44.auth.me();
      setUser(u);
      if (!u.riding_skill_level || u.riding_skill_level === 'none') return;
      base44.entities.Booking.filter({ rider_id: u.id }, '-created_date', 50)
        .then(setBookings)
        .catch(() => {})
        .finally(() => setLoading(false));
    });
  }, []);

  if (!user) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  if (!user.riding_skill_level || user.riding_skill_level === 'none') {
    return (
      <div className="pt-20">
        <EmptyState
          icon={Compass}
          title="Complete your profile"
          description="Set your riding skill level to start browsing and booking riding experiences."
          action={<Button asChild><Link to="/profile/setup">Set Up Profile</Link></Button>}
        />
      </div>
    );
  }

  return (
    <div className="pt-20 min-h-screen px-4 sm:px-6 lg:px-8 py-12">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <h1 className="font-heading text-3xl sm:text-4xl font-semibold">My Bookings</h1>
          <p className="mt-2 text-muted-foreground">Track your booking requests and riding experiences.</p>
        </div>

        {loading ? (
          <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
        ) : bookings.length === 0 ? (
          <EmptyState
            icon={Calendar}
            title="No bookings yet"
            description="Browse listings and request your first riding experience."
            action={<Button asChild><Link to="/listings">Browse Listings</Link></Button>}
          />
        ) : (
          <div className="space-y-4">
            {bookings.map((booking) => {
              const config = statusConfig[booking.status] || statusConfig.pending;
              return (
                <div key={booking.id} className="p-5 rounded-lg border border-border bg-card">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <Link to={`/listings/${booking.listing_id}`} className="font-heading text-lg font-semibold hover:text-primary">
                        {booking.listing_title}
                      </Link>
                      <div className="mt-2 flex items-center gap-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" /> {booking.requested_date}
                        </span>
                        {booking.requested_time && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5" /> {booking.requested_time}
                          </span>
                        )}
                      </div>
                      {booking.rider_message && (
                        <p className="mt-3 text-sm text-muted-foreground italic">"{booking.rider_message}"</p>
                      )}
                      {booking.owner_response && (
                        <div className="mt-3 p-3 rounded-md bg-accent">
                          <p className="text-xs text-muted-foreground mb-1">Owner response:</p>
                          <p className="text-sm">{booking.owner_response}</p>
                        </div>
                      )}
                    </div>
                    <Badge className={config.className}>
                      <config.icon className="h-3 w-3 mr-1" /> {config.label}
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}