# CHW25 V2 — Interactive Cancellation Implementation Spec

> Status: **implementation-ready design**  
> Precondition: Build `W_S` V2 checkpoint is visually accepted with minor non-blocking shell polish.  
> Scope: **Cancellation only**. Do not implement Encrypt / Build Y2 / Threshold / Media in this checkpoint.

---

# 0. Design decision

The cancellation scene is the most important explanatory scene in the CHW25 demo.

It must **not** be a multiline algebra slide and must **not** return to the V1 pattern of wide rounded rectangles containing formulas.

The visual story is:

```text
collapsed contributions
        ↓ expand
structured semantic terms
        ↓ user matches equal terms
manual cancellation
        ↓
residual terms only
        ↓ real compute_z()
        z
```

The user must feel that they are manipulating a correctness diagram, not clicking through an animation.

Core mathematical identity for user `i=2`, `S={2,4}`:

```text
L = c3 + c2^T r2
R = c1^T Y2
z = L - R
```

Correctness expansion:

```text
L = μ⌊q/2⌋ + s^T p + s^T(W0+W_S)r2 + ẽ2
R =            s^T p + s^T(W0+W_S)r2 + ẽ1
```

After cancelling the two shared contributions:

```text
z = μ⌊q/2⌋ - ẽ1 + ẽ2
```

Important truthfulness rule:

- the **matching/cancellation picture is a semantic explanation of the correctness identity**;
- the UI must not pretend that each visual cancellation is a separate numerical backend operation;
- the final numerical `z` must be obtained by the real `DemoEngine.compute_z_now()` -> formal `build_decryption_term()` + `compute_z()` path;
- `decrypt_with_trace()` may provide real `z_centered`, `noise_residual`, `c3`, `c2_dot_r_i`, `c1_term_total`, etc.;
- do not invent term values for `s^T p` or `s^T(W0+W_S)r2` unless the backend explicitly exposes them.

---

# 1. Visual acceptance of Build W_S

The refined Build `W_S` direction is accepted for progression.

Keep as global V2 language:

- light research-infographic canvas;
- large typed matrix glyphs;
- recipient halo;
- contextual action instead of global Execute;
- formula/code as tertiary drill-down;
- classroom mode by default;
- developer details hidden unless explicitly opened.

Minor shell issues such as whitespace tuning and tiny header badge polish are non-blocking and should be handled later as a single global pass, not per scene.

---

# 2. Scene composition

Reference logical scene: **1280×700** inside the V2 canvas.

The scene has three visual bands:

```text
Band A  provenance / collapsed contributions      y ≈ 120–240
Band B  expanded cancellation structure           y ≈ 285–500
Band C  residual -> z                              y ≈ 525–650
```

Do not show user avatars in this scene. The focus is the algebraic correctness relation for already-selected authorized user `u2`.

A small header annotation is sufficient:

```text
Decrypt for u2 · S={2,4}
```

---

# 3. Stage 1 — provenance before algebra

Before expansion, show two large **ContributionCapsule** objects, not formulas.

## 3.1 LEFT contribution

Visual provenance:

```text
[c3 ciphertext capsule]    +    [c2 capsule] × [r2 vector]
                 \              /
                  \            /
                    [   L   ]
```

- `c3`: purple ciphertext capsule;
- `c2`: purple ciphertext capsule;
- `r2`: blue/public vector strip;
- the output `L` capsule is a neutral white object with a thin slate border.

Small caption under L only:

```text
left contribution
```

## 3.2 RIGHT contribution

```text
[c1 ciphertext capsule]    ×    [Y2 bundle]
                 \              /
                  \            /
                    [   R   ]
```

- `c1`: purple ciphertext capsule;
- `Y2`: the decryption-bundle glyph planned by V2 visual vocabulary; for this checkpoint a compact bound-three-strip bundle is enough;
- output `R` uses the same neutral capsule style as L.

Small caption:

```text
right contribution
```

## 3.3 Relationship

Place a large, quiet minus operator spatially between the two outputs:

```text
[L]      −      [R]
```

Underneath, one compact result socket:

```text
z
```

Do **not** write `z = c3 + ...` on the main canvas.

## 3.4 Interaction

Each ContributionCapsule is clickable.

Clicking L or R performs an **unfold** animation into Band B.

Preferred interaction:

- first click L -> L unfolds;
- click R -> R unfolds;
- once both are expanded, matching interaction is enabled.

A small contextual action `Expand both` may exist for presentation convenience, but the capsules themselves must remain directly clickable.

---

# 4. Stage 2 — semantic term vocabulary

Do not use V1 `TermItem`.

Create typed cancellation glyphs. Labels may exist as captions, but the glyph must still communicate its role without the caption.

## 4.1 MessageHalfGlyph — μ⌊q/2⌋

Visual motif:

- warm gold block;
- split / half divider mark;
- tiny `μ` badge in upper-left;
- compact, approximately 118×70.

Semantic role: message-dependent half-q offset.

Color:

```text
SECRET / message gold: #D9912B
soft fill: #FFF3DE
```

Caption (small):

```text
μ · q/2
```

## 4.2 PublicDotGlyph — s^T p

Must visually resemble a dot product, not a formula card.

Motif:

```text
 amber s seed   ·   blue p vector strip
      ●         •        ▌
                          ▌
                          ▌
```

Pack these components into a compact transparent visual group; do not surround the entire object with a large rounded rectangle.

The L and R copies must be visually identical.

Caption may be:

```text
sᵀp
```

but must be secondary.

## 4.3 MatrixChainGlyph — s^T(W0+W_S)r2

This is the key non-text object.

Visual motif:

```text
 amber s seed  ->  [half-magenta W0 | half-green W_S mini matrix]  ->  r2 vector
       ●                   ▦▦▦▦                                   ▌
```

- left mini matrix half uses rerandomization magenta;
- right half uses aggregate green;
- `r2` is a thin blue vector strip;
- use two short arrow/flow segments;
- no large formula box.

The L and R copies must be visually identical.

Optional tiny caption:

```text
shared matrix term
```

The exact formula is revealed only through Formula drill-down or hover tooltip.

## 4.4 NoiseGlyph — ẽ1 / ẽ2

Visual motif:

- 4–6 coral particles;
- small `+` marker while still inside L/R contribution;
- irregular but deterministic particle placement;
- compact ~90×60.

Captions `ẽ1`, `ẽ2` are allowed but secondary.

---

# 5. Stage 2 layout — aligned correctness ledger

Once L and R are unfolded, arrange semantic objects in aligned columns.

```text
                 message         public-dot        matrix-chain          noise

L row          [ μq/2 ]          [ s·p ]           [ chain ]            [ ẽ2 ]

                         < matching columns >

R row                            [ s·p ]           [ chain ]            [ ẽ1 ]
```

Recommended logical x centers:

```text
message       x=235
public-dot    x=490
matrix-chain  x=785
noise         x=1080
```

Rows:

```text
L y=330
R y=470
```

A thin global minus marker is shown to the left of the R row, because the decryption expression is `L - R`.

This is crucial: the final sign of `ẽ1` comes from subtracting the R row.

Use tiny row labels only:

```text
L
R
```

Do not write full formulas as row headers.

---

# 6. Matching interaction

The user manually selects equal semantic terms.

## 6.1 Selection

- click one shared term in L;
- click one term in R;
- selection raises the glyph by 4 px and adds a thin semantic-color outline / halo;
- do not fill the whole item blue.

## 6.2 Correct match

Correct pairs:

```text
L.public_dot   <-> R.public_dot
L.matrix_chain <-> R.matrix_chain
```

If keys match:

1. draw a very thin vertical / gently curved connection between the pair;
2. both glyphs pulse once at scale 1.04;
3. a contextual action appears at the midpoint:

```text
Cancel pair
```

No global Execute button.

## 6.3 Incorrect match

If semantic keys differ:

- both selected glyphs move horizontally ±5 px and return over ~160ms;
- border briefly changes to noise/coral;
- a tiny local annotation appears for <1s:

```text
not the same contribution
```

No global error banner.

## 6.4 Cancel animation

On `Cancel pair`:

1. matched pair moves 12–18 px toward the centerline between rows;
2. both receive one diagonal strike;
3. overlap briefly;
4. scale to 0.82;
5. fade to 0;
6. corresponding column remains empty — do not immediately pack all remaining terms together during the first cancellation.

A faint neutral check/cancel mark may remain for ~700ms then disappear.

The user repeats for the second shared pair.

---

# 7. Stage 3 — residual expression

After both shared pairs are cancelled, collapse the empty matching columns and reflow only the remaining three semantic objects into Band C.

The visual transition is important.

## 7.1 Sign transformation

Because the full relation is `L - R`:

- `L` noise stays `+ẽ2`;
- `R` noise travels through the global minus operator;
- during that motion its small sign marker rotates / flips from `+` to `−`;
- it becomes `−ẽ1`.

This visually explains the sign rather than merely changing text.

## 7.2 Residual layout

```text
          [ μq/2 ]        [ - ẽ1 ]        [ + ẽ2 ]
```

These three objects should be noticeably larger than the cancelled items were at the moment of cancellation, because they are now the only remaining contributors.

A small contextual action appears below:

```text
Form z
```

---

# 8. Form z — real backend boundary

`Form z` is the boundary between pedagogical cancellation and real numerical computation.

On click:

1. call **real** `DemoEngine.compute_z_now()`;
2. `DemoEngine` must continue to call formal `build_decryption_term()` + `compute_z()`;
3. the three residual glyphs converge toward one central result glyph;
4. result resolves into a large **ZGlyph**.

## 8.1 ZGlyph

Visual:

- neutral/aggregate outline;
- central italic `z`;
- no big formula card;
- in classroom mode show `z_centered` as a small numeric annotation below, because the next threshold scene needs this concrete value;
- in developer mode additionally expose `z_raw`, term fingerprint, etc.

Example:

```text
        ╭──────────╮
        │    z     │
        ╰──────────╯
          -52360
```

After resolve, one compact annotation fades in for ~1.5s:

```text
z = μ⌊q/2⌋ − ẽ1 + ẽ2
```

Then it fades to muted/secondary state.

Do not implement the threshold ruler in this checkpoint.

---

# 9. Formula drill-down

`Formula` is tertiary and hidden by default.

When opened in this scene, it should show the correctness derivation in three short blocks:

```text
L = c3 + c2ᵀr2
  = μ⌊q/2⌋ + sᵀp + sᵀ(W0+W_S)r2 + ẽ2

R = c1ᵀY2
  = sᵀp + sᵀ(W0+W_S)r2 + ẽ1

z = L - R = μ⌊q/2⌋ - ẽ1 + ẽ2
```

No more than these three blocks.

The main canvas must remain understandable with this panel closed.

---

# 10. Implementation drill-down

Do not fake source code for visual term cancellation.

The code drawer must clearly distinguish:

```text
Visual explanation
The pair cancellation illustrates the correctness identity.

Real numerical implementation
1. build_decryption_term(...)
2. compute_z(...)
```

Show **real source lines** from `src/chw25_dbe/construction.py` using the existing source-reader path.

Preferred drawer sections:

```text
Paper operation
z = c3 + c2ᵀr_i - c1ᵀY_i

Real implementation · build_decryption_term
<real source>

Real implementation · compute_z
<real source>
```

If the current drawer supports one source block only, show `compute_z()` as primary and offer `Y_i helper` as a compact secondary disclosure.

No copied source strings.

---

# 11. Backend / trace requirements

Reuse existing `DemoEngine` semantics where possible:

```text
left_terms
right_terms
selected
cancelled
select_term()
can_cancel()
cancel_selected()
all_cancelled()
compute_z_now()
```

The V2 scene may adapt these states into typed visual metadata.

Do not move math into the scene.

For real numerical annotations, use `decrypt_with_trace()` or `compute_z_now()` output.

Existing trace supports:

```text
c3
c2_dot_r_i
c1_dot_y_ii
c1_dot_y_0i
c1_dot_y_ji
c1_term_total
c3_plus_c2_term
z_before_center
z_centered
noise_residual
decoded_mu
threshold
```

Do not fabricate numeric values for semantic terms that trace does not expose.

---

# 12. Suggested files

Add only the visual items necessary for this checkpoint:

```text
desktop_workbench_v2/
  cancellation_scene.py

  visuals/
    contribution_capsule.py
    message_half_glyph.py
    public_dot_glyph.py
    matrix_chain_glyph.py
    noise_glyph.py
    decryption_bundle_glyph.py
    z_glyph.py
    cancel_connection.py
```

Reuse global V2 theme, formula popover, code drawer and window shell.

Do not modify V1 packages.

---

# 13. Classroom mode

Default `classroom_mode=True`.

Hide by default:

- fingerprints;
- internal semantic keys such as `stp`, `w0ws`;
- backend success strings;
- raw term arrays;
- full trace values;
- source mapping metadata.

Show:

- compact mathematical labels;
- recipient context `u2 · S={2,4}`;
- the real final `z_centered`;
- tiny local instructions.

Developer mode may expose trace and source details.

---

# 14. Animation language

Use V2 movement grammar:

```text
unfold -> align -> select -> match -> cancel -> reflow -> transform sign -> converge -> resolve
```

Avoid:

- decorative floating;
- bouncing;
- particles unrelated to noise;
- page/slide transitions;
- disappearing everything between substates.

Objects persist whenever mathematically meaningful.

Recommended durations:

```text
unfold capsule      260–340ms
selection lift      100–140ms
match pulse         140–180ms
cancel converge     180–240ms
strike/fade         220–300ms
residual reflow     280–360ms
sign flip           180–240ms
form-z convergence  300–420ms
z resolve           220–300ms
```

---

# 15. Hard visual acceptance test

Add a debug flag conceptually equivalent to:

```text
hide_term_formula_labels=True
```

This hides:

- `sᵀp` captions;
- shared matrix-term captions;
- `μq/2` text caption where possible;
- `ẽ1/ẽ2` labels where possible.

Do **not** hide the visual motifs themselves.

The scene passes only if a reviewer can still see:

1. two contribution rows;
2. two identical matching visual pairs;
3. one message-only term on L;
4. distinct noise objects;
5. the matching pairs disappear;
6. three residual objects converge into `z`.

If removing formula captions makes the scene meaningless, the design is still too text-dependent.

---

# 16. Screenshot deliverables

Produce only these screenshots for review:

```text
cxl_01_collapsed_sources.png
cxl_02_expanded_terms.png
cxl_03_matching_pair_selected.png
cxl_04_first_pair_cancelled.png
cxl_05_shared_terms_gone.png
cxl_06_residual_signs.png
cxl_07_z_formed.png
cxl_debug_no_term_labels.png
```

Optional, only if already trivial through the shared shell:

```text
cxl_formula_popover.png
cxl_code_drawer.png
```

Do not record a video yet.

---

# 17. Tests

Keep all existing tests green.

Add focused non-GUI or lightweight tests for:

- visual semantic mapping preserves pair keys;
- L/R public-dot glyphs share the same semantic key;
- L/R matrix-chain glyphs share the same semantic key;
- noise/message glyphs are not cancellable;
- mismatched selection does not mutate `cancelled`;
- both shared pairs must be gone before `compute_z_now()`;
- final V2 z equals `decrypt_with_trace()['z_centered']`;
- V2 implementation drawer reads the real `compute_z` / `build_decryption_term` source;
- classroom adapter does not expose private vectors.

---

## Final design sentence

> **Cancellation should look like equal structures physically disappearing from `L - R`, leaving only the message and noise — the algebra is revealed by the motion, not written out first.**
