---
name: frontend-design
description: >
  Use this skill when building any web UI, frontend component, or HTML/CSS
  output — especially when it needs to look polished and professional rather
  than plain. Covers design principles, color, typography, layout, spacing, and
  component patterns. Trigger whenever the user asks for a webpage, dashboard,
  form, UI component, or says something looks bad and needs improvement.
---

# Frontend Design Skill

Use this skill to produce clean, modern, professional-looking UIs.
Follow these principles before writing any HTML/CSS.

---

## Core Principles

1. **Whitespace is not wasted** — generous padding and margins make UIs feel premium
2. **Consistency beats cleverness** — pick a spacing scale and stick to it
3. **Typography carries hierarchy** — size + weight differences do more than color
4. **One accent color** — use it sparingly for CTAs and highlights only
5. **Never use pure black** — use `#1a1a2e` or `#111827` for text instead

---

## Spacing Scale

Use multiples of 4px:

| Token | Value |
|---|---|
| xs | 4px |
| sm | 8px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| 2xl | 48px |
| 3xl | 64px |

---

## Typography Scale

```css
/* Base */
body { font-family: 'Inter', system-ui, sans-serif; font-size: 16px; line-height: 1.6; }

/* Scale */
.text-xs   { font-size: 12px; }
.text-sm   { font-size: 14px; }
.text-base { font-size: 16px; }
.text-lg   { font-size: 18px; }
.text-xl   { font-size: 20px; }
.text-2xl  { font-size: 24px; }
.text-3xl  { font-size: 30px; }
.text-4xl  { font-size: 36px; }
```

Use **font-weight 600–700** for headings, **400** for body, **500** for labels.

---

## Color Palette Starter

```css
:root {
  /* Neutrals */
  --color-bg:        #f9fafb;
  --color-surface:   #ffffff;
  --color-border:    #e5e7eb;
  --color-text:      #111827;
  --color-muted:     #6b7280;

  /* Accent (blue — swap freely) */
  --color-accent:    #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-light: #eff6ff;

  /* Status */
  --color-success:   #16a34a;
  --color-warning:   #d97706;
  --color-error:     #dc2626;
}
```

---

## Card Component

```html
<div style="
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
">
  Content here
</div>
```

---

## Button Styles

```css
/* Primary */
.btn-primary {
  background: #2563eb;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  border: none;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-primary:hover { background: #1d4ed8; }

/* Secondary */
.btn-secondary {
  background: white;
  color: #374151;
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
}
.btn-secondary:hover { background: #f9fafb; }
```

---

## Form Inputs

```css
input, select, textarea {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  background: white;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}
```

---

## Layout Patterns

### Centered Page
```css
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}
```

### Sidebar + Content
```css
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  min-height: 100vh;
}
```

### Card Grid
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
```

---

## Shadows

```css
--shadow-sm:  0 1px 2px rgba(0,0,0,0.05);
--shadow-md:  0 4px 6px rgba(0,0,0,0.07);
--shadow-lg:  0 10px 15px rgba(0,0,0,0.1);
--shadow-xl:  0 20px 25px rgba(0,0,0,0.1);
```

Use `shadow-sm` for cards, `shadow-md` for dropdowns, `shadow-lg` for modals.

---

## Common Mistakes to Avoid

- ❌ `color: black` → ✅ `color: #111827`
- ❌ `border-radius: 3px` → ✅ `border-radius: 8px` or `12px`
- ❌ No focus states → ✅ Always style `:focus`
- ❌ Centered everything → ✅ Left-align body text, center only headings/CTAs
- ❌ Too many font sizes → ✅ Stick to 3–4 sizes max
- ❌ Long lines of text → ✅ `max-width: 65ch` on paragraphs

---

## Responsive Breakpoints

```css
/* Mobile first */
@media (min-width: 640px)  { /* sm */ }
@media (min-width: 768px)  { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```
