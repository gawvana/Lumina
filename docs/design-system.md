# Lumina Mini App Design System Specification

## 1. Overview & Philosophy
Lumina's visual and interactive design adheres to **Telegram-Native + Apple-Level Restraint + Premium Education Product** aesthetics. The interface avoids visual clutter, gratuitous glassmorphism, or neon gradients, favoring clarity, scannability, purposeful micro-interactions, and accessible touch ergonomics.

---

## 2. Color System & Semantic Tokens

### Light Theme (Default)
| Token | Value | Purpose |
|---|---|---|
| `--bg-primary` | `#f8fafc` | View background canvas |
| `--bg-surface` | `#ffffff` | Elevated surfaces and containers |
| `--bg-card` | `rgba(255, 255, 255, 0.85)` | Blur card backdrop with border |
| `--bg-subtle` | `#f1f5f9` | Inset backgrounds, grouped controls |
| `--text-primary` | `#0f172a` | Headers, primary data figures |
| `--text-secondary` | `#475569` | Body labels, subtext |
| `--text-muted` | `#94a3b8` | Captions, metadata, inactive icons |
| `--color-primary` | `#0d9488` | Teal primary brand action color |
| `--color-accent` | `#d97706` | Amber attention / urgent deadline color |
| `--color-success` | `#10b981` | Emerald positive states, completed tasks |
| `--color-warning` | `#f59e0b` | Late attendance, warning badges |
| `--color-danger` | `#ef4444` | Absenteeism, failing scores, errors |
| `--color-info` | `#3b82f6` | Info highlights, announcements |
| `--border-color` | `#e2e8f0` | Subtle hairline dividers |

### Dark Theme (`body.dark-mode`)
Automatically synchronized with `Telegram.WebApp.colorScheme` or manually toggled:
| Token | Value | Purpose |
|---|---|---|
| `--bg-primary` | `#090d16` | Deep slate canvas |
| `--bg-surface` | `#0f172a` | Elevated surface |
| `--bg-card` | `rgba(30, 41, 59, 0.7)` | Translucent dark card |
| `--bg-subtle` | `#1e293b` | Form input backgrounds |
| `--text-primary` | `#f8fafc` | Crisp high-contrast text |
| `--text-secondary` | `#cbd5e1` | Secondary descriptions |
| `--text-muted` | `#64748b` | Muted metadata |
| `--color-primary` | `#14b8a6` | Luminescent teal |
| `--border-color` | `rgba(255, 255, 255, 0.08)` | Low-contrast borders |

---

## 3. Typography Scale
Font Family: `'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

| Role | Size | Weight | Line Height | Usage |
|---|---|---|---|---|
| **Display / Hero Name** | 20px | 800 | 1.2 | Student/Teacher greeting titles |
| **Section Title** | 18px | 700 | 1.3 | View headers, major sections |
| **Card Title** | 15px | 700 | 1.4 | Card headers, class names |
| **Body Primary** | 14px | 500 / 600 | 1.5 | General content, homework titles |
| **Subtext / Meta** | 12px | 500 | 1.4 | Timestamps, classroom numbers |
| **Micro Caption** | 10px / 11px | 600 / 700 | 1.2 | Navigation labels, uppercase tags |

---

## 4. Components

### A. Bottom Navigation (`.bottom-nav`)
- Dynamic 4-role context switching:
  - **Student**: Home, Grades, Homework, Schedule, Profile
  - **Teacher**: Dashboard, Journal, Homework, Profile
  - **Parent**: Overview, Grades, Attendance, Homework, Schedule, Profile
  - **Admin**: School Overview, Settings
- Pinned to bottom with safe-area padding: `calc(64px + env(safe-area-inset-bottom, 0px))`.
- Minimum tap target: 44px height per item with haptic feedback on selection.

### B. Cards & Metric Hero (`.hero-card`, `.card`)
- Hero cards use high-contrast brand gradients (`#0d9488` to `#0284c7`) with 3-metric statistics grid.
- Standard cards feature subtle hairline borders (`1px solid var(--border-color)`) and 14px border radius.

### C. Grade Pills (`.grade-pill`)
- Scale-aware circular badge indicators:
  - Grade 5: Emerald (`--color-success`)
  - Grade 4: Blue (`--color-info`)
  - Grade 3: Amber (`--color-warning`)
  - Grade 2: Red (`--color-danger`)

### D. Interactive Homework Checklist (`.hw-item`, `.hw-checkbox`)
- Toggleable checkbox with tactile feedback (`triggerHaptic('impact', 'light')`).
- Visual strike-through and 60% opacity reduction upon completion.

### E. Reusable Bottom Sheet Modals (`.modal-backdrop`, `.modal-content`)
- Slides smoothly up from the viewport bottom with backdrop blur.
- Handles dismissal via backdrop click or Escape key.

---

## 5. Security & Accessibility Standards
1. **XSS Prevention**: All user-supplied and database-persisted text strings are sanitized via `escapeHtml()` before rendering to the DOM.
2. **Touch Targets**: All buttons, nav items, and checkboxes enforce `min-height: 44px` and `min-width: 44px` per WCAG guidelines.
3. **Safe Areas**: Top headers respect `env(safe-area-inset-top)` and bottom navigation respects `env(safe-area-inset-bottom)`.
4. **Iconography**: Standardized on pinned Lucide Icons (`v0.469.0`) with decorative ARIA hiding (`aria-hidden="true"`).
