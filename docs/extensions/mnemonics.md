# After core: a mnemonic with MAI-Thinking

**Optional, after the guided core.** Add a short English memory suggestion to
the same app. Do not replace the deterministic answer matcher with an LLM.

**What, how, and which components:** a new button sends an English word to
Flask `/mnemonic`; Flask calls the gateway's chat-completions route using the
`mai-thinking` deployment; JavaScript displays the returned **plain text** in
the card. The model may be wrong, verbose, or unhelpful. Preview status and model
availability apply; there is no guaranteed JSON schema or verified multilingual
mnemonic coverage.

Sources: [MAI Thinking API](https://learn.microsoft.com/azure/foundry/foundry-models/how-to/use-foundry-models-mai-thinking),
[pinned deployment catalog](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/config/models.yaml),
and [gateway participant example](https://github.com/jeffrey-groneberg/mai-llm-hax-provider/blob/9d2fa8d6d2214764ea02c281498ef243e3420d29/app/catalog.py).

## Build it and see it work

Complete core lessons 1-5 first. **Append this route at the end of
`starter/app.py`**; its helpers were added in the core:

```python title="starter/app.py"
@app.post("/mnemonic")
def mnemonic():
    data = json_body()
    word = text_field(data, "word")
    base, headers = gateway_settings()
    response = httpx.post(
        f"{base}/mai/v1/chat/completions", headers=headers,
        json={
            "model": "mai-thinking",
            "messages": [{"role": "user", "content": (
                f"Write one short, imaginative English mnemonic for the English word "
                f"{word!r}. Use at most two sentences. Do not claim it is a verified fact."
            )}],
            "max_completion_tokens": 2048,
        }, timeout=TIMEOUT,
    )
    payload = upstream_json(response)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        abort(502, "The reasoning model returned no suggestion.")
    message = choices[0].get("message")
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        abort(502, "No text suggestion was returned. The model may have exhausted its output budget.")
    return jsonify(text=text.strip())
```

The `messages` prompt requests a length and tone; it does not enforce them.
`max_completion_tokens` bounds model output, including the reasoning budget.
Do not parse `choices[0].message.content` as JSON or assume it contains exactly
two sentences. The app reports an empty result instead of inventing a fallback.

In **`starter/templates/index.html`, replace**
`<!-- Add mnemonic controls here. -->` with:

```html title="starter/templates/index.html"
<details class="extension">
  <summary>Try a mnemonic <span class="eyebrow">AFTER CORE</span></summary>
  <p class="muted">Ask for a short English memory suggestion. Check it yourself; it never grades an answer.</p>
  <button id="generate-mnemonic" class="button secondary" type="button">Suggest a mnemonic</button>
  <p id="mnemonic-result" class="status" role="status"></p>
</details>
```

In **`starter/static/app.js`, insert before `// Start the page.`**:

```javascript title="starter/static/app.js"
$("#generate-mnemonic").addEventListener("click", () => {
  runAction("MAI Thinking is considering your word...", async () => {
    const response = await callApp("/mnemonic", jsonOptions({word: selectedWord().english}));
    const result = await appJSON(response);
    if (typeof result.text !== "string" || !result.text.trim()) {
      throw new Error("No text suggestion was returned.");
    }
    $("#mnemonic-result").textContent = result.text;
  });
});
```

Finally, **inside `selectWord` in that same JavaScript file, insert**
`$("#mnemonic-result").textContent = "";` **immediately after**
`$("#answer-result").hidden = true;`. This keeps an old suggestion off a newly
selected word.

**Run it end to end:** restart Flask, reload, select an English word, expand
**Try a mnemonic**, and press the button. Inspect `POST /mnemonic` and the text
on the card. Mark any factual or language mistake. Text is displayed with
`textContent`, never executed as HTML or accepted as a grading answer.
The [reference `/mnemonic`](https://github.com/jeffrey-groneberg/the-mai-workshop/blob/jeffrey-groneberg-mai-vocabulary-workshop/solution/app.py)
uses the same response shape.

## Experiment with your working feature

**Try one if you chose this extension. Predict -> change -> run -> compare ->
choose.** Each click makes a fresh request.

| Choice | Exact change and interpreting component | Observe and restore |
| --- | --- | --- |
| Example instead of mnemonic | In `starter/app.py`, change `one short, imaginative English mnemonic` in the `messages` prompt to `one simple English example sentence`. | Restart Flask and request the same word. Compare usefulness and accuracy, then choose or restore the prompt. MAI interprets the words, not an output schema. |
| A quieter tone | Replace `imaginative` in that prompt with `practical and understated`. Keep the same word and length request. | Restart, generate, and compare tone without assuming factual correctness improves. Keep your preference or restore `imaginative`. |

Larger additions such as explicitly approved answer variants or a practice
schedule are also after-core work. They are not prerequisites for the workshop's
completed core loop.
