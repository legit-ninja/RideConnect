import { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, CalendarDays } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const statusConfig = {
  pending: 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-500 border-yellow-500/30',
  approved: 'bg-green-500/15 text-green-600 dark:text-green-500 border-green-500/30',
  declined: 'bg-red-500/15 text-red-600 dark:text-red-500 border-red-500/30',
  completed: 'bg-primary/15 text-primary border-primary/30',
  cancelled: 'bg-muted text-muted-foreground border-border',
};

const dotConfig = {
  pending: 'bg-yellow-500',
  approved: 'bg-green-500',
  declined: 'bg-red-500',
  completed: 'bg-primary',
  cancelled: 'bg-muted-foreground',
};

function pad(n) { return String(n).padStart(2, '0'); }
function toDateString(year, month, day) { return `${year}-${pad(month + 1)}-${pad(day)}`; }

export default function BookingsCalendar({ bookings, onSelectDate }) {
  const today = new Date();
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState(null);

  const bookingsByDate = useMemo(() => {
    const map = {};
    for (const b of bookings) {
      if (!b.requested_date) continue;
      if (!map[b.requested_date]) map[b.requested_date] = [];
      map[b.requested_date].push(b);
    }
    return map;
  }, [bookings]);

  const calendarDays = useMemo(() => {
    const firstDay = new Date(viewYear, viewMonth, 1);
    const startWeekday = firstDay.getDay();
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();

    const cells = [];
    for (let i = 0; i < startWeekday; i++) cells.push(null);
    for (let d = 1; d <= daysInMonth; d++) cells.push(d);
    return cells;
  }, [viewYear, viewMonth]);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewMonth(11); setViewYear(viewYear - 1); }
    else setViewMonth(viewMonth - 1);
  };

  const nextMonth = () => {
    if (viewMonth === 11) { setViewMonth(0); setViewYear(viewYear + 1); }
    else setViewMonth(viewMonth + 1);
  };

  const goToday = () => {
    setViewYear(today.getFullYear());
    setViewMonth(today.getMonth());
  };

  const handleDayClick = (day) => {
    const dateStr = toDateString(viewYear, viewMonth, day);
    setSelectedDate(dateStr);
    if (onSelectDate) onSelectDate(dateStr);
  };

  const selectedBookings = selectedDate ? (bookingsByDate[selectedDate] || []) : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <div className="rounded-lg border border-border bg-card p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-heading text-xl font-semibold">
              {MONTHS[viewMonth]} {viewYear}
            </h3>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={prevMonth} className="h-8 w-8">
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={goToday} className="h-8 px-3 text-xs">
                Today
              </Button>
              <Button variant="ghost" size="icon" onClick={nextMonth} className="h-8 w-8">
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-7 gap-1 mb-2">
            {WEEKDAYS.map((wd) => (
              <div key={wd} className="text-center text-xs font-medium text-muted-foreground py-2">
                {wd}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {calendarDays.map((day, idx) => {
              if (day === null) return <div key={`empty-${idx}`} />;
              const dateStr = toDateString(viewYear, viewMonth, day);
              const dayBookings = bookingsByDate[dateStr] || [];
              const hasBookings = dayBookings.length > 0;
              const isToday = today.getFullYear() === viewYear && today.getMonth() === viewMonth && today.getDate() === day;
              const isSelected = selectedDate === dateStr;

              return (
                <button
                  key={day}
                  onClick={() => handleDayClick(day)}
                  className={`relative aspect-square sm:aspect-[4/3] rounded-md border text-left p-1.5 transition-colors flex flex-col
                    ${isSelected ? 'border-primary bg-primary/5' : hasBookings ? 'border-border bg-card hover:border-primary/40' : 'border-transparent hover:bg-accent/50'}
                    ${isToday && !isSelected ? 'ring-1 ring-primary/30' : ''}
                  `}
                >
                  <span className={`text-xs font-medium ${isToday ? 'text-primary' : 'text-foreground'}`}>
                    {day}
                  </span>
                  {hasBookings && (
                    <div className="mt-auto flex items-center gap-0.5 flex-wrap">
                      {dayBookings.slice(0, 3).map((b, i) => (
                        <span key={i} className={`h-1.5 w-1.5 rounded-full ${dotConfig[b.status] || 'bg-muted-foreground'}`} />
                      ))}
                      {dayBookings.length > 3 && (
                        <span className="text-[10px] text-muted-foreground">+{dayBookings.length - 3}</span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          <div className="mt-6 flex flex-wrap gap-3 pt-4 border-t border-border">
            {Object.entries(dotConfig).map(([status, color]) => (
              <div key={status} className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${color}`} />
                <span className="text-xs text-muted-foreground capitalize">{status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-1">
        <div className="rounded-lg border border-border bg-card p-4 sm:p-6 sticky top-24">
          <div className="flex items-center gap-2 mb-4">
            <CalendarDays className="h-5 w-5 text-primary" />
            <h3 className="font-heading text-lg font-semibold">
              {selectedDate ? new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) : 'Select a date'}
            </h3>
          </div>

          {!selectedDate ? (
            <p className="text-sm text-muted-foreground">Click any day on the calendar to see booking requests scheduled for that date.</p>
          ) : selectedBookings.length === 0 ? (
            <p className="text-sm text-muted-foreground">No booking requests for this date.</p>
          ) : (
            <div className="space-y-3">
              {selectedBookings.map((booking) => (
                <div key={booking.id} className="p-3 rounded-md border border-border bg-background">
                  <p className="font-medium text-sm">{booking.listing_title || 'Untitled listing'}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">From {booking.rider_name || 'Unknown rider'}</p>
                  {booking.requested_time && (
                    <p className="text-xs text-muted-foreground mt-0.5">Time: {booking.requested_time}</p>
                  )}
                  <Badge variant="outline" className={`mt-2 text-xs capitalize border ${statusConfig[booking.status] || ''}`}>
                    {booking.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}