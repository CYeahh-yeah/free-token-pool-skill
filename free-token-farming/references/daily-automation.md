# 每日自动化

每日自动化负责“核验 + 有资格才领 + 路由巡检”，不能只凭一个 HTTP 200 写成成功。电脑关机或 Codex 没运行时不会补跑，第二天按当前状态处理。

## 流水线

1. WorkDaddy 的 LaunchAgent 保持 daemon 在线；其 `daily-account-checkin` 预设需本人启用，按每小时间隔及面板事件检查所有账号，并跳过当天已验证成功的账号。`hub.py run` 只读账本，不重复签到。
2. `workbuddy-9router` LaunchAgent 每 5 分钟把本地 WorkBuddy 凭证同步到 9router。
3. 浏览器访问已登录 `https://www.modelscope.cn/magicube/usage`，等真实数据加载；只有注册登录 200 与绑定阿里云 50 两项都显示“今日已完成”，才运行 `hub.py observe-modelscope --balance <实际整数> --daily-complete`。
4. `hub.py run` 检查 TRAE、Qoder、魔搭、百灵、Cloudflare、WorkBuddy 与路由状态。TRAE 按北京时间每天最多领一次，先读官方状态，只在 `enable=true` 且未签到时提交，必须 `checked_in=true` 才算到账；`9074` 是平台拒绝，不换设备、不高频重试。
5. Qoder 当前只查资格与既有路由，`DISABLED` / `campaign_unavailable` 不提交领取，不宣称 100 Credits 到账。
6. 其他平台：按月发券和自动恢复额度不伪造签到；`waiting_invite` / `waiting_api_key` / `waiting_onboarding` 不重复提醒。
7. 每条已接 provider 每天做一次极短真实调用探测，可能消耗少量额度；`quota=not_observed` 表示没有官方 API 余额证据。

## 调度

让 Agent 用 `automation_update` 创建每天一次的 heartbeat，而不是手写 cron 或改系统服务。提示语必须保留：官方页面真实读回、正常静默、只报告新出现的登录失效/浏览器不可核验/明确额度耗尽/新签到错误/签到记录超过 36 小时/脚本失败；不得充值、启用付费或改默认模型。

## 失败处理

- 登录失效或浏览器无法核验：如实报告当前无法核验，不保存浏览器 cookies，不自动填凭据。
- 某平台领取被拒：记录，今天不重试。
- 路由探测无最终可见回复：停用本脚本管理的那条连接，不回退付费。
- 一般 429：当限速处理，不当额度耗尽。
- 明确额度耗尽：停用该连接；恢复要重新核官方额度后由人决定。

## 验收

```bash
python3 ~/Documents/CYeahhOS/08_AutomationOS/Integrations/free-token-hub/hub.py run
python3 ~/Documents/CYeahhOS/08_AutomationOS/Integrations/free-token-hub/hub.py status
curl -sS http://127.0.0.1:20128/api/combos
```

`hub.py status` 可能是较早快照，看时间戳再判断。报告把“活动资格 / 官方余额 / 领取回读 / 路由实测 / 本地 cost”分开写。
