# 从 Agent 调用免费池

9router 跑起来、`free-pool` 组合建好之后，同一个 OpenAI-compatible 端点可给本机多个 Agent 使用。9router 是统一路由层，不要求再串一层 Magpie；只有某个客户端确实不能直接填自定义 base URL 时，才把 Magpie 当可选二级配置。

## 端点

```text
Base URL: http://127.0.0.1:20128/v1
端点:     /chat/completions
模型:     free-pool
Key:      9router 客户端 key（本机保管，不进聊天或仓库）
```

可接入的客户端例子：Hermes、TRAE 的自定义 provider、Codex、Claude Code、Gemini CLI、OMB、WorkDaddy 自动化脚本、Python/Node 脚本。WorkBuddy 桌面客户端本身是否支持反向填这个自定义 provider，当前没有可靠验证；已验证的是“WorkBuddy 账号签到 → WorkDaddy/同步桥 → 9router → 其他 Agent”，以及单账号直连脚本。

## 调用例子

把 key 放进环境变量，不写进源码：

```bash
export NINE_ROUTER_KEY='<本机 9router key>'
curl -sS http://127.0.0.1:20128/v1/chat/completions \
  -H "Authorization: Bearer ${NINE_ROUTER_KEY}" \
  -H 'Content-Type: application/json' \
  -d '{"model":"free-pool","messages":[{"role":"user","content":"Reply only OK."}],"max_tokens":1024,"stream":false}'
```

验收要求读到可见最终回复。若首选 `cbcn/hy3` 因强制 reasoning 在 `max_tokens=64` 时返回空正文，把预算提到 1024 或改 `stream:true`；HTTP 200、空正文、只有 reasoning 都不算通过。

## 设计边界

- 每个平台用独立前缀连接，组合只负责按优先级回退。
- `free-pool` 只放当前零成本或明确赠送额度路由；`x0.xx credits` 的模型留在其他组合。
- 失败时停用失败连接或等待下一天，不自动切到付费模型。
- 不改已有的 `CYeahh-preview`、Hermes 默认模型或 OMB bot 默认模型。
- 9router 本地 `cost=0` 和 `usage.credit=0` 只是本地计费读数；官方计费另查客户端/活动页。

## 单账号直连

只用一个 WorkBuddy 账号、不想跑 9router 时，`assets/workbuddy-direct.js` 可作为子进程调用。它读取本机已登录 WorkBuddy 的凭据，不打印 token；stdout 是模型回复。当前脚本默认模型为 `glm-5.3-flash`，其静态计费 `x0.06 credits`，使用前应按 [workbuddy-models.md](workbuddy-models.md) 改成当前实际需要的模型并自行验证。多账号轮询仍用 9router。
