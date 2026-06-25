---
name: Seoyul Notes
colors:
  primary: "#284b63"
  secondary: "#84a59d"
  neutral: "#2b2b2b"
  tertiary: "#faf8f8"
typography:
  h1:
    fontFamily: Schibsted Grotesk
    fontSize: 2rem
  body-md:
    fontFamily: Source Sans Pro
    fontSize: 1rem
  label-caps:
    fontFamily: IBM Plex Mono
    fontSize: 0.75rem
rounded:
  sm: 4px
  md: 8px
spacing:
  sm: 8px
  md: 16px
---

## Overview

Seoyul Notes is a Quartz 4 digital garden with a calm, editorial identity. The light theme pairs a warm off-white page with deep charcoal text, accented by a muted slate blue for links and a soft sage green for secondary highlights. Type pairs the geometric Schibsted Grotesk for headers with the humanist Source Sans Pro for reading and IBM Plex Mono for code.

## Colors

- `#284b63` — primary / Quartz `secondary` role (links, header accents, interactive elements)
- `#84a59d` — secondary accent / Quartz `tertiary` role (graph nodes, hover states)
- `#2b2b2b` — neutral ink / Quartz `dark` role (body text)
- `#faf8f8` — page background / Quartz `light` role
- `#e5e5e5` — Quartz `lightgray` (borders, code background)
- `#b8b8b8` — Quartz `gray` (muted text, dates)

## Typography

- **Schibsted Grotesk** — headers (`typography.header`), used for h1–h6.
- **Source Sans Pro** — body copy (`typography.body`).
- **IBM Plex Mono** — code blocks and inline code (`typography.code`); also fits caps/label usage.

All fonts are served from Google Fonts (`fontOrigin: "googleFonts"`).
