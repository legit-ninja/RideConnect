import { useState, useEffect } from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import ListingCard from '@/components/ListingCard';
import EmptyState from '@/components/EmptyState';
import { base44 } from '@/api/base44Client';

export default function BrowseListings() {
  const [allListings, setAllListings] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [species, setSpecies] = useState('all');
  const [skillLevel, setSkillLevel] = useState('all');
  const [discipline, setDiscipline] = useState('all');

  useEffect(() => {
    base44.entities.Listing.filter({ status: 'active' }, '-created_date', 50)
      .then((data) => {
        setAllListings(data);
        setFiltered(data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let result = allListings;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(l =>
        l.title?.toLowerCase().includes(q) ||
        l.animal_name?.toLowerCase().includes(q) ||
        l.city?.toLowerCase().includes(q) ||
        l.state?.toLowerCase().includes(q)
      );
    }
    if (species !== 'all') result = result.filter(l => l.animal_species === species);
    if (skillLevel !== 'all') result = result.filter(l => l.skill_level_required === skillLevel);
    if (discipline !== 'all') result = result.filter(l => l.discipline === discipline);
    setFiltered(result);
  }, [search, species, skillLevel, discipline, allListings]);

  const clearFilters = () => {
    setSearch('');
    setSpecies('all');
    setSkillLevel('all');
    setDiscipline('all');
  };

  return (
    <div className="pt-20">
      <div className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
          <h1 className="font-heading text-4xl sm:text-5xl font-semibold">Browse Listings</h1>
          <p className="mt-2 text-muted-foreground">Discover verified riding experiences near you.</p>

          <div className="mt-8 flex flex-col lg:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, horse name, or location..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 h-11"
              />
            </div>
            <Select value={species} onValueChange={setSpecies}>
              <SelectTrigger className="w-full lg:w-44 h-11"><SelectValue placeholder="Species" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Species</SelectItem>
                <SelectItem value="horse">Horse</SelectItem>
                <SelectItem value="pony">Pony</SelectItem>
                <SelectItem value="donkey">Donkey</SelectItem>
                <SelectItem value="mule">Mule</SelectItem>
              </SelectContent>
            </Select>
            <Select value={skillLevel} onValueChange={setSkillLevel}>
              <SelectTrigger className="w-full lg:w-44 h-11"><SelectValue placeholder="Skill Level" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="beginner">Beginner</SelectItem>
                <SelectItem value="intermediate">Intermediate</SelectItem>
                <SelectItem value="advanced">Advanced</SelectItem>
              </SelectContent>
            </Select>
            <Select value={discipline} onValueChange={setDiscipline}>
              <SelectTrigger className="w-full lg:w-44 h-11"><SelectValue placeholder="Discipline" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Disciplines</SelectItem>
                <SelectItem value="dressage">Dressage</SelectItem>
                <SelectItem value="jumping">Jumping</SelectItem>
                <SelectItem value="trail">Trail</SelectItem>
                <SelectItem value="western">Western</SelectItem>
                <SelectItem value="general">General</SelectItem>
              </SelectContent>
            </Select>
            {(search || species !== 'all' || skillLevel !== 'all' || discipline !== 'all') && (
              <Button variant="ghost" onClick={clearFilters} className="h-11">Clear</Button>
            )}
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-between mb-8">
          <p className="text-sm text-muted-foreground">
            {loading ? 'Loading...' : `${filtered.length} ${filtered.length === 1 ? 'listing' : 'listings'} found`}
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="rounded-lg border border-border bg-card overflow-hidden animate-pulse">
                <div className="aspect-[4/5] bg-muted" />
                <div className="p-4 space-y-2">
                  <div className="h-5 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={SlidersHorizontal}
            title="No listings found"
            description="Try adjusting your filters or search terms to find more riding experiences."
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}