import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { base44 } from '@/api/base44Client';

export default function EditListing() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [photoUrl, setPhotoUrl] = useState('');
  const [form, setForm] = useState(null);

  useEffect(() => {
    base44.entities.Listing.filter({ id })
      .then((data) => {
        if (data.length > 0) setForm(data[0]);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const addPhoto = () => {
    if (photoUrl.trim()) {
      setForm({ ...form, photos: [...(form.photos || []), photoUrl.trim()] });
      setPhotoUrl('');
    }
  };

  const removePhoto = (idx) => {
    setForm({ ...form, photos: form.photos.filter((_, i) => i !== idx) });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await base44.entities.Listing.update(id, form);
      navigate('/owner/dashboard');
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

  if (!form) {
    return <div className="pt-20"><p className="text-center text-muted-foreground py-20">Listing not found.</p></div>;
  }

  return (
    <div className="pt-20 min-h-screen px-4 sm:px-6 lg:px-8 py-12">
      <div className="mx-auto max-w-2xl">
        <Link to="/owner/dashboard" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-primary mb-6">
          <ArrowLeft className="h-4 w-4" /> Back to dashboard
        </Link>

        <h1 className="font-heading text-3xl sm:text-4xl font-semibold mb-8">Edit Listing</h1>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-lg border border-border bg-card p-6 sm:p-8">
          <div>
            <Label htmlFor="title">Listing Title</Label>
            <Input id="title" required value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="mt-1.5 h-11" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="animal_name">Animal Name</Label>
              <Input id="animal_name" required value={form.animal_name || ''}
                onChange={(e) => setForm({ ...form, animal_name: e.target.value })}
                className="mt-1.5 h-11" />
            </div>
            <div>
              <Label htmlFor="animal_breed">Breed</Label>
              <Input id="animal_breed" value={form.animal_breed || ''}
                onChange={(e) => setForm({ ...form, animal_breed: e.target.value })}
                className="mt-1.5 h-11" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Species</Label>
              <Select value={form.animal_species || 'horse'} onValueChange={(v) => setForm({ ...form, animal_species: v })}>
                <SelectTrigger className="mt-1.5 h-11"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="horse">Horse</SelectItem>
                  <SelectItem value="pony">Pony</SelectItem>
                  <SelectItem value="donkey">Donkey</SelectItem>
                  <SelectItem value="mule">Mule</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Discipline</Label>
              <Select value={form.discipline || 'general'} onValueChange={(v) => setForm({ ...form, discipline: v })}>
                <SelectTrigger className="mt-1.5 h-11"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="dressage">Dressage</SelectItem>
                  <SelectItem value="jumping">Jumping</SelectItem>
                  <SelectItem value="trail">Trail</SelectItem>
                  <SelectItem value="western">Western</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>Skill Level Required</Label>
            <Select value={form.skill_level_required || 'beginner'} onValueChange={(v) => setForm({ ...form, skill_level_required: v })}>
              <SelectTrigger className="mt-1.5 h-11"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" rows={4} value={form.description || ''}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="mt-1.5" />
          </div>

          <div>
            <Label>Photos</Label>
            <div className="mt-2 flex gap-2">
              <Input value={photoUrl} onChange={(e) => setPhotoUrl(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addPhoto(); } }}
                placeholder="Paste image URL..." className="h-11" />
              <Button type="button" onClick={addPhoto} variant="outline" className="h-11">
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {(form.photos || []).length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {form.photos.map((photo, i) => (
                  <div key={i} className="relative h-20 w-24 rounded-md overflow-hidden border border-border">
                    <img src={photo} alt="" className="h-full w-full object-cover" />
                    <button type="button" onClick={() => removePhoto(i)}
                      className="absolute top-1 right-1 p-0.5 rounded-full bg-background/80 hover:bg-background">
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="city">City</Label>
              <Input id="city" value={form.city || ''} onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="mt-1.5 h-11" />
            </div>
            <div>
              <Label htmlFor="state">State</Label>
              <Input id="state" value={form.state || ''} onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="mt-1.5 h-11" />
            </div>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-border">
            <div>
              <Label className="cursor-pointer">Free Experience</Label>
              <p className="text-sm text-muted-foreground">Offer this ride at no cost</p>
            </div>
            <Switch checked={form.is_free || false} onCheckedChange={(v) => setForm({ ...form, is_free: v })} />
          </div>

          {!form.is_free && (
            <div>
              <Label htmlFor="price">Price ($)</Label>
              <Input id="price" type="number" min="0" value={form.price || 0}
                onChange={(e) => setForm({ ...form, price: parseFloat(e.target.value) || 0 })}
                className="mt-1.5 h-11" />
            </div>
          )}

          <div>
            <Label>Status</Label>
            <Select value={form.status || 'active'} onValueChange={(v) => setForm({ ...form, status: v })}>
              <SelectTrigger className="mt-1.5 h-11"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="archived">Archived</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" disabled={saving} className="w-full h-12 text-base">
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </form>
      </div>
    </div>
  );
}