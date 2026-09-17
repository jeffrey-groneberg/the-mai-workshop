# Readiness pre-work

Have the environment ready **before** the guided two-hour target session.
Pre-work installs tools and checks access; it does not implement the word list,
recording, or any other app feature.

The static guide's GitHub Pages deployment target is
[jeffrey-groneberg.github.io/the-mai-workshop/](https://jeffrey-groneberg.github.io/the-mai-workshop/).
Use the instructor-confirmed published guide, or the private **Workshop guide**
preview on port 8000. Neither runs your app: **Your app** (5050) and **Finished
solution** (5051) are separate Flask servers in Codespaces or on your laptop.
Pages cannot run Flask or hold private gateway configuration; keep both the
endpoint and key server-side, never in the published guide.

## Check access with the instructor

You need a GitHub account, access to this repository, permission to use
Codespaces, and an agreed compute/storage billing arrangement. Codespaces
availability and cost are separate from model quotas. A free Codespace is not
guaranteed for every participant.

The instructor must confirm repository-secret access, organizational browser /
network policies, and whether you need a participant-owned fork. Read-only
repository access can affect secret injection. Do not make ports public or relax
organization policy to work around access trouble. See GitHub's
[Codespaces security guidance](https://docs.github.com/en/codespaces/reference/security-in-github-codespaces)
and [account-specific secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces).

Obtain the approved portal details, private gateway origin, and individual
participant key from the instructor through the approved private channel.
Treat the gateway origin as sensitive, just like the key. The provider's key lifetime is **24 hours from initial
issuance**, not from your first model request. Arrange issuance for the event;
do not put either private configuration value in chat, screenshots, logs, Git,
or this guide. Access can also be revoked or rotated. The
[pinned provider README](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/README.md)
is the access-policy source.

## Create the Codespace

For this initial publication, use
**`jeffrey-groneberg-mai-vocabulary-workshop`**, not `main`: the default `main`
currently contains only a README. The
[workshop source branch](https://github.com/jeffrey-groneberg/the-mai-workshop/tree/jeffrey-groneberg-mai-vocabulary-workshop)
contains the starter, solution, guide, and dev container.

[Open branch-specific Codespaces creation](https://codespaces.new/jeffrey-groneberg/the-mai-workshop/tree/jeffrey-groneberg-mai-vocabulary-workshop)
and confirm the branch on the GitHub creation page. Alternatively, use
**Code > Codespaces > New with options** on the repository page and explicitly
select **`jeffrey-groneberg-mai-vocabulary-workshop`** and the approved machine.
If a participant-owned fork is required, confirm that the fork includes this
branch and select it there; the link above targets the original repository.

The dev container recommends **both
`APIM_BASE_URL` and `APIM_API_KEY`** as Codespaces secrets, by name and description
only; enter their private values in GitHub's secret fields. GitHub documents the
[recommended-secret prompt on the options creation path](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/configuring-dev-containers/specifying-recommended-secrets-for-a-repository);
do not expect it on every quick-create path.

If no prompt appears, create account-specific **Codespaces** secrets named
`APIM_BASE_URL` and `APIM_API_KEY`, and grant both access to the correct repository
or fork. These are not Actions secrets. Stop and restart an existing Codespace after changing
injected secrets, then restart Flask. If your permissions prevent this, ask the
instructor to resolve access or use the explicitly approved `.env` fallback
below; do not paste either value into source.

Wait for container setup to finish. It installs Python, Flask, HTTPX,
python-dotenv, and Zensical. Participants do not install runtime packages by
hand. GitHub's
[Python dev-container guide](https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/setting-up-your-python-project-for-codespaces)
explains this setup mechanism. After creation, confirm that `starter/`,
`solution/`, and `docs/` exist. If you see only a README, return to branch
selection rather than trying to recreate missing workshop files.

## Configure both private values server-side

Prefer the two Codespaces secrets above. `APIM_BASE_URL` must contain the
instructor's private HTTPS **origin only**, with no route, query, embedded
credentials, or fragment. Do not include `/speech`, `/mai`, or `/v1`; the app
adds each relative route itself. `APIM_API_KEY` contains your individual
participant key.

The gateway's [participant examples](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/app/catalog.py)
use a participant `api-key` for all REST endpoints, including Speech; this is
not a direct Azure Speech resource key.

**Fallback only:** if Codespaces secret injection is unavailable and the
instructor approves, create a root `.env` in the editor using the **empty**
`.env.example` as a guide:

```dotenv
APIM_BASE_URL=
APIM_API_KEY=
```

Keep the tracked example empty. Enter actual values only in your ignored `.env`,
after the ignore check below. Avoid shell commands containing either value.
Do not paste them into code, documentation, screenshots, logs, or provenance,
and never copy private environment files into `site/`. The local setup uses the
same fallback.

Check that `.env` is ignored without printing it:

```sh
git check-ignore .env
```

The command should print `.env`. If it does not, do not put either private value there. Both
apps load the root `.env` with `override=False`: an already-set environment
variable wins. An old injected endpoint or key therefore is **not** replaced by
editing `.env`; fix the corresponding Codespaces secret and restart instead.

Check the installed tools, without invoking a model:

```sh
python -c "import flask, httpx, dotenv; print('Python runtime is ready')"
zensical --version
```

There is no model call on app startup. The initial starter needs no gateway
configuration; missing or invalid settings produce a visible error when you
later use a model feature.

## Browser and data readiness

Keep ports 5050, 5051, and 8000 **Private**. The container servers use internal
HTTP; GitHub's forwarded URLs use browser-facing HTTPS. Do not configure local
TLS or change the port protocol to HTTPS. Open forwarded links with **Open in
Browser**, not an embedded preview. See
[GitHub port forwarding](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace).

The microphone belongs to **your browser**, not the remote Codespace. It needs a
secure context, browser permission, and permitted organizational policy
([MDN `getUserMedia`](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)).
The instructor must preflight the intended desktop browser and forwarded tab;
a local test does not establish that this path works.

The portal currently allows synthetic/sample data only. **Do not submit
personal or confidential content.** A real voice can itself be personal data.
Voluntary microphone use requires instructor-approved guidance and the app's
explicit consent; a checked box alone does not override portal policy. Otherwise
use the synthetic WAV path: the finished solution can generate and download a
short target-language sample with MAI Voice, and you build that capability in
lesson 2. No prepackaged `sample.wav` is assumed.

**Ready means:** the environment starts, dependencies import, private forwarding
is allowed, the instructor has checked gateway access/capacity and data guidance,
and you have a usable browser or synthetic-audio alternative. No live access has
been established merely by following these configuration checks.

Continue to [Open your app](lessons/00-open-your-app.md).
If Codespaces is unavailable, use [local setup](local-setup.md), not a different
application.
