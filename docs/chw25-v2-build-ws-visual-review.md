# CHW25 V2 Build W_S — Visual Review

Status: **Checkpoint not yet accepted; one focused refinement pass required before Cancellation.**

The current V2 implementation is a meaningful improvement over V1: light research-infographic theme, typed matrix glyphs, recipient halos, contextual aggregation, on-demand formula/code, and a real backend path are all correct directions. The remaining issue is no longer “too much text” in the old sense. The current problem is **visual hierarchy and causal storytelling are still too weak**.

## 1. What is accepted

Keep these without redesign:

- light theme and semantic colors;
- typed `MatrixGlyph` instead of generic `TokenItem`;
- fingerprint-derived symbolic cell pattern;
- `RecipientHalo` as membership cue;
- direct drag/drop of W2/W4;
- local `Compute W_S` action;
- real `DemoEngine.execute_build_ws()` -> formal `build_ws()` path;
- formula as optional popover;
- real source as optional drawer;
- no permanent OBJECTS / CODE columns.

These solve the architectural problem.

---

# 2. Main visual problems observed in screenshots

## 2.1 The scene is too sparse

At 1440×900, the important mathematical objects occupy a small part of the screen. Large empty areas dominate the composition.

The users, matrices, and final W_S are all too small for classroom/projector presentation.

**Required change:** increase the main visual objects by about 1.35–1.55× and compress their spatial spread.

Target approximate sizes:

- selected user glyph incl. halo: 92–104 px diameter;
- matrix glyph: 100–116 px wide, 76–88 px high;
- inactive user glyph: 52–60 px, not tiny;
- W_S result matrix: 116–128 px wide.

---

## 2.2 Sender is visually central but semantically inactive

The sender currently occupies the top-center focal position, but does not participate in Build W_S. This consumes hierarchy and whitespace without helping explain the operation.

**Required change:** demote Sender for this scene.

Preferred:

- remove Sender from the center of this checkpoint entirely; or
- place a small sender badge near the title/header, not on the main mathematical stage.

The Build W_S canvas should visually center on the recipient public matrices.

---

## 2.3 Result-state edges imply the wrong causal source

In the result screenshot, the blue curves connect **u2/u4 avatars directly to W_S** after W2/W4 matrix glyphs disappear.

This visually says:

`user -> W_S`

But the mathematical operation is:

`W2 + W4 -> W_S`

This is the most important visual correction.

**Required change:** flow edges must be owned by matrix objects, not by user avatars.

Before aggregation:

`u2 -> W2` and `u4 -> W4` may be thin local ownership connectors.

During/after aggregation:

`W2 -> aggregate` and `W4 -> aggregate` are the causal paths.

After result creation, keep small ghost/source matrix thumbnails (or a compact derivation row) so the viewer can still see the inputs that produced W_S.

Do not leave direct avatar-to-result curves.

---

## 2.4 The visual merge is still too “object movement” and not enough “matrix operation”

The ready state with overlapped matrix cards is better than V1, but the composition still reads like two draggable UI cards stacked on each other.

We want the PPT/research-diagram grammar to be clearer:

```text
matrix W2     +     matrix W4
        \           /
         \         /
            W_S
```

The plus sign is allowed because it is a mathematical operator, not explanatory prose.

**Required change:** once both matrices are placed, snap them into a clean derivation composition:

```text
      [matrix W2]   +   [matrix W4]
                 Compute
                    ↓
                [matrix W_S]
```

This is more diagrammatic and less like a drag-drop application.

The drag interaction remains real; the *settled composition* becomes publication/PPT-like.

---

## 2.5 W1/W3 are too visually similar to active content

Inactive users/matrices are useful context, but they currently consume too much stage width and remain visually “present” enough to compete with W2/W4.

**Required change:** retain them as context but demote them:

- move u1/u3 closer to side margins;
- reduce matrix opacity to about 28–35%;
- use neutral gray rather than pale blue;
- do not draw long ownership connectors for inactive users unless hovered;
- no visible labels by default except small `u1/u3`.

Selected recipients should dominate.

---

## 2.6 Formula / Implementation buttons are too visually heavy

The large filled blue buttons at lower-right look like application controls and compete with the mathematical scene.

**Required change:** make both tertiary controls.

Suggested style:

- white or transparent background;
- 1px neutral border;
- muted text;
- small icon;
- only blue on hover/active.

They should look like optional drill-down, not primary actions.

`Compute W_S` remains the only strong action in this scene.

---

## 2.7 Bottom task strip is still too software-like

The bottom strip is much better than V1 but still reads as application chrome.

**Required change:** reduce its height by ~25–35% and remove status-log language such as

`build_ws() executed -> W_S matches build_ws() ✓`

from the permanent visible presentation surface.

That message is useful for developer/debug mode, not classroom mode.

Classroom mode should show only a concise task hint such as:

`Combine the public matrices of the recipients in S.`

A developer mode may retain backend verification text.

---

# 3. Revised Build W_S composition

## Initial state

```text
CHW25 Broadcast Encryption                         S = {2,4}
Build the aggregate public matrix


      inactive                       inactive
        u1           u2                 u3           u4
                     ◎                               ◎
                     │                               │
                  ┌────────┐                      ┌────────┐
                  │ matrix │                      │ matrix │
                  │   W2   │                      │   W4   │
                  └────────┘                      └────────┘


                     ┌  aggregation focus  ┐
                     │                      │
                     └                      ┘
```

Selected users and matrices occupy the central ~60% of the canvas. u1/u3 live near the margins as context.

## One matrix placed

```text
                     [matrix W2]
                           +
                     [ghost matrix]

                    1 / 2 matrices
```

No long line from u2 to the aggregation area. The W2 glyph itself is the object that moved.

## Ready state

Snap into a clean mathematical arrangement:

```text
                 [matrix W2]  +  [matrix W4]

                         Compute W_S
                              ↓
```

Do not keep them awkwardly overlapping once both are placed.

## Result state

```text
          [small ghost W2]  +  [small ghost W4]
                         ↓

                    ┌──────────┐
                    │  matrix  │
                    │   W_S    │
                    └──────────┘

                       4 × 8
```

The source matrices remain visible at low opacity for derivation memory.

The formula annotation `W_S = W2 + W4` appears briefly or on Formula request; it is not required permanently.

---

# 4. Motion language for this pass

Use only these motions:

1. **pick up** — selected matrix rises 4 px / slight shadow;
2. **move** — drag follows pointer;
3. **snap** — matrix settles into derivation slot;
4. **align** — W2/W4 arrange into left/right operands;
5. **combine** — both patterns briefly compress toward center;
6. **resolve** — W_S matrix expands out from the center;
7. **memory** — small ghost W2/W4 remain above result.

Do not add decorative motion.

---

# 5. Classroom vs Developer mode

Introduce a lightweight presentation mode distinction now to avoid future UI conflict.

## Classroom mode (default)

Visible:

- mathematical canvas;
- current task;
- contextual action;
- Formula / Implementation tertiary buttons;
- compact metadata only when useful.

Hidden:

- fingerprints by default;
- backend verification log;
- helper-matching debug strings.

## Developer mode

May show:

- matrix fingerprints;
- `build_ws()` equality check;
- source mappings;
- raw variable inspector.

This prevents implementation evidence from degrading presentation design.

---

# 6. Acceptance screenshots for refinement pass

Produce only these five images:

1. `v2r_01_initial.png` — enlarged, compressed composition, sender demoted, active recipients dominant;
2. `v2r_02_one_matrix.png` — W2 in operand slot + ghost missing operand;
3. `v2r_03_ready_equation.png` — W2 matrix + W4 matrix in clean left/right operand composition with a plus sign;
4. `v2r_04_result_memory.png` — W_S output with small ghost W2/W4 retained as derivation memory; no avatar->W_S curves;
5. `v2r_05_classroom.png` — classroom mode, no fingerprints/debug log, Formula/Implementation visually tertiary.

Also provide one `hide_matrix_labels=True` screenshot again.

---

# 7. Gate

Do **not** start Cancellation until this refinement passes visual review.

The Build W_S checkpoint is accepted only when the result looks like a **living lecture/research diagram** rather than a sparse drag-drop application.
