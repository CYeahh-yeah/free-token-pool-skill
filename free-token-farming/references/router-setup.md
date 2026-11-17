# 9router 集成

## 前提

- 9router 已在本地跑，地址 `http://127.0.0.1:20128`。
- 已有 9router 客户端 key；它只在环境变量或本机配置里使用。
- 改组合前备份 `~/.9router/db/data.sqlite`。

## 流程

1. 在平台官网本人登录，拿 API key 或 token；不替用户处理验证码、协议或实名。
2. 用 `POST /api/provider-nodes` 建 provider 节点，给唯一前缀（`free-ling`、`free-ms`、`cf`、`qdcn`、`free-trae`、`cbcn`）。
3. 用 `POST /api/providers` 注册连接，填 API key 和默认模型。
4. 用 `<prefix>/<model>` 做短 chat、stream 和必要的 tools 请求，读到可见最终输出。
5. 用 `POST /api/combos` 或 `PUT /api/combos/<id>` 维护 `free-pool`；更改后从 `/api/combos` 回读。
6. 用 `free-pool` 再发一次短 chat 与 stream，确认组合命中预期模型。

## 当前 zero-cost 顺序证据

2026-11-17 的 `free-pool`：

```text
cbcn/hy3
free-trae/deepseek-v4.1-flash
qdcn/qfmodel
free-ms/Qwen/Qwen3.5-35B-A3B
free-ling/ling-3.1-flash
cf/@cf/qwen/qwen3-30b-a3b-fp8
```

`cbcn/hy3` 官方静态 `x0.00 credits`、远端带“限时折扣”，本机普通/流式/tools 实测通过。`cbcn/glm-5.3-flash x0.06 credits` 已从零成本组合移出；`cbcn/hy4-preview x0.29 credits` 不加入。其余平台的数字是官方赠送或活动额度，规则变化后重新核对。

## 已知限制

- TRAE 需要本地桥接，API 不是 OpenAI 兼容的。
- Cloudflare 通用 OpenAI 页面测试请求 `/models` 会报错；用 9router 原生 `cloudflare-ai`，并以 chat 实测为准。
- `hy3` 为强制推理模型；非流式 `max_tokens` 太低会只剩 reasoning，验收用 1024 或流式。
- 9router `/v1/models` 列得出模型，不等于该模型当前免费、余额充足或真实调用成功。
- 9router 本地 `cost=0` 不等于上游官方 credits 为零。
