# QQ / Gmail / MUST 学生邮箱与 DeepSeek 配置

## 当前选择：QQ 邮箱

当前网络实测 `smtp.qq.com:465` 可直连，TLS 证书验证成功，SMTP EHLO 返回 250。
应用已支持 465 隐式 TLS，`.env` 使用：

```dotenv
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_ADDRESS=你的QQ邮箱@qq.com
EMAIL_APP_PASSWORD=QQ邮箱生成的16位授权码
```

在 QQ 邮箱网页版右上角头像进入「设置 → 账号与安全 → 安全设置」，开启
POP3/IMAP/SMTP 服务并生成授权码，按页面提示完成本人验证。
使用授权码而非 QQ 登录密码；见 [QQ 官方说明](https://help.mail.qq.com/detail/106/985)。
地址和授权码只填本地 `.env`。本次切换已清空旧 Gmail 发件人及密码字段，避免误用于 QQ 登录。
收件地址在网页独立的 **Email settings → Recipient email** 填写，勾选
**Send report by email** 才发送。开启发送时地址必填，不再使用 `.env` 的 `EMAIL_TO`。
关闭发送时，无需收件地址也可生成报告及本地预览。

验证配置（只连接和登录，不发送邮件）：

```powershell
.\.venv\Scripts\python.exe -m deep_research.check_email
```

编辑发件配置后重启 Gradio，收件地址和发送选项直接在界面设置即可。
2026-10-25 用户填写配置后，运行 `.venv/Scripts/python.exe -m deep_research.check_email`
成功验证 TLS 连接和 QQ SMTP 登录；该诊断未发送邮件。用户随后反馈已收到应用发送的邮件。

## Gmail（此前配置，当前网络不可用）

如使用 Gmail，`.env` 中使用：

```dotenv
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=你的邮箱@gmail.com
EMAIL_APP_PASSWORD=Google生成的16位应用密码
```

先开启 Google 两步验证，再到 [应用密码页面](https://myaccount.google.com/apppasswords)
生成应用密码；可以直接粘贴带分组空格的应用密码，程序会在连接 Gmail 时自动去掉空白。
此处理仅针对 `smtp.gmail.com`，其他服务的密码保持原样。不要填写普通 Google 登录密码。
参见 [Google 应用密码说明](https://support.google.com/accounts/answer/185833) 和
[SMTP 参数说明](https://support.google.com/mail/answer/7104828)。
收件人仍可使用学校邮箱，无需登录收件人的邮箱。

2026-10-25 本地验证：DeepSeek 完整 Manager 流程已成功完成规划、6 次搜索、报告和邮件预览。
Gmail SMTP 重试 587（STARTTLS）和 465（SSL）均在连接/等待欢迎信息阶段超时，
尚未到达身份验证阶段；因此应用密码和实际发信未验证，修改密码空格不能解决该连接问题。
需先确认运行机器的网络可以访问 `smtp.gmail.com:587`；API 能访问不代表 SMTP 端口也可访问。
可以先不勾选真实发送，运行完整的研究与本地邮件预览。

## 先运行研究和邮件预览

在项目根目录 `.env` 填写以下项目；不要把实际 Key 放入示例文件或发送到聊天：

```dotenv
MODEL_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的DeepSeek官方API密钥
DEFAULT_MODEL_NAME=deepseek-flash
ENABLE_TRACING=false
```

然后重启界面：

```powershell
.\.venv\Scripts\python.exe -m deep_research.app
```

不勾选“实际发送邮件”即可运行研究、报告和邮件预览。
DeepSeek Search API 和模型使用同一把 Key；当前代码不会从 `OPENAI_API_KEY` 自动借用密钥。
若之前误填到 `OPENAI_API_KEY`，请在本地将它移到 `DEEPSEEK_API_KEY`。
本项目的 DeepSeek 接口固定为官方 `https://api.deepseek.com`。

## 学校邮箱是什么服务

[MUST 图书馆公开资料](https://lib.must.edu.mo/sites/default/files/assets/images/tutorial/%28Yellow%2920230809ResourcesandServicesChecklistA3.pdf)
将学生邮箱指向 Microsoft Office 365 登录入口。
这能说明邮箱平台，但不能确认你的账号是否允许第三方应用通过 SMTP 登录。

Microsoft 365 的客户端 SMTP 提交参数是 `smtp.office365.com`、端口 `587`、STARTTLS。
参见 [Microsoft 官方配置说明](https://learn.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-microsoft-365-or-office-365)。

## 只有学校允许密码式 SMTP 登录时，使用以下配置

```dotenv
EMAIL_SMTP_SERVER=smtp.office365.com
EMAIL_SMTP_PORT=587
EMAIL_ADDRESS=你的完整学号邮箱@student.must.edu.mo
EMAIL_APP_PASSWORD=学校允许用于SMTP登录的凭据
```

填写真实的完整地址；不要把上面的中文占位符或尖括号一起填写进去。
`EMAIL_ADDRESS` 是发送者，收件人在界面的 **Recipient email** 填写，可使用学校邮箱。

当前项目调用 `server.login(...)`，属于用户名/密码式 SMTP 验证。
字段虽然叫 `EMAIL_APP_PASSWORD`，并不意味着学校一定允许生成应用密码。
启用 MFA、学校安全默认值、身份验证策略或关闭 SMTP AUTH 都可能阻止这种登录。
应用密码也不能绕过禁止基本验证的租户策略。
参见 [Microsoft SMTP AUTH 管理说明](https://learn.microsoft.com/en-us/exchange/clients-and-mobile-in-exchange-online/authenticated-client-smtp-submission)。

截至本次核对（2026-10-25），Microsoft 的公开时间表说明基本验证行为在 2026 年 12 月前不变，
但学校自己的禁用策略可以早已生效；不能据此推断本账户可用。
参见 [Microsoft 更新的退役时间表](https://techcommunity.microsoft.com/blog/exchange/updated-exchange-online-smtp-auth-basic-authentication-deprecation-timeline/4489835)。

## 如果找不到应用密码或 SMTP 登录失败

可向学校 IT 查询：

> 我的 `@student.must.edu.mo` 账户是否允许 SMTP AUTH？是否允许用户名/密码式验证，
> 或必须使用 OAuth？学校是否提供获准的应用注册或程序发信方式？

不需要为了作业关闭 MFA 或降低学校的安全设置。
如果学校仅支持 OAuth，当前 SMTP 实现不能直接使用；需按学校允许的方式再接入 OAuth 或 Microsoft Graph。
这可能需要学校管理员同意或提供应用配置，不能仅凭邮箱地址完成。

如果只要求将报告送到学校邮箱，也可使用自己另一个允许 SMTP 的邮箱作为发件人，
在界面的 **Recipient email** 填写学校邮箱。学校邮箱作为收件人不需要在本程序内登录。
程序根据端口选择加密方式：465 使用隐式 TLS，其他端口使用 STARTTLS。

当前提供预览、配置说明和代码；未登录学校邮箱、未修改学校策略、未发送真实邮件。
