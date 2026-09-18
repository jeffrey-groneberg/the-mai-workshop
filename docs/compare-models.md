# Compare models and cost

Compare the same task, language, and output format—not just model names.
The [app's feature map](index.md#which-models-you-use) shows its four model choices.

## The MAI family

![Six featured MAI families: Voice for speech synthesis, Transcribe for audio to text, Image for generation and edits, Thinking for reasoning, Code for agentic coding through Copilot, and Cyber for defensive work through restricted MDASH. Frontier Tuning customizes models.](assets/diagrams/mai-family.webp){ width="960" height="549" loading="lazy" }

*MAI-generated diagram. [Full size](assets/diagrams/mai-family.webp) · [Prompts and revisions](assets/diagrams/provenance.json).*

These are the [currently featured families](https://microsoft.ai/models/),
checked **18 September 2026**, not every historical version.
[Voice](https://learn.microsoft.com/azure/ai-services/speech-service/mai-voices)
and [Image](https://microsoft.ai/models/mai-image-2-6/) include Flash variants.
[Code](https://microsoft.ai/models/mai-code-1-flash/) is offered through Copilot;
[Cyber](https://microsoft.ai/models/mai-cyber-1-flash/) has restricted MDASH access.
[Frontier Tuning](https://microsoft.ai/models/microsoft-frontier-tuning/) is model
customization, not a seventh model. Those three are not workshop runtime calls.

## What the prices establish

**Public Azure USD pay-as-you-go rates, checked 18 September 2026.**
These are normalized inference budgets, not measured app runs or a claim of
equal quality. Cache savings, free allowances, negotiated rates, and Batch/Flex
discounts are excluded.

| Task and workload | MAI | Comparable Azure model | Cost conclusion |
| --- | --- | --- | --- |
| Transcribe **1,000 audio minutes** | **MAI-Transcribe-2:** **$1.67** at the advertised **$0.10/hour promotion** | **Whisper `001`, Regional:** **$6.60** at $0.396/hour | **74.7% lower if the MAI promotion applies.** |
| Speak **1 million billable characters** | **MAI-Voice-2-Flash:** model-specific tariff not verified | **`tts` `001`, Regional:** **$15** | No verified MAI saving yet. |
| Generate **100 images at 1024 × 1024** | **MAI-Image-2.6-Flash:** $1.75/million text-input tokens; $19/million image-output tokens | **GPT Image 1, medium:** **$4.274** under the token assumptions below | MAI's token rates are lower; a per-image saving is **not established**. |
| Generate text with **1 million uncached input + 100,000 output tokens** | **MAI-Thinking-1:** **$2.80** at $2/$8 per million input/output tokens | **GPT-5-mini:** **$0.45** at $0.25/$2 | MAI costs **$2.35 more** for this token mix. |

**Transcription:** the [MAI announcement](https://microsoft.ai/news/mai-transcribe-2-is-the-fastest-most-accurate-and-cheapest-speech-recognition-model-in-the-world/)
quotes $0.10/hour; [Speech pricing](https://azure.microsoft.com/en-us/pricing/details/speech/)
marks a discount through **31 December 2026**, while its generic MAI table still
shows $0.36/hour. Confirm the applicable offer before budgeting. The comparison
uses MAI in **East US** and Whisper Regional in **North Central US**.
[Whisper retail rate](https://prices.azure.com/api/retail/prices?currencyCode=USD&%24filter=productName%20eq%20%27Azure%20OpenAI%27%20and%20armRegionName%20eq%20%27northcentralus%27%20and%20contains%28skuName%2C%27Whisper%27%29).

**Speech:** do not assign generic Neural/Neural HD prices to MAI-Voice-2-Flash
without a confirmed tariff. The baseline is ordinary Azure OpenAI `tts` in
**North Central US**, not `tts-hd` or token-metered `gpt-4o-mini-tts`.
[OpenAI pricing on Azure](https://azure.microsoft.com/en-us/pricing/details/azure-openai/).

**Images:** text-to-image only, with no input image or web grounding.
GPT Image 1 medium uses **1,056 output tokens/image** at
$40/million, plus an assumed **100 prompt tokens/image** at $5/million:
`100 × (100 × 5 + 1056 × 40) / 1,000,000 = $4.274`.
For MAI, independently assume **10,000 text-input tokens (100 per image)**,
costing $0.0175. Identical prompts need not tokenize identically across models.
MAI costs `$0.0175 + 19 × Q / 1,000,000`, where **Q is its actual total image-output
tokens**. No verified MAI pixel-to-token formula or equivalent `medium` setting
was found, so Q is not guessed.
[GPT image token table](https://developers.openai.com/api/docs/guides/image-generation#earlier-gpt-image-models) ·
[MAI retail rates](https://prices.azure.com/api/retail/prices?currencyCode=USD&%24filter=productName%20eq%20%27MAI%20Models%27%20and%20contains%28skuName%2C%272.6%27%29%20and%20contains%28skuName%2C%27Flash%27%29%20and%20armRegionName%20eq%20%27eastus%27).

**Text:** output counts include reasoning, not just the visible mnemonic.
GPT-5-mini is a smaller reasoning baseline for this short task, not an
equal-capability claim.
[MAI pricing](https://azure.microsoft.com/en-us/pricing/details/ai-foundry-models/microsoft/) ·
[Azure OpenAI pricing](https://azure.microsoft.com/en-us/pricing/details/azure-openai/).

Image/text rows use **Global Standard**: MAI in East US, GPT Image 1 in East US 2,
GPT-5-mini in East US. Versions: Image Flash `2026-07-31`, GPT Image 1
`2025-04-15`, Thinking `2026-06-01`, GPT-5-mini `2025-08-07`.
The older comparators remain listed; they are not presented as the latest models.

## Try a controlled comparison

Use the app and the comparator's existing playground—no new adapter needed.

1. Pick **one feature** and ten pairs in a language supported by both models.
   Reuse the same WAV for
   transcription, text/language for speech, or prompt and requested size for images.
2. Run each model three times. Record useful results, errors, total latency,
   and its actual billable units. For text, include reasoning tokens.
3. Compare **cost per useful result**, not just price per request. Keep voice,
   quality, deployment, region, and settings in your notes.

If the MAI voice tariff or actual image-output token count is unavailable,
record cost as **unverified** rather than ranking it.

Storage and answer matching make no model call. Gateway, hosting, and Codespaces
costs are separate.
