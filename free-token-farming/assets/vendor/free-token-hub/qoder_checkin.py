#!/usr/bin/env python3
"""Qoder CN official check-in readback. Does not copy or print OAuth tokens."""
import argparse
import json
import sqlite3
import hub

BASE = 'https://openapi.qoder.com.cn/sash/api/v1/me/daily-check-in'
FIELDS = ('status', 'rewardCredits', 'nextClaimAt', 'currentStreakDays', 'totalClaimDays', 'totalRewardCredits', 'lastClaimedAt', 'rewardExpiresAt')


def credential():
    # Reuse the account the user just authorized to local 9router. No app
    # credential extraction, no extra permission grants, no credential copy.
    with sqlite3.connect('file:' + str(hub.Path.home() / '.9router/db/data.sqlite') + '?mode=ro', uri=True) as db:
        row = db.execute("SELECT data FROM providerConnections WHERE provider='qoder-cn' AND isActive=1 ORDER BY createdAt LIMIT 1").fetchone()
    if not row:
        raise hub.Failure(0, 'qoder_connection_missing')
    token = json.loads(row[0]).get('accessToken')
    if not token:
        raise hub.Failure(0, 'qoder_credential_missing')
    return token


def unwrap(value):
    return value.get('data', value)


def check(claim=False):
    key = credential()
    before = unwrap(hub.request(BASE + '/status', key=key))
    report = {'status': 'not_claimed', 'official': {k: before[k] for k in FIELDS if k in before}, 'source': BASE + '/status'}
    state = before.get('status')
    if state == 'CLAIMED_TODAY':
        report['status'] = 'already_verified'
    elif state in ('DISABLED', 'NOT_STARTED', 'ENDED'):
        report['status'] = 'campaign_unavailable'
    elif state == 'CLAIMABLE' and claim:
        response = unwrap(hub.request(BASE + '/claim', key=key, method='POST'))
        after = unwrap(hub.request(BASE + '/status', key=key))
        report['claim_result'] = response.get('result')
        report['official'] = {k: after[k] for k in FIELDS if k in after}
        report['status'] = 'claimed_verified' if response.get('result') in ('CLAIMED', 'ALREADY_CLAIMED') and after.get('status') == 'CLAIMED_TODAY' else 'claim_not_verified'
    elif state == 'CLAIMABLE':
        report['status'] = 'eligible_pending_first_claim_verification'
    else:
        report['status'] = 'unknown_official_status'
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--claim', action='store_true')
    args = parser.parse_args()
    try:
        report = check(args.claim)
        hub.save(hub.PRIVATE / 'qoder-checkin.json', report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except hub.Failure as e:
        print(json.dumps({'status': e.kind, 'http_status': e.status}))
        raise SystemExit(1)
