# Daily Timestamp Creator

This repository contains a GitHub Action that automatically creates timestamped files every 5 minutes.

## How it works

1. A GitHub Action workflow runs every 5 minutes
2. It creates a new text file with the current timestamp in the `timestamps` directory
3. The file is committed and pushed automatically by the GitHub Actions bot

## Manual trigger

You can also manually trigger the workflow through the Actions tab in the GitHub repository.

## Files

All timestamp files are stored in the `timestamps/` directory with the format `timestamp_YYYYMMDD_HHMMSS.txt`. 