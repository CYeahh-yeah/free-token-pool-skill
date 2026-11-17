---
name: free-token-farming
description: 注册、领取并路由国内 AI 平台的官方免费模型额度，汇入一个 OpenAI 兼容的本地池子。适用于免费 token 平台、WorkBuddy 多账号签到、每日巡检、9router free-pool、Agent 统一调用等场景。
---

# 免费 Token 薅羊毛池

把各平台的官方免费模型额度，汇成本地一个 `free-pool` 端点。目标架构是：本人浏览器授权账号 → 官方额度读回 → 已验证 API 路由 → 9router → 统一的 `free-pool` 模型名，日常只需要调这个名字。

第一次接手时先读 [references/novice-onboarding.md](references/novice-onboarding.md)：照里面的依赖清单、目录树、第一句话和验收命令逐项做，不要假设朋友已装过 Agent、9router 或平台客户端。

## 操作规则

1. 每个平台先去官方价格页、活动页或积分页确认当前确实有免费额度，再动手。区分“活动规则 / 官方余额读回 / 签到成功回读 / 路由真实回复 / 本地计费为 0”；没有到账回读的领取不算成功。
2. 只接已经证实可达的端点。加路由之前必须发一次真实请求，读到可见的模型输出，不能是空的或者只有思考过程。
3. API key、OAuth token、cookie、账号 ID 绝对不能出现在聊天、报告、日志或自动化提示词里。放在 0700 权限的私有目录，文件 0600。
4. 不能替用户完成验证码、协议勾选、账号注册、手机验证等平台要求账号本人做的事。停在这一步，告诉用户怎么操作。
5. 每个平台每天只尝试一次领取。提交前先记录，成功与否以官方状态读回为准，不能看 HTTP 200 就当领到了。
6. 不轮换设备指纹，不伪装客户端类型，不暴力重试限流的接口，不绕平台限制。领取被拒就留到第二天。
7. 不充值，不开付费，不改已有默认模型。自己池子里的路由挂了就禁用那条连接，不许兜底到付费路由。
8. 每条路由在路由器里用独立前缀隔离。零成本组合和消耗 credits 的模型分开；不把静态计费非零的 WorkBuddy 模型写成免费。

## 平台速查

读 [references/platforms.md](references/platforms.md) 看当前已验证的平台清单：注册奖励、每日签到机制、官方 API 端点和已知限制。覆盖蚂蚁百灵、魔搭、Cloudflare Workers AI、Qoder CN、TRAE CN、WorkBuddy、商汤日日新。清单里没有的平台要自己先验证再用。模型名和计费每次以官方当前页面、客户端配置和远端配置为准。

WorkBuddy 是收益最大的平台，有独立的完整搭建文档：动手前先读 [references/workbuddy-setup.md](references/workbuddy-setup.md) 和 [references/workbuddy-models.md](references/workbuddy-models.md)。它需要 `assets/vendor/` 里展开的源码和 `assets/launch-agents/` 里的 `.xml` 模板。单账号想绕过 9router 可以用 `assets/workbuddy-direct.js` 直连；多账号自动轮询还是走 9router。多账号签到加积分能显著扩大可用额度，但平台规则和模型折扣都可能变化，不承诺永久或无限 token。

## 路由器搭建

读 [references/router-setup.md](references/router-setup.md) 看 9router 的接法：建 provider 节点、注册连接、测路由、拼 `free-pool` 组合模型，以及 Cloudflare `/models` 端点不兼容的处理办法。9router 已是统一 OpenAI-compatible 路由；Magpie 只是某些客户端确有需要时的可选二级配置，不把它写成必需。

## 每日自动化

读 [references/daily-automation.md](references/daily-automation.md) 看每日签到的流水线：怎么跑 `hub.py run`，TRAE 和 Qoder 的领取流程有什么不同，调度器怎么配，领取失败或者额度用完了怎么办。

## Agent 集成

读 [references/agent-integration.md](references/agent-integration.md) 看怎么把 Hermes、TRAE、WorkBuddy、Codex、Claude Code、OMB、WorkDaddy 自动化脚本，或者任何支持 OpenAI 协议的 agent，指向 9router 的 `free-pool` 端点。一个 key，一个模型名，往池子里加新平台后所有已接入的 agent 自动多一条可用额度。

## TRAE CN 桥接

读 [references/trae-bridge.md](references/trae-bridge.md) 看浏览器 OAuth 授权、本地中转服务、模型目录拉取，以及官方前端校验需要的 PKCE 回调路径修复。

## 什么时候停下来

- 平台要求账号本人完成某一步（验证、协议、验证码）——停下来，告诉用户怎么操作。
- 领取接口返回业务拒绝码（比如 TRAE 的 9074）——记录下来，今天不要再试。
- 官方活动页显示活动下线、结束或不可用——如实报告当前状态，不要假设别处还有。
- 路由测试拿不到可见的最终输出——不要把它加进池子。
- 官方客户端/远端配置写 `x0.xx credits` 或标“限时折扣”——不要当作永久免费，也不要加入零成本组合。
