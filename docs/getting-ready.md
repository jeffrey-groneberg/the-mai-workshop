# Setup

Use a GitHub account with Codespaces access and the gateway values supplied
by the instructor. Python dependencies install automatically.

## Create the Codespace

Use the default **`main`** branch.

1. [Fork the repository](https://github.com/jeffrey-groneberg/the-mai-workshop).
   Keep **Copy the main branch only** selected. For an existing fork, sync `main`.
2. In your fork, choose **Code > Codespaces > New with options**.
   Select `main` and a 2-core machine, or the smallest available.
3. Set both recommended **Codespaces secrets**:

| Setting | Value |
| --- | --- |
| `APIM_BASE_URL` | The instructor's HTTPS gateway origin, without a path such as `/speech` or `/mai/v1`. |
| `APIM_API_KEY` | Your participant key. |

If the creation page does not prompt for them, add
[account-specific Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces)
and grant access to your fork. These are not Actions secrets. Restart an
existing Codespace after changing them.

## Run the app

Wait for container setup, then run from the repository root:

```sh
python -m flask --app starter/app.py run --host 0.0.0.0 --port 5050
```

In **Ports**, open **Your app — 5050** with **Open in Browser**. Use the normal
HTTPS browser tab for microphone support. Leave forwarding at its default
settings; the Flask server itself uses HTTP.

Continue to [Open your app](lessons/00-open-your-app.md).

## Alternative configuration

For local use or unavailable secret injection, copy `.env.example` to a root
`.env` and fill in the two values:

```dotenv
APIM_BASE_URL=
APIM_API_KEY=
```

Existing environment variables override `.env`. Restart Flask after changing
configuration.

No Codespaces? Use [local setup](local-setup.md).
