#!/usr/bin/env python3
"""Free-token onboarding and daily checks. Credentials never enter reports."""
import argparse
import datetime as dt
import fcntl
import getpass
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PRIVATE = Path.home() / 'Library/Application Support/CYeahhOS/free-token-hub'
ROUTER = 'http://localhost:20128'
TZ = ZoneInfo('America/Vancouver')
SPECS = {
    'sensenova': {'name': '商汤 TokenPlan', 'prefix': 'free-sense', 'base': 'https://token.sensenova.cn/v1', 'model': 'sensenova-6.8-flash-lite', 'renewal': 'rolling', 'claim': 'not_required'},
    'ant-ling': {'name': '蚂蚁百灵', 'prefix': 'free-ling', 'base': 'https://api.ant-ling.com/v1', 'model': None, 'renewal': 'monthly', 'claim': 'not_required'},
    'modelscope': {'name': '魔搭', 'prefix': 'free-ms', 'base': None, 'model': None, 'renewal': 'daily_login', 'claim': 'login_and_credit_readback_required'},
    'cloudflare': {'name': 'Cloudflare Workers AI', 'prefix': 'free-cf', 'base': None, 'model': None, 'renewal': 'daily_utc', 'claim': 'not_required'},
}


class Failure(Exception):
    def __init__(self, status, kind='http_error'):
        self.status, self.kind = status, kind
        super().__init__(f'{kind}: HTTP {status}')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # Never forward credentials to a redirected host.


def request(url, body=None, key=None, method=None):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        # Classify in memory, never print/store upstream response or credentials.
        raw = e.read(65536).decode(errors='replace').lower()
        kind = 'quota_exhausted' if e.code == 402 or (e.code == 429 and any(w in raw for w in ['quota', 'insufficient_credit', 'balance', '积分不足', '额度不足'])) else 'http_error'
        raise Failure(e.code, kind) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise Failure(0, 'network_or_response_error') from None


def read_json(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def chat(base, key, model):
    body = {'model': model, 'messages': [{'role': 'user', 'content': 'Reply only OK.'}], 'max_tokens': 128, 'stream': False}
    # Ling defaults to deep thinking. A tiny output budget can be consumed by
    # reasoning before any visible answer; use its documented off switch.
    if model.rsplit('/', 1)[-1].lower().startswith('ling-'):
        body['thinking'] = {'type': 'disabled'}
    for budget in (128, 1024):
        body['max_tokens'] = budget
        result = request(base + '/chat/completions', body, key)
        choices = result.get('choices') or []
        choice = choices[0] if choices else {}
        content = choice.get('message', {}).get('content')
        if isinstance(content, str) and content.strip():
            return {'status': 'ok', 'usage': result.get('usage', {})}
        # One bounded retry only for proven truncation. Reasoning alone is not
        # a successful final answer and HTTP 200 alone is not a passing probe.
        if budget == 128 and choice.get('finish_reason') in ('length', 'max_tokens'):
            continue
        kind = 'probe_output_limit' if choice.get('finish_reason') in ('length', 'max_tokens') else 'empty_model_response'
        raise Failure(200, kind)


def router_key():
    key = os.environ.get('HERMES_CUSTOM_9ROUTER_API_KEY')
    if not key:
        p = Path.home() / '.hermes/.env'
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('HERMES_CUSTOM_9ROUTER_API_KEY='):
                    key = line.split('=', 1)[1].strip().strip('\"\'')
    if not key:
        raise Failure(0, 'router_client_key_missing')
    return key


def allowed_base(provider, base):
    if provider in ('sensenova', 'ant-ling'):
        return base == SPECS[provider]['base']
    if provider == 'modelscope':
        return base == 'https://api-inference.modelscope.cn/v1'
    if provider == 'cloudflare':
        import re
        return bool(re.fullmatch(r'https://api.cloudflare.com/client/v4/accounts/[a-fA-F0-9]{32}/ai/v1', base))
    return False


def connect(provider, base, model, key):
    if not allowed_base(provider, base):
        raise ValueError('Base URL is not an approved official endpoint')
    # Validate both official and local credentials before making router changes.
    client_key = router_key()
    try:
        chat(base, key, model)
    except Failure as e:
        raise Failure(e.status, 'official_' + e.kind) from None
    spec = SPECS[provider]
    cfg = read_json(PRIVATE / 'accounts.json', {})
    nodes = request(ROUTER + '/api/provider-nodes')['nodes']
    node = next((n for n in nodes if n.get('prefix') == spec['prefix']), None)
    previous = cfg.get(provider, {})
    if node and node['id'] != previous.get('node_id'):
        raise ValueError('Prefix already exists and is not managed by this hub')
    if not node:
        result = request(ROUTER + '/api/provider-nodes', {'name': spec['name'], 'prefix': spec['prefix'], 'type': 'openai-compatible', 'apiType': 'chat', 'baseUrl': base})
        node = result.get('node', result)
        # Save ownership immediately so interrupted setup can be safely resumed.
        cfg[provider] = {**previous, 'node_id': node['id'], 'base': base, 'model': model, 'key': key, 'phase': 'node_created'}
        save(PRIVATE / 'accounts.json', cfg)
    connections = request(ROUTER + '/api/providers')['connections']
    owned = next((c for c in connections if c['id'] == previous.get('connection_id') and c['provider'] == node['id']), None)
    if not owned and any(c['provider'] == node['id'] for c in connections):
        raise ValueError('Untracked connection on managed node; inspect before continuing')
    payload = {'name': 'Free token hub · ' + provider, 'apiKey': key, 'defaultModel': model}
    if owned:
        request(ROUTER + '/api/providers/' + owned['id'], {**payload, 'isActive': True}, method='PUT')
        connection_id = owned['id']
    else:
        result = request(ROUTER + '/api/providers', {**payload, 'provider': node['id']})
        connection_id = result.get('connection', result)['id']
    cfg[provider] = {'node_id': node['id'], 'connection_id': connection_id, 'base': base, 'model': model, 'key': key, 'phase': 'testing'}
    save(PRIVATE / 'accounts.json', cfg)
    try:
        chat(ROUTER + '/v1', client_key, spec['prefix'] + '/' + model)
    except Failure:
        request(ROUTER + '/api/providers/' + connection_id, {'isActive': False}, method='PUT')
        cfg[provider]['phase'] = 'route_failed_disabled'
        save(PRIVATE / 'accounts.json', cfg)
        raise
    cfg[provider]['phase'] = 'connected'
    save(PRIVATE / 'accounts.json', cfg)
    return {'provider': provider, 'status': 'connected', 'route': spec['prefix'] + '/' + model}


def workbuddy(now):
    path = Path.home() / 'Library/Application Support/WorkDaddy/credit-usage.db'
    if not path.exists():
        return {'status': 'unavailable'}
    with sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True) as db:
        date = db.execute('SELECT max(checkin_date) FROM daily_checkin_records').fetchone()[0]
        # Dates are from the upstream check-in ledger, not assumed local dates.
        rows = db.execute('SELECT response_code,message,checked_at FROM daily_checkin_records WHERE checkin_date=?', (date,)).fetchall()
    success = sum(code == 0 or (code == 10001 and '已签到' in message) for code, message, _ in rows)
    stamps = [stamp / 1000 if stamp > 10**12 else stamp for _, _, stamp in rows]
    age = now.timestamp() - max(stamps) if stamps else None
    return {'status': 'recent_verified' if age is not None and 0 <= age <= 36*3600 and success == len(rows) else 'needs_attention',
            'ledger_date': date, 'successful_accounts': success, 'recorded_accounts': len(rows), 'claim': 'existing_workdaddy_task'}


def run(force=False):
    now = dt.datetime.now(TZ)
    state = read_json(PRIVATE / 'state.json', {})
    cfg = read_json(PRIVATE / 'accounts.json', {})
    onboarding = read_json(PRIVATE / 'onboarding.json', {})
    observations = read_json(PRIVATE / 'observations.json', {})
    report = {'checked_at': now.isoformat(), 'workbuddy': workbuddy(now), 'providers': {}}
    trae_config = read_json(PRIVATE / 'trae-account.json', {})
    if trae_config.get('enabled'):
        previous_trae = state.get('trae_cn', {})
        if not force and previous_trae.get('probe_date') == now.date().isoformat():
            report['trae_cn'] = previous_trae
        else:
            try:
                bridge = ROOT.parent / 'trae-cn-bridge'
                env = dict(os.environ, TRAE_PROXY_CRED_DIR=str(Path.home() / 'Library/Application Support/CYeahhOS/trae-cn'))
                proc = subprocess.run([str(Path.home() / '.local/bin/node'), str(bridge / 'daily-local.mjs'), '--claim'], env=env, capture_output=True, text=True, timeout=100, cwd=bridge)
                checkin = json.loads(proc.stdout)
                if proc.returncode:
                    raise Failure(0, 'trae_daily_check_failed')
                connections = request(ROUTER + '/api/providers')['connections']
                current = next((c for c in connections if c['id'] == trae_config['connection_id'] and c['provider'] == trae_config['node_id']), None)
                if not current:
                    raise Failure(0, 'managed_connection_missing')
                if not current.get('isActive'):
                    raise Failure(0, 'disabled_needs_review')
                if checkin.get('balance', 0) <= 0:
                    request(ROUTER + '/api/providers/' + current['id'], {'isActive': False}, method='PUT')
                    raise Failure(0, 'quota_exhausted_disabled')
                chat(ROUTER + '/v1', router_key(), trae_config['route'])
                report['trae_cn'] = {'status': 'route_verified', 'probe_date': now.date().isoformat(), 'checkin': checkin}
            except Failure as e:
                report['trae_cn'] = {'status': e.kind, 'http_status': e.status, 'probe_date': now.date().isoformat()}
            except (OSError, ValueError, subprocess.TimeoutExpired):
                report['trae_cn'] = {'status': 'trae_daily_check_failed', 'probe_date': now.date().isoformat()}
    qoder_config = read_json(PRIVATE / 'qoder-account.json', {})
    if qoder_config.get('enabled'):
        previous_qoder = state.get('qoder_cn', {})
        if not force and previous_qoder.get('probe_date') == now.date().isoformat():
            report['qoder_cn'] = previous_qoder
        else:
            try:
                from qoder_checkin import check as qoder_check
                checkin = qoder_check(claim=False)  # First real claim must be verified before automating it.
                chat(ROUTER + '/v1', router_key(), 'qdcn/qfmodel')
                report['qoder_cn'] = {'status': 'route_verified', 'probe_date': now.date().isoformat(), 'checkin': checkin}
                save(PRIVATE / 'qoder-checkin.json', checkin)
            except Failure as e:
                report['qoder_cn'] = {'status': e.kind, 'http_status': e.status, 'probe_date': now.date().isoformat()}
    for provider, spec in SPECS.items():
        account = cfg.get(provider)
        if not account or account.get('phase') != 'connected':
            report['providers'][provider] = {'status': onboarding.get(provider, {}).get('status', 'waiting_onboarding'), 'claim': spec['claim'], 'quota': 'not_observed'}
            continue
        previous = state.get('providers', {}).get(provider, {})
        if not force and previous.get('probe_date') == now.date().isoformat():
            report['providers'][provider] = previous
            continue
        entry = {'probe_date': now.date().isoformat(), 'claim': spec['claim'], 'quota': 'not_observed', 'renewal': spec['renewal']}
        try:
            # Probe only the hub's own connections, never unrelated paid routes.
            connections = request(ROUTER + '/api/providers')['connections']
            current = next((c for c in connections if c['id'] == account['connection_id'] and c['provider'] == account['node_id']), None)
            if not current:
                raise Failure(0, 'managed_connection_missing')
            if not current.get('isActive'):
                entry['status'] = 'disabled_needs_review'
            else:
                chat(ROUTER + '/v1', router_key(), account.get('route_prefix', spec['prefix']) + '/' + account['model'])
                entry['status'] = 'route_verified'
        except Failure as e:
            entry.update(status=e.kind, http_status=e.status)
            if e.kind == 'quota_exhausted':
                request(ROUTER + '/api/providers/' + account['connection_id'], {'isActive': False}, method='PUT')
                entry['status'] = 'quota_exhausted_disabled'
        report['providers'][provider] = entry
    ms = observations.get('modelscope')
    if ms:
        today = now.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()
        report['providers']['modelscope']['credit_observation'] = ms
        report['providers']['modelscope']['claim'] = 'daily_250_verified' if ms['platform_date'] == today and ms['daily_complete'] else 'daily_browser_check_required'
    # Surface new failures to the scheduler; unchanged onboarding stays quiet.
    bad = {'http_error', 'network_or_response_error', 'quota_exhausted_disabled', 'managed_connection_missing', 'router_client_key_missing', 'empty_model_response', 'probe_output_limit', 'disabled_needs_review'}
    changes = []
    trae_result = report.get('trae_cn', {})
    old_trae = state.get('trae_cn', {})
    if trae_result.get('status') not in (None, 'route_verified') and trae_result.get('status') != old_trae.get('status'):
        changes.append('trae_cn')
    if trae_result.get('checkin', {}).get('claim_code') not in (None, 0) and trae_result.get('checkin', {}).get('claim_code') != old_trae.get('checkin', {}).get('claim_code'):
        changes.append('trae_cn_claim')
    if report['workbuddy'].get('status') == 'needs_attention' and state.get('workbuddy', {}).get('status') != 'needs_attention':
        changes.append('workbuddy')
    qoder_status = report.get('qoder_cn', {}).get('status')
    if qoder_status and qoder_status != 'route_verified' and qoder_status != state.get('qoder_cn', {}).get('status'):
        changes.append('qoder_cn')
    if report.get('qoder_cn', {}).get('checkin', {}).get('status') == 'eligible_pending_first_claim_verification' and state.get('qoder_cn', {}).get('checkin', {}).get('status') != 'eligible_pending_first_claim_verification':
        changes.append('qoder_cn_first_claim_now_available')
    for provider, row in report['providers'].items():
        if row.get('status') in bad and row.get('status') != state.get('providers', {}).get(provider, {}).get('status'):
            changes.append(provider)
    report['new_failures'] = changes
    save(PRIVATE / 'state.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    daily = sub.add_parser('run')
    daily.add_argument('--force', action='store_true')
    observe = sub.add_parser('observe-modelscope', help='Record an actual browser readback; never infer it from a model response')
    observe.add_argument('--balance', type=int, required=True)
    observe.add_argument('--daily-complete', action='store_true', help='Use only when both daily 200 and bound-account 50 are shown as completed')
    setup = sub.add_parser('connect')
    setup.add_argument('provider', choices=SPECS)
    setup.add_argument('--base')
    setup.add_argument('--model')
    args = parser.parse_args()
    PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (PRIVATE / 'hub.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('{"status":"already_running"}')
            return
        try:
            if args.command == 'connect':
                spec = SPECS[args.provider]
                base, model = args.base or spec['base'], args.model or spec['model']
                if not base or not model:
                    parser.error('Official base URL and account-visible model are required')
                result = connect(args.provider, base.rstrip('/'), model, getpass.getpass('API key (not displayed): '))
            elif args.command == 'run':
                result = run(args.force)
            elif args.command == 'observe-modelscope':
                if args.balance < 0:
                    parser.error('balance cannot be negative')
                now = dt.datetime.now(dt.timezone.utc)
                result = {'observed_at': now.isoformat(), 'platform_date': now.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat(), 'balance': args.balance, 'daily_complete': args.daily_complete, 'source': 'https://www.modelscope.cn/magicube/usage'}
                observations = read_json(PRIVATE / 'observations.json', {})
                observations['modelscope'] = result
                save(PRIVATE / 'observations.json', observations)
            else:
                result = read_json(PRIVATE / 'state.json', {'status': 'not_run'})
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.command == 'run' and result.get('new_failures'):
                raise SystemExit(1)
        except (Failure, ValueError) as e:
            # No exception repr from network clients can leak headers or keys.
            print(json.dumps({'status': 'error', 'reason': str(e)}, ensure_ascii=False))
            raise SystemExit(1)


if __name__ == '__main__':
    main()
