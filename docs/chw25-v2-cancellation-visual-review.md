# CHW25 V2 — Cancellation Visual Review

> Review target: `desktop_workbench_v2` Checkpoint 2 screenshots  
> Status: **direction approved, checkpoint not yet passed**  
> Scope: one focused refinement only; do not start Encrypt / Y2 / Threshold / Media yet.

---

## 0. Verdict

The scene is now genuinely more visual than V1: the two shared terms are recognizable by shape, cancellation is a direct interaction, and the final `z` is backed by the real backend. This is the correct product direction.

However, the scene is not yet presentation-ready. The remaining problem is no longer “too much text”; it is **visual hierarchy and algebraic staging**.

The main issues are:

1. the source band stays visible for the entire sequence and competes with the active proof;
2. expanded terms float too far apart, weakening the idea that they are aligned components of two expressions;
3. the global subtraction `L - R` is visually ambiguous, especially during the sign flip of `e1`;
4. selected/cancelled terms still look too much like UI widgets;
5. the residual and final-z stages are too low and too sparse;
6. the final frame does not sufficiently clear the previous proof state, so `z` does not become the hero object.

The next pass should refine these points without changing the backend or interaction model.

---

# 1. Keep unchanged

The following decisions are approved and must remain:

- light research-infographic theme;
- `ContributionCapsule` source explanation;
- typed visual glyphs instead of generic `TermItem`;
- public-dot / matrix-chain structural matching;
- user selects one term on each side;
- wrong match = local feedback only;
- `Form z` calls the real `DemoEngine.compute_z_now()`;
- no invented numerical values for the proof-only common terms;
- formula and implementation remain optional drill-down layers;
- `z_centered` comes from the actual backend / trace;
- `hide_term_formula_labels` debug criterion.

No cryptographic refactor is needed.

---

# 2. Source band: collapse after expansion

## Current issue

The top band (`c3`, `c2`, `r2`, `c1`, `Y2`) remains fully visible through cancellation, residual formation, and the final `z` frame.

This makes the screen feel like two unrelated diagrams stacked vertically. It also consumes approximately the upper third of the canvas after its explanatory job is finished.

## Required behavior

### Collapsed state

Keep the source band large and clear:

```text
c3 + c2 × r2  ->  L       L - R       R  <-  c1 × Y2
```

This is the correct opening explanation.

### After `Expand both`

The source objects should animate into a **breadcrumb band**:

- scale to ~55–65% of current size;
- opacity 0.20–0.30;
- move upward closer to the subtitle/header;
- `L` and `R` source capsules disappear after expansion;
- keep only a faint source memory, not an active diagram.

The cancellation ledger then owns the visual center.

### Residual / final-z stages

Fade the source breadcrumb further to ~10–15% or hide it entirely.

The final `z` frame must not compete with large `c1/c2/c3` blocks.

---

# 3. Rebuild the expanded ledger as aligned columns

## Current issue

The four semantic terms are spread across too much horizontal space. Although the two matching shapes are identical, they feel like independent floating icons rather than corresponding components of two algebraic expressions.

## Required layout

Use a compact two-row ledger with four aligned semantic columns:

```text
                 MESSAGE        PUBLIC DOT        MATRIX CHAIN        NOISE

L                  [M]             [P]                [C]              [N2]

R                                   [P]                [C]              [N1]
```

Column headings should be very subtle and may be omitted in classroom mode if the shapes are clear. If used, headings must be small muted labels, not cards.

### Geometry

At 1440×900 reference size:

- ledger central width: ~930–1000 px;
- row gap: ~120–135 px;
- each semantic glyph gets a consistent visual footprint;
- `MessageHalfGlyph` should not be more than ~1.25× the visual area of `PublicDotGlyph` / `MatrixChainGlyph`;
- increase `NoiseGlyph` visual mass slightly (particle spread ~70–90 px) so it is not visually negligible.

The user should immediately see “same column = candidate for cancellation”.

---

# 4. Clarify `L - R`

## Current issue

The standalone red minus at the far left of the R row reads like a unary minus attached to an arbitrary row item. Later, after `e1` becomes `-e1`, the old global minus still remains visible, causing duplicated subtraction semantics.

## Required model

Represent subtraction as an **operator applied to the entire R row**, not as a loose symbol.

Preferred visual:

```text
L row
────────────────────────────────────────────

             z = L  −  R

R row  [subtraction bracket / red left rail]
────────────────────────────────────────────
```

Alternative accepted implementation:

- a thin coral/red vertical rail or brace along the left edge of the R row;
- a small `− R` marker attached to that rail;
- the rail visually means “the whole row is subtracted”.

### Sign-flip animation

When both shared terms are cancelled:

1. keep `e1` in the R noise column;
2. animate the subtraction rail/`− R` marker toward `e1`;
3. merge the operator into the noise glyph;
4. `e1` becomes `−e1`;
5. **the global subtraction rail/marker disappears completely**.

After the sign flip there must be only one minus meaning on screen: the `−e1` residual.

---

# 5. Selection and cancellation should look mathematical, not destructive UI

## Current issue

The selected pair is surrounded by dashed rectangular focus boxes and the contextual button is a strong red `Cancel pair`. This resembles a delete action in a desktop application.

## Required visual behavior

### Selection

Replace generic dashed rectangles with semantic emphasis around the glyph itself:

- 2–3 px soft outline / halo following the glyph bounding silhouette;
- small lift (`y - 4 px`);
- matching pair connection is a thin line/curve using the term's own semantic color.

Do not introduce a new generic card around the term.

### Context action

`Cancel pair` is not an error/destructive operation. Use a neutral/semantic action style:

- white / very light fill;
- border in the matched term color;
- matched-term-colored text;
- only on hover may the fill strengthen slightly.

Do not use warning red for the button.

### Successful cancellation

Sequence:

```text
match -> lift -> connect -> converge 15–25 px -> diagonal strike -> fade -> reflow
```

The two tokens should be fully removed after the animation.

A completed screenshot must never show a half-faded shared term as if it were still part of the equation.

---

# 6. Stable screenshots after each cancellation

The current `cxl_04` / `cxl_05` frames capture transitional remnants. For presentation review we need **settled states**, not mid-animation states.

After first pair is cancelled:

```text
L: [message]   [empty shared column]   [matrix-chain]   [noise2]
R:             [empty shared column]   [matrix-chain]   [noise1]
```

The ledger may compress the empty column slightly, but it must be obvious that the pair is gone.

After second pair is cancelled:

```text
L: [message]   [noise2]
R:             [noise1]
```

No public-dot or matrix-chain object remains, even faintly.

The next screenshot should then show the subtraction operator migrating into `e1`.

---

# 7. Residual stage must become the visual focus

## Current issue

The residuals are very low and far apart, while the previous source band remains visually strong. The viewer's eye does not immediately read:

```text
μq/2 - e1 + e2
```

## Required residual composition

After sign flip, move the three residual glyphs into a centered horizontal expression:

```text
        [ μq/2 ]      [ −e1 ]      [ +e2 ]

                      Form z
```

- center the expression around x≈720;
- y≈500–560 at 1440×900;
- increase residual glyph scale ~1.15–1.30 compared with ledger state;
- use spatial proximity rather than a long textual formula;
- `Form z` should sit directly beneath the residual trio.

The source breadcrumb should be extremely faint or hidden at this point.

---

# 8. Final z should be a hero state

## Current issue

The current `ZGlyph` is correct, but it sits low while previous source objects remain large above it. The scene does not visually “resolve”.

## Required final state

On `Form z`:

1. residual trio converges toward the center;
2. residuals shrink/fade as they merge;
3. `ZGlyph` expands into the central hero position;
4. all proof ledger artifacts disappear;
5. source breadcrumb fades to <=10% or disappears;
6. the only strong object is `z` with the real centered value.

Suggested settled layout:

```text
                         z
                   ┌──────────┐
                   │ -52362   │
                   └──────────┘

             small muted derivation memory
             μq/2   −e1   +e2
```

The one-line formula `z = μ⌊q/2⌋ − e1 + e2` should be optional or muted secondary text, not equal visual weight to z.

This final `ZGlyph` position should be chosen so that the next Threshold scene can transform the **same object** into the number-line marker without a slide cut.

---

# 9. Caption behavior

The no-label debug screenshot demonstrates that the semantic shapes are working. Keep that success.

For classroom mode:

- captions such as `sᵀp` and `sᵀ(W0+W_S)r2` may appear during the first 1–2 seconds after expansion;
- then reduce opacity to ~45–60%;
- on hover/click, restore full opacity;
- formulas must never be required to locate matching terms.

This gives the lecturer names to reference without making text the primary visual layer.

---

# 10. Defer these global issues

Do not fix these in this refinement unless trivial:

- bottom `Build W_S / Cancellation` navigation style;
- global typography polish;
- exact header spacing;
- full responsive layout.

These should be handled after all core scenes exist.

---

# 11. Acceptance screenshots for the refinement

Produce exactly these settled screenshots:

```text
cxlr_01_collapsed.png
cxlr_02_compact_ledger.png
cxlr_03_pair_selected.png
cxlr_04_after_first_cancel.png
cxlr_05_after_second_cancel.png
cxlr_06_sign_flip.png
cxlr_07_residual_centered.png
cxlr_08_z_hero.png
cxlr_debug_no_labels.png
```

Important:

- screenshots 04/05 must be taken **after animations settle**;
- screenshot 06 must show the subtraction operator merging into e1, with no duplicate global minus afterward;
- screenshot 08 must clearly make `z` the dominant object.

---

# 12. Pass criteria

Cancellation V2 passes when a viewer can understand, without opening Formula:

1. L and R each expand into structured contributions;
2. two columns contain visually identical common terms;
3. the user matches and removes those two pairs;
4. the global subtraction turns R's remaining noise into a negative residual;
5. the three residuals become one real backend `z` value;
6. the scene visibly resolves instead of leaving the old proof scattered around the canvas.

The mathematical interaction model is already correct. This refinement is about making the **proof read as a single visual story**.
