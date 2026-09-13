# CHW25 Interactive Cryptography Canvas — Visual Language V2

> Status: **design freeze candidate / no UI implementation yet**  
> Branch: `visualization-v2`  
> Purpose: replace the current text-card / debugger-first visual language with a research-infographic canvas while preserving the real CHW25 backend and direct interaction.

---

## 0. Product definition

The target is **not** a slide player, video player, dashboard, or IDE.

It is an **Interactive Cryptography Canvas**:

- the canvas looks like a clean research/PPT diagram;
- the user directly manipulates cryptographic objects;
- the backend performs the real computation;
- animation only explains the state change caused by that operation;
- formulas and source code are drill-down layers, not the default visual surface.

Core principle:

```text
SEE THE OBJECT  ->  MANIPULATE THE OBJECT  ->  SEE THE STATE CHANGE
                          |
                          +-> Formula (optional)
                          +-> Real code (optional)
```

And for every important operation:

```text
Paper Formula <-> Real Python Helper <-> Visual Operation
```

The current 7 helpers in `src/chw25_dbe/construction.py` remain the semantic source of truth:

- `build_ws`
- `compute_c1`
- `compute_c2`
- `compute_c3`
- `build_decryption_term`
- `compute_z`
- `decode_z`

---

## 1. Why V1 still looked like text

The existing Workbench is technically correct, but its primitives force a text-heavy result:

- `TokenItem` = rounded rectangle + text label;
- `TermItem` = wide rounded rectangle + formula string;
- `UserItem` = circle + `u_i` text;
- `MainWindow` permanently reserves left OBJECTS and right CODE columns;
- `BuildWSScene` represents matrices as `W2`, `W4` text tokens;
- `CancellationScene` represents mathematical structure primarily as formula strings.

V2 therefore changes **visual primitives and information hierarchy**, not the cryptographic model.

---

# 2. Overall composition

## 2.1 Canvas-first layout

Reference canvas: **1440×900**; must scale to 1366×768 and 1920×1080.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CHW25 Broadcast Encryption                         S = {2,4}   μ = 1 │
│ subtle subtitle / current operation                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│                                                                        │
│                      INTERACTIVE VISUAL CANVAS                         │
│                                                                        │
│          sender / parameters / users / matrix glyphs / flow           │
│                                                                        │
│                                                                        │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ Current task                                 [ Formula ] [ </> Code ] │
│ short instruction                    [Hint] [Reset current operation]  │
└────────────────────────────────────────────────────────────────────────┘
```

Rules:

- Canvas gets **at least 82% of usable area**.
- No permanent left OBJECTS panel.
- No permanent CODE panel.
- No slide navigation such as `1 Select / 2 WS / 3 Encrypt ...`.
- Current task is a compact contextual strip, not a presentation timeline.
- `Formula` and `</> Code` open temporary drawers/popovers and close back to full canvas.

---

# 3. Light research-infographic theme

## 3.1 Base palette

```text
background      #F4F6FA
canvas          #FFFFFF
surface-soft    #F8FAFD
border          #DCE3EC
border-strong   #C7D1DE
text            #182234
muted           #728096
faint           #A9B4C4
```

## 3.2 Semantic palette

```text
public / matrix       #3F73C8
public-soft           #EAF1FB
secret                #D9912B
secret-soft           #FFF3DE
recipient / success   #31966A
recipient-soft        #E8F6EF
rerandomization       #B05AA7
rerandom-soft         #F7EAF5
ciphertext             #7357B8
ciphertext-soft        #F0EBFA
noise                  #D86666
noise-soft             #FCECEC
aggregate               #6F963E
aggregate-soft          #EEF5E5
inactive                #AAB4C2
```

Color encodes **cryptographic role** and stays stable across every scene.

Do not use gradients except a very subtle depth tint inside a glyph. No neon, glow, or hacker-dark styling.

## 3.3 Typography

- UI Chinese/English: `Microsoft YaHei UI` / `Segoe UI`.
- Mathematical annotation: serif/math font if available; otherwise clean Segoe UI with italic variables.
- Source code drawer only: `JetBrains Mono` or `Consolas`.
- Formula/code fonts must not leak into the normal canvas.

---

# 4. Visual vocabulary

The following are **different drawable object types**. Do not collapse them into one generic `TokenItem`.

| Object | Visual representation | Main semantic cue |
|---|---|---|
| User | simple avatar glyph + short `u_i` caption | person/recipient |
| Authorized user | user glyph + green outer halo | membership in S |
| Matrix `A`, `W_i`, `W_S`, `W_0` | 5×4 or 6×4 mini-cell matrix tile | rectangular grid |
| Vector `p`, `r_i`, `y_i` | narrow stacked strip / bar vector | one-dimensional structure |
| Secret key `y_ii` | vector strip with small key-notch/badge | amber + PRIVATE cue |
| Public cross-term `y_{j,i}` | vector strip with public badge | blue |
| Rerandomization `y_0i`, `W_0` | vector/matrix with dotted-magenta outline | ephemeral source |
| Random secret `s` | small amber seed/orb feeding a lane | per-encryption secret |
| Noise `e` | coral particles/dots entering a computation edge | perturbation |
| Ciphertext component `c1/c2/c3` | small purple capsule | encrypted component |
| Ciphertext `ct` | larger capsule/envelope holding 3 component marks | common broadcast object |
| Aggregation | overlap/stack area, not a box labeled “SUM” | composition |
| `Y_i` | bound bundle of three vector strips | decryption material |
| Cancellation term | compact shaped math token with semantic icon | pairable term |
| AES session key | sealed key-card, no raw bytes | protected secret |
| Media | image/video/file card with lock overlay | encrypted payload |

### Matrix glyph

A matrix is never drawn as `[W2]` alone. It must look like a matrix first:

```text
┌─────────────┐
│ ▪ ▫ ▪ ▫ ▪  │
│ ▫ ▪ ▪ ▫ ▫  │
│ ▪ ▪ ▫ ▪ ▫  │
│ ▫ ▫ ▪ ▪ ▪  │
└─────────────┘
      W₂
```

The cells are symbolic, not actual matrix values. Click/Formula/Code drill-down can show shape and fingerprint.

### Vector glyph

```text
│■│
│□│
│■│   y₂₂
│■│
```

Again: symbolic structure first, label second.

---

# 5. Information hierarchy

For every scene:

1. **visual object and spatial relation**;
2. user action;
3. state-change animation;
4. one short annotation / one formula at most;
5. optional formula drawer;
6. optional real-code drawer.

Target ratio on the main canvas:

- visual objects / paths / spatial relations: **75–85%**;
- labels and short annotations: **10–20%**;
- formulas visible by default: **0–10%**;
- source code visible by default: **0%**.

No scene may use a large multiline formula as the main object.

---

# 6. Core scene A — Select recipient set S

## Goal

Explain broadcast membership visually before any algebra.

## Layout

```text
                              Sender
                                ◉


          u1             u2             u3             u4
          ◯             ◉              ◯             ◉
                        halo                          halo

                       S = {2,4}
```

- Four users occupy the lower third of the canvas.
- Sender occupies upper center.
- Clicking u2/u4 toggles a green recipient halo.
- Non-selected users stay fully visible but neutral gray-blue; do not “disable” them as if they do not exist.
- `S={2,4}` is a small annotation, not a giant card.

## Interaction

- Click a user to add/remove from S.
- The user glyph itself reacts: outer ring expands 4–6 px and settles.
- No formula panel.
- `Formula` button may reveal `S ⊆ [N]` only if requested.

---

# 7. Core scene B — Build W_S

## Goal

Make `W_S = Σ_{j∈S} W_j` visible as **matrix aggregation**, not text addition.

## Initial layout

```text
       u2                                         u4
       ◉                                          ◉
       │                                          │
   ┌───────┐                                  ┌───────┐
   │matrix │                                  │matrix │
   │  W₂   │                                  │  W₄   │
   └───────┘                                  └───────┘

                     aggregation zone
                           · · ·
```

Each selected user exposes a public matrix tile directly below/above the user. `W1/W3` remain available but are visually outside the current selected set.

## Direct manipulation

The user drags matrix tiles into the central aggregation zone.

After W2 is placed:

```text
                      ┌───────┐
                      │  W₂   │
                      └───────┘
                     awaiting W₄
```

After W4 is placed, the tiles overlap with ~18 px offset and a subtle aggregate-green bracket appears.

A contextual action appears **inside the canvas near the aggregate**, not in a global bottom Execute button:

```text
          Compute W_S
```

## State-change animation

On compute:

1. W2 and W4 move into exact alignment;
2. both scale to 0.96;
3. cell patterns cross-fade into one aggregate matrix glyph;
4. outline changes to aggregate green;
5. caption becomes `W_S`;
6. a tiny annotation appears for ~1.5s: `W_S = W₂ + W₄`.

Do not show `[W2] + [W4]` as the main visual representation.

## Error interaction

Dragging W1/W3 into the aggregate zone produces a brief return animation and a small contextual note near that matrix:

`u1 ∉ S` / `u3 ∉ S`

No global red error banner.

---

# 8. Core scene C — Encrypt / form c1,c2,c3

## Goal

Explain encryption as a **three-lane computation network**.

## Layout

```text
                           random s
                              ●
                       ┌──────┼──────┐
                       │      │      │
                       ▼      ▼      ▼

        ┌─────┐     ┌────────────┐    ┌─────┐
        │  A  │     │  W₀ + W_S │    │  p  │
        │grid │     │ matrix     │    │vec  │
        └──┬──┘     └─────┬──────┘    └──┬──┘
           │              │              │
      coral noise     coral noise    coral noise
          · · ·           · · ·          · · ·
           │              │              │
           ▼              ▼              ▼
        ╭─────╮        ╭─────╮        ╭─────╮
        │ c₁  │        │ c₂  │        │ c₃  │
        ╰─────╯        ╰─────╯        ╰─────╯
              ╲           │          ╱
               ╲          │         ╱
                ╰──────►  ct  ◄────╯
```

### Visual behavior

- `s` is one persistent amber object whose three thin paths branch into the lanes.
- noise is shown as 2–4 coral particles entering each appropriate lane; do not animate dozens of particles.
- `A`, `W0+WS`, `p` retain their matrix/vector glyph shapes.
- output components are purple ciphertext capsules.
- final `ct` is a larger common capsule containing three tiny component indicators.

### Interaction

The user can click one lane (`c1`, `c2`, or `c3`). Selection enlarges that lane slightly and enables two contextual actions:

- `Formula`
- `</> Implementation`

Example Formula drawer for c1:

`c₁ᵀ = sᵀA + eᵀ`

Code drawer shows the real `compute_c1()` helper and current shape/fingerprint only.

---

# 9. Core scene D — Build Y₂

## Goal

Explain that authorized decryption combines **three differently sourced materials**.

## Layout

```text
 u2 local device            Encryption epoch            u4 public directory
 ┌─────────────┐            ┌──────────────┐            ┌──────────────┐
 │ secret vec  │            │ ephemeral vec│            │ public vec   │
 │    y₂₂      │            │    y₀₂       │            │    y₄₂       │
 └─────────────┘            └──────────────┘            └──────────────┘
       amber                     magenta                      blue
           ╲                        │                         ╱
            ╲                       │                        ╱
             ╲                      │                       ╱
                    decryption bundle area
                         ┌──────────┐
                         │  Y₂     │
                         │ ║ ║ ║   │
                         └──────────┘
```

The crucial message is **source diversity**:

- `y22`: local private material;
- `y02`: rerandomization / encryption-time material;
- `y42`: public cross-term from u4.

## Interaction

The user clicks or drags the three source glyphs into the bundle area. When all three are present, they physically bind into one `Y₂` bundle using a brace/band animation.

Only after the bundle is formed does a small one-line annotation appear:

`Y₂ = y₂₂ + y₀₂ + y₄₂`

This formula must never be the first thing the user sees.

---

# 10. Core scene E — Interactive cancellation

## Goal

Make correctness understandable through **visual matching and cancellation**, not multiline algebra.

## Visual tokens

Terms are not generic rounded rectangles. Give each semantic term a small distinctive motif:

- `μ⌊q/2⌋`: solid neutral-gold block with half-q divider mark;
- `sᵀp`: blue vector-product token (dot + vector strip motif);
- `sᵀ(W0+WS)r₂`: magenta/green matrix-chain token (matrix tile + path motif);
- noise `ẽ₁/ẽ₂`: coral speckled token.

## Layout

```text
LEFT contribution                         RIGHT contribution

 [ μq/2 ]   [ sᵀp ]   [ matrix-chain ]   [ noise ẽ₂ ]

             [ sᵀp ]   [ matrix-chain ]   [ noise ẽ₁ ]

                     z = LEFT − RIGHT
```

No giant `LEFT L = ...` and `RIGHT R = ...` text boxes. Small labels `LEFT` / `RIGHT` are enough.

## Direct interaction

1. User clicks one token on LEFT.
2. User clicks the corresponding token on RIGHT.
3. If semantic keys match, both tokens lift 4 px and a thin connecting curve appears.
4. A contextual `Cancel pair` action appears between them.
5. On cancel, the two tokens slide toward one another, overlap briefly, receive a diagonal strike, shrink/fade, and the remaining tokens reflow.
6. If terms do not match, selected tokens perform a tiny horizontal “no” motion and return; nothing else changes.

After the two shared terms are cancelled, the canvas contains only:

```text
 [ μq/2 ]      [ +ẽ₂ ]      [ −ẽ₁ ]
```

These three leftovers then converge into a single result object:

```text
╭───────────────╮
│       z       │
│   -52360      │   <- actual trace value
╰───────────────╯
```

Only at this point may a one-line formula appear underneath:

`z = μ⌊q/2⌋ − ẽ₁ + ẽ₂`

## Threshold continuation

The result object itself becomes the marker on the threshold ruler; do not create a disconnected new slide.

```text
 -q/2      -q/4             0             q/4       q/2
  |----------|==============|==============|----------|
  ● z
```

The central green band means decode 0. Outer zones mean decode 1.

The user chooses `0` or `1`; only then call real `decode_z()` and show correctness.

---

# 11. Formula and real-code drill-down

## Default state

No formula panel and no code panel.

## Formula action

`Formula` opens a compact floating sheet occupying at most 25–30% width. It contains:

- the one paper equation relevant to the selected visual operation;
- a one-sentence interpretation;
- optional dimensions.

## Code action

`</> Implementation` opens a right drawer, max ~360 px at 1440 width.

Structure:

```text
Paper operation
W_S = Σ W_j

Real implementation
construction.py · build_ws

136 def build_ws(...):
137     ...
140     for j in sorted(s_set):
141         W_S = mod_q(...)

Inputs
S = {2,4}
W2 = matrix(4×8), fp ...
W4 = matrix(4×8), fp ...

Output
W_S = matrix(4×8), fp ...
```

The drawer is temporary. Closing it restores the full canvas.

No permanent debugger layout.

---

# 12. Interaction model

Avoid generic global `Execute` whenever a contextual action can be attached to the visual operation.

Examples:

- After placing W2/W4 into aggregate zone → `Compute W_S` appears near the aggregate.
- After selecting matching cancellation terms → `Cancel pair` appears between them.
- After leftovers form z → `Place z on threshold` / automatic short transition.
- After threshold appears → choose `[0]` or `[1]`.

Global controls should be limited to:

- Reset scene
- Hint
- Formula
- Code

The user should feel that they are **operating the mathematical diagram**, not operating application chrome.

---

# 13. Qt implementation direction

Keep:

- `DemoEngine` state model and calls into formal helpers;
- QGraphicsScene / QGraphicsView as the interaction canvas;
- `construction.py` helpers as single source of mathematical truth.

Replace / retire from primary V2 visuals:

- generic `TokenItem` as the universal representation;
- generic wide `TermItem` formula cards;
- permanent `ObjectPanel`;
- permanent `CodePanel`;
- dark palette;
- task-switching UI that resembles slide navigation.

Create typed graphics items:

```text
visuals/
  user_glyph.py
  matrix_glyph.py
  vector_glyph.py
  secret_key_glyph.py
  ciphertext_glyph.py
  noise_glyph.py
  bundle_glyph.py
  cancel_term_glyph.py
  recipient_halo.py
  flow_edge.py
```

A small `VisualModel` / adapter may expose only visual metadata (shape, fingerprints, role, source, authorization) from the backend. It must not perform cryptographic math.

---

# 14. Migration order

Do **not** rebuild the whole application at once.

Implementation checkpoints:

1. visual primitives only: UserGlyph + MatrixGlyph + VectorGlyph + light canvas;
2. Scene B only: Build W_S with real drag/drop and matrix merge;
3. visual review;
4. Scene E only: Cancellation with non-text-heavy semantic terms;
5. visual review;
6. add Encrypt computation network;
7. add Build Y2 source convergence;
8. add Select S and threshold continuity;
9. only after approval, integrate hybrid media.

At every checkpoint, visual screenshots are reviewed before expanding scope.

---

# 15. Acceptance criteria for V2

A screenshot should still communicate the current mathematical operation **even if most labels are temporarily hidden**.

If hiding labels makes the scene meaningless, the scene is still too text-dependent.

For the two first implementation checkpoints:

### Build W_S passes if

- matrices are visually recognizable without reading `W2/W4`;
- source users and recipient membership are obvious;
- aggregation is shown spatially;
- output W_S is visibly derived from the two inputs;
- formula is optional, not required to understand the transformation.

### Cancellation passes if

- matching terms are recognizable by visual semantics and location;
- selecting/cancelling is a direct manipulation of terms;
- removed terms visibly disappear from the expression structure;
- remaining terms visibly converge into z;
- formula text is secondary.

---

## Final design sentence

> **The UI should look like a living research diagram whose objects are backed by real code — not like a debugger that happens to animate.**
