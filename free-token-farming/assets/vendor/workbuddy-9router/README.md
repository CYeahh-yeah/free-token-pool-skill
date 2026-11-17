# WorkBuddy → 9Router 本机接入

## Windows 单账号桥接

Windows 用户目录内的 `wb-win-bridge.cjs` 对应本目录的 `windows-local-bridge.cjs`。它读取当前 Windows WorkBuddy 的登录会话，只向本机 `127.0.0.1:20128` 同步，不读取 Mac 账号，不改组合顺序，不修改 WorkBuddy 的登录文件。

Windows 9Router 中的连接名是 `WorkBuddy Windows local`。已实测通过 Windows 9Router 请求 `cbcn/glm-5.3-flash`，HTTP 200，返回正文 `WB_OK`。尚未实测后续会话刷新或组合模型调用。

桥接每分钟检查本机登录会话是否更新。可最小化桥接窗口；关闭该窗口或重启 Windows 后，需要先启动 9Router，然后在 Windows 用户目录的 PowerShell 运行 `cmd /c start node wb-win-bridge.cjs --watch`。不需要开机自启。

## macOS 多账号接入

2026-10-16 部署。仅使用本机已有账号；同日扩展到 3 个：CYeahh、Yeahh博士2026、C.。

## 使用

- WorkDaddy 管理页：http://127.0.0.1:47832
- 9Router：http://127.0.0.1:20128
- OpenAI 兼容 Base URL：`http://127.0.0.1:20128/v1`
- 模型：`cbcn/glm-5.3-flash`
- 供应商：CodeBuddy CN；连接名称：`WorkBuddy · CYeahh`
- 客户端继续使用已有的 9Router API Key，不使用 WorkBuddy 登录凭证。

WorkDaddy 使用相邻 `../workdaddy-local/` 上游源码（AGPL-3.0-or-later）。数据和凭据位于 `~/Library/Application Support/WorkDaddy/`，不写入此目录。同步程序每 5 分钟读取已有备份和当前登录文件，将凭证通过本机管理 API 同步到对应 9Router 连接；临期凭证通过 WorkBuddy 官方刷新接口更新，刷新结果只保留在进程内存，9Router 按其既有机制保存接入密钥。未改动官方登录文件。

两个用户 LaunchAgent 登录后启动并保持运行：

- `~/Library/LaunchAgents/com.cyeahh.workdaddy.plist`
- `~/Library/LaunchAgents/com.cyeahh.workbuddy-9router.plist`

每日签到由 WorkDaddy 任务 `cyeahh-daily-account-checkin` 执行，每日本机时间 09:00，不切换登录。电脑须开机且用户已登录；休眠错过时不会自动补跑。补偿任务 `claim-compensation-onetime` 已执行并停用。首次安装自动启用的弹窗关闭、自动发消息任务已停用，其余非签到任务保持停用。

## 已核验

- 补偿领取：`/v2/billing/meter/claim-compensation` 返回 404；无 `/v2` 路径返回 `code:0,msg:OK`。
- 官方积分查询：领取前 800，领取后 1300，增加 500。
- 首次签到检查：`verified:true,already:true`，官方消息“今天已签到，请明天再来”。没有将其记作新增签到积分。
- 带已有 9Router API Key 的实际模型调用 HTTP 200，回复 `ROUTE_OK`，用量 33 输入 / 4 输出 tokens。
- 两个 LaunchAgent 均有运行 PID；补偿任务 `enabled:false,compatible:true`；每日签到任务 `enabled:true,compatible:true`。
- 09:00 的未来定时执行、未来令牌刷新尚未到触发时间，不能视为已经端到端验证。

## 限制

当前 WorkBuddy 版本启动后未开放 CDP 调试端口，WorkDaddy 内嵌增强面板尚未注入。独立管理页、后台账号请求、签到和模型调用可用。不降级或修改官方应用来解决面板问题。

仅验证 GLM-5.3-Flash；9Router 列出的其他 CodeBuddy CN 模型并未逐个测试。官方活动、模型和价格以实际服务返回为准。增加账号需用户自行登录，未注册新账号。

## 检查与停止

```sh
node sync-credentials.cjs --once
launchctl list com.cyeahh.workdaddy
launchctl list com.cyeahh.workbuddy-9router
launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/com.cyeahh.workbuddy-9router.plist"
launchctl bootout gui/$(id -u) "$HOME/Library/LaunchAgents/com.cyeahh.workdaddy.plist"
```

停止后需避免下次登录启动时，可将这两个 plist 移出 LaunchAgents。9Router 里停用或删除上述连接即可撤销路由；不会影响其他供应商。接入前数据库快照位于 `~/.9router/db/backups/before-workbuddy-20261016T015304.sqlite`，仅用于必要时的人工恢复，不能覆盖后续其他变更。

## 来源

- 用户文章：https://mp.weixin.qq.com/s/xbwAYiZjacM32GGO9xEfeg
- WorkDaddy 上游：https://github.com/babygoton/WorkDaddy

## 2026-10-16 新增账号核验

后台自动同步已创建 `WorkBuddy · Yeahh博士2026` 与 `WorkBuddy · C.` 两个连接，均启用，按账号 UID 去重。逐个使用新账号凭据调用官方 GLM-5.3-Flash 接口，均 HTTP 200 并返回 `ACCOUNT_OK`。9Router 现有模型路由仍为 `cbcn/glm-5.3-flash`，客户端无需增加账号专属模型 ID。未改变既有账号选择策略。
