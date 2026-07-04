import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Compass } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ThemeToggle from '@/components/ThemeToggle';
import UserMenu from '@/components/UserMenu';

const navLinks = [
  { label: 'Browse', path: '/listings' },
  { label: 'How it Works', path: '/#how-it-works' },
  { label: 'For Owners', path: '/owner/dashboard' },
];

export default function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';
  const transparent = isHome && !scrolled;

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        transparent
          ? 'bg-transparent border-transparent'
          : 'bg-background/95 backdrop-blur-md border-b border-border'
      }`}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-20 items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <Compass className={`h-6 w-6 transition-colors ${transparent ? 'text-primary' : 'text-primary'}`} />
            <span className={`font-heading text-xl font-semibold tracking-tight ${transparent ? 'text-white' : 'text-foreground'}`}>
              RideConnect
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-medium transition-colors hover:text-primary ${
                  transparent ? 'text-white/80' : 'text-muted-foreground'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden sm:block">
              <ThemeToggle />
            </div>
            <UserMenu />
            <button
              className="md:hidden p-2"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Menu"
            >
              {mobileOpen
                ? <X className={`h-5 w-5 ${transparent ? 'text-white' : 'text-foreground'}`} />
                : <Menu className={`h-5 w-5 ${transparent ? 'text-white' : 'text-foreground'}`} />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-background border-b border-border">
          <nav className="flex flex-col px-4 py-4 gap-3">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileOpen(false)}
                className="text-sm font-medium text-muted-foreground hover:text-primary py-2"
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-2 border-t border-border">
              <ThemeToggle />
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}