# CHW25 V2 — Checkpoint 1/2 Implementation Spec

> Scope: **visual primitives + Build `W_S` only**  
> Status: implementation-ready specification  
> Depends on: `docs/chw25-visual-language-v2.md`  
> Do not expand scope beyond this document before visual review.

---

# 1. Objective

Replace the current text-token Workbench representation of

\[
W_S=\sum_{j\in S} W_j
\]

with a **canvas-first, diagram-native, directly manipulated matrix aggregation scene**.

The user must understand the operation even if labels `W2`, `W4`, `W_S` are temporarily hidden.

This checkpoint proves three things:

1. the new light research-infographic visual language works in Qt;
2. matrix/public-key objects are visually recognizable objects rather than text boxes;
3. direct manipulation remains backed by the real `build_ws()` helper.

---

# 2. Non-goals

Do **not** implement in this checkpoint:

- cancellation V2;
- Encrypt lanes;
- Build `Y_i`;
- threshold;
- media/AES;
- full Setup / KeyGen animation;
- permanent code panel;
- permanent object list;
- timeline/slide navigation;
- a generic replacement for every old scene.

Old `desktop_workbench/` files may remain for reference. The new V2 scene should be isolated enough that rollback/comparison is easy.

---

# 3. Backend contract

Use existing:

```python
DemoEngine.add_to_ws(uid)
DemoEngine.remove_from_ws(uid)
DemoEngine.execute_build_ws()
DemoEngine.reset_ws()
```

The actual math continues to call:

```python
src.chw25_dbe.construction.build_ws(...)
```

Do not duplicate `W_S` arithmetic in graphics code.

The V2 canvas is allowed to read only visual metadata from backend objects:

- user id;
- membership in `S`;
- matrix shape;
- matrix fingerprint;
- aggregate slots;
- whether execution completed.

No real matrix cell values need to be painted.

---

# 4. Virtual canvas and scaling

Use a logical scene coordinate system of:

```text
1280 × 720
```

The `QGraphicsView` should scale the whole scene with aspect ratio preserved on resize (`fitInView` or equivalent).

Target window sizes:

- 1366×768
- 1440×900
- 1920×1080

No scene object should depend on absolute screen pixels outside the 1280×720 virtual coordinate system.

---

# 5. Main composition

The Build `W_S` view is one canvas, not three application columns.

Approximate logical layout:

```text
 y=0
 ┌──────────────────────────────────────────────────────────────────────┐
 │  CHW25 Broadcast Encryption                       S = {2,4}          │
 │  Aggregate the public matrices of the selected recipients           │
 │                                                                      │
 │                         Sender                                       │
 │                           ◉                                          │
 │                                                                      │
 │                                                                      │
 │     u1               u2                  u3                u4         │
 │     ◯                ◉                   ◯                 ◉          │
 │                      │                                     │         │
 │                  matrix W2                           matrix W4        │
 │                    glyph                               glyph          │
 │                       ╲                                 ╱             │
 │                        ╲                               ╱              │
 │                          aggregation focus                            │
 │                                ↓                                     │
 │                           matrix W_S                                  │
 │                                                                      │
 │                                                          [Formula]   │
 │                                                  [</> Implementation]│
 └──────────────────────────────────────────────────────────────────────┘
 y=720
```

Canvas background: `#FFFFFF`.
Outer window/background: `#F4F6FA`.

Do not draw a card around the entire canvas. Let the whitespace be the structure.

---

# 6. Exact visual hierarchy

## 6.1 Header

At `(48, 30)`:

```text
CHW25 Broadcast Encryption
```

- 22–24 px equivalent, semibold, `#182234`.

At `(48, 62)`:

```text
Aggregate the public matrices of the selected recipients
```

- 12–13 px, `#728096`.

At upper right around `(1120, 46)`:

```text
S = {2,4}
```

- compact green-tinted recipient badge;
- this badge may still contain text because it is a status annotation, not a cryptographic object.

## 6.2 Sender

Center at approximately `(640, 120)`.

Use a small sender glyph, not a `TokenItem("Sender")` rectangle.

Suggested design:

- 32 px circular source node;
- thin outgoing broadcast arc/antenna motif;
- caption `Sender` below in muted text.

Sender is contextual only in this scene; it must not dominate.

## 6.3 Users

Centers:

```text
u1  (170, 285)
u2  (460, 285)
u3  (820, 285)
u4  (1110,285)
```

User glyph design:

- head: small circle;
- shoulders/body: simple `QPainterPath` arc;
- no enclosing large circle as the primary shape;
- caption `u1`, `u2`, ... below;
- selected recipients u2/u4 get a soft green halo ring;
- unselected users remain neutral, not dimmed to near-invisibility.

Authorized halo:

- stroke `#31966A`;
- very soft fill `#E8F6EF` at low alpha;
- halo radius ~42 logical px;
- user body itself stays neutral blue-gray.

Membership must be readable from the halo, not from green text alone.

---

# 7. MatrixGlyph specification

Create a typed `MatrixGlyph`, not a generic text token.

Suggested file:

```text
desktop_workbench_v2/visuals/matrix_glyph.py
```

or equivalent isolated V2 package.

## Geometry

Default logical size:

```text
92 × 72
```

Interior symbolic grid:

```text
5 columns × 4 rows
```

Cells are small rounded squares/rectangles, e.g. 8–10 px, with 5–6 px gaps.

The pattern is **deterministic from the matrix fingerprint**, so W2/W4/W_S look consistently different while revealing no matrix values.

Example deterministic rendering rule:

- derive 20 bits from SHA-256/fingerprint;
- for each cell choose filled/public-blue or faint/public-soft;
- this is purely visual metadata and must not be described as actual matrix entries.

## Public matrix style

- outer border: `#3F73C8`, 1.8–2 px;
- base fill: `#FFFFFF`;
- selected/drag state: `#EAF1FB` soft tint;
- grid cells: mix `#3F73C8` and `#D6E4F7`.

Caption under glyph:

```text
W₂
```

Caption is secondary. It should not be inside the matrix tile.

A tiny public badge may use a globe/open-lock style vector icon, not the word `PUBLIC` in a box.

## Aggregate matrix style

`W_S` uses aggregate semantic color:

- border `#6F963E`;
- filled cells using `#6F963E` / `#DDEACB`;
- caption `W_S`.

The output must still be visibly the **same object class (matrix)** as W2/W4.

---

# 8. Exposing W2 and W4 from users

W2 and W4 initially sit near their source users, not in a global object palette.

Suggested centers:

```text
W2 (460, 410)
W4 (1110,410)
```

A thin blue connector from each selected user to its public matrix establishes ownership/source.

u1/u3 may show a much smaller, low-emphasis matrix thumbnail near them, but these are not draggable in the default selected-set scene.

This avoids the current mistake where the object exists independently of the user and therefore loses semantic origin.

---

# 9. Aggregation focus area

Do not use the current dashed rounded rectangle labeled `W_S Aggregator`.

The aggregation zone should initially be a **spatial focus**, not a container widget.

Center:

```text
(785, 510)
```

Before any matrix is placed:

- very light aggregate-colored bracket / dotted focus marks;
- small caption `combine recipient matrices`;
- no `[ ? ]` text expression.

When W2 is dropped:

- W2 snaps to center `(760, 505)`;
- an empty translucent matrix silhouette appears offset to the right `(805,520)` to suggest another matrix is expected;
- caption becomes `1 of 2 recipient matrices`.

When W4 is dropped:

- W4 snaps to offset position `(805,520)`;
- both matrices are visibly overlapping by ~25–30 px;
- a soft aggregate-green brace/arc connects them;
- contextual action `Compute W_S` appears below at `(785, 615)`.

`Compute W_S` is the only primary button in this scene and exists near the operation, not in a global footer.

---

# 10. Drag behavior

## Valid drag

Only recipient matrices W2/W4 are draggable in this fixed POC scene.

During drag:

- glyph lifts visually (small shadow or 1.04 scale);
- connector to user becomes dashed/stretchable or fades;
- aggregation focus subtly brightens when hovered.

On valid drop:

- call `DemoEngine.add_to_ws(uid)`;
- if accepted, snap matrix into aggregation position with 180–260 ms easing;
- update contextual count.

## Invalid drag

If W1/W3 are made draggable for demonstration/testing:

- on drop over aggregation focus call backend and receive rejection;
- matrix does not remain in zone;
- perform short return animation;
- near the matrix show a temporary small note:

```text
u1 ∉ S
```

or

```text
u3 ∉ S
```

for ~1.2 s.

Do not show a global red error banner.

---

# 11. `Compute W_S` action and merge animation

The button appears only when the backend state contains all recipients required by `S`.

On click:

1. call `DemoEngine.execute_build_ws()`;
2. if result is successful, disable further dragging during transition;
3. animate W2 and W4 into exact alignment at `(785,510)` over ~260 ms;
4. pause ~80 ms;
5. cross-fade their public-blue cell patterns into one aggregate-green matrix pattern over ~320 ms;
6. input captions W2/W4 fade;
7. output caption `W_S` fades in;
8. a thin green derivation arc from u2/u4 remains for ~600 ms, then fades to a subtle state;
9. show one compact annotation under output for ~1.5 s:

```text
W_S = W₂ + W₄
```

10. under or beside the result matrix, show only compact metadata:

```text
4 × 8   ·   fp ec357d8e
```

The metadata is secondary muted text.

The visual result should primarily be **one aggregate matrix glyph**, not the formula string.

---

# 12. Formula and implementation drill-down for this scene

At lower/right edge of canvas, unobtrusive secondary actions:

```text
Formula
</> Implementation
```

They must not be large primary buttons.

## Formula popover

Show:

\[
W_S = \sum_{j\in S} W_j
\]

For current `S={2,4}`:

\[
W_S = W_2 + W_4.
\]

One sentence only:

> Aggregate exactly the public matrices of the recipients in the current broadcast set.

## Implementation drawer

Temporary right drawer, max 360 logical px at 1440-window scale.

Show **real source** from `build_ws` only:

```python
def build_ws(...):
    W_S = np.zeros(...)
    for j in sorted(s_set):
        W_S = mod_q(W_S + pks[j].W, q)
    return W_S
```

And compact live values:

```text
S      {2,4}
W2     matrix 4×8 · fp ....
W4     matrix 4×8 · fp ....
W_S    matrix 4×8 · fp ....
```

Closing the drawer restores full canvas width.

Do not reuse the permanent V1 CodePanel layout.

---

# 13. Suggested V2 classes

Create new typed primitives instead of mutating `TokenItem` into another universal object.

Minimum:

```text
desktop_workbench_v2/
  main.py
  main_window.py
  build_ws_scene.py
  theme.py
  formula_popover.py
  code_drawer.py
  visual_adapter.py

  visuals/
    user_glyph.py
    matrix_glyph.py
    recipient_halo.py
    flow_edge.py
    aggregate_focus.py
```

### `VisualAdapter`

May provide:

```python
matrix_visual(uid) -> {
    "label": "W2",
    "shape": (4,8),
    "fingerprint": "...",
    "pattern_bits": [...],
    "recipient": True,
}
```

`pattern_bits` may be derived from fingerprint purely for deterministic drawing.

It must not perform cryptographic arithmetic.

---

# 14. Keep old V1 intact during this checkpoint

Do not rewrite/delete:

```text
desktop_workbench/
desktop/
web/
visualization/
```

Build V2 in an isolated package so screenshots can be compared side-by-side.

Do not modify CHW25 crypto logic except imports needed to reuse existing helpers.

---

# 15. Tests required

Existing 191 tests must remain passing.

Add non-GUI/model tests where practical:

1. `VisualAdapter` matrix pattern is deterministic for same fingerprint.
2. Different fingerprints normally produce different visual patterns.
3. Visual adapter never exposes raw matrix cells.
4. W2/W4 backend add/execute path still equals real `build_ws()`.
5. W1/W3 rejection remains enforced by backend.
6. Code drawer reads the real `build_ws` source, not copied source text.

A GUI test is not required for exact pixels.

---

# 16. Screenshot review package

After implementation, stop and provide exactly these screenshots at 1440×900 (or nearest stable size):

1. `v2_01_initial.png`
   - users + halos + W2/W4 matrix glyphs + empty spatial aggregate focus.

2. `v2_02_w2_placed.png`
   - W2 inside focus + second-matrix silhouette.

3. `v2_03_ready.png`
   - W2/W4 overlapping + contextual `Compute W_S`.

4. `v2_04_result.png`
   - one aggregate-green W_S matrix glyph + compact metadata.

5. `v2_05_formula.png`
   - result scene with Formula popover open.

6. `v2_06_code_drawer.png`
   - result scene with temporary real-code drawer open.

Do not record an auto-play video for this checkpoint.

---

# 17. Hard visual acceptance test

Before reporting completion, hide these text labels in a debug flag:

```text
W2
W4
W_S
```

Take one internal screenshot.

If a reviewer can still visually infer:

- two selected users each own a public matrix;
- those matrices are being combined;
- one matrix result is produced;

then the design passes the V2 visual-language test.

If hiding those labels makes the scene incomprehensible, the implementation is still too text-dependent and must not be presented as complete.

---

# 18. Definition of done

This checkpoint is done only if:

- the scene is recognizably a research/lecture diagram rather than an IDE;
- the matrix objects are recognizable before reading captions;
- `W_S` aggregation is expressed through spatial overlap/merge;
- source-user relationships are visible;
- direct drag/drop remains real interaction;
- the real `build_ws()` computes the result;
- formula/code are optional drill-down layers;
- the light theme is implemented;
- no permanent code/object sidebars remain in this V2 checkpoint;
- no other CHW25 scenes were expanded prematurely.
