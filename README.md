# 免费模型统一池 Skill（free-token-farming）

## 产品定位

把国内 AI 平台的官方免费/赠送额度，经本人登录和官方状态回读后汇入本机 `9router` 的 `free-pool`，供各类 Agent 调用。核心卖点是 WorkBuddy 多账号本地签到叠加，日常用量基本实现 token 自由；但当前 `hy3` 是“限时折扣到 0”，不是永久免费承诺。

中文 Skill、全部展开源码、依赖清单、首次提示语、安装脚本、许可证和小红书素材都放在一起。朋友不需要预先懂 Agent 或 API。

## GitHub 上怎么下载

- 直接下载：[`free-token-farming-skill.zip`](https://github.com/CYeahh-yeah/free-token-pool-skill/blob/main/free-token-farming-skill.zip)；页面右上角点 `Download raw file`，也可以 `git clone https://github.com/CYeahh-yeah/free-token-pool-skill.git` 后使用仓库根目录同名文件。
- 解压后把 `free-token-farming/` 放进 `~/.codex/skills/`，打开 Codex 先读 [`安装说明.md`](https://github.com/CYeahh-yeah/free-token-pool-skill/blob/main/%E5%AE%89%E8%A3%85%E8%AF%B4%E6%98%8E.md) 或 [`最短安装指南.md`](https://github.com/CYeahh-yeah/free-token-pool-skill/blob/main/%E6%9C%80%E7%9F%AD%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97.md)。
- 仓库的 `free-token-farming/` 是同一套展开源码；不想解压 zip，可按安装说明让 Agent 从该目录安装。
- 仓库不包含 API key、cookie、浏览器会话或本机绝对路径；登录、验证码、实名、协议和 Key 填写由本人完成。

## 当前版本（2026-11-17）

- Skill 源：`~/.codex/skills/free-token-farming/`；中文 `SKILL.md`、`references/`、`agents/openai.yaml`。
- 仓库中 `free-token-farming/` 目录及展开源码（本地产品目录另有 zip）：给朋友/GitHub 的完整 Skill + 展开源码 + 中文说明 + LICENSE/NOTICE。
- 小红书 Red Skill 上传包见本地产品目录，本仓库只放可审计文本源码：小红书 Red Skill 提交版，内容一致但只保留平台易接受的文本/源码扩展名。
- `free-token-farming-skill-install.md`：最短安装路径和第一句话。
- `小红书帖子-免费AI模型白嫖池.md`：短行正文、标题、平台审核风险修正说明。
- `封面与内页提示词_2026-11-17.md`：正式封面的 kmage 图生图变量与内页确定性排版提纲。
- `free-pool-page2~6.png`：1080 × 1440 内页 v2，不含本人像，页码 `2/6`–`6/6`，CTA 为文末链接。
- `free-pool-cover-img2img.png`：保留首版真人封面。人物相似度仍须本人确认；重新生成正式封面必须走账号规定的 kmage 网页图生图和指定底图。
- `archive-2026-11-09/`：首发版快照，保留英文旧文档、旧图、旧 zip 和旧正文。

## 当前模型事实

WorkBuddy 客户端 `product.json` 58 个静态模型，官方 `/v3/config` 39 个远端模型，本机 9router `cbcn/` 11 个模型。只有 `cbcn/hy3` 当前 `x0.00 credits` 且远端标“限时折扣”，普通/流式/tools 实测有可见回复，已置于 `free-pool` 第一位。

`hy4-flash` 当前三层都不存在；`hy4-preview` 为 `x0.29 credits`；`hy4-preview-f` 只是 14 天首次试用 banner，9router 未暴露；`glm-5.3-flash` 为 `x0.06 credits`，已从零成本组合移出。9router `usageHistory.cost=0` 是本地计费读数，不能当上游官方免费证明。

## 平台状态边界

魔搭 2026-11-17 官方两项今日完成、余额 549；百灵/Cloudflare 按月或每日赠送额度已接入；WorkBuddy 现有账本 3/3 成功。Qoder 当前 `DISABLED` / `campaign_unavailable`，TRAE 最近签到 `9074` 且 `checked_in=false`，两者都没有领取到账。商汤等待邀请码。所有数字是当天本机快照，平台规则变化后重新核对。

## 架构与 Agent

`本人登录 → 官方额度/领取状态 → 独立 API 路由 → 9router free-pool → Hermes / TRAE / WorkBuddy 额度 / Codex / Claude Code / Gemini CLI / OMB / 自定义脚本`。

9router 是统一 OpenAI-compatible 路由；Magpie 只有在特定客户端不能直接填 base URL 时才是可选二级配置。WorkBuddy 桌面客户端反向直连 9router 尚未验证；已验证的是 WorkDaddy 同步桥把 WorkBuddy 额度供其他 Agent 使用。

## 发布与审核

小红书正文不使用 Markdown 表格，对照表放在内页；CTA 统一“文末链接领取”。旧版评论区引导已删除。平台没有给出可核验的具体审核驳回原因；包内已修正英文主文档、`.plist`、`.icns`、嵌套 zip、`.DS_Store`、绝对用户名路径、伪 `sk-` 样例、过度免费承诺、第三方许可证归属和页码混乱。这些是推断出的风险修正，不冒充平台结论。

中文 Skill 文档与整合流程为本次整理成果；WorkDaddy 为 AGPL-3.0-or-later、trae-cn-provider 为 MIT。详见包内 `NOTICE.md` 和 `LICENSES/`。不把整套第三方代码写成原创。

## 验收

- `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py free-token-farming`
- 解压两个 zip 到临时目录，核对文件类型、路径、许可证、无凭据/绝对路径。
- `python3 -m unittest` 跑 `assets/vendor/free-token-hub/test_*.py`；对关键 JS/MJS 做 `node --check`。
- `GET http://127.0.0.1:20128/api/combos` 回读 `free-pool`；用短 chat、stream 和 tools 读可见回复。
- `python3 .../free-token-hub/hub.py run` 只用于本机巡检；朋友机器必须先完成本人登录和官方额度核验。


## GitHub 使用

本仓库直接包含 `free-token-farming/` Skill、中文 `安装说明.md`、`NOTICE.md`、`LICENSES/` 与全部展开源码。朋友可克隆仓库后按 `安装说明.md` 操作；也可直接下载根目录的 `free-token-farming-skill.zip`。仓库不含任何 API key、cookie、浏览器会话或本机绝对路径。当前分享链接是本仓库的 `main` 分支，尚未创建 GitHub Release。
