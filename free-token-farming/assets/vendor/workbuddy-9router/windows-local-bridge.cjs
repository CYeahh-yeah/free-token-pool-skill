'use strict';

// Current Windows WorkBuddy login -> same-machine 9Router provider API.
// Read the existing unencrypted local session only. Leave vendor files untouched.
const fs = require('node:fs/promises');
const path = require('node:path');
const BASE = 'http://127.0.0.1:20128';
const PROVIDER = 'codebuddy-cn';
const NAME = 'WorkBuddy Windows local';
const POLL_MS = 60_000;
const file = process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA,
  'CodeBuddyExtension', 'Data', 'Public', 'auth', 'workbuddy-desktop.info');

function fail(message) { throw new Error(message); }
function safeError(e) { return e instanceof Error && /^(WorkBuddy|9Router|Windows)/.test(e.message) ? e.message : 'Local bridge operation failed'; }
async function readSession() {
  if (!file || process.platform !== 'win32') fail('Windows local profile is required');
  let source;
  try { source = await fs.readFile(file, 'utf8'); }
  catch { fail('WorkBuddy login file is unavailable; sign in on Windows first'); }
  let root;
  try { root = JSON.parse(source.replace(/^\uFEFF/, '')); }
  catch { fail('WorkBuddy login file is unreadable'); }
  const uid = root.account?.uid;
  const token = root.auth?.accessToken;
  if (typeof token !== 'string') fail('WorkBuddy has no directly readable access token; use a supported sign-in or export');
  if (!/^[A-Za-z0-9_-]{1,128}$/.test(String(uid ?? '')) || token.length < 30)
    fail('WorkBuddy local session is missing account or token fields');
  if (token.split('.').length === 3) {
    let exp;
    try { exp = JSON.parse(Buffer.from(token.split('.')[1], 'base64url')).exp; }
    catch { fail('WorkBuddy local session format is invalid'); }
    if (Number.isFinite(exp) && exp * 1000 <= Date.now() + 15000)
      fail('WorkBuddy local session is expired; reopen WorkBuddy or sign in again');
  }
  return { uid: String(uid), token };
}
async function router(subpath, method='GET', payload) {
  const r = await fetch(BASE + '/api/providers' + subpath, {
    method, redirect:'error', signal:AbortSignal.timeout(12000),
    headers: payload ? {'content-type':'application/json','origin':BASE} : {},
    body: payload ? JSON.stringify(payload) : undefined,
  }).catch(() => fail('9Router local provider API is unreachable'));
  if (!r.ok) { await r.body?.cancel(); fail('9Router provider API HTTP ' + r.status); }
  return r.json();
}
async function providerList() {
  const { connections } = await router('');
  if (!Array.isArray(connections)) fail('9Router provider API response is unexpected');
  return connections;
}
async function sync(session, allowCreate) {
  const connections = await providerList();
  const own = connections.find(c=>c.provider===PROVIDER && c.name===NAME);
  if (own && String(own.providerSpecificData?.workbuddyUid ?? '') !== session.uid)
    fail('9Router bridge belongs to a different WorkBuddy account; no change was made');
  if (own && !own.isActive) fail('9Router bridge connection is disabled; it was left disabled');
  if (!own && !allowCreate) fail('9Router bridge connection not present');
  const payload = {name: NAME, apiKey: session.token, providerSpecificData:{workbuddyUid:session.uid}};
  if (own) await router('/'+encodeURIComponent(own.id), 'PUT', payload);
  else await router('', 'POST', {...payload, provider:PROVIDER, defaultModel:'glm-5.3-flash'});
  const verified=(await providerList()).find(c=>c.provider===PROVIDER && c.name===NAME);
  if (!verified?.isActive || String(verified.providerSpecificData?.workbuddyUid ?? '')!==session.uid)
    fail('9Router did not return the expected active WorkBuddy connection');
}
async function main() {
  const mode=process.argv[2]||'--check';
  if (!['--check','--once','--watch'].includes(mode)) fail('Windows bridge: invalid mode');
  const session=await readSession();
  const connections=await providerList();
  console.log('WorkBuddy Windows local session readable; 9Router provider API reachable.');
  if (mode==='--check') {
    const present=connections.some(c=>c.provider===PROVIDER && c.name===NAME);
    console.log(present ? 'Local bridge connection already exists.' : 'No bridge connection yet. No changes made.');
    return;
  }
  await sync(session,true);
  console.log('Verified active: WorkBuddy Windows local / cbcn.');
  if (mode==='--once') return;
  let previous=session.token;
  let inFlight=false;
  setInterval(async()=>{
    if (inFlight) return;
    inFlight=true;
    try {
      const next=await readSession();
      if (next.uid!==session.uid) fail('WorkBuddy account changed; bridge stopped without overwriting it');
      if (next.token!==previous) {await sync(next,false);previous=next.token;console.log('WorkBuddy session updated locally.');}
    } catch(e) {
      console.error(safeError(e));
      if (/account changed|disabled|not present/.test(safeError(e))) process.exit(1);
    } finally { inFlight=false; }
  },POLL_MS);
}
main().catch(e=>{console.error(safeError(e));process.exitCode=1;});
