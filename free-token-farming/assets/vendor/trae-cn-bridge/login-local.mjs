// CYeahhOS: user-authorized browser login only; no local credential extraction.
import fs from 'node:fs';
import path from 'node:path';
import { webLogin } from './src/trae-auth.js';
import { detectEnv, saveCredentials, CRED_DIR } from './src/env.js';

fs.mkdirSync(CRED_DIR, { recursive: true, mode: 0o700 });
const urlFile = path.join(CRED_DIR, 'authorization-url.json');
try {
  const creds = await webLogin({
    ideVersion: detectEnv().ideVersion,
    onAuthorizeUrl(url) {
      const target = new URL(url);
      if (target.origin !== 'https://www.trae.cn') throw new Error('Unexpected authorization destination');
      fs.writeFileSync(urlFile, JSON.stringify({ url }), { mode: 0o600 });
      console.log('TRAE CN authorization page ready; waiting for user login and consent.');
    },
    onProgress() { console.log('Processing user-authorized login.'); },
  });
  saveCredentials(creds);
  fs.rmSync(urlFile, { force: true });
  console.log('TRAE CN login saved locally (0600). No credentials printed.');
} catch {
  fs.rmSync(urlFile, { force: true });
  console.error('TRAE CN login did not complete. No credentials printed.');
  process.exitCode = 1;
}
