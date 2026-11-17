'use strict';
/**
 * WorkBuddy direct-call script — bypasses 9router, calls the official CodeBuddy CN
 * inference endpoint directly using the locally stored WorkBuddy credential.
 *
 * Verified 2026-11-09: stream:true + CodeBuddy headers + local authorization
 * returns a real model reply from copilot.tencent.com/v2/chat/completions.
 *
 * Usage:
 *   node workbuddy-direct.js                    # use official auth file
 *   node workbuddy-direct.js "your prompt"      # custom prompt
 *
 * Does NOT store or log tokens. Credential stays in memory only.
 */
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

function resolveWdScripts() {
  for (const p of [
    path.join(__dirname, 'vendor/workdaddy-local/scripts'),
    path.join(process.env.HOME || '', 'Documents/CYeahhOS/08_AutomationOS/Integrations/workdaddy-local/scripts'),
    path.join(process.env.HOME || '', '.codex/skills/free-token-farming/assets/vendor/workdaddy-local/scripts'),
  ]) {
    try { require(path.join(p, 'lib.js')); return p; } catch { }
  }
  throw new Error('workdaddy-local/scripts not found; run assets/install.sh first');
}
const wd = resolveWdScripts();
const { wdCompatDecryptAuthJson } = require(path.join(wd, 'lib.js'));
const { shouldRefreshAccessToken } = require(path.join(wd, 'token-refresh.js'));

const authFile = path.join(os.homedir(), 'Library/Application Support/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info');
const dataDir = path.join(os.homedir(), 'Library/Application Support/WorkDaddy');

function loadAuth() {
  try {
    const root = wdCompatDecryptAuthJson(JSON.parse(fs.readFileSync(authFile, 'utf8')));
    if (root.account?.uid && root.auth) return root;
  } catch { }
  const files = fs.readdirSync(dataDir).filter(f => f.endsWith('.info'));
  for (const f of files) {
    try {
      const root = wdCompatDecryptAuthJson(JSON.parse(fs.readFileSync(path.join(dataDir, 'accounts', f), 'utf8')));
      if (root.account?.uid && root.auth) return root;
    } catch { }
  }
  throw new Error('No WorkBuddy credential available. Log in to WorkBuddy desktop once.');
}

async function callDirect(auth, prompt) {
  const rid = randomUUID();
  const model = process.env.WORKBUDDY_DIRECT_MODEL || 'glm-5.3-flash';
  const body = {
    model,
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 128,
    stream: true,
  };
  const headers = {
    Authorization: `Bearer ${auth.accessToken}`,
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
    'User-Agent': 'CLI/2.108.1 CodeBuddy/2.108.1',
    'X-Product': 'SaaS',
    'X-IDE-Type': 'CLI',
    'X-IDE-Name': 'CLI',
    'x-requested-with': 'XMLHttpRequest',
    'x-codebuddy-request': '1',
    'X-Request-ID': rid,
    'X-Conversation-ID': randomUUID(),
    'X-Conversation-Request-ID': rid,
    'X-Conversation-Message-ID': rid,
  };
  const res = await fetch('https://copilot.tencent.com/v2/chat/completions', {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${text.slice(0, 300)}`);
  }
  const raw = await res.text();
  const lines = raw.split(/\r?\n/).filter(l => l.startsWith('data:'));
  let content = '';
  for (const line of lines) {
    const payload = line.slice(5).trim();
    if (payload === '[DONE]') continue;
    try {
      const chunk = JSON.parse(payload);
      const delta = chunk.choices?.[0]?.delta?.content;
      if (typeof delta === 'string') content += delta;
    } catch { }
  }
  return content;
}

async function main() {
  const prompt = process.argv[2] || 'Reply only OK.';
  const root = loadAuth();
  console.error(`[workbuddy-direct] uid=${root.account?.uid} prompt="${prompt.slice(0, 40)}${prompt.length > 40 ? '...' : ''}"`);
  const content = await callDirect(root.auth, prompt);
  if (content) {
    console.log(content);
  } else {
    console.error('[workbuddy-direct] empty response');
    process.exitCode = 1;
  }
}
main().catch(e => { console.error('[workbuddy-direct] error:', e.message); process.exitCode = 1; });
