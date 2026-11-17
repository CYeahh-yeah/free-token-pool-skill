# 平台参考

以下是 2026-11-17 的本机状态。活动规则、余额、模型和领取资格都可能变化；到朋友机器上先按官方页面重新读回，不能照抄为“已到账”。“路由实测”只表示一次真实模型回复，不等于余额 API 已实现。

| 平台 | 官方额度/活动 | 领取状态 | 本机路由与模型 | 边界 |
|---|---|---|---|---|
| 蚂蚁百灵 | 官方赠送额度，按月发券 | 无需每日签到，已接入 | `free-ling/ling-3.1-flash` | flash 需 `thinking: {type:'disabled'}`，否则推理可能吃光输出预算 |
| 魔搭 | 注册登录 200、绑定阿里云 50、每日登录权益 | 2026-11-17 官方两项今日已完成，余额 549；访问已登录页面触发 | `free-ms/Qwen/Qwen3.5-35B-A3B` | 邮箱验证、实名和已登录浏览器由本人准备；初始占位 0 不是余额 |
| Cloudflare Workers AI | Free 计划每日 10000 Neurons | 已接入，无每日签到 | `cf/@cf/qwen/qwen3-30b-a3b-fp8` | 通用 OpenAI provider 的 `/models` 页面测试会假报错；用 9router 原生 `cloudflare-ai` 并用 chat 实测 |
| Qoder CN | 客户端曾显示每日 100 Credits | `DISABLED` / `campaign_unavailable`，未领取 | `qdcn/qfmodel` | 设备授权和路由已验证；首次领取未验证，不启用自动领取 |
| TRAE CN | 每月登录 500、每日签到 100 积分 | 最近签到 `9074`、`checked_in=false`，未到账；官方余额曾读回 479 | `free-trae/deepseek-v4.1-flash` | 本人浏览器 PKCE 授权；按北京时间每天最多一次，必须 `checked_in=true` 才算到账 |
| WorkBuddy | 多账号本地每日签到，积分叠加 | 2026-11-17 账本 3/3 成功 | `cbcn/hy3` 当前 `x0.00 credits` | `hy3` 是“限时折扣”而非永久免费；`glm-5.3-flash x0.06` 不进零成本池 |
| 商汤日日新 | 公测滚动额度 | `waiting_invite` | 未接入 | 需要邀请码；不绕过、不重复提醒 |

WorkBuddy 多账号签到能显著扩大可用额度，日常多账号叠加后基本实现 token 自由；同时必须写清“当前折扣和平台规则可能变化”，不说永久免费、无限 token 或收益保证。模型清单见 [workbuddy-models.md](workbuddy-models.md)。

## 每平台接入验收

1. 官方页面：活动规则、余额或签到状态有可见读回。
2. 官方 API：短 chat 返回可见最终回复；必要时补 stream、tools。
3. 9router：用独立前缀路由再发一次，记录命中的 provider/model 和状态。
4. 组合：`free-pool` 顺序调整前备份数据库，调整后从 `/api/combos` 回读。
5. 余额字段：`quota=not_observed` 表示没有官方 API 余额读回，不写成 0 或已领取。

## 源文件

- 来源入口：https://aihot.news/free-tokens
- 官方规则散见各平台活动页/用量页；每个平台的精确 URL 和变更日期以当天浏览器页面为准。
- 本机巡检实现：`assets/vendor/free-token-hub/README.md`。
