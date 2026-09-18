# Make a visual memory cue

Generate a picture that helps you remember a word.

**Flow:** button → Flask `/image` → MAI Image → base64 PNG → browser image.
The request uses deployment `mai-image-flash`, an English prompt, and
1024 × 1024 dimensions. Flask decodes `data[0].b64_json`.
[API details](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-image).

## Build

In **`starter/app.py`, insert these imports at the top**, keeping the existing
imports:

```python title="starter/app.py"
import base64
import binascii
import struct
```

**Append to `starter/app.py`.** The route checks the returned PNG before
serving its bytes.

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
This restores a word's cached image without another request.

**Run:** restart Flask, reload, and press **Make a memory image**.
Network shows `POST /image` and an `image/png` response. Switch words and back:
the picture returns. Reloading clears images, not the word list.

![The app's memory-image section displaying a watercolor apple below its scene prompt.](../assets/workshop/05-memory-image.webp){ width="484" loading="lazy" }

*Captured with an example image response.*

### One word, two explicit scenes

The scene prompt distinguishes two meanings of `bank`:

| **River bank**: the natural edge of a river | **Savings bank**: a financial institution |
| --- | --- |
| ![Generated teaching illustration of a river and its grassy bank](../assets/images/river-bank.webp){ width="280" height="280" loading="lazy" } | ![Generated teaching illustration of a savings-bank building with coins and a piggy bank](../assets/images/savings-bank.webp){ width="280" height="280" loading="lazy" } |

*MAI-generated examples with different prompts. [Exact prompts](../assets/images/provenance.json).*

## Try one

- For `apple`, compare an empty scene with
  `A single apple on a picnic blanket, soft watercolor`.
- For `bank`, compare `A river bank with reeds, no buildings` with
  `A bank building on a city street`. Which matches your saved translation?

Generate both versions and keep the more useful prompt. Each Generate click
makes a new request.

**Finish:** use the full loop—select, listen, record or upload, check, and picture.
Then try [optional mnemonics](../extensions/mnemonics.md).
