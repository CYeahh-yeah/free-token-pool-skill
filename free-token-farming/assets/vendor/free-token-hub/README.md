# 免费额度统一接入与巡检

入口：`python3 hub.py run`；查看上次结果：`python3 hub.py status`。

凭据、锁和运行状态保存在 `~/Library/Application Support/CYeahhOS/free-token-hub/`。凭据文件为 0600，父目录为 0700，报告不含密钥或上游原始错误。网络请求不跟随重定向。

## 已有与待办

- WorkBuddy：只读取现有 WorkDaddy 签到数据库，不重复创建签到任务。2026-11-08 的三个账号均有 code=0 的官方响应记录。
- 商汤：用户已确认需要邀请码，waiting_invite，不绕过邀请限制。公测滚动额度自动恢复，无需签到。
- 百灵：已登录；充值页显示现金余额0、赠送额度20元。凭证页尚无凭证。等待用户创建并通过本机表单输入 Key；按月自动发券，无需每日签到。
- 魔搭：邮箱已验证，阿里云已实名绑定。官方魔粒页显示余额350，注册登录200与绑定阿里云50均为“今日已完成”。已记录当前平台日期的官方读回。每天由同一 Codex 自动化访问已登录魔粒页，核对后通过 observe-modelscope 记录；不使用猜测的签到接口，不导出浏览器cookies。等待用户创建访问令牌并输入本机表单。
- Cloudflare：已登录，计划页明确显示 Free 为 Current plan，免费档含每日10000 Neurons。已定位 Workers AI 专用 Token 创建入口，等待用户创建和输入；不升级付费方案。
- Qoder/TRAE：候选，需要验证适配和实际活动积分扣减；当前未自动登录或领取。

## 接入

`python3 hub.py connect sensenova` 通过隐藏交互输入 API Key。其他供应商需加 `--model`，魔搭和 Cloudflare 还需使用已核对的官方 `--base`。不要把 Key 写进命令行、文档或聊天。

临时本机表单：`python3 setup_server.py`，仅监听 `http://127.0.0.1:47833/`，由用户亲自输入 Key，检查免费资格后提交。POST 校验 Host、Origin 和随机 CSRF，不记录请求日志。服务只用于交互接入，不添加后台自启，接入完成后停止。

魔搭官方读回命令：`python3 hub.py observe-modelscope --balance 实际余额 --daily-complete`。只有每日200及绑定50均明确完成才可加 daily-complete；平台日期用 Asia/Shanghai，用户调度时间仍用 America/Vancouver。余额与完成标记分别记录，不从余额增减推断成功。

脚本先向官方接口作极短测试，再通过本机 9router 管理 API 创建独立供应商和连接，并作真实路由调用。独立前缀为 `free-sense`、`free-ling`、`free-ms`、`free-cf`。只有两次调用均成功才标记 connected。路由失败会停用该脚本创建的连接。不会修改现有账号和 Hermes 默认模型。

## 巡检边界

每日每个平台至多一次实际调用探测（可能消耗少量额度），不是余额查询。首次输出预算128 tokens；只有明确输出截断才再试一次1024 tokens。Ling按官方参数关闭思考，避免推理消耗全部输出预算；必须读到最终可见回复才判定通过，不把HTTP 200或仅推理内容作为成功。quota=not_observed 明确表示尚未实现官方余额读回，不能据此声称有免费余额或领取成功。

只有明确额度耗尽响应才停用本脚本管理的连接。一般 429 限速不当作额度耗尽。停用后需要核对额度恢复再重新 connect，不自动开启人工停用的连接。不作付费充值，不自动确认协议，不在免费资格未核对前接入。

调度由当前 Codex 聊天的每日自动化执行；电脑需开机且 Codex 可运行。等待用户首次登录的平台不反复提醒。未来新增余额或领取适配，必须先观察官方工作流并保留到账读回证据。

## 来源

- https://aihot.news/free-tokens
- https://platform.sensenova.cn/docs#points
- https://modelscope.cn/posts/435591
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developer.ant-ling.com/zh-CN/docs/getting-started/changelog/billing-upgrade/
- https://developer.ant-ling.com/zh-CN/docs/api-reference/chat/openai/

验证：`python3 -m unittest -v test_hub.py`。离线测试覆盖凭据文件权限、非官方地址拒绝、未开户不冒充领取、每日去重、普通限速与额度耗尽区分、仅停用自己的连接、不重启人工停用连接。

## 接入验证进展

百灵、魔搭、Cloudflare 三者均已 connected，独立巡检均 route_verified。路由分别为 `free-ling/ling-3.1-flash`、`free-ms/Qwen/Qwen3.5-35B-A3B`、`free-cf/@cf/qwen/qwen3-30b-a3b-fp8`。临时填 Key 服务已停止。

Qoder CN 官方签名的 ARM64 客户端已安装到 /Applications/QoderWork CN.app，安装包保存在外置盘；已准备原生 qdcn 设备授权，等待用户登录和确认。尚未证明每日100 Credits领取或调用成功，不写入自动领取调度。官方说明要求在桌面端每日北京时间10:00后主动领取，不能把网页登录当领取。

TRAE CN 官方说明确认免费用户每日签到100积分、每月登录500积分；但本机trae执行器与登录配置目前指向国际站，不冒充已支持国内版积分。

### Cloudflare 页面测试修复

通用 OpenAI Compatible 的连接测试请求 /models；Cloudflare 该端点不可用，因此页面报 Invalid API key or base URL，但普通及流式聊天实际上成功。已改用 9router 原生 cloudflare-ai，连接测试与模型测试均通过，且原生流式请求HTTP200、包含最终[DONE]和可见中文回复。新路由为 `cf/@cf/qwen/qwen3-30b-a3b-fp8`。旧 free-cf 连接保留但停用，回滚资料仅在私有 accounts.json。已在页面补充该Qwen模型，并停用免费计划不可用的Kimi K2.6。后续轮换Cloudflare Token请在原生Cloudflare供应商编辑，不使用旧通用接入表单。

### Qoder CN 路由与签到

用户已完成设备授权，`qdcn/qfmodel`真实调用成功。官方签名客户端的积分模块可追溯到 `/sash/api/v1/me/daily-check-in/status`（GET）与`/claim`（POST），不是猜测端点。只复用已授权到本机9router的凭据，不读取或导出客户端凭据，不写入日志。当前官方状态为DISABLED、累计奖励0，因此没有提交领取，没有声称100 Credits到账。

`python3 qoder_checkin.py`只查询；`--claim`也必须先读到CLAIMABLE才提交一次，并要求领取结果及状态读回同时证实成功。当前每日巡检只监测Qoder资格与模型可用性，首次真实领取成功前不启用自动领取。资格从不可用变可用时提出首次验证提醒。

静态分析范围是客户端出厂代码的一个27361字节积分模块，所选模块SHA256与ASAR声明一致；全包分析因范围过大未完成，附带esbuild二进制存在打包后签名造成的ASAR声明哈希差异，但应用签名核验通过，未执行解包代码。REA所选模块证据：ev_6802f6c98dd6308cb0a0b163c6e57c4b1ae776396c92772fea98033f32c642fa，覆盖为partial，不能据此声称观察了客户端运行时；实际DISABLED与路由响应来自独立上游实测。

## 统一免费池与剩余工作

已新增组合free-pool，含qdcn/qfmodel、cbcn/glm-5.3-flash、free-ms/Qwen/Qwen3.5-35B-A3B、free-ling/ling-3.1-flash、cf/@cf/qwen/qwen3-30b-a3b-fp8；真实回复、工具调用及首模型失败后的回退均通过，未修改现有组合或默认模型。

Qoder状态解释更正：旧daily-check-in返回DISABLED只是旧合约证据；新campaigns接口只读返回空列表，客户端类型可能影响可见性，不能认定活动全局不可领。首次领取未核实，继续保持自动领取关闭。

TRAE CN桥接已准备在相邻trae-cn-bridge；官方授权页网络错误，官网登录页可正常打开，等待本人登录。凭据未取得，未启动转发服务，未加入免费池。


## TRAE 国内版本人授权桥接

已完成浏览器PKCE授权，不读取客户端加密凭据。路由 `free-trae/deepseek-v4.1-flash` 已通过真实回复、流式、工具调用和9router页面测试，加入free-pool。relay仅监听127.0.0.1:47834、随机Bearer，LaunchAgent为com.cyeahhos.trae-cn-bridge。详细本地配置见相邻trae-cn-bridge/CYEAHHOS_SETUP.md。

hub.py run会运行相邻daily-local.mjs --claim，按北京时间每天最多一次领取尝试；先读官方状态，只在enable且未签到时提交，必须领取code=0且回读checked_in=true才算到账。9074为平台拒绝，不高频重试、不换设备。首轮9074未到账，500每月登录赠送余额核验时499.96，模型调用消耗免费积分。后续额度为0时仅停用本脚本拥有的TRAE连接，不自动恢复停用连接、不自动付费。

每日09:15温哥华原自动任务已更新，未来实际首轮触发尚待验证。TRAE已接入，Qoder每日100领取仍未验证、商汤仍缺邀请码；不得把两者写成已领到。
