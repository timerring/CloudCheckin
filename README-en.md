# Daily Actions


<div align="center">
  <picture>
    <img src="https://cdn.jsdelivr.net/gh/timerring/scratchpad2023/2024/2025-05-25-14-57-31.png" alt="workflow"  width="500" height="300"/>
  </picture>

This repository uses GitHub Actions to automate daily check-ins and automated question answering tasks.

English Version |
[中文版本](./README.md)
</div>

## Features

> More platforms are welcome to issue or PR.

Automatically completes platform tasks daily, with notifications sent through a telegram bot upon completion. If failures occur, notifications are sent directly via Github email.

- **Nodeseek**
  - Automatic check-in
- **V2EX**
  - Automatic check-in
- **1point3acres**
  - Automatic check-in
  - Automatic question answering

## How to Use

### Fork the repository

Fork the repository to your own. Then add the secrets to the repository. Then just wait for the workflow to run.

> If you don't need a particular platform, you can simply delete the corresponding platform's workflow file in the `.github/workflows` directory.

### Configure Telegram Notifications

1. Follow the [telegram bot](https://core.telegram.org/bots/features#botfather) instructions to create a telegram bot and obtain the `token`
2. Add the bot to your contacts and send it a message. Then visit https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates to get the `chat id` (Replace `{TELEGRAM_TOKEN}` with the token obtained in step 1)
3. Add the `token` and `chat id` to the repository secrets as `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID` (under settings -> secrets and variables -> actions -> new repository secret)

### Configure Nodeseek Check-in

1. Get the `cookie` from the Nodeseek website (See [COOKIE Retrieval Guide](https://blog.timerring.com/posts/the-way-to-get-cookie/))
2. Add the `cookie` to the repository secrets as `NODESEEK_COOKIE` (under settings -> secrets and variables -> actions -> new repository secret)

### Configure V2EX Check-in

1. Get the `cookie` from the V2EX website (See [COOKIE Retrieval Guide](https://blog.timerring.com/posts/the-way-to-get-cookie/))
2. Add the `cookie` to the repository secrets as `V2EX_COOKIE` (under settings -> secrets and variables -> actions -> new repository secret)

### Configure 1point3acres Check-in

1. Get the `cookie` from the 1point3acres website (See [COOKIE Retrieval Guide](https://blog.timerring.com/posts/the-way-to-get-cookie/))
2. Add the `cookie` to the repository secrets as `ONEPOINT3ACRES_COOKIE` (under settings -> secrets and variables -> actions -> new repository secret)
3. Get an `api key` from [2captcha](https://2captcha.com/) by topping up your account (Due to 1point3acres' check-in and question answering requiring cloudflare turnstile verification, we use 2captcha's API to solve the verification)
   - Note: 2captcha's API is paid, starting from $3, and supports Alipay. Each successful verification costs about $0.00145, $3 can be used 2068 times, approximately 2.83 years.
4. Add the `api key` to the repository secrets as `TWOCAPTCHA_APIKEY` (under settings -> secrets and variables -> actions -> new repository secret)

## How It Works

1. The GitHub Action workflow runs around 09:00 Beijing time (01:00 UTC) every day
2. Upon success, the workflow sends notifications through the Telegram bot
3. Upon failure, the workflow also sends notifications through the Telegram bot and exits with a non-zero code, triggering GitHub email notifications

## Manual Trigger

You can also manually trigger the workflow through the Actions tab in the GitHub repository by clicking run workflow.

## References

- [1point3acres](https://github.com/harryhare/1point3acres)
- [V2EX](https://github.com/CruiseTian/action-hub)
- [nodeseek](https://github.com/xinycai/nodeseek_signin)