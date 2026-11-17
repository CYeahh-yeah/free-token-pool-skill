import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import hub


class HubTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name)
        self.override = patch.object(hub, 'PRIVATE', self.private)
        self.override.start()
        self.addCleanup(self.override.stop)

    def config(self):
        hub.save(self.private / 'accounts.json', {'sensenova': {'phase': 'connected', 'connection_id': 'owned', 'node_id': 'node', 'model': 'test'}})

    def test_ling_probe_disables_thinking_and_requires_visible_reply(self):
        with patch.object(hub, 'request', return_value={'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}]}) as request:
            hub.chat('https://api.ant-ling.com/v1', 'test-key', 'free-ling/ling-3.1-flash')
        body = request.call_args.args[1]
        self.assertEqual(body['thinking'], {'type': 'disabled'})
        self.assertEqual(body['max_tokens'], 128)

    def test_reasoning_truncation_retries_once_then_requires_answer(self):
        truncated = {'choices': [{'message': {'content': '', 'reasoning_content': 'thinking'}, 'finish_reason': 'length'}]}
        with patch.object(hub, 'request', side_effect=[truncated, {'choices': [{'message': {'content': 'OK'}, 'finish_reason': 'stop'}]}]) as request:
            self.assertEqual(hub.chat('https://example.test/v1', 'test', 'qwen')['status'], 'ok')
        self.assertEqual(request.call_count, 2)
        with patch.object(hub, 'request', return_value=truncated) as request:
            with self.assertRaises(hub.Failure) as err:
                hub.chat('https://example.test/v1', 'test', 'qwen')
        self.assertEqual(err.exception.kind, 'probe_output_limit')
        self.assertEqual(request.call_count, 2)

    def test_empty_200_is_still_a_failure(self):
        with patch.object(hub, 'request', return_value={'choices': [{'message': {'content': ''}, 'finish_reason': 'stop'}]}) as request:
            with self.assertRaises(hub.Failure):
                hub.chat('https://example.test/v1', 'test', 'qwen')
        self.assertEqual(request.call_count, 1)

    def test_unapproved_origin_rejected_before_network(self):
        with patch.object(hub, 'request') as request:
            with self.assertRaises(ValueError):
                hub.connect('sensenova', 'https://wrong.example/v1', 'test', 'secret')
            request.assert_not_called()

    def test_private_file_permissions(self):
        p = self.private / 'accounts.json'
        hub.save(p, {'key': 'secret'})
        self.assertEqual(p.stat().st_mode & 0o777, 0o600)

    def test_onboarding_is_not_claim_success(self):
        with patch.object(hub, 'workbuddy', return_value={'status': 'unavailable'}):
            result = hub.run()
        for row in result['providers'].values():
            self.assertEqual(row['status'], 'waiting_onboarding')
            self.assertEqual(row['quota'], 'not_observed')

    def test_quota_failure_disables_only_owned_connection(self):
        self.config()
        writes = []
        def api(url, body=None, **kwargs):
            if body:
                writes.append((url, body))
                return {}
            return {'connections': [{'id': 'owned', 'provider': 'node', 'isActive': True}, {'id': 'unrelated', 'provider': 'other', 'isActive': True}]}
        with patch.object(hub, 'request', side_effect=api), patch.object(hub, 'router_key', return_value='private'), patch.object(hub, 'chat', side_effect=hub.Failure(402, 'quota_exhausted')), patch.object(hub, 'workbuddy', return_value={}):
            result = hub.run()
        self.assertEqual(writes, [(hub.ROUTER + '/api/providers/owned', {'isActive': False})])
        self.assertEqual(result['providers']['sensenova']['status'], 'quota_exhausted_disabled')

    def test_rate_limit_does_not_disable_and_daily_probe_is_deduplicated(self):
        self.config()
        with patch.object(hub, 'request', return_value={'connections': [{'id': 'owned', 'provider': 'node', 'isActive': True}]}) as api, patch.object(hub, 'router_key', return_value='private'), patch.object(hub, 'chat', side_effect=hub.Failure(429)) as chat, patch.object(hub, 'workbuddy', return_value={}):
            result = hub.run()
            hub.run()
        self.assertEqual(result['providers']['sensenova']['status'], 'http_error')
        self.assertEqual(chat.call_count, 1)
        self.assertEqual(api.call_count, 1)
        self.assertNotIn('private', json.dumps(result))

    def test_disabled_connection_is_not_reenabled(self):
        self.config()
        with patch.object(hub, 'request', return_value={'connections': [{'id': 'owned', 'provider': 'node', 'isActive': False}]}) as api, patch.object(hub, 'chat') as chat, patch.object(hub, 'workbuddy', return_value={}):
            result = hub.run()
        self.assertEqual(result['providers']['sensenova']['status'], 'disabled_needs_review')
        chat.assert_not_called()
        self.assertEqual(api.call_count, 1)

    def test_native_cloudflare_uses_native_route_prefix(self):
        hub.save(self.private / 'accounts.json', {'cloudflare': {'phase': 'connected', 'connection_id': 'owned', 'node_id': 'cloudflare-ai', 'route_prefix': 'cf', 'model': '@cf/qwen/example'}})
        with patch.object(hub, 'request', return_value={'connections': [{'id': 'owned', 'provider': 'cloudflare-ai', 'isActive': True}]}), patch.object(hub, 'router_key', return_value='private'), patch.object(hub, 'chat', return_value={'status': 'ok'}) as chat, patch.object(hub, 'workbuddy', return_value={}):
            result = hub.run()
        chat.assert_called_once_with(hub.ROUTER + '/v1', 'private', 'cf/@cf/qwen/example')
        self.assertEqual(result['providers']['cloudflare']['status'], 'route_verified')

    def test_failed_route_is_disabled_and_never_marked_connected(self):
        writes = []
        def api(url, body=None, **kwargs):
            if url.endswith('/provider-nodes'):
                return {'nodes': []} if body is None else {'node': {'id': 'new-node'}}
            if url.endswith('/providers'):
                return {'connections': []} if body is None else {'connection': {'id': 'new-connection'}}
            writes.append((url, body))
            return {}
        with patch.object(hub, 'router_key', return_value='router-secret'), patch.object(hub, 'request', side_effect=api), patch.object(hub, 'chat', side_effect=[{'status': 'ok'}, hub.Failure(401)]):
            with self.assertRaises(hub.Failure):
                hub.connect('sensenova', hub.SPECS['sensenova']['base'], 'model', 'vendor-secret')
        cfg = hub.read_json(self.private / 'accounts.json', {})
        self.assertEqual(cfg['sensenova']['phase'], 'route_failed_disabled')
        self.assertEqual(writes, [(hub.ROUTER + '/api/providers/new-connection', {'isActive': False})])

    def test_success_requires_both_official_and_router_probes(self):
        def api(url, body=None, **kwargs):
            if url.endswith('/provider-nodes'):
                return {'nodes': []} if body is None else {'node': {'id': 'new-node'}}
            if url.endswith('/providers'):
                return {'connections': []} if body is None else {'connection': {'id': 'new-connection'}}
            raise AssertionError(url)
        with patch.object(hub, 'router_key', return_value='router-secret'), patch.object(hub, 'request', side_effect=api), patch.object(hub, 'chat', return_value={'status': 'ok'}) as chat:
            result = hub.connect('sensenova', hub.SPECS['sensenova']['base'], 'model', 'vendor-secret')
        self.assertEqual(chat.call_count, 2)
        self.assertEqual(result['status'], 'connected')
        self.assertNotIn('secret', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
