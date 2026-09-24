# Setup

Use a GitHub account with Codespaces access and the gateway values supplied
by the instructor. Python dependencies install automatically.

## Get your gateway values

Your instructor shows an event page with a QR code, a link, and an admission
code.

1. Open the link **on the computer you will code on**. The key is 32
   characters; copying it from a phone is error-prone.
2. Enter the admission code and choose **Join**.
3. On the model page, scroll to **Your shared API key** and choose
   **Get shared key**.
4. Copy **Shared gateway** as `APIM_BASE_URL` and the key as `APIM_API_KEY`.

The key lasts 24 hours from when you first retrieve it. On a second day, get it
again and update your secret or `.env`, then restart the Codespace or Flask.

## Create the Codespace

Use the default **`main`** branch.

1. [Fork the repository](https://github.com/jeffrey-groneberg/the-mai-workshop).
   Keep **Copy the main branch only** selected. For an existing fork, sync `main`.
2. In your fork, choose **Code > Codespaces > New with options**.
   Select `main` and a 2-core machine, or the smallest available.
3. Set both recommended **Codespaces secrets**:

| Setting | Value |
| --- | --- |
| `APIM_BASE_URL` | The **Shared gateway** origin, without a path such as `/speech` or `/mai/v1`. |
| `APIM_API_KEY` | Your participant key from **Get shared key**. |

If the creation page does not prompt for them, add
[account-specific Codespaces secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces)
and grant access to your fork. These are not Actions secrets. Restart an
existing Codespace after changing them.

## Run the app

Wait for container setup, then run from the repository root:

```sh
python -m flask --app starter/app.py run --reload --host 0.0.0.0 --port 5050
```

In **Ports**, open **Your app — 5050** with **Open in Browser**. Use the normal
HTTPS browser tab for microphone support. Leave forwarding at its default
settings; the Flask server itself uses HTTP. If the page says
*No gateway settings yet*, check the secrets and restart the Codespace.

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
