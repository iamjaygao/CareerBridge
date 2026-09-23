# VoiceOver Walkthrough — CareerBridge Public Flows

Manual screen-reader pass covering what Lighthouse cannot score. Lighthouse's
accessibility category leaves ~10 audits as "manual" (`focus-traps`,
`logical-tab-order`, `focusable-controls`, `interactive-element-affordance`)
and marks ~50 more "not applicable". This checklist covers that gap.

**Scope:** public routes only. Authenticated pages need the Docker stack and
are out of scope for this pass — say so when you report results.

---

## Setup

```bash
cd frontend
CI=false npm run build
npx serve -s build -l 3000
```

Open `http://localhost:3000` in Safari (VoiceOver's best-supported browser).

| Key | Action |
|---|---|
| `Cmd + F5` | Toggle VoiceOver on/off |
| `VO` | = `Control + Option` (the VoiceOver modifier) |
| `VO + U` | Open the rotor, then `←/→` to switch list type |
| `VO + →` / `VO + ←` | Next / previous element |
| `VO + Space` | Activate the focused element |
| `VO + Cmd + H` | Jump to next heading |
| `Tab` | Next focusable control |
| `Control` | Pause speech (use this constantly) |

---

## Test 1 — Landing page landmarks and skip link (`/`)

| # | Step | Expected | Pass? |
|---|---|---|---|
| 1.1 | Load `/`, press `Tab` once | First stop is **"Skip to main content, link"**, and it becomes visually visible at top-left | ☐ |
| 1.2 | Press `Return` on it | Focus moves into `<main>`; next `Tab` lands on a control *inside* page content, not back in the nav | ☐ |
| 1.3 | `VO + U` → rotor → **Landmarks** | Lists exactly: banner/header, navigation, main, contentinfo/footer | ☐ |
| 1.4 | `VO + U` → rotor → **Headings** | Starts with one `h1` "Know your next role…", then h2/h3 only — **no jumps** (no h1→h6) | ☐ |
| 1.5 | `VO + Cmd + H` repeatedly to the end | Every heading read is real section content — the stat numbers ("50k+") and testimonial names ("Sarah Chen") are **not** announced as headings | ☐ |

> 1.4 and 1.5 are the items we fixed. 1.5 is the regression check: those used to
> be `<h6>`/`<h4>` and are now `<p>`.

---

## Test 2 — Login form (`/login`)

Validation is client-side (yup + react-hook-form), so this works with no backend.

| # | Step | Expected | Pass? |
|---|---|---|---|
| 2.1 | Load `/login` | Focus lands on the "Username or Email" field and VoiceOver announces its label | ☐ |
| 2.2 | `VO + U` → rotor → **Form Controls** | Both fields announce a name — never "edit text" with no label | ☐ |
| 2.3 | Submit empty via `Return` | Error text is **announced**, not silently rendered. Listen for "Username or email is required" | ☐ |
| 2.4 | `Tab` to the password field | Announced as "secure edit text" / password | ☐ |
| 2.5 | `Tab` past the button | Reaches "Don't have an account? Sign Up, link" | ☐ |

> **2.3 is the one most likely to fail.** MUI's `helperText` renders as plain
> text linked via `aria-describedby`; whether VoiceOver announces it on submit
> depends on focus position. If it stays silent, that is a real finding — note
> it. The fix would be a live region, which we have not implemented.

---

## Test 3 — Register form (`/register`)

Seven fields including a MUI `Select`, which is the usual weak spot.

| # | Step | Expected | Pass? |
|---|---|---|---|
| 3.1 | `Tab` through all fields in order | Tab order matches visual order top-to-bottom | ☐ |
| 3.2 | Reach the **Role** Select | Announced with a name and current value, as a popup/combobox | ☐ |
| 3.3 | `VO + Space` to open it, arrow through | Each option is announced; `Esc` closes and returns focus to the trigger | ☐ |
| 3.4 | Submit with a short password | Validation error is reachable and readable | ☐ |

---

## Test 4 — Header navigation, desktop and mobile

| # | Step | Expected | Pass? |
|---|---|---|---|
| 4.1 | On `/`, rotor → **Landmarks** → navigation | Enters the header nav; links are announced individually | ☐ |
| 4.2 | Narrow the window below ~900px | Hamburger button is announced with a name, not "button" alone | ☐ |
| 4.3 | Activate the hamburger | Focus moves **into** the drawer; `Tab` cycles inside it and does not escape behind the overlay | ☐ |
| 4.4 | Press `Esc` | Drawer closes and focus returns to the hamburger button | ☐ |

> 4.2 is a likely failure: audit found only 2 `aria-label`s on IconButtons
> across the whole app. If it announces bare "button", record it.

---

## Test 5 — Error / empty state (`/mentors`)

With no backend the API call fails. This tests whether failure is perceivable.

| # | Step | Expected | Pass? |
|---|---|---|---|
| 5.1 | Load `/mentors` | Loading state is announced or at least reachable | ☐ |
| 5.2 | Wait for the request to fail | The error/empty state is **reachable by VoiceOver**, not a purely visual placeholder | ☐ |

---

## Recording results

For each ☐ that fails, write down: route, step number, what VoiceOver actually
said, and what it should have said. A failure found here is worth more than a
clean sheet — it is the evidence that you tested beyond the automated tooling.

### Summary to fill in

```
Date:
Browser / OS:
Routes covered:  / , /login , /register , /mentors
Passed:   __ / 19
Findings: 
  1.
  2.
```

### What this does and does not license you to claim

| ✅ Can say | ❌ Cannot say |
|---|---|
| "Screen-reader tested (VoiceOver) on public flows" | "WCAG 2.1 AA compliant" |
| "Verified landmark, heading, and focus behaviour manually" | "Fully accessible" / "site-wide" |
| Specific findings and fixes | Anything about authenticated pages |
