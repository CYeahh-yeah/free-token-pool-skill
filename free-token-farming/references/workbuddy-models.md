# WorkBuddy 模型清单与计费边界

本页记录 2026-11-17 的一次实测。规则随时可能变，每次交付前重新核对官方客户端、官方远端配置和本机 9router，不能拿这份快照当永久价格表。

## 三层事实要分开

| 层 | 当天数量 | 读法 |
|---|---:|---|
| WorkBuddy 5.9.3 客户端静态 `product.json` | 58 个模型 | 本机出厂可见模型与 `credits` 静态标价；不等于全部可调用 |
| 官方 `https://www.workbuddy.cn/v3/config` 远端配置 | 39 个模型 | 当前远端可见模型、标签和试用 banner；不等于每个模型已在本机路由 |
| 本机 9router `/v1/models` 的 `cbcn/` | 11 个模型 | 本机实际暴露的路由；还要逐个真实调用验证 |

9router 当天暴露：`cbcn/deepseek-v4-pro`、`cbcn/deepseek-v4.1-flash`、`cbcn/glm-5.1`、`cbcn/glm-5.2`、`cbcn/glm-5.3`、`cbcn/glm-5.3-flash`、`cbcn/hy3`、`cbcn/hy4-preview`、`cbcn/kimi-k2.8-preview`、`cbcn/kimi-k3-1`、`cbcn/minimax-m3`。

## Hy3 / Hy4 专项结论

| 名称 | 客户端静态计费 | 远端配置 | 9router | 结论 |
|---|---|---|---|---|
| `hy3` | `x0.00 credits` | 标签 `badge:限时折扣:#FF0000` | `cbcn/hy3` | 当前零成本候选；属于限时折扣到 0，不是永久免费承诺 |
| `hy3-x` | `x0.05 credits` | 未暴露 | 未暴露 | 非零成本 |
| `hy4-preview` | `x0.29 credits` | 不在 `data.models` | `cbcn/hy4-preview` | 可调用但静态标价非零，不加入零成本池 |
| `hy4-preview-x` | `x0.29 credits` | 未暴露 | 未暴露 | 非零成本 |
| `hy4-preview-f` | 不是模型条目 | `ModelTrialBanner`：`targetModelId=hy4-preview`、`trialDays=14`、`firstUseTimeKey=hy4.first_user_time` | 未暴露 | 首次使用 14 天试用入口，不是通用免费模型；本机 9router 未验证 |
| `hy4-flash` | 不存在 | 不存在 | 不存在 | 没有这个模型，不能写成免费 |

`hy4-flash` 可能是把 `hy4-preview` 或 `hy4-preview-f` 记混了。远端原始 JSON 当天只出现 `hy4-preview`、`hy4-preview-f`、`hy4.first_user_time` 三个相关字符串。

其他静态计费非零的例子：`glm-5.3-flash x0.06`、`deepseek-v4.1-flash x0.03`、`minimax-m3-pay x0.25`、`deepseek-v4-pro x0.51`、`kimi-k2.8-preview x0.77`、`glm-5.3/glm-5.2 x0.79`、`kimi-k3-2 x1.62`、`default x2.00`。`credits` 为空只表示静态表没标价，不能反推免费。

## 9router 的 `cost=0` 不是官方免费证明

`usageHistory.cost` 和响应里的 `usage.credit` 是 9router 本地计费或估算字段。历史里 `cbcn/hy4-preview` 的 `cost=0.0` 不能覆盖客户端的 `x0.29 credits`，也不能说明 WorkBuddy 没扣积分。判断零成本必须同时看官方 `x0.00 credits` 和当前活动标签，并把“限时折扣”写进交付说明。

## 零成本路由的实测边界

2026-11-17 把 `cbcn/hy3` 置于 `free-pool` 第一位，移出静态计费 `x0.06 credits` 的 `cbcn/glm-5.3-flash`。短测试结论：

- `cbcn/hy3` 普通 chat：`max_tokens=1024` 返回可见 `OK`，`finish_reason=stop`；`max_tokens=64` 可能因强制 reasoning 占完预算而返回空正文，验收时要给足预算或用流式。
- `cbcn/hy3` 流式与 tool-call 请求：返回可见 `OK`，状态 `ok`。
- `free-pool` 普通与流式：命中 `hy3`，返回可见 `OK`。
- `usageHistory` 的 `cost=0.0` 仅用于确认本机路由计费读数，不用于宣称上游永久免费。

`CYeahh-preview`、Hermes 默认模型和 OMB bot 默认模型均不属于本页所管的零成本池，不要顺手改。

## 重新核对

1. 读 WorkBuddy 客户端 `product.json` 的 `models[].credits`。
2. 用已登录凭据读官方 `/v3/config`，核对 `data.models[].tags`、`data.productFeaturesConfig.ModelTrialBanner.banners`。
3. 读 `http://127.0.0.1:20128/v1/models` 与 `/api/combos`，不要把“模型存在”当成“真实调用成功”。
4. 用短 chat、stream、tools 三种请求读可见输出；把 `cost` 与官方 `credits` 分层报告。
