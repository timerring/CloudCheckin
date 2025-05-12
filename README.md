# My Daily Actions

This repository contains a GitHub Action that automatically executes a set of actions every day.

## How it works

1. A GitHub Action workflow runs on beijing time 08:00 every day(UTC time 00:00).
2. If success, the workflow will echo the success message to the log file.
3. The file is committed and pushed automatically by the GitHub Actions bot

## Manual trigger

You can also manually trigger the workflow through the Actions tab in the GitHub repository.

## Function

- V2EX checkin automatically