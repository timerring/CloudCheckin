# Cloudflare workers Example

## How to Run

First ensure that your Wrangler version is up to date.

```bash
$ wrangler -v
```

Now, if you run `wrangler dev` within this directory, it should use the config
in `wrangler.toml` to run the example.

You can also run `wrangler deploy` to deploy the example.

## ⚠️ Deprecation Notice

**This approach is currently deprecated and does not work as expected.**

After deploying to Cloudflare Workers, requests from CF edge nodes carry identifiable characteristics that cause many platforms (e.g., NodeSeek) to block or restrict access. Additionally, some platforms have disabled IPv6 access, and Cloudflare Workers cannot reliably force IPv4-only outbound connections.

The current workaround is to use Cloudflare Workers **only as a scheduled trigger** to invoke CircleCI webhooks, rather than performing check-ins directly.

If you're interested in making this approach work, contributions and further exploration are welcome!