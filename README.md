# My Daily Actions

This repository contains a GitHub Action that automatically executes a set of actions every day.

## Function

Automatically perform daily check-ins on my frequently-used platforms.

- Nodeseek
- V2EX

## How to use

### To use telegram notification

1. Follow the instructions from [telegram bot](https://core.telegram.org/bots/features#botfather)  and create a telegram bot and get the `token`.
2. Then add the bot to your contact and send a message to it. Then check the url https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates to get the `chat id`. (Substitute `{TELEGRAM_TOKEN}` with the token you got in step 1)
3. Add the `token` and `chat id` to the repository secrets as `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`. (settings -> secrets and variables -> actions -> new repository secret)

### To use nodeseek checkin

1. Get the `cookie` from the nodeseek website. How to get? Check the common tutorial.
2. Add the `cookie` to the repository secrets as `NODESEEK_COOKIE`. (settings -> secrets and variables -> actions -> new repository secret)

## How it works

1. A GitHub Action workflow runs on beijing time 09:00 every day(UTC time 01:00).
2. If success, the workflow will notify via the telegram bot.
3. If failed, the workflow will also notify via the telegram bot and exit with a non-zero exit code, which will let the github action to fail and send email notification.

## Manual trigger

You can also manually trigger the workflow through the Actions tab in the GitHub repository.

## References

- [nodeseek](https://github.com/xinycai/nodeseek_signin)
- [V2EX](https://github.com/CruiseTian/action-hub)
