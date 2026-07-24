# Design.md — Visual Direction for MemoryVerse AI

## 1. Design Thesis

MemoryVerse turns scattered documents into a growing, connected record of a person's journey. The visual language should feel like an **archive that's alive** — layered, cumulative, and organic, not a sterile database UI. The concrete reference point: **growth rings and topographic contour lines** — a record that visibly accumulates over time, the same way a tree ring or a contour map encodes history in its layers. This is distinct from a generic "AI product" look and ties directly to the product's actual thesis: identity that grows with every upload.

*(Self-check: this is deliberately not the cream+terracotta default, not the near-black+acid-accent default, and not a broadsheet/newspaper layout — it's grounded in the product's own growth metaphor instead.)*

## 2. Color Palette

| Token | Hex | Use |
|---|---|---|
| `--bg-base` | `#14201C` | App background — deep forest charcoal, not pure black |
| `--bg-surface` | `#1E2E27` | Cards, panels, upload zones |
| `--bg-surface-raised` | `#293D34` | Modals, hover states |
| `--accent-gold` | `#E8A93B` | Achievements, certifications, career-match highlights — the "seal" color |
| `--accent-sage` | `#6FA98C` | Skills, connections, growth indicators |
| `--text-primary` | `#F2EFE6` | Body text, headings — warm off-white, not stark white |
| `--text-muted` | `#9CA8A0` | Secondary text, timestamps, metadata |
| `--border-hairline` | `#324840` | Dividers, card borders |
| `--state-error` | `#D97759` | Errors, gaps in career match analysis |

**Rule:** gold is reserved for things the user has *achieved* (certifications, completed matches). Sage is reserved for *capability in progress* (skills, active connections). Never mix their semantic roles — this consistency is what makes the graph legible at a glance.

## 3. Typography

| Role | Typeface | Notes |
|---|---|---|
| Display (headings, hero moments) | **Fraunces** | Warm, editorial serif with real character — used for page titles and the Career Intelligence match score, not for body copy |
| Body | **Inter** | Clean, highly legible at small sizes for dense document lists |
| Utility / data (timestamps, entity labels, graph node labels, code-like metadata) | **IBM Plex Mono** | Reinforces the "record/ledger" feel wherever exact data appears |

**Type scale:** display 40/32/24px (page title / section title / card title), body 16/14px (primary / secondary), utility 13px monospace throughout.

Use Fraunces sparingly — one hero moment per screen (a page title, a match score, a milestone headline). Everywhere else stays quiet so the one display moment actually reads as special.

## 4. Layout Concepts

**Dashboard:** a card grid of recent uploads, each card showing category (color-coded via the gold/sage system), extracted title, and date. No numbered markers here — this isn't a sequence.

**Knowledge Graph (signature screen):** full-bleed dark canvas, nodes rendered as soft glowing points — gold for achievements, sage for skills/projects — connected by thin luminous threads. This is the one screen where the "growth ring" metaphor becomes literal and interactive. Clicking an edge surfaces its explanation in a small floating card near the cursor, not a full modal — keep the graph itself uninterrupted.

**Timeline:** a real sequence, so numbered/dated markers are appropriate here (unlike the dashboard). Vertical timeline, left-aligned dates in `IBM Plex Mono`, entries connecting back to graph nodes on hover.

**Career Intelligence:** job description input at top, match score rendered large in Fraunces with the gold accent, gap analysis as a short list with `--state-error` markers for missing items, generated resume/cover letter shown in a document-style panel (utility mono for any inline citations back to source files).

## 5. Signature Element

The **constellation knowledge graph** is the one thing this product should be remembered by. Every other screen stays visually quiet and disciplined so this one screen lands with full impact in the demo. Resist the temptation to add graph-style glow effects elsewhere — spend the visual boldness in exactly one place.

## 6. Motion

- Graph nodes gently pulse on load (a single orchestrated moment, not continuous distraction).
- New document upload: card fades/slides in as it's categorized — communicates "this just happened," not decoration for its own sake.
- Respect `prefers-reduced-motion` — disable pulse/slide animations, keep instant state changes only.

## 7. Accessibility Floor

- All text meets WCAG AA contrast against its background token.
- Visible keyboard focus states on every interactive element (upload zone, graph nodes, search input) — use `--accent-gold` as the focus ring color.
- Responsive down to mobile: graph view collapses to a simpler list-of-connections view below 768px rather than a cramped canvas.
