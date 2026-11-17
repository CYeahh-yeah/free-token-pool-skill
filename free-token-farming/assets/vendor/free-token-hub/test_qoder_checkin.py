import unittest
from unittest.mock import patch
import qoder_checkin as q


class QoderTests(unittest.TestCase):
    def test_disabled_campaign_never_posts_claim(self):
        with patch.object(q, 'credential', return_value='test'), patch.object(q.hub, 'request', return_value={'status': 'DISABLED', 'rewardCredits': 100}) as request:
            result = q.check(claim=True)
        self.assertEqual(result['status'], 'campaign_unavailable')
        self.assertEqual(request.call_count, 1)

    def test_claimable_read_only_does_not_claim(self):
        with patch.object(q, 'credential', return_value='test'), patch.object(q.hub, 'request', return_value={'status': 'CLAIMABLE'}) as request:
            self.assertEqual(q.check()['status'], 'eligible_pending_first_claim_verification')
        self.assertEqual(request.call_count, 1)

    def test_claim_requires_official_readback(self):
        with patch.object(q, 'credential', return_value='test'), patch.object(q.hub, 'request', side_effect=[{'status': 'CLAIMABLE'}, {'result': 'CLAIMED'}, {'status': 'CLAIMABLE'}]):
            self.assertEqual(q.check(claim=True)['status'], 'claim_not_verified')
        with patch.object(q, 'credential', return_value='test'), patch.object(q.hub, 'request', side_effect=[{'status': 'CLAIMABLE'}, {'result': 'CLAIMED'}, {'status': 'CLAIMED_TODAY','rewardCredits':100}]):
            self.assertEqual(q.check(claim=True)['status'], 'claimed_verified')
