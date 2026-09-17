# Run locally

Install Git and Python 3.12, then clone `main`:

```sh
git clone https://github.com/jeffrey-groneberg/the-mai-workshop.git
cd the-mai-workshop
```

## Install

**macOS / Linux**

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Windows, use `.\.venv\Scripts\python.exe` wherever a lesson says `python`.

## Configure

Copy `.env.example` to a root `.env`. Fill in `APIM_BASE_URL` with the
instructor's HTTPS gateway origin, without an API path, and `APIM_API_KEY`
with your participant key. Existing environment variables override `.env`.

## Start

Run these in separate terminals. On macOS/Linux, activate the environment
in each terminal first.

```sh
python -m flask --app starter/app.py run --host 127.0.0.1 --port 5050
```

```sh
python -m flask --app solution/app.py run --host 127.0.0.1 --port 5051
```

Open [your app](http://127.0.0.1:5050) and the
[solution](http://127.0.0.1:5051). Follow [lesson 00](lessons/00-open-your-app.md)
using these local commands.

After Python or HTML edits, restart Flask and reload the browser.
JavaScript/CSS edits need a browser reload.

## Preview the guide

Optional; otherwise read the published workshop.

```sh
python -m pip install -r requirements-docs.txt
zensical serve --dev-addr 127.0.0.1:8000
```

On Windows, use `.\.venv\Scripts\zensical.exe` for the second command.
