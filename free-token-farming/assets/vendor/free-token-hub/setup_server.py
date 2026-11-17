#!/usr/bin/env python3
"""Temporary loopback-only setup form. User enters keys; logs never contain keys."""
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import secrets
from urllib.parse import urlparse
import hub

PORT = 47833
ORIGIN = f'http://127.0.0.1:{PORT}'
CSRF = os.environ.get('FREE_TOKEN_SETUP_CSRF') or secrets.token_urlsafe(32)
CF_ACCOUNT = '2b08180a3b3a7703711db689a2339b94'
PRESETS = {
    'ant-ling': {'base': 'https://api.ant-ling.com/v1', 'model': 'ling-3.1-flash'},
    'cloudflare': {'base': f'https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/v1', 'model': '@cf/qwen/qwen3-30b-a3b-fp8'},
    'modelscope': {'base': 'https://api-inference.modelscope.cn/v1', 'model': 'Qwen/Qwen3.5-35B-A3B'},
}
PAGE = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>免费模型接入 9router</title><style>body{font:17px system-ui;max-width:760px;margin:48px auto;padding:0 22px;background:#f6f7f9;color:#18202b}section{background:white;border-radius:16px;padding:26px;margin:20px 0}label{display:block;margin:16px 0 6px}input,select,button{box-sizing:border-box;width:100%;font:inherit;padding:12px;border:1px solid #ccd3df;border-radius:8px}button{margin-top:20px;background:#215ad2;color:white;cursor:pointer}small{color:#566176}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{font-size:28px}a{color:#215ad2}</style>
<h1>免费模型接入 9router</h1><p>把平台生成的 API Key 填在这里。Key 只交给本机脚本和你自己的 9router，不会显示在聊天或结果中。</p>
<section><form id="setup"><label>平台</label><select id="provider"><option value="ant-ling">蚂蚁百灵（已看到 20 元赠送额度）</option><option value="cloudflare">Cloudflare Workers AI</option><option value="modelscope">魔搭（邮箱已验证，当前 350 魔粒）</option></select>
<label>模型 ID</label><input id="model" required autocomplete="off"><small>已填入官方文档中的模型；助手会继续核验实际调用结果。</small>
<label>API Key / Token</label><input id="key" type="password" required autocomplete="off" spellcheck="false">
<label><input id="free" type="checkbox" required style="width:auto"> 我已确认使用免费额度，未开启付费升级或自动充值。</label>
<button id="submit">验证并接入 9router</button></form><pre id="result" aria-live="polite"></pre></section>
<section><b>当前接入状态</b><pre id="status"></pre><p>商汤：等待邀请码。WorkBuddy：沿用现有每日签到，不需在此填写。</p><small>本页面的“测试通过”只证明调用成功；余额和领取结果以官方页面为准。</small></section>
<script>const presets=__PRESETS__;const csrf=__CSRF__;const form=document.querySelector('#setup'), provider=document.querySelector('#provider'),model=document.querySelector('#model'),key=document.querySelector('#key'),result=document.querySelector('#result'),button=document.querySelector('#submit');provider.onchange=()=>{model.value=presets[provider.value].model;key.value='';document.querySelector('#free').checked=false};provider.onchange();
async function refresh(){const r=await fetch('/status');const d=await r.json();const names={'ant-ling':'蚂蚁百灵',cloudflare:'Cloudflare',modelscope:'魔搭'};document.querySelector('#status').textContent=Object.entries(d).map(([p,v])=>names[p]+'：'+(v.status==='connected'?'已接通':v.status==='waiting_onboarding'?'等待填入 Key':'待检查')+(v.model?' · '+v.model:'')).join(String.fromCharCode(10))}refresh();form.onsubmit=async e=>{e.preventDefault();button.disabled=true;result.textContent='正在验证官方接口和 9router，请稍候…';const credential=key.value;try{const r=await fetch('/connect',{method:'POST',headers:{'Content-Type':'application/json','X-Setup-CSRF':csrf},body:JSON.stringify({provider:provider.value,model:model.value,key:credential,freeConfirmed:document.querySelector('#free').checked})});const d=await r.json();if(d.status==='connected')key.value='';result.textContent=d.status==='connected'?'已接入：'+d.route+'。官方接口与 9router 实测均通过。':(d.message||d.reason||'接入失败，请让助手检查。');await refresh()}catch(e){result.textContent='本机接入服务连接失败，请让助手检查。'}finally{button.disabled=false}};</script></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, kind='application/json'):
        data = body.encode() if isinstance(body, str) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', kind + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(data)

    def valid_host(self):
        return self.headers.get('Host') == f'127.0.0.1:{PORT}'

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {'status': 'invalid_host'})
        if self.path == '/':
            return self.send(200, PAGE.replace('__PRESETS__', json.dumps(PRESETS)).replace('__CSRF__', json.dumps(CSRF)), 'text/html')
        if self.path == '/status':
            cfg = hub.read_json(hub.PRIVATE / 'accounts.json', {})
            return self.send(200, {p: {'status': cfg.get(p, {}).get('phase', 'waiting_onboarding'), 'model': cfg.get(p, {}).get('model')} for p in PRESETS})
        self.send(404, {'status': 'not_found'})

    def do_POST(self):
        if not self.valid_host() or self.path != '/connect' or self.headers.get('Origin') != ORIGIN or self.headers.get('X-Setup-CSRF') != CSRF:
            return self.send(403, {'status': 'request_rejected'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError('invalid_body')
            data = json.loads(self.rfile.read(size))
            preset = PRESETS[data['provider']]
            if data.get('freeConfirmed') is not True or not data.get('key') or not data.get('model'):
                raise ValueError('missing_confirmation_or_fields')
            hub.PRIVATE.mkdir(parents=True, exist_ok=True, mode=0o700)
            with (hub.PRIVATE / 'hub.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                answer = hub.connect(data['provider'], preset['base'], data['model'].strip(), data['key'].strip())
            self.send(200, answer)
        except hub.Failure as e:
            self.send(400, {'status': 'error', 'reason': str(e), 'message': ('官方接口拒绝此凭据（401）。请重新复制完整的 API Key 或访问令牌，勿复制名称或凭证编号。' if e.kind.startswith('official_') and e.status == 401 else '模型回复未完整返回，请让助手检查测试参数。' if 'probe_output_limit' in e.kind or 'empty_model_response' in e.kind else str(e))})
        except (KeyError, ValueError, TypeError, BlockingIOError):
            self.send(400, {'status': 'error', 'reason': '请检查字段，或稍候重试；其他接入操作可能正在执行。'})
        except Exception:
            self.send(500, {'status': 'error', 'reason': '本机接入失败，请让助手检查；密钥未写入日志。'})


if __name__ == '__main__':
    print(f'Setup available at {ORIGIN}; no credential logging.', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
