import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const rawBody = await req.text();
    let body = {};
    try { body = rawBody ? JSON.parse(rawBody) : {}; } catch { body = {}; }

    const newReq = new Request(req.url, {
      method: req.method,
      headers: req.headers,
      body: rawBody,
    });
    const base44 = createClientFromRequest(newReq);
    const user = await base44.auth.me();
    if (!user) return Response.json({ error: 'Unauthorized' }, { status: 401 });

    const { accessToken } = await base44.asServiceRole.connectors.getConnection('github');
    const headers = {
      'Authorization': `Bearer ${accessToken}`,
      'Accept': 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    };

    const { action } = body;

    if (action === 'list_repos') {
      const res = await fetch('https://api.github.com/user/repos?sort=updated&per_page=50&type=all', { headers });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to fetch repos' }, { status: res.status });
      return Response.json(data.map(r => ({ id: r.id, name: r.name, full_name: r.full_name, owner: r.owner.login, private: r.private, description: r.description, html_url: r.html_url })));
    }

    const { owner, repo } = body;

    if (action === 'list_tasks') {
      const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues?state=open&per_page=50`, { headers });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to fetch issues' }, { status: res.status });
      const issues = data.filter(i => !i.pull_request);
      return Response.json(issues.map(i => ({
        number: i.number, title: i.title, body: i.body, state: i.state,
        labels: (i.labels || []).map(l => l.name), assignee: i.assignee?.login,
        created_at: i.created_at, html_url: i.html_url, user: i.user?.login,
      })));
    }

    if (action === 'list_prs') {
      const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls?state=open&per_page=50`, { headers });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to fetch PRs' }, { status: res.status });
      return Response.json(data.map(p => ({
        number: p.number, title: p.title, body: p.body, state: p.state,
        draft: p.draft, mergeable: p.mergeable, head: p.head?.ref, base: p.base?.ref,
        created_at: p.created_at, html_url: p.html_url, user: p.user?.login,
      })));
    }

    if (action === 'create_task') {
      const { title, body: issueBody, labels } = body;
      const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body: issueBody, labels: labels || [] }),
      });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to create issue' }, { status: res.status });
      return Response.json({ number: data.number, title: data.title, html_url: data.html_url, state: data.state });
    }

    if (action === 'close_task') {
      const { number } = body;
      const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/issues/${number}`, {
        method: 'PATCH',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ state: 'closed' }),
      });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to close issue' }, { status: res.status });
      return Response.json({ number: data.number, state: data.state });
    }

    if (action === 'merge_pr') {
      const { number, commit_title } = body;
      const res = await fetch(`https://api.github.com/repos/${owner}/${repo}/pulls/${number}/merge`, {
        method: 'PUT',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ commit_title: commit_title || `Merge pull request #${number}` }),
      });
      const data = await res.json();
      if (!res.ok) return Response.json({ error: data.message || 'Failed to merge PR' }, { status: res.status });
      return Response.json({ number, merged: data.merged, message: data.message });
    }

    return Response.json({ error: 'Unknown action' }, { status: 400 });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
});