# CHW25 V2 — Encrypt Scene Implementation Specification

> Status: implementation spec after Build W_S + Cancellation approval
> Scope: **Encrypt only**
> Product language: light research-infographic / interactive cryptography canvas

---

## 0. Design decision

Cancellation V2 is approved after the focused refinement. Do not keep polishing it now.

The next scene must make the encryption formula feel like a **living computation diagram**, not three formulas placed in cards.

The visual story is:

```text
shared ephemeral material
        |
        +----------------+----------------+
        |                |                |
        v                v                v
      lane c1          lane c2          lane c3
        |                |                |
        v                v                v
       c1               c2               c3
         \               |               /
          \              |              /
             assemble ciphertext
```

Core formulas implemented by real helpers:

```text
c1^T = s^T A + e^T
c2^T = s^T(W0 + W_S) + e^T K_W
c3   = s^T p + e^T k_p + mu floor(q/2)
```

The source of truth remains `src/chw25_dbe/construction.py`:

- `compute_c1`
- `compute_c2`
- `compute_c3`
- `derive_rerandomization`
- `build_ws`

Do not duplicate these formulas in the scene layer.

---

# 1. Backend execution model

## 1.1 Current problem

`encrypt()` currently samples `s, e, K_W, k_p` internally and immediately computes all three ciphertext components. That is correct for production, but it does not support a user-controlled staged teaching scene because the visual scene needs to run `c1`, `c2`, and `c3` separately using the **same sampled material**.

Do not fake this by calling `encrypt()` first and replaying the result.

## 1.2 Required DemoEngine extension

Extend the V2 teaching execution layer with one prepared encryption state. It is acceptable for the DemoEngine to sample random material because sampling is not a duplicated cryptographic formula.

Suggested state:

```python
self.enc_prepared = False
self.enc_s = None
self.enc_e = None
self.enc_K_W = None
self.enc_k_p = None
self.enc_xi = None
self.enc_W0 = None
self.enc_WS = None
self.enc_c1 = None
self.enc_c2 = None
self.enc_c3 = None
self.enc_ct = None
self.enc_done = set()
```

Add methods conceptually equivalent to:

```python
prepare_encrypt_demo()
execute_c1()
execute_c2()
execute_c3()
assemble_ciphertext()
reset_encrypt_demo()
```

### prepare_encrypt_demo()

Must:

1. sample `xi` if needed;
2. sample `s`, `e`, `K_W`, `k_p` with the same algebra helpers used by `encrypt()`;
3. call real `derive_rerandomization(pp, S, xi)` for `W0`;
4. call real `build_ws(pp, pks, S)` for `W_S`;
5. store the prepared material;
6. compute **none** of `c1/c2/c3` yet.

### execute_c1()

Must call only:

```python
compute_c1(pp, enc_s, enc_e)
```

Store the exact result.

### execute_c2()

Must call only:

```python
compute_c2(pp, enc_W0, enc_WS, enc_s, enc_K_W, enc_e)
```

Store the exact result.

### execute_c3()

Must call only:

```python
compute_c3(pp, enc_s, enc_e, enc_k_p, mu)
```

Store the exact result.

### assemble_ciphertext()

Enabled only after all three component executions. Construct a real `Ciphertext(xi, c1, c2, c3)` from the stored values.

For final integration, this assembled ciphertext should become the same scenario ciphertext used by later decrypt/cancellation scenes. If changing existing DemoEngine initialization now risks breaking prior checkpoints, keep this integration behind an explicit method and test it; do not duplicate formulas.

## 1.3 Classroom privacy rule

The classroom UI must **not** print raw arrays/values for:

- `s`
- `e`
- `K_W`
- `k_p`

They are represented symbolically only.

Developer drawer may show shape / fingerprint / role, but not dump complete secret/random vectors by default.

---

# 2. Scene identity

Header:

```text
CHW25 Broadcast Encryption
Encrypt one bit μ = 1 to S = {2,4}
```

Do not display an IDE-like task name.

Main conceptual message:

> One ephemeral secret/noise source feeds three parallel computations, producing c1, c2, c3, which are assembled into one broadcast ciphertext.

---

# 3. Overall layout

Use the canvas from the approved V2 scenes.

Reference composition (logical, not exact pixels):

```text
                           EPHEMERAL MATERIAL

                         [ amber s seed ]
                               |
                    .----------+----------.
                    |          |          |
                    v          v          v

                ┌────────┐ ┌────────┐ ┌────────┐
                │  LANE1 │ │  LANE2 │ │  LANE3 │
                │   c1   │ │   c2   │ │   c3   │
                └────────┘ └────────┘ └────────┘

                    c1         c2         c3
                     \          |          /
                      \         |         /
                        [ ciphertext ct ]
```

Actual scene should use visual glyphs, not these boxes.

Three lanes occupy about 75% of canvas width with equal visual weight.

Do not make the lanes giant bordered panels. Separate them by whitespace and very faint vertical guide rhythm only if needed.

---

# 4. Shared visual vocabulary

Reuse existing approved primitives where possible:

- `MatrixGlyph`
- vector-strip motif from cancellation
- noise particles
- ciphertext purple palette
- aggregate green for `W_S`
- rerandomization magenta for `W0`

Add typed encrypt-specific primitives:

```text
visuals/
  random_seed_glyph.py
  composite_matrix_glyph.py
  binary_filter_glyph.py
  message_bit_glyph.py
  ciphertext_component_glyph.py
  ciphertext_envelope_glyph.py
  compute_lane_edge.py
```

Do not reuse a generic Rectangle+Text token as the main representation.

---

# 5. Shared inputs

## 5.1 s — ephemeral random secret

Visual:

- amber circular seed/orb;
- small inner `s` caption may exist;
- it branches into all three lanes;
- it should feel like **one object reused three times**, not three unrelated copies.

Animation when the scene is prepared:

- one `s` appears above the three lanes;
- three fine amber branch lines grow toward each lane;
- no formula shown.

## 5.2 e — noise source

Visual:

- one coral particle cloud placed near the shared `s` source but offset;
- when a lane runs, 2–4 particles peel off and travel into that lane;
- do not show dozens of particles;
- do not display numeric noise values.

The audience should understand that the same encryption-time noise vector participates in all three component formulas.

---

# 6. Lane 1 — c1

Formula:

```text
c1^T = s^T A + e^T
```

## Visual grammar

```text
        s branch
           |
           v
     [ blue matrix A ]
           |
        product path
           + <--- coral noise particles e
           |
           v
       [ purple c1 ]
```

### A glyph

Use a blue matrix grid, visually consistent with `W_i` matrices.

### Compute interaction

Initial lane is ready but output capsule absent.

Contextual action near the lane:

```text
Run c1
```

On click:

1. real `execute_c1()` is called;
2. amber path from `s` pulses once through A;
3. 2–4 coral particles enter at the plus junction;
4. junction contracts;
5. a purple `c1` component capsule resolves below the lane;
6. optional 900ms tiny annotation appears: `s·A + noise` — not full formula;
7. annotation fades.

The component capsule may show:

```text
c1
m-vector
```

in developer mode only. Classroom mode: just `c1` and structural glyph.

---

# 7. Lane 2 — c2

Formula:

```text
c2^T = s^T(W0 + W_S) + e^T K_W
```

This must be the most visually rich lane because it connects directly to the previously approved Build W_S scene.

## 7.1 W0 + W_S composite

Do not write a large text card `W0+WS`.

Use two matrix glyphs:

- `W0`: magenta rerandomization matrix;
- `W_S`: green aggregate matrix, visually identical to prior scene result.

They should initially appear side-by-side with a small mathematical `+`, then on lane activation morph into a single **split-role composite matrix**:

```text
┌───────────────┐
│ magenta|green │
│ magenta|green │
│ magenta|green │
└───────────────┘
     W0 + W_S
```

Caption is secondary; color split carries the concept.

## 7.2 e^T K_W branch

Do not simply send noise directly into c2, because the formal formula contains `K_W`.

Visual:

- coral noise particles enter a compact neutral-blue/gray binary matrix/filter glyph;
- that glyph is `K_W`;
- output joins the main c2 lane at a plus junction.

`K_W` is symbolic. Do not show its entries.

## Interaction

Contextual action:

```text
Run c2
```

On click:

1. real `execute_c2()`;
2. W0 and W_S visually compose into one split matrix;
3. `s` branch flows through the composite matrix;
4. coral particles pass through K_W side branch;
5. both branches meet at the plus junction;
6. a purple `c2` capsule resolves.

The W_S glyph used here should look recognizably derived from the Build W_S scene, not redrawn in an unrelated style.

---

# 8. Lane 3 — c3

Formula:

```text
c3 = s^T p + e^T k_p + μ floor(q/2)
```

This lane visually combines three concepts:

1. public dot product `s^T p`;
2. noise-filter branch `e^T k_p`;
3. message embedding `μ floor(q/2)`.

Reuse motifs already introduced in Cancellation where possible.

## 8.1 public-dot branch

Use the same motif as cancellation `PublicDotGlyph`:

```text
[s seed] · [blue p vector]
```

This cross-scene consistency is important.

## 8.2 k_p branch

Represent `k_p` as a short binary-vector filter, not a matrix.

Coral particles pass through it and join the lane.

## 8.3 message bit

Use a small gold `MessageBitGlyph`:

- clearly contains `μ = 1`;
- next to it a half-q divider motif, visually related to the cancellation `MessageHalfGlyph`;
- the audience should recognize later that the same message contribution survives decryption.

## Interaction

Contextual action:

```text
Run c3
```

On click:

1. real `execute_c3()`;
2. `s` flows into public-dot motif;
3. a few noise particles pass through k_p;
4. message glyph enters from below/side;
5. the three contributions converge;
6. purple `c3` capsule resolves.

---

# 9. Interaction order

This scene is user-controlled, not a timeline player.

The user may run lanes individually. Recommended teaching order:

```text
c1 -> c2 -> c3
```

But code should not hard-fail if the user selects another lane first unless there is a true dependency.

Each unexecuted lane shows a subtle contextual action:

```text
Run c1
Run c2
Run c3
```

Once executed, the action disappears and the resulting component remains.

No global `Animate Step`.

---

# 10. Assemble ciphertext

Only after all three lane outputs exist, show one local action centered below them:

```text
Assemble ciphertext
```

On click:

1. call real `assemble_ciphertext()` in DemoEngine;
2. c1/c2/c3 capsules move along three curved paths to center;
3. a small `xi` tab appears as a neutral metadata tab — do not show raw bytes;
4. components dock into a larger purple envelope/capsule;
5. result resolves as:

```text
        ┌────────────────────────┐
        │       ciphertext       │
        │   ξ   c1   c2   c3    │
        └────────────────────────┘
                    ct
```

Again: this is a visual envelope, not a text box.

After assembly, the three lane diagrams fade to ~25% and remain as derivation memory for 1–2 seconds, then settle at ~15–20%.

The ciphertext becomes the hero object.

This final state should visually prepare for later broadcast/media integration.

---

# 11. Formula drill-down

Default canvas shows no large equations.

Selecting a lane and clicking `Formula` opens a compact formula popover specific to that lane.

### c1

```text
c1^T = s^T A + e^T
```

Interpretation:

> Mix the ephemeral secret through public matrix A, then add small noise.

### c2

```text
c2^T = s^T(W0 + W_S) + e^T K_W
```

Interpretation:

> Bind the ciphertext to the rerandomization matrix and the recipient aggregate, with a noise-filter branch.

### c3

```text
c3 = s^T p + e^T k_p + μ floor(q/2)
```

Interpretation:

> Mask the encoded message bit with the public vector contribution and noise.

Do not show all three full equations at once by default.

A global Formula click after ciphertext assembly may show the three equations together in a compact summary.

---

# 12. Real implementation drawer

`</> Implementation` is contextual.

If c1 selected, show the real `compute_c1()` source lines.

If c2 selected, show real `compute_c2()`.

If c3 selected, show real `compute_c3()`.

After ciphertext assembly, drawer may show the relevant portion of real `encrypt()` demonstrating that it calls:

```python
W_S = build_ws(...)
c1 = compute_c1(...)
c2 = compute_c2(...)
c3 = compute_c3(...)
return Ciphertext(...)
```

The drawer must read actual disk source. Do not maintain copied source strings.

### Drawer metadata in classroom mode

Allowed:

- shapes;
- fingerprints;
- `S={2,4}`;
- `mu=1`;
- which lane executed;
- ciphertext component shape.

Do not dump raw ephemeral material.

---

# 13. Motion language

Use the approved V2 pattern:

```text
appear -> branch -> flow -> combine -> resolve -> memory
```

Recommended timing:

- branch/path grow: 180–260ms;
- object travel: 260–420ms;
- plus-junction combine: 140–220ms;
- capsule resolve: 260–340ms;
- final ciphertext assembly: 500–700ms total.

No decorative bouncing, spinning, or glow pulses.

Every animation must explain data dependence.

---

# 14. Classroom mode visual hierarchy

Strong:

- active lane inputs;
- current flowing branch;
- ciphertext component being created;
- final ciphertext.

Medium:

- idle lane structures;
- shared s/e sources;
- lane labels.

Weak:

- captions;
- shape/fingerprint metadata;
- previous scene navigation.

Do not allow blue/purple tertiary buttons to visually compete with the three cryptographic lanes.

---

# 15. Debug label-hiding acceptance

Add:

```text
hide_encrypt_formula_labels=True
```

In debug mode hide captions such as:

- `A`
- `W0`
- `W_S`
- `K_W`
- `p`
- `k_p`
- `c1/c2/c3`

Do **not** hide the structural glyphs or semantic colors.

A reviewer should still infer:

1. one shared random seed branches into three computations;
2. first lane uses one public matrix plus noise;
3. second lane uses a magenta+green composite matrix and filtered noise;
4. third lane uses a vector dot motif, noise filter, and message block;
5. three purple results assemble into one ciphertext.

If the debug screenshot becomes meaningless without labels, the scene remains too text-dependent.

---

# 16. Test requirements

Keep all existing tests green.

Add V2 encrypt tests covering at least:

1. `prepare_encrypt_demo()` creates correct shapes for s/e/K_W/k_p/W0/WS;
2. no c1/c2/c3 computed before lane execution;
3. `execute_c1()` exactly equals formal `compute_c1()`;
4. `execute_c2()` exactly equals formal `compute_c2()`;
5. `execute_c3()` exactly equals formal `compute_c3()`;
6. each lane can only resolve once or resolves idempotently;
7. `assemble_ciphertext()` blocked until all 3 are ready;
8. assembled ct fields equal stored component results;
9. authorized `u2` decrypts assembled ciphertext to `mu` using formal decrypt path;
10. source drawer reads actual `construction.py` lines;
11. classroom visual adapter exposes no full raw s/e/K_W/k_p arrays;
12. W_S used in c2 is exactly real `build_ws(pp,pks,S)`;
13. W0 used in c2 is exactly real `derive_rerandomization(...)[0]`.

Do not weaken existing cancellation/build_ws tests.

---

# 17. Screenshots for review

Produce exactly these stable-state screenshots:

```text
enc_01_prepared.png
enc_02_c1_running_or_resolved.png
enc_03_c2_composite.png
enc_04_c2_resolved.png
enc_05_c3_message_mix.png
enc_06_all_components_ready.png
enc_07_ciphertext_assembled.png
enc_08_formula_c2.png
enc_09_implementation_c2.png
enc_debug_no_labels.png
```

No video yet.

Review priority:

1. does the screenshot look like a research/PPT computation diagram?
2. is the data flow understandable before reading formulas?
3. is W_S visibly continuous with the prior scene?
4. does c3 visually foreshadow the message term that survives cancellation?
5. does the final ciphertext feel like one assembled broadcast object?

---

# 18. Scope freeze

This checkpoint must **not** implement:

- Build Y2 scene;
- Threshold scene;
- Media scene;
- complete global navigation redesign;
- responsive-layout polish;
- final cross-scene transition animation.

Those come after Encrypt visual review.

Do not modify the formal mathematical formulas.

---

## Final acceptance sentence

> The Encrypt scene passes when an observer can explain “one ephemeral secret/noise source creates three different ciphertext components, which are assembled into one broadcast ciphertext” from the picture alone, then optionally open the paper formula and the real Python helper to verify the exact computation.
