import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Users, Compass, Award, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ListingCard from '@/components/ListingCard';
import { base44 } from '@/api/base44Client';

const heroImage = 'https://images.unsplash.com/photo-1534068590799-09895a701e3e?w=1920&q=80';

const steps = [
  { icon: Users, title: 'Create your profile', desc: 'Set your riding skill level and get verified. Owners trust riders who are transparent about their experience.' },
  { icon: Compass, title: 'Browse verified listings', desc: 'Explore riding experiences from trusted owners. Filter by skill level, discipline, and location.' },
  { icon: Shield, title: 'Connect & ride', desc: 'Request a booking, message the owner, and enjoy a safe, vetted riding experience.' },
];

const values = [
  { icon: Shield, title: 'Trust First', desc: 'Every rider is verified. Every owner is vetted. Safety is not optional.' },
  { icon: Award, title: 'Quality Experiences', desc: 'Curated listings from passionate animal owners who care about their animals and riders.' },
  { icon: Users, title: 'Community Driven', desc: 'Built on friend invites and verified connections, not anonymous strangers.' },
];

export default function Home() {
  const [listings, setListings] = useState([]);

  useEffect(() => {
    base44.entities.Listing.filter({ status: 'active' }, '-created_date', 6)
      .then(setListings)
      .catch(() => {});
  }, []);

  return (
    <div>
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img src={heroImage} alt="Horse in misty field" className="h-full w-full object-cover" />
          <div className="absolute inset-0 hero-overlay" />
        </div>
        <div className="relative z-10 mx-auto max-w-4xl px-4 text-center pt-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
          >
            <span className="inline-block px-4 py-1.5 rounded-full bg-primary/10 border border-primary/30 text-primary text-xs font-medium tracking-wide uppercase mb-6">
              Trust-First Riding Marketplace
            </span>
            <h1 className="font-heading text-5xl sm:text-6xl lg:text-7xl font-semibold text-white leading-[1.05] text-balance">
              Where riders and owners connect with confidence
            </h1>
            <p className="mt-6 text-lg sm:text-xl text-white/70 max-w-2xl mx-auto leading-relaxed">
              Discover verified riding experiences from trusted animal owners. Every listing is vetted, every rider is certified.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 h-12 text-base">
                <Link to="/listings">Browse Listings <ArrowRight className="ml-2 h-4 w-4" /></Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="border-white/30 text-white bg-white/5 backdrop-blur hover:bg-white/10 px-8 h-12 text-base">
                <Link to="/register">Join as Rider</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <span className="text-xs font-medium tracking-wide uppercase text-primary">How it Works</span>
            <h2 className="mt-2 font-heading text-4xl sm:text-5xl font-semibold">A simpler way to ride</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.15 }}
                className="relative p-8 rounded-lg border border-border bg-card"
              >
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                  <step.icon className="h-6 w-6 text-primary" />
                </div>
                <span className="absolute top-8 right-8 font-heading text-5xl font-bold text-muted/30">{i + 1}</span>
                <h3 className="font-heading text-xl font-semibold">{step.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured listings */}
      <section className="py-24 px-4 bg-card">
        <div className="mx-auto max-w-7xl">
          <div className="flex items-end justify-between mb-12">
            <div>
              <span className="text-xs font-medium tracking-wide uppercase text-primary">Featured</span>
              <h2 className="mt-2 font-heading text-4xl sm:text-5xl font-semibold">Curated experiences</h2>
            </div>
            <Link to="/listings" className="hidden sm:flex items-center gap-1 text-sm font-medium text-primary hover:underline">
              View all <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {listings.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        </div>
      </section>

      {/* Value props */}
      <section className="py-24 px-4">
        <div className="mx-auto max-w-7xl">
          <div className="text-center mb-16">
            <span className="text-xs font-medium tracking-wide uppercase text-primary">Why RideConnect</span>
            <h2 className="mt-2 font-heading text-4xl sm:text-5xl font-semibold">Built on trust</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {values.map((value, i) => (
              <div key={i} className="text-center p-8">
                <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                  <value.icon className="h-7 w-7 text-primary" />
                </div>
                <h3 className="font-heading text-xl font-semibold">{value.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground leading-relaxed max-w-xs mx-auto">{value.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4">
        <div className="mx-auto max-w-4xl rounded-2xl overflow-hidden relative">
          <img src="https://images.unsplash.com/photo-1554454741-5dd2a9c1c7c4?w=1920&q=80" alt="" className="absolute inset-0 h-full w-full object-cover" />
          <div className="absolute inset-0 bg-gradient-to-r from-background via-background/90 to-background/40" />
          <div className="relative p-12 sm:p-16">
            <h2 className="font-heading text-4xl sm:text-5xl font-semibold text-balance">Ready to ride?</h2>
            <p className="mt-4 text-muted-foreground max-w-md">Join RideConnect today and connect with verified owners for your next riding experience.</p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90 px-8 h-12 text-base">
                <Link to="/register">Create Account</Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="px-8 h-12 text-base">
                <Link to="/listings">Browse Listings</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}