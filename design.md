This design system relies on a **"Soft-Tech Editorial"** aesthetic. It blends the density of a developer tool with the softness of a modern editorial reading experience. The core philosophy is **low-contrast containment**, where distinct functional areas are separated by whitespace and subtle color shifts rather than hard borders.

### 1. Color Palette
The palette is heavily desaturated, avoiding pure blacks or stark whites to reduce eye strain.

* **Canvas (Global Background):** A pale, organic greige or desaturated sage. It should feel like recycled paper or stone.
    * *Approx:* `#E8ECE6` or `#F0F2EF`
* **Surface (Active Areas):** High-brightness off-white. Used for the main editor and floating panels to create a sense of "elevation" without heavy shadows.
    * *Approx:* `#FFFFFF` or `#FAFAFA`
* **Ink (Primary Text):** Deep charcoal/slate. Never pure black (`#000`).
    * *Approx:* `#333333` or `#2D3035`
* **Accents:**
    * *Semantic Green:* A soft matcha or pastel green for active states and tags.
    * *Highlight Clay:* A muted terracotta/orange for text diffs or attention.
* **UI Elements:** Light cool greys for unselected icons and button backgrounds.

### 2. Typography
The system uses a distinct pairing to separate "Interface" from "Content."

* **Interface (Nav, Buttons, Headers):** A geometric, highly legible Sans-Serif (e.g., *Inter*, *Geist*, or *Graphik*). Weights should be bold for headers, medium for controls.
* **Editor (Main Content):** A clean Monospace font (e.g., *JetBrains Mono*, *Roboto Mono*, or *SF Mono*). This signals to the user that the center column is for technical drafting or code.

### 3. Geometry & Shape (The "Squircle")
* **Border Radius:** Aggressive rounding.
    * **Containers/Cards:** Large radii (approx `16px` to `24px`).
    * **Buttons/Tags:** Pill-shaped (fully rounded caps, `999px`).
* **Borders:** Almost non-existent. Separation is achieved through color (White card on Sage background).
    * *Exception:* Very subtle, light grey borders may be used on internal grouping elements if needed.

### 4. Layout Architecture
The layout uses a **Floating Panel** approach rather than an edge-to-edge dashboard.

* **The "Island" Header:** The top navigation bar is not attached to the top of the browser window. It floats as a pill-shaped container with margin on all sides.
* **Three-Column Flow:**
    1.  **Macro View (Left):** Narrower width. Used for high-level structure or outlines.
    2.  **Focus View (Center):** Wide, paper-like aspect ratio. This is the primary workspace.
    3.  **Context View (Right):** Medium width. Used for metadata, tools, or contextual attributes.
* **Margins:** Generous distinct padding between the browser edge and the internal cards (`~24px`). The background color frames the entire UI.

### 5. Component Styling

**Buttons & Controls**
* **Ghost Buttons:** Most controls have no background, relying on hover states or slight grey fills (`#F3F4F6`) when active.
* **Iconography:** Simple, stroke-based icons (1.5px stroke width). Dark grey color.

**Data Chips / Tags**
* Located in the right column.
* **Structure:** Block-level elements with rounded corners.
* **Visuals:** Pastel background fills (matcha green, soft grey) with dark, legible text. No borders on tags.

**Skeleton / Abstract Representations**
* (Seen in the left column)
* Instead of dense text, use horizontal rounded bars (grey strips) to represent lines of text in a preview or outline mode. This reduces visual noise for secondary information.

### 6. Depth & Elevation
* **Shadows:** Extremely subtle or non-existent. The contrast between the "Sage" background and "White" cards does the heavy lifting.
* If shadows are used, they should be large, diffuse, and very low opacity (e.g., `0 10px 40px rgba(0,0,0,0.04)`).

### Implementation Note (CSS Hints)
To achieve this look, focus on:
* `gap: 16px` or `24px` in your flex/grid containers.
* `background-color: var(--sage-surface)` on the body.
* `box-shadow: none` for a flatter look, or `backdrop-filter: blur()` if you make the header slightly translucent.
* `letter-spacing: -0.02em` on sans-serif headings for that tight, modern feel.