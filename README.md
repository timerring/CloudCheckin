# My Daily Actions

<div align="center">
  <picture>
    <img src="https://cdn.jsdelivr.net/gh/timerring/scratchpad2023/2024/2025-05-25-14-45-17.png" alt="workflow"  width="500" height="500"/>
  </picture>

本仓库采用 GitHub Action 实现每日签到以及自动答题等任务功能。

[English Version](./README-en.md) |
中文版本 |
</div>

## 功能

> 欢迎 :star:，添加更多平台欢迎 issue 或者 PR。

每天自动完成平台任务，完成以后会通过 telegram 机器人通知，如果失败则会直接通过 Github 发送邮件通知。

- **Nodeseek**
  - 自动签到
- **V2EX**
  - 自动签到
- **一亩三分地**
  - 自动签到
  - 自动答题

## 快速开始

Fork 本仓库到你自己的仓库，然后添加对应的配置项到仓库的 secrets 中（在 settings -> secrets and variables -> actions -> new repository secret）。然后等待工作流自动运行即可，非常简单无需别的操作。

> 如果不需要某个平台，可以直接删除 `.github/workflows` 目录下该平台对应的 workflow 文件即可。

### 配置 Telegram 通知

1. 按照 [telegram bot](https://core.telegram.org/bots/features#botfather) 的说明创建一个 telegram 机器人并获取 `token`
2. 将机器人添加到您的联系人并发送一条消息。然后访问 https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates 获取 `chat id`（将 `{TELEGRAM_TOKEN}` 替换为步骤1中获得的 token）
3. 将 `token` 和 `chat id` 添加到仓库密钥中，分别命名为 `TELEGRAM_TOKEN` 和 `TELEGRAM_CHAT_ID`（在 settings -> secrets and variables -> actions -> new repository secret）

### 配置 Nodeseek 签到

1. 从 Nodeseek 网站获取 `cookie`（获取方法请参考 [COOKIE 获取教程](https://blog.timerring.com/posts/the-way-to-get-cookie/)）
2. 将 `cookie` 添加到仓库密钥中，命名为 `NODESEEK_COOKIE`（在 settings -> secrets and variables -> actions -> new repository secret）

### 配置 V2EX 签到

1. 从 V2EX 网站获取 `cookie`（获取方法请参考 [COOKIE 获取教程](https://blog.timerring.com/posts/the-way-to-get-cookie/)）
2. 将 `cookie` 添加到仓库密钥中，命名为 `V2EX_COOKIE`（在 settings -> secrets and variables -> actions -> new repository secret）

### 配置 一亩三分地 签到

1. 从 一亩三分地 网站获取 `cookie`（获取方法请参考 [COOKIE 获取教程](https://blog.timerring.com/posts/the-way-to-get-cookie/)）
2. 将 `cookie` 添加到仓库密钥中，命名为 `ONEPOINT3ACRES_COOKIE`（在 settings -> secrets and variables -> actions -> new repository secret）
3. 从 [2captcha](https://2captcha.com/) 充值获取 `api key`，(由于一亩三分地的签到以及答题需要通过 cloudflare turnsite 的验证，因此这里通过 2captcha 的 api 来解决验证问题)
   - 注意： 2captcha 的 api 需要付费，3 美元起充，支持支付宝。每次成功通过验证约 0.00145 美元，3 美元能用 2068 次，约 2.83 年。
4. 将 `api key` 添加到仓库密钥中，命名为 `TWOCAPTCHA_APIKEY`（在 settings -> secrets and variables -> actions -> new repository secret）

## 工作原理

1. GitHub Action 工作流会在每天北京时间 09:00（UTC 时间 01:00）左右运行
2. 如果成功，工作流会通过 Telegram 机器人发送通知
3. 如果失败，工作流也会通过 Telegram 机器人发送通知，并以非零退出码退出，这可以让 GitHub 发送邮件提醒通知

## 手动触发

您也可以通过 GitHub 仓库的 Actions 标签页手动触发工作流，直接 run workflow 即可。

## 参考

- [nodeseek](https://github.com/xinycai/nodeseek_signin)
- [V2EX](https://github.com/CruiseTian/action-hub)
- [一亩三分地](https://github.com/harryhare/1point3acres)