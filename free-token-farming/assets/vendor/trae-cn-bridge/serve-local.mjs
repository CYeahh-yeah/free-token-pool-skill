import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { CRED_DIR, detectEnv, loadCredentials } from './src/env.js';
import { TraeProvider, startServer } from './src/openai-server.js';

const keyPath = path.join(CRED_DIR, 'relay-key');
if (!fs.existsSync(keyPath)) fs.writeFileSync(keyPath, crypto.randomBytes(32).toString('hex'), {mode: 0o600});
const apiKey = fs.readFileSync(keyPath, 'utf8').trim();
const provider = new TraeProvider({
  env: detectEnv(), credentials: loadCredentials(),
  defaultModel: 'deepseek-v4.1-flash',
  logger: {info() {}, warn() {}, error() {}},
});
if (!provider.ready) throw new Error('User authorization required');
const {server} = await startServer(provider, {host: '127.0.0.1', port: 47834, apiKey});
console.log('TRAE loopback relay listening on 127.0.0.1:47834; authentication required.');
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => server.close(() => process.exit(0)));
