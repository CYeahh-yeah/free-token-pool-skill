# TRAE CN 桥接

TRAE 国内版（trae.cn）的 API 不是 OpenAI 兼容的，所以需要一个本地中转服务把它转成 OpenAI 协议，再给 9router 用。

## 步骤

1. 先运行 Skill 根目录的 `bash assets/install.sh`，源码会展开到 `~/Documents/CYeahhOS/08_AutomationOS/Integrations/trae-cn-bridge/`。
2. 进入该目录运行 `npm ci`（Node.js 22+）。
3. `node login-local.mjs` 起本地 OAuth 流程，浏览器打开 `https://www.trae.cn` 授权页，你亲自点“登录并打开 TRAE”。Agent 不代填账号、验证码或协议。
4. 授权成功后凭据存在本机 0600 文件；运行 `node serve-local.mjs`，本地 relay 只监听 `127.0.0.1:47834` 并要求随机 Bearer key。
5. 9router 里加一个 OpenAI 兼容 provider，base 填 `http://127.0.0.1:47834/v1`，模型 `deepseek-v4.1-flash`，路由前缀 `free-trae`。

## 每日领取

`node daily-local.mjs --claim` 按北京时间每日最多提交一次领取；先读官方状态，只在 `enable=true` 且未签到时提交，并要求 `code=0` 且状态回读 `checked_in=true`。失败常见返回 9074（参与人数超限），记录下来，明天再试；不得换设备身份或高频重试。统一巡检 `hub.py run` 会调用相邻目录的 `daily-local.mjs`。

## 注意

- TRAE 的 Cloud-IDE-JWT token 生命周期约 14 天，过期后重新跑 login-local.mjs。
- 官方前端对 PKCE 回调路径有校验，本机桥接已经修复，不用自己改。
- 上游 trae-cn-provider 为 MIT，本机快照 commit `aa11c98663e99025219071639fbea4d3b1364aaf`；许可证全文见 `LICENSES/TRAE-BRIDGE-LICENSE`。
- 分发源码已去掉历史文档和测试里的伪 key 样例，避免平台审核把 `sk-...` 当真实凭据。
