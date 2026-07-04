import { useState } from 'react';
import { GitBranch, GitPullRequest, Plus, RefreshCw, ExternalLink, CheckCircle2, GitMerge, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { base44 } from '@/api/base44Client';

export default function GithubManager() {
  const [repos, setRepos] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState('');
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [prs, setPrs] = useState([]);
  const [loadingData, setLoadingData] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', body: '', labels: '' });
  const [creating, setCreating] = useState(false);
  const [actionLoading, setActionLoading] = useState({});

  const fetchRepos = async () => {
    setLoadingRepos(true);
    try {
      const res = await base44.functions.invoke('githubManager', { action: 'list_repos' });
      setRepos(res.data);
    } catch {}
    setLoadingRepos(false);
  };

  const fetchData = async (fullName) => {
    const [owner, repo] = fullName.split('/');
    setLoadingData(true);
    try {
      const [tasksRes, prsRes] = await Promise.all([
        base44.functions.invoke('githubManager', { action: 'list_tasks', owner, repo }),
        base44.functions.invoke('githubManager', { action: 'list_prs', owner, repo }),
      ]);
      setTasks(tasksRes.data);
      setPrs(prsRes.data);
    } catch {
      setTasks([]);
      setPrs([]);
    }
    setLoadingData(false);
  };

  const handleRepoSelect = (value) => {
    setSelectedRepo(value);
    setShowCreate(false);
    fetchData(value);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    const [owner, repo] = selectedRepo.split('/');
    setCreating(true);
    try {
      await base44.functions.invoke('githubManager', {
        action: 'create_task', owner, repo,
        title: newTask.title,
        body: newTask.body,
        labels: newTask.labels ? newTask.labels.split(',').map(l => l.trim()).filter(Boolean) : [],
      });
      setNewTask({ title: '', body: '', labels: '' });
      setShowCreate(false);
      fetchData(selectedRepo);
    } catch {}
    setCreating(false);
  };

  const handleClose = async (number) => {
    const [owner, repo] = selectedRepo.split('/');
    setActionLoading(prev => ({ ...prev, [`task-${number}`]: true }));
    try {
      await base44.functions.invoke('githubManager', { action: 'close_task', owner, repo, number });
      setTasks(tasks.filter(t => t.number !== number));
    } catch {}
    setActionLoading(prev => ({ ...prev, [`task-${number}`]: false }));
  };

  const handleMerge = async (number) => {
    const [owner, repo] = selectedRepo.split('/');
    setActionLoading(prev => ({ ...prev, [`pr-${number}`]: true }));
    try {
      await base44.functions.invoke('githubManager', { action: 'merge_pr', owner, repo, number });
      setPrs(prs.filter(p => p.number !== number));
    } catch {}
    setActionLoading(prev => ({ ...prev, [`pr-${number}`]: false }));
  };

  return (
    <div className="pt-20 min-h-screen px-4 sm:px-6 lg:px-8 py-12">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <h1 className="font-heading text-3xl sm:text-4xl font-semibold flex items-center gap-3">
            <GitBranch className="h-8 w-8 text-primary" /> Development Tasks
          </h1>
          <p className="mt-2 text-muted-foreground">Manage issues and pull requests across your repositories.</p>
        </div>

        <div className="mb-6 flex flex-col sm:flex-row gap-3">
          <Select onOpenChange={(open) => { if (open && repos.length === 0) fetchRepos(); }} value={selectedRepo} onValueChange={handleRepoSelect}>
            <SelectTrigger className="w-full sm:w-80 h-11">
              <SelectValue placeholder={loadingRepos ? 'Loading repos...' : 'Select a repository'} />
            </SelectTrigger>
            <SelectContent>
              {repos.map(r => (
                <SelectItem key={r.id} value={r.full_name}>
                  <span className="truncate">{r.full_name}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedRepo && (
            <Button variant="outline" onClick={() => fetchData(selectedRepo)} disabled={loadingData} className="h-11">
              <RefreshCw className={`mr-2 h-4 w-4 ${loadingData ? 'animate-spin' : ''}`} /> Refresh
            </Button>
          )}
        </div>

        {!selectedRepo ? (
          <div className="rounded-lg border border-dashed border-border p-16 text-center">
            <GitBranch className="mx-auto h-10 w-10 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">Select a repository to view and manage its tasks and pull requests.</p>
          </div>
        ) : (
          <Tabs defaultValue="tasks">
            <TabsList className="mb-6">
              <TabsTrigger value="tasks">
                <Plus className="mr-1.5 h-3.5 w-3.5" /> Issues ({tasks.length})
              </TabsTrigger>
              <TabsTrigger value="prs">
                <GitPullRequest className="mr-1.5 h-3.5 w-3.5" /> Pull Requests ({prs.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="tasks" className="space-y-3">
              <Button onClick={() => setShowCreate(!showCreate)} variant="outline" className="w-full h-11 justify-start">
                <Plus className="mr-2 h-4 w-4" /> {showCreate ? 'Cancel' : 'New Issue'}
              </Button>

              {showCreate && (
                <form onSubmit={handleCreate} className="rounded-lg border border-border bg-card p-6 space-y-4">
                  <div>
                    <Label htmlFor="title">Title</Label>
                    <Input id="title" required value={newTask.title}
                      onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                      placeholder="Issue title" className="mt-1.5 h-11" />
                  </div>
                  <div>
                    <Label htmlFor="body">Description</Label>
                    <Textarea id="body" rows={4} value={newTask.body}
                      onChange={(e) => setNewTask({ ...newTask, body: e.target.value })}
                      placeholder="Describe the task..." className="mt-1.5" />
                  </div>
                  <div>
                    <Label htmlFor="labels">Labels (comma-separated)</Label>
                    <Input id="labels" value={newTask.labels}
                      onChange={(e) => setNewTask({ ...newTask, labels: e.target.value })}
                      placeholder="bug, frontend, ui" className="mt-1.5 h-11" />
                  </div>
                  <Button type="submit" disabled={creating} className="h-11">
                    {creating ? 'Creating...' : 'Create Issue'}
                  </Button>
                </form>
              )}

              {loadingData ? (
                <div className="flex justify-center py-12"><div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" /></div>
              ) : tasks.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border p-12 text-center text-muted-foreground">No open issues. Nice work!</div>
              ) : (
                tasks.map(task => (
                  <div key={task.number} className="p-4 rounded-lg border border-border bg-card flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-muted-foreground">#{task.number}</span>
                        <h3 className="font-medium truncate">{task.title}</h3>
                      </div>
                      {task.labels?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {task.labels.map(label => <Badge key={label} variant="secondary" className="text-xs">{label}</Badge>)}
                        </div>
                      )}
                      <p className="mt-1 text-xs text-muted-foreground">
                        opened by {task.user} · {task.assignee ? `assigned to ${task.assignee}` : 'unassigned'}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <a href={task.html_url} target="_blank" rel="noreferrer">
                        <Button variant="ghost" size="icon" className="h-8 w-8"><ExternalLink className="h-4 w-4" /></Button>
                      </a>
                      <Button variant="ghost" size="sm" onClick={() => handleClose(task.number)} disabled={actionLoading[`task-${task.number}`]}>
                        <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Close
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>

            <TabsContent value="prs" className="space-y-3">
              {loadingData ? (
                <div className="flex justify-center py-12"><div className="w-8 h-8 border-4 border-border border-t-primary rounded-full animate-spin" /></div>
              ) : prs.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border p-12 text-center text-muted-foreground">No open pull requests.</div>
              ) : (
                prs.map(pr => (
                  <div key={pr.number} className="p-4 rounded-lg border border-border bg-card flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-muted-foreground">#{pr.number}</span>
                        <h3 className="font-medium truncate">{pr.title}</h3>
                        {pr.draft && <Badge variant="outline" className="text-xs">Draft</Badge>}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {pr.head} → {pr.base} · by {pr.user}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <a href={pr.html_url} target="_blank" rel="noreferrer">
                        <Button variant="ghost" size="icon" className="h-8 w-8"><ExternalLink className="h-4 w-4" /></Button>
                      </a>
                      <Button size="sm" onClick={() => handleMerge(pr.number)} disabled={actionLoading[`pr-${pr.number}`] || pr.draft}>
                        <GitMerge className="mr-1 h-3.5 w-3.5" /> {actionLoading[`pr-${pr.number}`] ? 'Merging...' : 'Merge'}
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  );
}