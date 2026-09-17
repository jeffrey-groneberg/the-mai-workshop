---
name: MAI Vocabulary Workshop
description: Warm editorial paper and restrained controls for learning and vocabulary practice.
colors:
  paper: "#fef9ed"
  ink: "#5d524b"
  muted: "#75665b"
  sand: "#f7ecd9"
  line: "#d9cbbc"
  field: "#fffcf5"
  field-border: "#a18c7a"
  control-border: "#c5b29e"
  focus: "#795338"
  error: "#813e32"
  success: "#405c44"
  error-surface: "#f7e7dd"
  success-surface: "#edf0df"
  warning-surface: "#f8ebd5"
typography:
  display:
    fontFamily: '"Source Serif 4", "Iowan Old Style", "Noto Serif", "Noto Serif CJK SC", "Noto Serif Devanagari", "Noto Serif Thai", Georgia, serif'
    fontWeight: 400
  body-app:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", "Noto Sans", "Noto Sans CJK SC", "Noto Sans Devanagari", "Noto Sans Thai", sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.65
  body-guide:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", "Noto Sans", "Noto Sans CJK SC", "Noto Sans Devanagari", "Noto Sans Thai", sans-serif'
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.75
  label:
    fontFamily: '"Red Hat Mono", ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", monospace'
  button-app:
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.4
  button-guide:
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  navigation: "0.5rem"
  control: "0.75rem"
  notice: "0.875rem"
  image: "1rem"
  panel-mobile: "1.25rem"
  panel: "1.75rem"
  pill: "999px"
spacing:
  tight: "0.5rem"
  small: "0.75rem"
  base: "1rem"
  comfortable: "1.5rem"
  section: "1.75rem"
  generous: "2rem"
  wide: "3rem"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.button-app}"
    rounded: "{rounded.pill}"
    padding: "0.7rem 1.2rem"
  button-secondary:
    backgroundColor: "{colors.sand}"
    textColor: "{colors.ink}"
    typography: "{typography.button-app}"
    rounded: "{rounded.pill}"
    padding: "0.7rem 1.2rem"
  button-text:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.button-app}"
    rounded: "{rounded.pill}"
    padding: "0.7rem 0.35rem"
  guide-button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.button-guide}"
    rounded: "{rounded.pill}"
    padding: "0.65rem 1.2rem"
  guide-button-secondary:
    backgroundColor: "{colors.sand}"
    textColor: "{colors.ink}"
    typography: "{typography.button-guide}"
    rounded: "{rounded.pill}"
    padding: "0.65rem 1.2rem"
  field:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0.65rem 0.85rem"
  practice-panel:
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "clamp(1.5rem, 3.2vw, 2.75rem)"
  guide-navigation-active:
    backgroundColor: "{colors.sand}"
    textColor: "{colors.ink}"
    rounded: "{rounded.navigation}"
    padding: "0.35rem 0.5rem"
---

# Design System: MAI Vocabulary Workshop

## Overview

**Creative North Star: "Microsoft AI companion"**

Warm paper, brown serif headings, quiet sans-serif reading text and compact
monospaced utility labels connect the guide and vocabulary app. Spacious,
open sections surround a small number of softly tinted working surfaces.

The user chose [Microsoft AI models](https://microsoft.ai/models/) and approved
the collection/practice layout. This extends that reference: seed not applicable;
no selection roll or separate bespoke comp was performed. Source Serif 4 is the
approved redistributable replacement for commercial Bradford LL.

**Key Characteristics:**
- Editorial headings, readable prose and functional mono labels.
- Paper-first layouts, fine brown rules and sand pill controls.
- Explicit interaction states and restrained original teaching artwork.

Source authority: [guide CSS](docs/stylesheets/workshop.css),
[guide home](docs/index.md), [template overrides](overrides/),
[app CSS](solution/static/style.css), [app template](solution/templates/index.html)
and [browser behavior](solution/static/app.js). The
[starter stylesheet](starter/static/style.css) is identical to the app stylesheet;
its [template](starter/templates/index.html) remains a sample, not the completed
practice loop. Keep the existing four-main-file app structure; this record adds
no UI framework or token package.

## Colors

Brown supplies emphasis rather than a bright brand accent; warm neutrals do most
of the work. Frontmatter records shared/repeated values, not every CSS literal.
Guide custom properties use the `--workshop-` prefix; app equivalents are
unprefixed. Both surfaces explicitly use the light color scheme.
Sidecar tonal ramps are generated swatch previews, not shipped CSS color scales.

### Primary
- **Ink:** headings, body text, wordmark and solid primary actions.
- **Focus:** the darker warm outline for keyboard interaction.

### Neutral
- **Paper / Sand:** page ground and secondary controls/navigation selection.
- **Muted:** supporting copy, captions and metadata, not disabled text.
- **Line:** quiet dividers and container edges.
- **Field / Field Border / Control Border:** near-paper entry surfaces and
  stronger interactive boundaries, distinct from decorative rules.

### Feedback
- **Error / Error Surface:** alert copy and warm rose notices.
- **Success / Success Surface:** matched-answer feedback.
- **Warning Surface:** retry feedback and guide warnings.
  Feedback also has written meaning and distinct borders; these are semantic
  states, not additional brand accents.

## Typography

**Display Font:** Source Serif 4, with the frontmatter's serif/script fallbacks.  
**Body Font:** the frontmatter's system sans-serif stack.  
**Label/Mono Font:** Red Hat Mono, also used for guide code.

Self-hosted font files and licenses live in `docs/assets/fonts/` and each app's
`static/fonts/`. Fonts use `font-display: swap`; synthesis is disabled.
The guide preloads Source Serif 4 through `overrides/main.html`.

### Hierarchy

| Role | Guide | App |
| --- | --- | --- |
| Display | Home: `clamp(2.5rem, 6vw, 4.65rem)`, line-height `1.06`; article h1: `2.65rem` / `1.13` | Intro: `clamp(2.7rem, 5.6vw, 5rem)` / `1.07` |
| Headline | Article h2: `1.65rem` / `1.2`; home sections: `1.75rem` | h2: `1.9rem` / `1.2` |
| Title | Article h3: `1.2rem` / `1.3` | h3: `1.45rem` / `1.2` |
| Body | `body-guide`; paragraphs capped at `73ch` | `body-app`; intro copy capped at `48ch` |
| Functional mono | Tabs `0.625rem`, secondary navigation title `0.6rem`, lesson markers `0.65rem` | Count/reference link `0.75rem`; step numbers `0.6875rem` |

Headings are regular-weight and balanced; h1 tracking is `-0.035em`. App h2
shares that tracking; guide article h2 uses `-0.025em`. The selected practice
word grows to `clamp(2.5rem, 4.5vw, 4rem)` and wraps long content.

**Units matter:** guide rems inherit Zensical's root sizing (base `125%`, with
`137.5%` at `100em` and `150%` at `125em`); the app leaves the browser root size unchanged.
Do not copy guide rem values into the app as if their rendered sizes matched.

**The Type Has a Job Rule.** Serif carries headings and vocabulary; sans carries
instructions and status; mono identifies navigation, counts, steps and code.
Functional labels are not a license to add decorative above-heading copy.

## Layout

- **Guide:** the shell caps at `76rem`, home content at `65rem`; lessons retain
  Zensical navigation, search and reading structure. The home uses an open
  three-column rhythm and two-column explanatory/lesson sections, not a card
  for each paragraph. Main section gaps recur around the `wide` spacing step;
  section starts use larger `4–4.5rem` intervals.
- **App:** header, main and footer share an `83rem` maximum with horizontal
  padding `clamp(1.25rem, 4.5vw, 4rem)`. The workspace is
  `minmax(0, 0.85fr) minmax(0, 1.15fr)`, top-aligned, with a
  `clamp(2rem, 4.5vw, 4rem)` gap. Collection stays on open paper; practice gets
  the tinted panel. Repeated practice steps use equal top margin/padding
  (`section`) and a thin divider.
- **Guide breakpoints:** `76.234375em` adjusts the drawer/header treatment;
  `60em` tightens gaps and stacks file descriptions; `44.984375em` stacks home
  grids and reduces headings. Below `24em`, actions fill the available width
  and file descriptions stack again.
- **App breakpoints:** at `50rem`, collection precedes practice in one column;
  at `30rem`, panels use `panel-mobile` corners and `1.25rem` padding, the
  footer stacks and controls tighten; at `23rem`, paired inputs stack.
- Action rows wrap, grid children have `min-width: 0`, and long words/statuses
  wrap rather than widening the page. Guide print styles remove the home wash,
  reduce large gaps and preserve underlined links.

Spacing and corner tokens above name repeated source literals; they are not
additional CSS custom properties.

## Elevation & Depth

**The Paper Before Panels Rule.** Use open paper and fine rules for hierarchy;
tint working surfaces instead of boxing every section.

The app has no shadows. Its practice/starter panels use a low-contrast
peach-to-paper wash; the guide home uses a related warm wash. These gradients
belong to the chosen world. Guide headers, code, tables and admonitions stay
flat. Soft shadows remain on search output and the back-to-top affordance only:
`0 0.4rem 1.2rem #5d524b1a` and `0 0.25rem 0.75rem #5d524b14`.
They are utility elevation, not a general card treatment.

## Shapes

Pill-shaped actions/search contrast with gently rounded fields, notices, images
and larger panels. Default edges are thin (`1px`); field borders are stronger
in color than structural dividers. The frontmatter's corner steps describe the
app and shared image/control shapes; guide tables/admonitions use their own
nearby `0.7rem` rounding. Do not normalize those surface-specific values away.

## Components

### Buttons and fields
- Primary actions use paper text on ink; secondary actions are sand
  with a control-colored border; text actions remain visibly underlined.
  App buttons have a `2.875rem` minimum height; guide actions use `2.5rem`.
- Hover-capable devices darken primary fills or warm secondary fills. Active
  fills are separately defined; background/border transitions are `160ms ease-out`.
  Disabled app actions have muted sand fills and a not-allowed cursor.
- App fields/selects have visible labels, full width, a `3rem` minimum height,
  and a field-colored fill. Native required/length constraints are present.
  CSS supplies a stronger error border for `aria-invalid="true"`; current
  validation reports through the alert rather than setting that attribute.

### Navigation and reading surfaces
- Serif wordmarks anchor quiet headers. Guide navigation uses sans-serif;
  top tabs and utility labels use mono. Active links combine weight and
  underlining; primary navigation adds sand. Mobile keeps Zensical's drawer
  and search controls. Real framework SVG icons remain functional affordances.
- Guide links stay underlined. Code panels, copy controls, tables, disclosure
  blocks and admonitions inherit the warm palette without losing their
  reading/interaction roles.

### Collection and practice
- Saved words are divided rows with a wide selectable button. Selection uses
  `aria-pressed`, a stronger border, sand fill and heavier type. The live row
  is plain word/locale text; dormant nested-label styles are not a row pattern.
- Removal uses a small authored SVG inside a labeled button; it is not a text
  glyph or a place to inject participant content.
- One practice panel changes from an explanatory empty state to the selected
  word, revealable translation and divided tasks. Optional material remains
  a native disclosure. The solution identity is ordinary connection/status
  copy, not a decorative kicker.

### States and accessibility

**The State in Words Rule.** Pair state styling with explicit copy and native
control semantics; color alone does not explain selection, progress or results.

- Keep skip links, associated labels, native buttons/selects/checkboxes/audio
  controls, `role="alert"` errors and polite live status regions. Adding a word
  returns focus to the English input; translations/transcripts carry locale
  language attributes.
- Keyboard outlines use the focus token (`3px`, offset `3px` guide / `4px`
  app). Forced colors use system outlines/borders and preserve selected-state
  outlines. There is no blanket claim that every inherited control is audited.
- Pending model work disables competing model actions and announces progress.
  A strong `[hidden]` rule prevents unrevealed content or unavailable controls
  from becoming visible through layout CSS.
- Recording requires consent; preview precedes explicit sending. Synthetic
  WAV download/upload offers a microphone alternative. Errors, transcript
  matches and retries explain what happened; matching is not a score.
- Reduced motion disables animations/transitions and restores automatic
  scrolling across both surfaces. Hover styling does not require touch users
  to hover.

### Images

The three WebP illustrations in `docs/assets/images/` are original
MAI-Image-2.6 teaching assets: the wide vocabulary journey and two square,
explicitly prompted senses of “bank.” Their muted watercolor palette and open
paper backgrounds complement the UI. Preserve meaningful alt text, dimensions,
lazy loading and the AI-generated teaching disclosure.
[Exact prompts/provenance](docs/assets/images/provenance.json) distinguish them
from participant outputs; they are neither stock reference images nor live
gateway evidence.

The app's memory figure appears only after a returned image is decoded, is
capped at `24rem`, and has responsive width, rounded corners, alt text and a
caption identifying it as a generated cue rather than a verified definition.
Do not replace failed/absent model results with the teaching illustrations.

## Do's and Don'ts

### Do:
- **Do** preserve the Microsoft AI companion palette and approved font roles.
- **Do** keep open reading areas distinct from tinted working surfaces.
- **Do** retain explicit state copy, keyboard outlines, reduced motion and native controls.
- **Do** distinguish labeled teaching illustrations from requested app outputs.

### Don't:
- **Don't** add decorative above-heading labels or substitute text glyphs for icons.
- **Don't** use the system sans-serif as the display face or add hard offset shadows.
- **Don't** flatten guide/app type sizes into one rem scale or add a UI framework.
- **Don't** turn unused CSS, one-off ornaments or remaining defects into reusable rules.

**Not canonized:** the empty state's letter ornament and unused style branches
are not reusable tokens. Keep starter identity and component explanations as
ordinary copy rather than adding decorative above-heading labels.
