import fs from 'node:fs';
import path from 'node:path';
import { CRED_DIR, detectEnv, loadCredentials } from './src/env.js';
import { TraeProvider } from './src/openai-server.js';
import { fetchQuota } from './src/quota.js';

const file = path.join(CRED_DIR, 'daily-state.json');
const lock = path.join(CRED_DIR, 'daily.lock');
const claimEnabled = process.argv.includes('--claim');
const today = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Shanghai'}).format(new Date());
let locked = false;
function save(value) {
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2), {mode:0o600});
  fs.renameSync(tmp, file);
}
try {
  fs.mkdirSync(lock, {mode:0o700}); locked = true;
  const previous = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file,'utf8')) : {};
  const env = detectEnv();
  const provider = new TraeProvider({env, credentials:loadCredentials(), logger:{info(){},warn(){}}});
  const creds = await provider.ensureFresh();
  async function post(action) {
    const r = await fetch(`https://api.trae.cn/trae/api/v2/ug/checkin_credits/${action}`, {
      method:'POST', redirect:'error', signal:AbortSignal.timeout(20000),
      headers:{'content-type':'application/json',Authorization:`Cloud-IDE-JWT ${creds.token}`,
        'x-ide-token':creds.token,'x-device-id':creds.deviceInfo.DeviceID}, body:'{}',
    });
    if (!r.ok) throw new Error('official_http_error');
    const j = await r.json();
    return Object.fromEntries(['code','enable','checked_in','did_checked_in','credits','extra_credits'].filter(k=>k in j).map(k=>[k,j[k]]));
  }
  const before = await post('status');
  let report = {...previous, platform_date:today, checked_at:new Date().toISOString(), before};
  if (before.code !== 0 || typeof before.enable !== 'boolean' || typeof before.checked_in !== 'boolean') {
    throw new Error('official_status_invalid');
  }
  if (before.checked_in) report.status='already_claimed';
  else if (!before.enable) report.status='campaign_unavailable';
  else if (!claimEnabled) report.status='eligible';
  else if (previous.attempt_date === today) report.status='attempted_today';
  else {
    // Record before transmission: even a timeout cannot trigger repeated claims.
    report={...report,attempt_date:today,status:'attempt_recorded'}; save(report);
    const claim=await post('claim');
    const after=await post('status');
    report={...report,claim_code:claim.code,after,
      status:claim.code===0 && after.checked_in===true ? 'claimed_verified' : 'claim_not_verified'};
  }
  const quota=await fetchQuota(creds,{userAgent:`Trae/${env.ideVersion}`});
  report.balance=quota.remaining;
  report.total=quota.total;
  save(report);
  console.log(JSON.stringify(report));
} catch {
  console.log(JSON.stringify({status:'trae_daily_check_failed'}));
  process.exitCode=1;
} finally {
  if (locked) fs.rmdirSync(lock);
}
