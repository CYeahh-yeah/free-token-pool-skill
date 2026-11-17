'use strict';
// Only transfers credentials between this user's local WorkDaddy and 9Router.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const wd = path.resolve(__dirname, '../workdaddy-local/scripts');
const {wdCompatDecryptAuthJson} = require(path.join(wd, 'lib.js'));
const {refreshAuthToken, shouldRefreshAccessToken} = require(path.join(wd, 'token-refresh.js'));
const dataDir = path.join(os.homedir(), 'Library/Application Support/WorkDaddy');
const authFile = path.join(os.homedir(), 'Library/Application Support/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info');
const cache = new Map();
async function router(route, body, method = 'POST') {
  const r = await fetch('http://127.0.0.1:20128/api/' + route, {
    method: body ? method : 'GET', headers: {'Content-Type':'application/json'},
    body: body ? JSON.stringify(body) : undefined, signal: AbortSignal.timeout(15000),
  });
  if (!r.ok) throw new Error('9Router HTTP ' + r.status);
  return r.json();
}
async function sync() {
  const {connections} = await router('providers');
  const files = fs.readdirSync(path.join(dataDir, 'accounts')).filter(f => f.endsWith('.info'));
  for (const file of files) {
    let root = wdCompatDecryptAuthJson(JSON.parse(fs.readFileSync(path.join(dataDir, 'accounts', file), 'utf8')));
    const uid = root.account?.uid;
    if (!uid || !root.auth) continue;
    // Prefer current official credentials after the desktop app refreshes them.
    if (fs.existsSync(authFile)) {
      const current = wdCompatDecryptAuthJson(JSON.parse(fs.readFileSync(authFile, 'utf8')));
      if (current.account?.uid === uid && Number(current.auth?.lastRefreshTime || 0) >= Number(root.auth.lastRefreshTime || 0)) root = current;
    }
    const signature = root.auth.accessToken;
    if (typeof signature !== 'string' || !signature) throw new Error('WorkBuddy credential unavailable');
    let saved = cache.get(uid);
    if (!saved || saved.source !== signature) saved = {source: signature, auth: root.auth};
    if (shouldRefreshAccessToken(saved.auth, Date.now(), 300000)) {
      const result = await refreshAuthToken(saved.auth, {apiHost:'https://www.workbuddy.cn', fetchImpl:(url, init) => fetch(url, {...init,signal:AbortSignal.timeout(15000)})});
      if (!result.ok) throw new Error('WorkBuddy credential refresh failed');
      saved.auth = result.auth;
    }
    const name = 'WorkBuddy · ' + (typeof root.account.nickname === 'string' ? root.account.nickname : uid);
    const connection = connections.find(c => c.provider === 'codebuddy-cn' && (c.providerSpecificData?.workbuddyUid === uid || c.name === name));
    if (!connection || saved.synced !== saved.auth.accessToken) {
      const payload = {name, apiKey:saved.auth.accessToken, providerSpecificData:{workbuddyUid:uid}};
      if (connection) await router('providers/' + connection.id, payload, 'PUT');
      else await router('providers', {...payload,provider:'codebuddy-cn',defaultModel:'glm-5.3-flash'});
      saved.synced = saved.auth.accessToken;
      console.log(new Date().toISOString(), 'credential synced for local account');
    }
    cache.set(uid, saved);
  }
}
async function tick() { try { await sync(); } catch(e) { console.error(new Date().toISOString(), 'sync failed:', e.message.startsWith('9Router HTTP') ? e.message : 'local credential or upstream refresh error'); process.exitCode = 1; } }
(async()=>{await tick(); if (!process.argv.includes('--once')) {process.exitCode=0;setInterval(tick,300000);}})();
