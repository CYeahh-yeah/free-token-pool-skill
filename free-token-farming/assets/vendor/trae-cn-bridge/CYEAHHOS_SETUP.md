# TRAE 国内版接入准备

来源：https://github.com/JsonLing/trae-cn-provider ，MIT，基线提交 `aa11c98663e99025219071639fbea4d3b1364aaf`。已通过 npm ci --ignore-scripts 安装锁定依赖；上游8个离线测试套件通过。没有运行修改Codex配置或发布网关的CLI命令。

本地修改：src/trae-auth.js 使用官网要求的固定 /authorize 回调路径，并校验随机 loginTraceID 和 loopback Host；PKCE S256 保留，仅接受个人账号官方凭据主机 api.trae.cn / api.trae.com.cn，网络换码不跟随重定向；登录响应与错误输出不显示账户信息或原始令牌。src/env.js 使用本机 product.json 的真实 buildId=1198742665986 作为目录接口的版本筛选键，agent.appId 取自 bootConfig；不使用人为抬高的版本号。login-local.mjs 仅走本人浏览器授权，不读取或解密现有客户端凭据。

已核对本机官方 Trae CN.app 的 product.json，模型域名 trae-api-cn.mchost.guru 在其公开配置中；客户端版本3.3.91。凭据目标目录为 ~/Library/Application Support/CYeahhOS/trae-cn/（0700），凭据文件0600；只在用户授权后生成。

官网本人授权成功，凭据0600。目录18个模型；DeepSeek-V4.1-Flash 实测普通回复、SSE流式+DOne及工具调用add_numbers(a=2,b=3)通过；9router free-trae/deepseek-v4.1-flash 真实调用及页面测试valid=true。已加入free-pool，不改默认模型。

签到：北京时间2026-11-09，状态enable=true、checked_in=false，基础100+额外100；实际claim返回9074（当前参与用户太多），回读仍未签到，因此未到账。初始每月登录赠送500，最近核验499.96（实测消耗）。daily-local.mjs 按北京时间每日最多尝试一次，先记录尝试再请求，只有claim.code=0且checked_in=true才算成功；保留同一设备，不轮换。上游拒绝不作为成功。

本机relay由com.cyeahhos.trae-cn-bridge LaunchAgent管理，只监听127.0.0.1:47834，随机Bearer0600。serve-local.mjs 不输出密钥。免费额度脚本hub.py run已包含daily-local.mjs --claim；既有每日09:15温哥华自动任务已更新。实际未来定时运行仍待首轮触发。

离线npm test 8套件再次全部通过；新增固定官方回调路径、Host/loginTraceID验证测试；另行验证每日重复执行不再claim。

启动交互登录：设置 TRAE_PROXY_CRED_DIR 为上述私有目录后运行 node login-local.mjs。授权URL只写在私有临时文件中，不贴入聊天；交互完成或超时后删除。不得用旧会话URL重试、轮换设备绕过签到限制、自动确认验证码和协议。
