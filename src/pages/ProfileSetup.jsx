import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { base44 } from '@/api/base44Client';

const skillLevels = [
  { value: 'beginner', label: 'Beginner', desc: 'New to riding or limited experience' },
  { value: 'intermediate', label: 'Intermediate', desc: 'Comfortable with basic gaits and control' },
  { value: 'advanced', label: 'Advanced', desc: 'Experienced in multiple disciplines' },
];

export default function ProfileSetup() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    riding_skill_level: 'beginner',
    roles: ['rider'],
    bio: '',
    city: '',
    state: '',
    phone: '',
  });

  useEffect(() => {
    base44.auth.isAuthenticated().then(async (authed) => {
      if (!authed) { navigate('/login'); return; }
      try {
        const u = await base44.auth.me();
        setUser(u);
        setForm({
          full_name: u.full_name || '',
          riding_skill_level: u.riding_skill_level || 'beginner',
          roles: u.roles || ['rider'],
          bio: u.bio || '',
          city: u.city || '',
          state: u.state || '',
          phone: u.phone || '',
        });
      } catch {}
      setLoading(false);
    });
  }, [navigate]);

  const toggleRole = (role) => {
    const roles = form.roles.includes(role)
      ? form.roles.filter(r => r !== role)
      : [...form.roles, role];
    if (roles.length === 0) roles.push('rider');
    setForm({ ...form, roles });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await base44.auth.updateMe({
        full_name: form.full_name,
        riding_skill_level: form.riding_skill_level,
        roles: form.roles,
        bio: form.bio,
        city: form.city,
        state: form.state,
        phone: form.phone,
      });
      navigate(form.roles.includes('owner') ? '/owner/dashboard' : '/dashboard');
    } catch (err) {
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="pt-20 min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="pt-20 min-h-screen px-4 py-12">
      <div className="mx-auto max-w-2xl">
        <div className="text-center mb-10">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
            <Shield className="h-6 w-6 text-primary" />
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-semibold">Complete Your Profile</h1>
          <p className="mt-2 text-muted-foreground">Tell us about your riding experience so owners can trust you.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-lg border border-border bg-card p-6 sm:p-8">
          <div>
            <Label htmlFor="full_name">Full Name</Label>
            <Input id="full_name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Your full name" className="mt-1.5 h-11" />
          </div>

          <div>
            <Label>Riding Skill Level</Label>
            <div className="mt-2 space-y-2">
              {skillLevels.map((level) => (
                <button
                  key={level.value}
                  type="button"
                  onClick={() => setForm({ ...form, riding_skill_level: level.value })}
                  className={`w-full text-left p-4 rounded-lg border transition-colors ${
                    form.riding_skill_level === level.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{level.label}</p>
                      <p className="text-sm text-muted-foreground">{level.desc}</p>
                    </div>
                    {form.riding_skill_level === level.value && <Check className="h-5 w-5 text-primary" />}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <Label>I want to</Label>
            <div className="mt-2 flex gap-3">
              {[
                { value: 'rider', label: 'Ride' },
                { value: 'owner', label: 'List Animals' },
              ].map((role) => (
                <button
                  key={role.value}
                  type="button"
                  onClick={() => toggleRole(role.value)}
                  className={`flex-1 p-4 rounded-lg border transition-colors ${
                    form.roles.includes(role.value)
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-border hover:border-primary/40'
                  }`}
                >
                  <span className="font-medium">{role.label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="city">City</Label>
              <Input id="city" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}
                placeholder="City" className="mt-1.5 h-11" />
            </div>
            <div>
              <Label htmlFor="state">State</Label>
              <Input id="state" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })}
                placeholder="State" className="mt-1.5 h-11" />
            </div>
          </div>

          <div>
            <Label htmlFor="phone">Phone (optional)</Label>
            <Input id="phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
              placeholder="Phone number" className="mt-1.5 h-11" />
          </div>

          <div>
            <Label htmlFor="bio">Bio (optional)</Label>
            <Textarea id="bio" rows={3} value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })}
              placeholder="Tell owners about your riding experience..." className="mt-1.5" />
          </div>

          <Button type="submit" disabled={saving} className="w-full h-12 text-base">
            {saving ? 'Saving...' : 'Save Profile'}
          </Button>
        </form>
      </div>
    </div>
  );
}