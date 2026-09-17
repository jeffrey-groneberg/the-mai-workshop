# Local setup fallback

Use this only when Codespaces is unavailable or you intentionally choose local
development. The app and lesson edits are identical: work in `starter/`, inspect
`solution/`, and keep four main source files per app.

You can read the instructor-confirmed static GitHub Pages guide while running
Flask locally. Pages cannot run either app or hold private gateway configuration. The Zensical server
below is only a local documentation preview; it is unnecessary when using the
published guide.

Install Git and the Python version specified by the repository's dev-container
configuration (Python 3.12). Clone the repository's default `main` branch:

```sh
git clone https://github.com/jeffrey-groneberg/the-mai-workshop.git
cd the-mai-workshop
```

A trusted download from `main` works too. Run the following commands from
the repository root. Local Python, microphone permission, and network access
need their own readiness check; do this before the core session.

## macOS or Linux

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-docs.txt
```

If `python3.12` has a different command name on your machine, use the installed
Python 3.12 executable for the first command. After activation, `python` refers
to this virtual environment, not system Python.

## Windows PowerShell

Use the virtual environment's Python directly; activation and changing
PowerShell execution policy are unnecessary:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-docs.txt
```

The Codespaces `python` commands in the lessons become
`.\.venv\Scripts\python.exe` on this path. Do not change system security policy
merely to activate a workshop environment.

## Configure the same server-side gateway

In the editor, create a root `.env` using the empty `.env.example` as a guide.
**Both `APIM_BASE_URL` and `APIM_API_KEY` are sensitive configuration.** Set
`APIM_BASE_URL` privately to the instructor's HTTPS gateway **origin only**,
without any path, and `APIM_API_KEY` to your individual key. No live values or
gateway-host examples are included in this repository. Verify that `.env` is
ignored before saving either value:

```sh
git check-ignore .env
```

The command must print `.env`. Keep both values empty in the tracked
`.env.example`. Never paste either private value into tracked files, shell
history, logs, screenshots, provenance, or browser storage, and never copy
private environment files into `site/`. Both apps use
`load_dotenv(..., override=False)`: existing environment variables override
`.env`. Restart Flask after changing configuration.

## Run each server separately

On macOS/Linux with the environment activated, run these in **separate
terminals** from the repository root. Activate the environment in each terminal:

```sh
python -m flask --app starter/app.py run --host 127.0.0.1 --port 5050
```

```sh
python -m flask --app solution/app.py run --host 127.0.0.1 --port 5051
```

```sh
zensical serve --dev-addr 127.0.0.1:8000
```

On Windows PowerShell, the corresponding separate-terminal commands are:

```powershell
.\.venv\Scripts\python.exe -m flask --app starter/app.py run --host 127.0.0.1 --port 5050
```

```powershell
.\.venv\Scripts\python.exe -m flask --app solution/app.py run --host 127.0.0.1 --port 5051
```

```powershell
.\.venv\Scripts\zensical.exe serve --dev-addr 127.0.0.1:8000
```

Open [Your app](http://127.0.0.1:5050),
[Finished solution](http://127.0.0.1:5051), and
[Workshop guide](http://127.0.0.1:8000) in normal browser tabs. Keep loopback
binding; do not substitute `0.0.0.0` or use another device's LAN address.
The private Codespaces container binding is not the local fallback binding.

Browsers treat loopback as potentially trustworthy, but microphone permission,
audio decoding, hardware, and policy still need checking
([MDN secure contexts](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts)).
Use an approved synthetic WAV if capture is unavailable or microphone guidance
is not approved. Audio still leaves your laptop after explicit Send; local Flask
does not make the hosted model local.

Continue with [Open your app](lessons/00-open-your-app.md), substituting the
local commands above. Use `Ctrl+C` in the appropriate terminal before restarting
Flask after Python or HTML-template edits, then reload the browser. JavaScript
and CSS edits need a browser refresh. Do not run Flask's interactive debugger.
