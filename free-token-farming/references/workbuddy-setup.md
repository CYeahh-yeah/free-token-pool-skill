# WorkBuddy 搭建（收益最大的平台）

WorkBuddy 是整个免费池里收益最高的：支持多账号、每日自动签到，几个账号叠起来能显著扩大可用额度，多账号日常叠加后基本实现 token 自由。这依赖平台当前签到规则和模型折扣，不是永久或无限保证。这一页是完整的复刻指南。

## 前提

- macOS，装好 Node.js 22+（`node --version` 可查，路径由安装脚本自动探测）。
- WorkBuddy 桌面客户端至少登录过一次账号（Agent 不能替你注册账号）。
- 9router 已在本地跑起来，地址 `http://127.0.0.1:20128`。
- 不需要任何付费订阅。

## 第一步 — 安装展开源码

在 Skill 根目录运行：

```bash
bash assets/install.sh
```

脚本把 `assets/vendor/workdaddy-local`（AGPL-3.0-or-later）、`workbuddy-9router`、`free-token-hub`、`trae-cn-bridge` 复制到当前用户的 `~/Documents/CYeahhOS/08_AutomationOS/Integrations/`，不覆盖已有目录。不要把旧包里带原作者 home 绝对路径的文件拷到朋友电脑。

## 第二步 — 安装 LaunchAgent

两个 `.xml` 模板让服务跨登录持续运行。先由安装脚本替换 `__HOME__` 为当前用户 home，再由本人决定是否加载：

```bash
bash assets/install-launch-agents.sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cyeahh.workdaddy.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cyeahh.workbuddy-9router.plist
```

两个都是 `KeepAlive=true, RunAtLoad=true`。第一个跑 WorkDaddy 的 daemon（本地 HTTP 端口 47832，读凭证并刷新）；第二个跑 `sync-credentials.cjs`，每 5 分钟把每个 WorkBuddy 账号的 token 推到 9router，作为一条独立的 `codebuddy-cn` 连接，名字叫 `WorkBuddy · <昵称>`。不再分发 `.plist` 或嵌套 zip，因为小红书 Red Skill 会过滤这些格式。

WorkDaddy 自带的 `daily-account-checkin` 预设默认 `enabled=false`，它按每小时间隔、客户端加载和打开面板检查所有账号，跳过当天已确认成功的账号。本人要在 WorkDaddy 面板启用该任务，或自行创建等价的 `account.forEach + account.checkin` 任务。`hub.py run` 只读取官方签到账本，不替用户启用或重复签到。

注意：小红书 Red Skill 平台不接受 `.plist` 扩展名，所以包里这两个文件用 `.xml` 扩展名存，内容一样。安装时复制回 `.plist` 扩展名，macOS 能正常识别。

## 第三步 — 每日签到

启用 WorkDaddy 的 `daily-account-checkin` 预设后，daemon 按每小时间隔及面板事件检查每个账号，并用当天已验证记录去重；这不是固定 09:00 的一次性 cron。官方响应只有 `code=0`，或 `code=10001` 且文案明确表示已签到/已领取，才算成功。结果写入 `~/Library/Application Support/WorkDaddy/credit-usage.db`，由 `hub.py run` 读取最近账本验证；2026-11-17 本机 3/3 成功属于历史快照，朋友机器上要重新回读。

## 第四步 — 走 9router 路由

凭证同步完成后，9router 的 `cbcn/` 模型以 `/v1/models` 实际列表为准。2026-11-17 当前零成本候选是 `cbcn/hy3`（官方 `x0.00 credits`、标“限时折扣”），模型清单和证据见 [workbuddy-models.md](workbuddy-models.md)。用你已有的 9router 客户端 key，通过 `/v1/chat/completions` 调用 `free-pool`。每个账号是一条连接，路由器自动挑活跃的那条。用短提示 `Reply only OK.` 验证，给 `hy3` 至少 1024 `max_tokens` 或改用流式，确认有可见输出。

`cbcn/glm-5.3-flash` 静态计费 `x0.06 credits`，`cbcn/hy4-preview` 为 `x0.29 credits`；两者都不要写成零成本。9router 本地 `cost=0` 不能代替官方计费。

## 第四步 b — 直连模式（不走 9router）

想完全跳过 9router，用打包好的直连脚本：

```bash
node assets/workbuddy-direct.js                      # "Reply only OK."
node assets/workbuddy-direct.js "用一句话解释量子隧穿。"
```

这个脚本读本地加密的 WorkBuddy 凭证，必要时刷新（用 WorkDaddy 的解密函数），带正确的 CodeBuddy 请求头调官方 `copilot.tencent.com/v2/chat/completions` 端点。模型回复打到 stdout，token 和密钥不打印。脚本默认模型当前仍为 `glm-5.3-flash`；如果要零成本调用，先按官方当前配置把模型改为 `hy3` 并实测。

直连模式每次调用一个账号。要多账号轮询，要么反复调它（脚本自动找第一个可用凭证），要么保留 9router 桥。

2026-11-09 实测通过，请求格式如下：

```
POST https://copilot.tencent.com/v2/chat/completions
Authorization: Bearer <accessToken>
User-Agent: CLI/2.108.1 CodeBuddy/2.108.1
X-Product: SaaS
X-IDE-Type: CLI
X-IDE-Name: CLI
x-requested-with: XMLHttpRequest
x-codebuddy-request: 1
X-Request-ID / X-Conversation-ID / X-Conversation-Request-ID / X-Conversation-Message-ID: <随机 UUID>
Content-Type: application/json

{"model":"glm-5.3-flash","messages":[...],"stream":true}
```

`stream: false` 在这个端点返回 HTTP 400，必须用 SSE（`stream: true`）。

## 扩量：加更多账号

在桌面客户端再登一个你本人有权使用的 WorkBuddy 账号。WorkDaddy 的同步自动捡到新的 `.info` 账号文件，按 UID 建一条独立的连接。多账号叠加是这套方案收益最大的来源，但不伪造账号、不轮换设备身份、不绕过平台规则。

## 关键技术细节

- 凭证刷新用 WorkBuddy 的官方 token-refresh 端点；刷新后的 token 只在内存里，推给 9router，明文不落盘。
- 优先用官方的 `workbuddy-desktop.info` 文件而不是过期备份：桌面应用刷新得比备份新就用新的。
- 连接按 `workbuddyUid` 去重，不按名字，改名不会造成重复。
- 桌面应用没开的时候，同步桥仍能从备份的账号文件工作；CDP 注入是可选的，不阻塞签到。

## 停用或卸载

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cyeahh.workbuddy-9router.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.cyeahh.workdaddy.plist
```

然后在 9router 里禁用或删除 `WorkBuddy · *` 那些连接。上游源码在 https://github.com/babygoton/WorkDaddy （AGPL-3.0-or-later），本机快照 commit `a90bc404303efa271b56c457a3aa9003d358bc0a`；许可证全文见 `LICENSES/WORKDADDY-LICENSE`，归属见 `NOTICE.md`。
