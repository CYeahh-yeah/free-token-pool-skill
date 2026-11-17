import json
from pathlib import Path
import subprocess
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import setup_server as setup


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), setup.Handler)
        self.port = self.server.server_port
        self.origin = f'http://127.0.0.1:{self.port}'
        self.patches = [patch.object(setup, 'PORT', self.port), patch.object(setup, 'ORIGIN', self.origin), patch.object(setup.hub, 'PRIVATE', Path(self.temp.name))]
        for p in self.patches:
            p.start()
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def post(self, origin=None, csrf=None, free=True):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        if csrf:
            headers['X-Setup-CSRF'] = csrf
        data = {'provider': 'ant-ling', 'model': 'ling-3.1-flash', 'key': 'test-secret-not-real', 'freeConfirmed': free}
        return urllib.request.urlopen(urllib.request.Request(self.origin + '/connect', json.dumps(data).encode(), headers=headers))

    def test_cross_origin_and_missing_csrf_rejected_before_connect(self):
        with patch.object(setup.hub, 'connect') as connect:
            for origin, csrf in [('http://evil.example', setup.CSRF), (self.origin, None)]:
                with self.assertRaises(urllib.error.HTTPError) as err:
                    self.post(origin, csrf)
                self.assertEqual(err.exception.code, 403)
            connect.assert_not_called()

    def test_user_confirmation_required(self):
        with patch.object(setup.hub, 'connect') as connect:
            with self.assertRaises(urllib.error.HTTPError) as err:
                self.post(self.origin, setup.CSRF, free=False)
            self.assertEqual(err.exception.code, 400)
            connect.assert_not_called()

    def test_form_script_is_valid_and_status_never_exposes_key(self):
        with urllib.request.urlopen(self.origin + '/') as response:
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            page = response.read().decode()
        script = re.search('<script>(.*?)</script>', page, re.S).group(1)
        result = subprocess.run(['node', '--check'], input=script, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        setup.hub.save(Path(self.temp.name) / 'accounts.json', {'ant-ling': {'key': 'must-not-leak', 'phase': 'connected', 'model': 'test'}})
        with urllib.request.urlopen(self.origin + '/status') as response:
            body = response.read().decode()
        self.assertNotIn('must-not-leak', body)

    def test_valid_user_submission_uses_fixed_official_origin(self):
        with patch.object(setup.hub, 'connect', return_value={'status': 'connected', 'route': 'free-ling/test'}) as connect:
            with self.post(self.origin, setup.CSRF) as response:
                self.assertEqual(json.load(response)['status'], 'connected')
        connect.assert_called_once_with('ant-ling', 'https://api.ant-ling.com/v1', 'ling-3.1-flash', 'test-secret-not-real')


if __name__ == '__main__':
    unittest.main()
