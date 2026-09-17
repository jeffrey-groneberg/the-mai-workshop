# Make a visual memory cue

**What:** generate an image for the selected English word, keep the latest
successful image on its card while this page is open, and complete the whole
practice loop.

**How and which components:** button -> JavaScript sends the English word and
scene -> Flask `/image` -> gateway `/mai/v1/images/generations` -> MAI Image ->
base64 PNG -> validated bytes -> browser image. Nothing is generated on page
load or merely selecting a word.

`mai-image-flash` is the gateway **deployment name**, not an SSML voice ID.
The image offering is preview. Use an **English prompt**, request
`width=1024, height=1024`, and read `data[0].b64_json`.
The documented minimum dimension is 768 and the pixel budget is at most
1,048,576; a small card thumbnail is **not** a tiny API image.
Sources: [MAI image API](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image),
[pinned deployment catalog](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/config/models.yaml),
and [participant request](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/app/catalog.py).

## Build it and see it work

In **`starter/app.py`, insert these imports at the top**, keeping the existing
imports:

```python title="starter/app.py"
import base64
import binascii
import struct
```

**Append this route at the end of `starter/app.py`.** It reuses your existing
input, configuration, JSON, and error helpers. Base64 decoding alone would not
establish that an output is a PNG, so check its signature, IHDR, and dimensions;
the browser will also decode it before display.

```python title="starter/app.py"
@app.post("/image")
def image():
    data = json_body()
    word = text_field(data, "word")
    detail = data.get("detail", "")
    if not isinstance(detail, str) or len(detail) > 360:
        abort(400, "The optional scene must be text of up to 360 characters.")
    base, headers = gateway_settings()
    response = httpx.post(
        f"{base}/mai/v1/images/generations", headers=headers,
        json={
            "model": "mai-image-flash",
            "prompt": (
                f'Illustrate the English vocabulary word "{word}" as a memorable, '
                f"clear visual cue. No letters or captions. {detail}"
            ),
            "width": 1024, "height": 1024,
        }, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    entries = payload.get("data")
    if not isinstance(entries, list) or not entries or not isinstance(entries[0], dict):
        abort(502, "The image model returned no image.")
    encoded = entries[0].get("b64_json")
    if not isinstance(encoded, str) or len(encoded) > 24 * 1024 * 1024:
        abort(502, "The image model returned an invalid image payload.")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        abort(502, "The image model returned invalid base64.")
    if (
        len(image_bytes) < 33 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n"
        or image_bytes[12:16] != b"IHDR"
        or struct.unpack(">II", image_bytes[16:24]) != (1024, 1024)
    ):
        abort(502, "The image model did not return the requested PNG.")
    return Response(image_bytes, mimetype="image/png")
```

In **`starter/templates/index.html`, replace**
`<!-- Add memory controls here. -->` with:

```html title="starter/templates/index.html"
<section class="practice-step" aria-labelledby="image-title">
  <div class="step-title"><span class="step-number">02</span><h3 id="image-title">Give the word a picture.</h3></div>
  <label for="image-detail">A scene or style, in English</label>
  <input id="image-detail" maxlength="360" placeholder="A tiny apple wearing a crown">
  <button id="generate-image" class="button secondary" type="button">Make a memory image</button>
  <p id="image-status" class="status" role="status"></p>
  <figure id="memory-figure" class="memory-figure" hidden>
    <div id="image-mount"></div>
    <figcaption>A generated visual cue, not a verified definition.</figcaption>
  </figure>
</section>
```

In **`starter/static/app.js`, insert immediately before `// Start the page.`**:

```javascript title="starter/static/app.js"
const imageCache = new Map();

function renderMemory() {
  const cached = imageCache.get(selectedId);
  $("#image-mount").replaceChildren(...(cached ? [cached.picture] : []));
  $("#memory-figure").hidden = !cached;
  $("#image-detail").value = cached?.detail ?? "";
  $("#generate-image").textContent = cached ? "Generate a new image" : "Make a memory image";
  $("#image-status").textContent = cached ? "Kept for this page only. A new image makes another model request." : "";
}

$("#generate-image").addEventListener("click", () => {
  runAction("MAI Image is making a visual cue...", async () => {
    const word = selectedWord();
    const detail = $("#image-detail").value.trim();
    const response = await callApp("/image", jsonOptions({word: word.english, detail}));
    if (!response.headers.get("Content-Type")?.includes("image/png")) {
      throw new Error("Expected a PNG. Reopen the app if Codespaces sign-in expired.");
    }
    const url = URL.createObjectURL(await response.blob());
    const picture = new Image();
    picture.id = "memory-image";
    picture.alt = `Generated visual cue for ${word.english}`;
    picture.src = url;
    try { await picture.decode(); }
    catch {
      URL.revokeObjectURL(url);
      throw new Error("The returned image could not be displayed.");
    }
    const previous = imageCache.get(word.id);
    if (previous) URL.revokeObjectURL(previous.url);
    imageCache.set(word.id, {picture, url, detail});
    renderMemory();
  });
});
window.addEventListener("pagehide", () => {
  for (const cached of imageCache.values()) URL.revokeObjectURL(cached.url);
});
```

Finally, in **`starter/static/app.js`, inside `selectWord`, insert**
`renderMemory();` **immediately before that function's final `renderList();`.**
Do not insert it in `renderList` itself. This restores an already generated
image when selecting its word; selecting a word does not make a new request.

**Run it end to end:** restart Flask, reload, select a sample pair, and press
**Make a memory image**. Network shows `POST /image` with `word` and `detail`,
then an `image/png` response. A decoded image appears on the selected card.
Switch to another word and back: the image returns without another model call.
Reloading clears page-only media, but not saved vocabulary.

Now use the complete loop in **Your app**: select a pair, hear both languages,
record under approved guidance or choose a synthetic WAV, preview, explicitly
send, inspect transcript/match feedback, and view its image. Your build is a
small independent implementation of the core, not a wrapper around the
[finished solution](https://github.com/jeffrey-groneberg/the-mai-workshop/tree/jeffrey-groneberg-mai-vocabulary-workshop/solution).
It locks controls during work rather than implementing the reference's richer
cancellation behavior; its image deployment is explicit here rather than an
environment override. Errors remain visible in both.

### One word, two explicit scenes

An explicit **English scene prompt** disambiguates the intended meaning of
`bank`. Compare these two deliberately prompted teaching examples:

| **River bank**: the natural edge of a river | **Savings bank**: a financial institution |
| --- | --- |
| ![Generated teaching illustration of a river and its grassy bank](../assets/images/river-bank.webp){ width="280" height="280" loading="lazy" } | ![Generated teaching illustration of a savings-bank building with coins and a piggy bank](../assets/images/savings-bank.webp){ width="280" height="280" loading="lazy" } |

These are **generated teaching examples**, made with MAI-Image-2.6 using different
explicit scene prompts. They are **not evidence of the bare word `bank`'s default
output**, or of acceptance by a participant's gateway. The
[exact prompts and provenance](../assets/images/provenance.json) record how they
were made. Use the ambiguity experiment below to explore your own requests.

## Experiment with your working feature

**Try one. Predict -> change -> run -> compare -> choose.** Every intentional
**Generate a new image** click makes another potentially billable request,
including repeated prompts. Shared quota, content policy, and capacity apply;
there is no guaranteed latency or identical result.

| Choice | Exact change and interpreting component | Observe and restore |
| --- | --- | --- |
| Specify a scene | In the card's English scene field, compare an empty field with `A single apple on a picnic blanket, soft watercolor`. Flask appends this to the English prompt; MAI interprets it. | Generate each, compare how clearly it cues the intended meaning, and keep your preferred scene. Clear the field to restore the baseline. The tiny subject in a prompt is still a 1024 x 1024 API image. |
| Resolve ambiguity | For an illustrative English word such as `bank`, compare `A river bank with reeds, no buildings` and `A bank building on a city street`. Keep the saved translation appropriate to your intended meaning. | Generate both and compare against that translation. Choose the prompt that communicates the meaning, or discard the entry. A plausible image is not proof that the word or translation is correct. |

**Core complete when your own app works and you have tried one choice on every
core page.** The fixed two-hour target remains unvalidated until a
representative learner-paced pilot includes these edits, experiments, and real
service behavior. Do not count a fast fixture replay or reference demonstration
as that pilot.

[MAI-Thinking mnemonics](../extensions/mnemonics.md) are an **after-core,
optional** addition. Troubleshooting and API details are in
[Reference](../reference.md).
