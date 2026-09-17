---
name: MAI Vocabulary Workshop
description: Native Zensical documentation, with a separate editorial style for the Flask apps.
colors:
  app-paper: "#fef9ed"
  app-ink: "#5d524b"
  app-muted: "#75665b"
  app-sand: "#f7ecd9"
  app-line: "#d9cbbc"
  app-focus: "#795338"
  app-error: "#813e32"
  app-success: "#405c44"
typography:
  app-display:
    fontFamily: '"Source Serif 4", Georgia, serif'
    fontWeight: 400
  app-body:
    fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif'
    fontSize: "1rem"
    lineHeight: 1.65
  app-utility:
    fontFamily: '"Red Hat Mono", ui-monospace, monospace'
rounded:
  app-control: "0.75rem"
  app-panel: "1.75rem"
  app-pill: "999px"
---

# Design System: MAI Vocabulary Workshop

## Overview

The documentation and the applications have deliberately separate visual rules.

**Workshop guide:** use native Zensical styling. The user replaced the custom
Microsoft AI companion skin because readable prose and code take priority.
`zensical.toml` must not add a custom stylesheet, palette, font, or template
override. Use ordinary Markdown and Zensical's built-in components.

**Flask applications:** retain the approved Microsoft AI companion character:
warm paper, brown ink, serif vocabulary/headings, sans-serif controls, and
compact mono utilities. These styles are defined in
`solution/static/style.css` and `starter/static/style.css`, not in the guide.
The user-pinned reference is https://microsoft.ai/models/; no random selection
roll or separate comp was produced.

## Colors

The frontmatter colors apply **only to the Flask apps**. Their warm neutrals
separate open collection space from the lightly tinted practice panel. Errors
and matches have explicit text as well as color.

Let the pinned Zensical version own the guide's native colors, code highlighting,
borders, and navigation states. Do not copy the app palette into documentation.

## Typography

The guide inherits Zensical's standard heading, body, and code typography.
Do not add oversized display headings, forced line breaks, or serif code-page
styling. Code blocks remain selectable and use the native copy control.

The apps use self-hosted Source Serif 4 and Red Hat Mono with their licenses
under each app's `static/fonts/`. Body text uses system/script fallbacks.
Display text is regular weight and long vocabulary/status text wraps.

## Layout

The guide is a documentation layout: standard header, navigation, article
column, table of contents, and mobile drawer. Its homepage is a short
introduction, lesson table, setup guidance, and a supporting illustration.

The apps retain their two-column collection/practice workspace. At `50rem`
the columns stack; narrower breakpoints tighten controls and stack paired
inputs. App headers, main content, and footers share an `83rem` maximum width.

## Elevation & Depth

Use Zensical's existing depth rules for the guide.

Apps are flat and paper-first: fine rules and restrained peach washes rather
than nested shadowed cards. Keep the existing CSS; do not create a shared
documentation/app theme package.

## Shapes

App actions are pills; fields and notices have softer corners, with the larger
practice panel using the app-panel radius. Native Zensical shapes are independent.

## Components

- **Guide:** ordinary Markdown headings, paragraphs, lists, tables, code fences,
  disclosures, and built-in navigation/search/copy affordances.
- **App:** labeled inputs, native controls, authored SVG removal icons, explicit
  selection/progress/error states, and a focused practice panel.
- **Accessibility:** keep keyboard focus, skip links, status/alert semantics,
  language attributes, sensible wrapping, and reduced-motion behavior.
- **Images:** retain the three original MAI teaching illustrations and their
  provenance. Use them as supporting content with alt text and AI-generated
  captions, not a replacement for instructions or live model results.

## Do's and Don'ts

- **Do** prioritize reading and code in the workshop guide.
- **Do** keep the four-main-file apps visually appealing and independent.
- **Do** preserve teaching outcomes, experimentation, and private configuration.
- **Don't** reintroduce guide-specific CSS, custom fonts, or marketing layouts
  without a new user request.
- **Don't** alter the app styling merely because the guide uses native styling.
- **Don't** put real endpoint URLs or API keys in source, metadata, or assets.
