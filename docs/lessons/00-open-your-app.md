# Open your app

**What:** open a styled page you own, and inspect the finished goal separately.
This begins the guided core; [environment readiness](../getting-ready.md) is
pre-work.

**How and which components:** Python runs `starter/app.py`; Flask renders
`starter/templates/index.html`, then your browser requests
`starter/static/style.css` and `starter/static/app.js`. GitHub forwards the
private port over HTTPS. No model is involved in this page.

## Build it and see it work

Confirm that the editor is on **`jeffrey-groneberg-mai-vocabulary-workshop`**
and contains `starter/`, `solution/`, and `docs/`. A default-main Codespace
currently has only a README; use [readiness pre-work](../getting-ready.md) to
select the workshop branch instead.

In a Codespaces terminal, from the repository root, run:

```sh
python -m flask --app starter/app.py run --host 0.0.0.0 --port 5050
```

In the Ports panel, keep **Your app** (5050) **Private** and choose **Open in
Browser**. Use a normal browser tab, not an iframe/editor preview. You should
see a sample word and "JavaScript is connected." This is a functioning starting
page, not a finished word list or a page of broken AI buttons.

In a **second terminal**, run the independent reference:

```sh
python -m flask --app solution/app.py run --host 0.0.0.0 --port 5051
```

Open **Finished solution** (5051) in another tab. Inspect the intended
listen / say / check / picture loop. Model actions require valid instructor
access and approved sample data; opening the page makes no inference request.
Its saved vocabulary is separate from Your app because the origins differ.

Keep the instructor-confirmed GitHub Pages guide open if you are reading it
there. Pages hosts these **static instructions**, not Flask, your microphone
workflow, or private gateway configuration. Both the endpoint and key stay
server-side. All app actions belong in the separate **Your
app** tab.

To preview the guide in your Codespace instead, use a **third terminal**:

```sh
zensical serve --dev-addr 0.0.0.0:8000
```

Open **Workshop guide** (8000). This preview and the published guide serve the
same purpose; you need only one. Keep the editor, guide, and Your app nearby.
The [local fallback](../local-setup.md) has separate loopback commands.

| File you edit | Job |
| --- | --- |
| `starter/app.py` | Render the page and, later, make server-side model requests. |
| `starter/templates/index.html` | Define headings, fields, buttons, and result containers. |
| `starter/static/app.js` | Handle browser events, local storage, audio, and calls to Flask. |
| `starter/static/style.css` | Style the page, including the classes reused by later lessons. |

Keep the existing CSS and licensed assets. **All learner edits stay in
`starter/`.** The [solution Python](https://github.com/jeffrey-groneberg/the-mai-workshop/blob/jeffrey-groneberg-mai-vocabulary-workshop/solution/app.py),
[JavaScript](https://github.com/jeffrey-groneberg/the-mai-workshop/blob/jeffrey-groneberg-mai-vocabulary-workshop/solution/static/app.js),
and [HTML](https://github.com/jeffrey-groneberg/the-mai-workshop/blob/jeffrey-groneberg-mai-vocabulary-workshop/solution/templates/index.html)
are readable references pinned to the workshop branch. You can also open those
files in your editor. Do not overwrite your files with them or import their
implementation.

**Run it end to end:** reload Your app. In browser developer tools, Network shows
`GET /`, `/static/style.css`, and `/static/app.js`; the Flask terminal shows the
same requests. The sample word came from Python, the surrounding markup from
HTML, its appearance from CSS, and the status line from JavaScript.

**Edit/run convention for every lesson:** save all named edits before running
its checkpoint. After a Python edit, stop **Your app's** terminal with
`Ctrl+C`, then run its same command again. After an HTML or JavaScript edit,
reload the app; use a hard refresh if the browser shows an older file. We do
not enable the interactive debugger. Leave the solution server alone.

## Experiment with your working feature

**Try one. Predict -> change -> run -> compare -> choose.**

| Choice | Exact change and component | Observe and restore |
| --- | --- | --- |
| A different sample | In `starter/app.py`, change `sample_word="apple"` to `sample_word="river"`. Flask passes this value to the template. | Restart Flask and reload. Does the word change while the JavaScript message stays the same? Compare, then keep your choice or restore `"apple"`. |
| A different message | In `starter/static/app.js`, replace the quoted status message with `"My browser is ready to build."`. JavaScript, not Flask, writes this line. | Save and reload. Compare with the original line, then choose which to keep. No model or Python change is needed. |

Lesson 1 replaces the small starting files, so neither choice becomes a hidden
prerequisite. Continue to [Make it your vocabulary](01-word-list.md).
