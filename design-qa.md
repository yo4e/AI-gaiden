# AI外電 Issue #32 Design QA

## Comparison target

- Source visual truth: `/Users/yo4e/GitHub/AI-gaiden/ChatGPT Image 2026年8月4日 10_39_05.png` and `/Users/yo4e/GitHub/AI-gaiden/ai-gaiden-product-design-policy.png`
- Policy priority: `/Users/yo4e/GitHub/AI-gaiden/DESIGN_POLICY.md`
- Implementation: local Astro preview at `http://127.0.0.1:4173/`
- Primary route: `/`
- State: static home page with the current repository article data; no interaction state or external link navigation

## Captures

- Desktop viewport: `/Users/yo4e/.codex/visualizations/2026/08/05/019fd1ce-1db6-71d1-9f6c-a034f6ecc767/design-qa-home-desktop-viewport.png` — 1440 × 1000 CSS px, device scale factor 1
- Tablet viewport: `/Users/yo4e/.codex/visualizations/2026/08/05/019fd1ce-1db6-71d1-9f6c-a034f6ecc767/design-qa-home-tablet.png` — 768 × 1000 CSS px, device scale factor 1
- Mobile viewport: `/Users/yo4e/.codex/visualizations/2026/08/05/019fd1ce-1db6-71d1-9f6c-a034f6ecc767/design-qa-home-mobile.png` — 390 × 844 CSS px, device scale factor 1
- Focused latest-card region: `/Users/yo4e/.codex/visualizations/2026/08/05/019fd1ce-1db6-71d1-9f6c-a034f6ecc767/design-qa-home-lower.png`
- Focused policy/footer region: `/Users/yo4e/.codex/visualizations/2026/08/05/019fd1ce-1db6-71d1-9f6c-a034f6ecc767/design-qa-home-archive.png`

The source images are long concept boards rather than fixed viewport screenshots. Comparison used the same visible content regions—header, split hero, article card, archive/policy/footer—and treated the written policy as authoritative where the images showed unimplemented search, column, or decorative artwork.

## Findings

- No actionable P0/P1/P2 visual findings remain.
- Typography: system Japanese sans-serif is used consistently; the H1, metadata, body, and navigation hierarchy is clear at desktop, tablet, mobile, and narrow viewport widths.
- Spacing/layout: the desktop hero is split into copy and information-panel columns; the tablet and mobile layouts stack naturally. Article cards keep a stable two-column structure on desktop and become one column on mobile.
- Colors/tokens: the implementation is light-first with white, pale gray/blue-gray, dark ink, and one muted blue accent. Shared line, surface, focus, and radius values are centralized in `theme.css`; gradients and shadows are absent.
- Image fidelity: no new heavy visual asset was introduced. The hero uses a lightweight semantic information panel as required by the policy, and article imagery continues to use the existing RSS/default-image policy.
- Copy/content: internal article links and external official links are visibly distinct. The required `試験運用中` notice appears once in the shared layout on every checked route.
- Accessibility: semantic landmarks and heading levels are present, the skip link receives a visible 3px focus outline when keyboard-focused, no horizontal overflow was observed at 1440, 768, or 390px, and `prefers-reduced-motion` is respected.

## Route and console checks

Checked `/`, a daily digest, an individual article, `/archive/`, `/sources/`, a source detail page, `/about/`, `/editorial-policy/`, `/privacy/`, and a 404 route. Each rendered one trial banner, one main landmark, a page-specific H1/title/canonical, and the expected preview/index robots state. Browser console warnings and errors were empty.

## Comparison history

1. The first full-page browser capture was discarded because the in-app browser's full-page capture duplicated the page; it was not used as evidence.
2. Re-captured valid viewport and focused-region screenshots at 1440px, 768px, and 390px. The split hero, card hierarchy, responsive stacking, policy callout, principles row, and footer were visually verified against the concept boards and policy.

## Open implementation note

The current repository has seven real daily digest dates. The homepage caps the list at eight without inventing empty daily pages or fake content; a future eighth real digest will occupy the eighth grid slot automatically. This is a content-availability note, not a visual QA failure.

## Implementation Checklist

- [x] Light theme and shared design tokens
- [x] Shared header, footer, and trial-operation banner
- [x] Split hero and lightweight information panel
- [x] Two-column latest article cards and distinct official links
- [x] Eight-edition cap with a fixed desktop two-column grid and mobile one-column fallback
- [x] Responsive, focus-visible, semantic, reduced-motion-aware layout
- [x] Local preview, route, console, and viewport checks

final result: passed
