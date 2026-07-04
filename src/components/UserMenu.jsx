import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { LayoutDashboard, LogOut, User, Shield, ChevronDown } from 'lucide-react';
import { base44 } from '@/api/base44Client';

export default function UserMenu() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    base44.auth.isAuthenticated().then(async (authed) => {
      if (authed) {
        try { setUser(await base44.auth.me()); } catch {}
      }
    });
  }, []);

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Button variant="ghost" onClick={() => navigate('/login')} className="text-sm">Sign In</Button>
        <Button onClick={() => navigate('/register')} className="text-sm">Get Started</Button>
      </div>
    );
  }

  const initials = (user.full_name || user.email || 'U').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  const isOwner = (user.roles || []).includes('owner');

  const handleLogout = async () => {
    await base44.auth.logout();
    window.location.href = '/';
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-full p-1 pr-2 hover:bg-accent transition-colors">
          <Avatar className="h-8 w-8 border border-border">
            <AvatarImage src={user.avatar_url} />
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">{initials}</AvatarFallback>
          </Avatar>
          <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5">
          <p className="text-sm font-medium truncate">{user.full_name || 'Member'}</p>
          <p className="text-xs text-muted-foreground truncate">{user.email}</p>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/dashboard')}>
          <LayoutDashboard className="mr-2 h-4 w-4" /> Dashboard
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => navigate('/profile/setup')}>
          <User className="mr-2 h-4 w-4" /> Profile
        </DropdownMenuItem>
        {isOwner && (
          <DropdownMenuItem onClick={() => navigate('/owner/dashboard')}>
            <Shield className="mr-2 h-4 w-4" /> Owner Panel
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
          <LogOut className="mr-2 h-4 w-4" /> Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}