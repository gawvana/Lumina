---
name: lucide-icons
description: Official guide and comprehensive reference for Lucide Icons across Vanilla HTML/JS, React, Vue, Svelte, and Tailwind CSS. Includes icon naming conventions, accessibility rules (ARIA), sizing, styling, animation, and catalog lookup. Use whenever adding, replacing, or configuring icons in the UI.
---

# Lucide Icons Design & Implementation Guide

[Lucide](https://lucide.dev) is the modern standard vector icon toolkit (fork of Feather Icons) providing 1,600+ clean, consistent, customizable SVG icons designed on a 24×24 grid with 2px default stroke.

## 1. Quickstart & Integration by Stack

### A. Vanilla HTML + JavaScript (No Build Step)
Include the production CDN script before the closing `</body>` tag or in the `<head>`:

```html
<!-- Include CDN -->
<script src="https://unpkg.com/lucide@latest"></script>

<!-- Add icon placeholders using data-lucide attribute (kebab-case) -->
<button class="btn" aria-label="Search">
  <i data-lucide="search"></i>
  <span>Search</span>
</button>

<script>
  // Replace all [data-lucide] placeholders with inline SVG
  lucide.createIcons();
</script>
```

> **Crucial Rule for Dynamic DOM**: Whenever new DOM elements with `data-lucide` are added dynamically (e.g. via `innerHTML`, templates, modals, tabs, or AJAX), you **must** call `lucide.createIcons()` again to render the newly inserted icons!

### B. React / Next.js
Install:
```bash
npm install lucide-react
```

Usage (PascalCase):
```tsx
import { ArrowRight, CheckCircle2, Loader2, Sparkles } from 'lucide-react';

export function CallToAction() {
  return (
    <button className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
      <Sparkles className="w-4 h-4 text-yellow-300" />
      <span>Get Started</span>
      <ArrowRight className="w-4 h-4" strokeWidth={2} />
    </button>
  );
}
```

### C. Vue 3 / Nuxt
Install:
```bash
npm install lucide-vue-next
```

Usage:
```vue
<script setup>
import { ArrowRight, CheckCircle2 } from 'lucide-vue-next';
</script>

<template>
  <button class="btn">
    <span>Continue</span>
    <ArrowRight :size="18" :stroke-width="2" />
  </button>
</template>
```

### D. Direct SVG Embedding (Zero External Runtime)
Every Lucide icon can be rendered as pure inline SVG with:
- `viewBox="0 0 24 24"`
- `fill="none"`
- `stroke="currentColor"`
- `stroke-width="2"` (or 1.75)
- `stroke-linecap="round"`
- `stroke-linejoin="round"`

---

## 2. Icon Naming & Verification (Avoid Hallucinations)

Lucide uses:
- **Kebab-case** for HTML data attributes and filenames: `arrow-right`, `check-circle-2`, `trash-2`, `loader-2`
- **PascalCase** for React/Vue/Svelte components: `ArrowRight`, `CheckCircle2`, `Trash2`, `Loader2`

### Common Pitfalls & Replacements
- **DO NOT** use FontAwesome prefixes (`fa-`, `fas fa-star`).
- **DO NOT** use Material Icons naming (`chat_bubble`, `arrow_forward`).
- **DO NOT** guess unverified icon names:
  - Wrong: `chat-bubble`, `chat` -> **Correct**: `message-square` or `message-circle`
  - Wrong: `cross`, `close` -> **Correct**: `x`
  - Wrong: `bin`, `delete` -> **Correct**: `trash-2` or `trash`
  - Wrong: `spinner` -> **Correct**: `loader-2` or `refresh-cw`
  - Wrong: `magnifier` -> **Correct**: `search`
  - Wrong: `gear`, `cog` -> **Correct**: `settings`
  - Wrong: `exit` -> **Correct**: `log-out`
  - Wrong: `enter` -> **Correct**: `log-in`
  - Wrong: `warning` -> **Correct**: `alert-triangle`
  - Wrong: `error` -> **Correct**: `alert-circle`
  - Wrong: `success` -> **Correct**: `check-circle-2`

---

## 3. Canonical Icon Catalog (Most Used)

### Navigation & Layout
- `menu`, `x` (drawers, modals, mobile nav)
- `chevron-left`, `chevron-right`, `chevron-up`, `chevron-down` (collapsibles, dropdowns)
- `arrow-left`, `arrow-right`, `arrow-up`, `arrow-down` (directional buttons, pagination)
- `arrow-up-right` (external links, growth metrics)
- `home`, `compass`, `map-pin`, `globe`
- `sidebar`, `panel-left`, `panel-right`, `grid`, `layout`

### Core Actions & CRUD
- `plus`, `minus` (add, subtract)
- `trash-2` (delete / destructive action)
- `edit`, `edit-2`, `edit-3` (modify content)
- `check` (confirm, tick)
- `copy` (clipboard)
- `share-2` (share)
- `download`, `upload` (file transfer)
- `filter`, `sliders`, `arrow-up-down` (sorting & filtering)
- `refresh-cw`, `rotate-cw` (reload / sync)
- `external-link` (open new tab)

### Status & Feedback
- `check-circle-2` (success, verified)
- `alert-circle` (error, failed)
- `alert-triangle` (warning, caution)
- `info` (information, tooltip)
- `help-circle` (help, FAQ)
- `loader-2` (loading spinner, processing)
- `clock` (pending, scheduled)

### UI & Controls
- `settings` (configuration, preferences)
- `search` (search input bar)
- `bell`, `bell-off` (notifications)
- `user`, `users`, `user-plus`, `user-check` (accounts & team)
- `log-in`, `log-out` (authentication)
- `eye`, `eye-off` (password reveal)
- `lock`, `unlock`, `shield`, `key` (security)
- `moon`, `sun` (dark/light mode toggle)
- `calendar`, `clock`, `bookmark`, `heart`, `star`

### Communication & Media
- `mail`, `send`, `message-square`, `message-circle`, `phone`
- `image`, `video`, `camera`, `mic`, `mic-off`
- `volume-2`, `volume-x`, `play`, `pause`
- `file`, `file-text`, `folder`, `paperclip`

### E-Commerce & SaaS
- `shopping-cart`, `shopping-bag`
- `credit-card`, `dollar-sign`, `wallet`, `receipt`
- `sparkles` (AI, magic, premium features)
- `zap` (speed, instant, automated)
- `trending-up`, `trending-down`, `bar-chart-3`, `pie-chart`, `activity` (metrics)

---

## 4. Accessibility (a11y) Golden Rules

1. **Decorative Icons (Beside text)**:
   Must be hidden from screen readers to prevent reading duplicate information:
   ```html
   <!-- Vanilla HTML -->
   <button class="btn">
     <i data-lucide="download" aria-hidden="true"></i>
     <span>Download Report</span>
   </button>

   <!-- React -->
   <button className="btn">
     <Download aria-hidden="true" className="w-4 h-4" />
     <span>Download Report</span>
   </button>
   ```

2. **Standalone Icon Buttons (No visible label)**:
   Must provide an accessible name via `aria-label`:
   ```html
   <!-- Vanilla HTML -->
   <button type="button" class="icon-btn" aria-label="Close dialog">
     <i data-lucide="x" aria-hidden="true"></i>
   </button>

   <!-- React -->
   <button type="button" className="icon-btn" aria-label="Close dialog">
     <X aria-hidden="true" className="w-4 h-4" />
   </button>
   ```

3. **Status Indicators**:
   Provide accessible screen-reader-only text alongside visual icons:
   ```html
   <span class="status-badge">
     <i data-lucide="check-circle-2" aria-hidden="true"></i>
     <span class="sr-only">Status: Completed</span>
   </span>
   ```

---

## 5. Sizing & Styling Standards

| Size Variant | Pixel Size | Tailwind Classes | Recommended Stroke | Best Used For |
|---|---|---|---|---|
| **Micro / Badge** | 14px | `w-3.5 h-3.5` | `strokeWidth={2}` | Inline badges, pills, small tags |
| **Small / Inline** | 16px | `w-4 h-4` | `strokeWidth={2}` | Inside buttons, dropdown menu items |
| **Medium / Base** | 20px | `w-5 h-5` | `strokeWidth={1.75}` or `2` | Input field adornments, nav links |
| **Standard** | 24px | `w-6 h-6` | `strokeWidth={1.75}` | Page headers, cards, feature icons |
| **Hero / Feature** | 32px–48px | `w-8 h-8` to `w-12 h-12` | `strokeWidth={1.5}` | Empty states, feature blocks |

### Spinner Animation
Always use `loader-2` with spinning animation for pending/loading states:
```html
<!-- Vanilla CSS -->
<i data-lucide="loader-2" class="spin-icon" aria-hidden="true"></i>
<style>
  .spin-icon {
    animation: spin 1s linear infinite;
  }
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>

<!-- Tailwind CSS -->
<Loader2 className="w-5 h-5 animate-spin text-indigo-500" aria-hidden="true" />
```
