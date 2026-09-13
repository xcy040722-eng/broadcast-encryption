"""CHW25 DBE — Manim 算法动画（经典场景：N=4, S={2,4}, user=u2, μ=1）。

设计原则：
- **少文字、以对象运动表达算法**；每段最多一个标题 + 一个核心公式。
- 所有数值来自 `trace_adapter.build_scene_data`（真实运行），Manim 不做密码学计算。
- 不使用 LaTeX（避免依赖）；全部用 Pango `Text` + **ASCII 记法**（规避字形缺失）。
  记法：s^T p、c2^T r2、W0+WS、mu*floor(q/2)、e~1、e~2、y_ii、y_ji。

渲染：见 render_demo.py
"""

from __future__ import annotations

import numpy as np
from manim import (
    UP, DOWN, LEFT, RIGHT, ORIGIN,
    Arrow, Circle, Create, DashedLine, Dot, FadeIn, FadeOut,
    ImageMobject, Indicate, LaggedStart, Line, NumberLine, RoundedRectangle,
    Scene, Square, Text, Transform, VGroup,
)

try:  # 作为包导入
    from .trace_adapter import build_scene_data
except ImportError:  # manim CLI 直接加载该文件
    import os as _os
    import sys as _sys

    _HERE = _os.path.dirname(_os.path.abspath(__file__))
    _ROOT = _os.path.abspath(_os.path.join(_HERE, "..", ".."))
    for _p in (_HERE, _ROOT):
        if _p not in _sys.path:
            _sys.path.insert(0, _p)
    from trace_adapter import build_scene_data

# ---------- 配色 ----------
BG = "#0f1420"
C_TITLE = "#7fb3ff"
C_PARAM = "#4dabf7"      # A, p
C_PUB = "#38d9a9"        # W
C_SEC = "#ff922b"        # y (secret / opening)
C_RECIP = "#51cf66"      # authorized
C_NONREC = "#5c6773"     # non-recipient
C_CT = "#ffd43b"         # ciphertext
C_COMMON = "#e64980"     # 公共项（待划消）
C_RESULT = "#3fb950"
C_DIM = "#cfe3ff"

FONT = "Segoe UI"        # 显式字体，避免默认衬线 + 字形缺失

VERSE = 0.62             # 常规动画时长


def T(s: str, size: int = 30, color: str = "#e6edf3") -> Text:
    """统一的文本构造（显式无衬线字体）。"""
    return Text(s, font=FONT, font_size=size, color=color)


def title(text: str) -> Text:
    return T(text, size=40, color=C_TITLE).to_edge(UP, buff=0.35)


def token(label: str, color: str, w: float = 1.5, h: float = 0.72, size: int = 26) -> VGroup:
    box = RoundedRectangle(
        width=w, height=h, corner_radius=0.14,
        stroke_color=color, stroke_width=2.5,
        fill_color=color, fill_opacity=0.16,
    )
    txt = T(label, size=size, color=color).move_to(box.get_center())
    return VGroup(box, txt)


def node(label: str, color: str, r: float = 0.42) -> VGroup:
    c = Circle(radius=r, stroke_color=color, stroke_width=2.5,
               fill_color=color, fill_opacity=0.18)
    t = T(label, size=26, color=color).move_to(c.get_center())
    return VGroup(c, t)


def user_grid_positions(n: int, y: float = 0.0, gap: float = 2.0):
    """N<=4 单行；N=5..8 两行。"""
    if n <= 4:
        return [((i - (n - 1) / 2) * gap, y, 0) for i in range(n)]
    cols = int(np.ceil(n / 2))
    pos = []
    for i in range(n):
        r, c = divmod(i, cols)
        pos.append(((c - (cols - 1) / 2) * gap, y + 0.9 - r * 1.8, 0))
    return pos


class CHW25Scene(Scene):
    """Setup → KeyGen → Select S → Encrypt → Broadcast
    → u2 授权 → Cancellation → Threshold → Hybrid。"""

    def construct(self):
        self.camera.background_color = BG
        try:
            from demo.media_data import PNG_BYTES
            media = PNG_BYTES
        except Exception:
            media = None
        d = build_scene_data(N=4, s_set={2, 4}, mu=1, focus_user=2,
                             media_bytes=media, media_name="recovered.png")
        self.data = d

        self.sec_setup(d)
        self.sec_keygen(d)
        self.sec_select_s(d)
        self.sec_encrypt(d)
        self.sec_broadcast(d)
        self.sec_authorized(d)
        self.sec_cancellation(d)
        self.sec_threshold(d)
        self.sec_hybrid(d)
        self.wait(0.6)

    # ---------------- ① Setup ----------------
    def sec_setup(self, d):
        t = title("Setup")
        self.play(FadeIn(t, shift=DOWN * 0.3), run_time=0.5)

        A = RoundedRectangle(width=2.7, height=1.5, corner_radius=0.16,
                             stroke_color=C_PARAM, stroke_width=3,
                             fill_color=C_PARAM, fill_opacity=0.14)
        A_txt = VGroup(
            T("A", size=46, color=C_PARAM),
            T(f"shape {tuple(d['A_shape'])}", size=22, color="#8b9bb4"),
            T(f"head {d['A_head']}", size=20, color="#8b9bb4"),
        ).arrange(DOWN, buff=0.08).move_to(A.get_center())
        A_grp = VGroup(A, A_txt).move_to(LEFT * 3.0)

        p_box = RoundedRectangle(width=2.4, height=0.95, corner_radius=0.14,
                                 stroke_color=C_PARAM, stroke_width=3,
                                 fill_color=C_PARAM, fill_opacity=0.14)
        p_txt = VGroup(
            T("p", size=40, color=C_PARAM),
            T(f"shape {tuple(d['p_shape'])}", size=20, color="#8b9bb4"),
        ).arrange(DOWN, buff=0.04).move_to(p_box.get_center())
        p_grp = VGroup(p_box, p_txt).move_to(RIGHT * 2.6)

        self.play(FadeIn(A_grp, scale=0.85), run_time=0.8)
        self.play(FadeIn(p_grp, shift=LEFT * 0.6), run_time=VERSE)
        self.wait(0.3)
        self.play(FadeOut(t), FadeOut(A_grp), FadeOut(p_grp), run_time=0.5)

    # ---------------- ② KeyGen ----------------
    def sec_keygen(self, d):
        t = title("KeyGen")
        self.play(FadeIn(t), run_time=0.4)

        pos = user_grid_positions(len(d["users"]), y=0.6)
        users = VGroup(*[node(f"u{u['id']}", C_NONREC) for u in d["users"]])
        for nd, p in zip(users, pos):
            nd.move_to(p)
        self.play(LaggedStart(*[FadeIn(u, scale=0.6) for u in users], lag_ratio=0.15),
                  run_time=0.9)

        created = VGroup()
        pairs = []
        for u, nd in zip(d["users"], users):
            y_tok = token(f"y{u['id']}{u['id']}", C_SEC, w=1.2, h=0.56, size=22)
            w_tok = token(f"W{u['id']}", C_PUB, w=1.0, h=0.56, size=22)
            y_tok.next_to(nd, DOWN, buff=0.5).shift(LEFT * 0.72)
            w_tok.next_to(nd, DOWN, buff=0.5).shift(RIGHT * 0.72)
            created.add(y_tok, w_tok)
            pairs.append((y_tok, w_tok))

        formula = T("A . y_ii  =  W_i r_i + p", size=30, color=C_DIM).to_edge(DOWN, buff=0.5)
        self.play(LaggedStart(*[FadeIn(g, scale=0.6) for g in created], lag_ratio=0.12),
                  run_time=1.3)
        self.play(FadeIn(formula), run_time=0.45)
        for y_tok, w_tok in pairs:
            self.play(Indicate(y_tok, color=C_PARAM, scale_factor=1.18), run_time=0.2)
            self.play(Indicate(w_tok, color=C_PUB, scale_factor=1.22), run_time=0.2)
        self.wait(0.25)

        self.play(FadeOut(t), FadeOut(formula), FadeOut(users), FadeOut(created),
                  run_time=0.55)

    # ---------------- ③ Select S ----------------
    def sec_select_s(self, d):
        t = title("Select S")
        self.play(FadeIn(t), run_time=0.4)

        pos = user_grid_positions(len(d["users"]), y=0.6)
        users = VGroup(*[node(f"u{u['id']}",
                              C_RECIP if u["is_recipient"] else C_NONREC)
                         for u in d["users"]])
        for nd, p in zip(users, pos):
            nd.move_to(p)
        self.play(LaggedStart(*[FadeIn(u, scale=0.6) for u in users], lag_ratio=0.12),
                  run_time=0.85)
        # recipient_ids 是 1-based；users 是 0-based VGroup
        self.play(*[Indicate(users[i - 1], color=C_RECIP, scale_factor=1.25)
                    for i in d["recipient_ids"]], run_time=0.75)

        w2 = token("W2", C_PUB, w=1.0, h=0.6).next_to(users[1], UP, buff=0.4)
        w4 = token("W4", C_PUB, w=1.0, h=0.6).next_to(users[3], UP, buff=0.4)
        merged = VGroup(w2, w4)
        self.play(FadeIn(merged), run_time=0.45)

        target = UP * 2.4
        self.play(w2.animate.move_to(target + LEFT * 0.42),
                  w4.animate.move_to(target + RIGHT * 0.42), run_time=0.75)

        ws = token("W_S", C_PUB, w=1.4, h=0.68).move_to(target)
        self.play(Transform(merged, ws), run_time=0.8)
        formula = T("W_S  =  W2 + W4", size=30, color=C_DIM).to_edge(DOWN, buff=0.5)
        self.play(Indicate(merged, color="#74c0fc", scale_factor=1.18),
                  FadeIn(formula), run_time=0.55)
        self.wait(0.3)

        # 关键：fade out 的是被 Transform 的 merged（真正在场景里的对象）
        self.play(FadeOut(t), FadeOut(users), FadeOut(merged), FadeOut(formula),
                  run_time=0.55)

    # ---------------- ④ Encrypt ----------------
    def sec_encrypt(self, d):
        t = title("Encrypt")
        self.play(FadeIn(t), run_time=0.4)

        s_tok = token("s", C_PARAM, w=0.9, h=0.6).move_to(LEFT * 7.6)
        e_tok = token("e", C_SEC, w=0.9, h=0.6).move_to(RIGHT * 7.6)
        self.play(s_tok.animate.move_to(LEFT * 4.9 + UP * 1.7),
                  e_tok.animate.move_to(RIGHT * 4.9 + UP * 1.7), run_time=0.8)

        src = [("A", C_PARAM), ("W0+WS", C_PUB), ("p", C_PARAM)]
        outs = [("c1", d["ct"]["c1"][0]), ("c2", d["ct"]["c2"][0]), ("c3", d["ct"]["c3"])]
        ys = [1.15, 0.0, -1.15]
        paths = VGroup()
        for (name, col), (oname, oval), y in zip(src, outs, ys):
            src_tok = token(name, col, w=1.5, h=0.6, size=23).move_to(LEFT * 4.9 + UP * y)
            out_tok = token(f"{oname}={oval}", C_CT, w=2.7, h=0.62, size=20).move_to(
                RIGHT * 4.5 + UP * y)
            arr = Arrow(src_tok.get_right(), out_tok.get_left(),
                        buff=0.12, stroke_width=3, color="#3d5a80",
                        max_tip_length_to_length_ratio=0.08)
            paths.add(VGroup(src_tok, arr, out_tok))

        self.play(LaggedStart(*[FadeIn(g, shift=RIGHT * 0.3) for g in paths], lag_ratio=0.25),
                  run_time=1.5)
        self.wait(0.25)

        capsule = RoundedRectangle(width=5.2, height=1.0, corner_radius=0.3,
                                   stroke_color=C_CT, stroke_width=3,
                                   fill_color=C_CT, fill_opacity=0.16)
        cap_txt = T("ct = (xi, c1, c2, c3)", size=28, color=C_CT)
        cap = VGroup(capsule, cap_txt).move_to(DOWN * 2.5)
        self.play(FadeOut(paths), FadeOut(s_tok), FadeOut(e_tok),
                  FadeIn(cap, scale=0.8), run_time=0.85)
        self.play(Indicate(cap, color="#ffe066", scale_factor=1.08), run_time=0.5)
        self.wait(0.25)
        self.play(FadeOut(t), FadeOut(cap), run_time=0.5)

    # ---------------- ⑤ Broadcast ----------------
    def sec_broadcast(self, d):
        t = title("Broadcast")
        self.play(FadeIn(t), run_time=0.4)

        cap = token("ct", C_CT, w=1.6, h=0.9).move_to(UP * 1.5)
        self.play(FadeIn(cap, scale=0.7), run_time=0.45)

        pos = user_grid_positions(len(d["users"]), y=-1.9)
        users = VGroup(*[node(f"u{u['id']}",
                              C_RECIP if u["is_recipient"] else C_NONREC)
                         for u in d["users"]])
        for nd, p in zip(users, pos):
            nd.move_to(p)
        self.play(LaggedStart(*[FadeIn(u, scale=0.6) for u in users], lag_ratio=0.1),
                  run_time=0.8)

        ripples = VGroup()
        for k in range(3):
            c = Circle(radius=0.55 + k * 0.45, stroke_color=C_CT, stroke_width=2,
                       fill_opacity=0).move_to(cap.get_center())
            c.set_opacity(0.7 - k * 0.2)
            ripples.add(c)
        self.play(LaggedStart(*[Create(c) for c in ripples], lag_ratio=0.3), run_time=1.3)
        self.play(FadeOut(ripples), run_time=0.35)

        lines = VGroup(*[
            DashedLine(cap.get_bottom(), u.get_top(), dash_length=0.12,
                       stroke_color=C_RECIP if du["is_recipient"] else C_NONREC,
                       stroke_width=2.5, stroke_opacity=0.9)
            for u, du in zip(users, d["users"])
        ])
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.12), run_time=1.0)
        self.play(*[Indicate(users[i - 1], color=C_RECIP, scale_factor=1.3)
                    for i in d["recipient_ids"]], run_time=0.85)
        self.wait(0.35)
        self.play(FadeOut(t), FadeOut(cap), FadeOut(users), FadeOut(lines), run_time=0.55)

    # ---------------- ⑥ Authorized u2 ----------------
    def sec_authorized(self, d):
        uid = d["trace"]["user"]
        t = title(f"Authorized  u{uid}")
        self.play(FadeIn(t), run_time=0.4)

        sigma = node("SUM", C_RESULT, r=0.66).move_to(ORIGIN + DOWN * 0.25)
        self.play(FadeIn(sigma, scale=0.6), run_time=0.45)

        jobj = sorted(int(k) for k in d["trace"]["c1_dot_y_ji"].keys())
        sources = [
            (f"y{uid}{uid}", C_SEC, LEFT * 4.8 + UP * 1.9),
            (f"y0{uid}", C_SEC, LEFT * 4.8 + DOWN * 1.5),
        ]
        for j in jobj:
            sources.append((f"y{j}{uid}", C_SEC, RIGHT * 4.8 + UP * 1.9))

        toks = VGroup(*[
            token(name, col, w=1.5, h=0.62, size=22).move_to(p)
            for name, col, p in sources
        ])
        self.play(LaggedStart(*[FadeIn(tk, scale=0.6, shift=RIGHT * 0.2) for tk in toks],
                              lag_ratio=0.2), run_time=1.1)

        # 顺序吸收：每个 token 依次没入 SUM 节点（避免堆叠）
        for tk in toks:
            self.play(tk.animate.move_to(sigma.get_center()).set_opacity(0.0),
                      run_time=0.42)
            self.play(Indicate(sigma, color=C_RESULT, scale_factor=1.12), run_time=0.14)
        self.remove(toks)
        self.play(FadeOut(sigma[1]), run_time=0.22)   # 收起 SUM 文本，避免与 Y2 重叠
        y2 = token(f"Y{uid}", C_RESULT, w=1.5, h=0.7)
        y2.move_to(sigma.get_center())
        self.play(FadeIn(y2, scale=0.75),
                  Indicate(sigma[0], color=C_RESULT, scale_factor=1.15), run_time=0.7)
        y2_holder = VGroup(y2)

        terms = " + ".join([f"y{uid}{uid}", f"y0{uid}"] + [f"y{j}{uid}" for j in jobj])
        formula = T(f"Y{uid} = {terms}", size=28, color=C_DIM).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(formula), run_time=0.45)
        self.wait(0.35)

        # 标题一并交给下一段淡出（避免标题重叠）
        self.keep = {"title": t, "sigma": sigma, "y2": y2_holder, "formula": formula}

    # ---------------- ⑦ Cancellation（核心） ----------------
    def sec_cancellation(self, d):
        uid = d["trace"]["user"]
        tr = d["trace"]

        # 淡出上一段遗留（标题 / y2 / formula / sigma）
        leftover = VGroup(self.keep["title"], self.keep["y2"],
                          self.keep["formula"], self.keep["sigma"])

        t = title("Cancellation")
        self.play(FadeIn(t), FadeOut(leftover), run_time=0.55)

        L0 = T(f"L = c3 + c2^T r{uid}", size=30, color=C_DIM).move_to(LEFT * 3.7 + UP * 1.9)
        R0 = T(f"R = c1^T Y{uid}", size=30, color=C_DIM).move_to(RIGHT * 3.7 + UP * 1.9)
        self.play(FadeIn(L0, shift=DOWN * 0.2), FadeIn(R0, shift=DOWN * 0.2),
                  run_time=VERSE)
        self.wait(0.2)

        def expanded(rows, y0):
            grp = VGroup()
            for i, (txt, col) in enumerate(rows):
                grp.add(T(txt, size=26, color=col).move_to(y0 + DOWN * i * 0.5))
            return grp

        common = f"s^T (W0+WS) r{uid}"
        Lx = expanded([
            ("mu * floor(q/2)", "#e6edf3"),
            ("+ s^T p", C_COMMON),
            (f"+ {common}", C_COMMON),
            ("+ e~2", "#e6edf3"),
        ], LEFT * 3.7 + UP * 1.35)
        Rx = expanded([
            ("+ s^T p", C_COMMON),
            (f"+ {common}", C_COMMON),
            ("+ e~1", "#e6edf3"),
        ], RIGHT * 3.7 + UP * 1.6)

        self.play(Transform(L0, Lx), Transform(R0, Rx), run_time=1.1)
        self.wait(0.25)

        # 注意：Transform(A, B) 后，场景里的是 A（外观已变为 B）。
        # 因此后续操作与淡出都必须作用在 L0 / R0 上。
        L_common, R_common = L0[1:3], R0[0:2]
        conns = VGroup(*[
            DashedLine(a.get_right(), b.get_left(), dash_length=0.10,
                       stroke_color=C_COMMON, stroke_width=2.2)
            for a, b in zip(L_common, R_common)
        ])
        self.play(Create(conns), run_time=0.7)
        self.play(Indicate(L_common, color="#ff8fab", scale_factor=1.06),
                  Indicate(R_common, color="#ff8fab", scale_factor=1.06), run_time=0.65)
        self.play(L_common.animate.set_opacity(0.10),
                  R_common.animate.set_opacity(0.10),
                  conns.animate.set_opacity(0.0), run_time=0.9)
        self.wait(0.2)

        # 先淡出 L/R，再淡入结果（避免重叠）
        self.play(FadeOut(L0), FadeOut(R0), FadeOut(conns), run_time=0.45)

        z_txt = T(f"z = mu*floor(q/2) - e~1 + e~2  =  {tr['z_centered']}",
                  size=34, color=C_RESULT).move_to(ORIGIN + DOWN * 0.2)
        self.play(FadeIn(z_txt, scale=0.88), run_time=0.7)
        num = T(f"noise = {tr['noise_residual']}", size=26, color="#8b9bb4")
        num.next_to(z_txt, DOWN, buff=0.3)
        self.play(FadeIn(num), run_time=0.4)
        self.wait(0.55)
        self.z_obj = z_txt
        self.play(FadeOut(t), FadeOut(num), run_time=0.45)

    # ---------------- ⑧ Threshold ----------------
    def sec_threshold(self, d):
        tr = d["trace"]
        t = title("Threshold decoding")
        self.play(FadeIn(t), FadeOut(self.z_obj), run_time=0.5)

        nl = NumberLine(x_range=[-1, 1, 0.5], length=11.0, include_numbers=False,
                        stroke_width=2.5, color="#8b9bb4").move_to(DOWN * 0.3)
        labels = VGroup(*[
            T(lab, size=22, color="#8b9bb4").move_to(nl.n2p(frac) + DOWN * 0.45)
            for frac, lab in [(-1.0, "-q/2"), (-0.5, "-q/4"), (0.0, "0"),
                              (0.5, "q/4"), (1.0, "q/2")]
        ])
        band = Line(nl.n2p(-0.5), nl.n2p(0.5), stroke_width=10,
                    color=C_RESULT, stroke_opacity=0.35)
        self.play(Create(nl), FadeIn(labels), Create(band), run_time=0.85)

        zc = tr["z_centered"]
        frac = max(-1.0, min(1.0, zc / tr["half_q"]))
        mark = Dot(nl.n2p(0.0), radius=0.12, color=C_SEC)
        self.play(FadeIn(mark, scale=0.5), run_time=0.3)
        self.play(mark.animate.move_to(nl.n2p(frac)), run_time=1.1)

        mu_txt = T(f"z_centered = {zc}   ->   mu = {tr['decoded_mu']}",
                   size=30, color=C_RESULT).to_edge(DOWN, buff=0.85)
        ok_txt = T("(matches the encrypted bit)", size=22, color="#8b9bb4")
        ok_txt.next_to(mu_txt, DOWN, buff=0.16)
        self.play(FadeIn(mu_txt), FadeIn(ok_txt), run_time=0.55)
        self.wait(0.7)

        self.play(FadeOut(t), FadeOut(nl), FadeOut(labels), FadeOut(band),
                  FadeOut(mark), FadeOut(mu_txt), FadeOut(ok_txt), run_time=0.55)

    # ---------------- ⑨ Hybrid ----------------
    def sec_hybrid(self, d):
        t = title("Hybrid  ·  DBE -> AES-256 -> Media")
        self.play(FadeIn(t), run_time=0.4)

        h = d["hybrid"] or {"bit_count": 256, "key_fingerprint": d["keyset_id"][:8],
                            "key_length_bytes": 32, "match": None,
                            "recovered_image_path": None}

        n, cell = 16, 0.20
        grid = VGroup()
        for r in range(n):
            for c in range(n):
                sq = Square(side_length=cell * 0.86, stroke_width=0,
                            fill_color=C_CT, fill_opacity=0.25)
                sq.move_to(LEFT * 3.5 + RIGHT * c * cell + UP * 2.0 + DOWN * r * cell)
                grid.add(sq)
        self.play(FadeIn(grid), run_time=0.45)
        self.play(LaggedStart(*[c.animate.set_fill(C_RECIP, opacity=0.95) for c in grid],
                              lag_ratio=0.0015), run_time=2.0)

        key_tok = token("AES-256 Session Key", C_RECIP, w=4.2, h=0.9, size=25)
        key_tok.move_to(LEFT * 3.5 + DOWN * 0.7)
        fp = T(f"sha256[:8] = {h['key_fingerprint']}   (key bytes hidden)",
               size=20, color="#8b9bb4").next_to(key_tok, DOWN, buff=0.2)
        # grid 变为 key token 的外观；之后**只操作 grid**（避免对象重复入场景）
        self.play(Transform(grid, key_tok), FadeIn(fp), run_time=1.0)

        img_path = h.get("recovered_image_path")
        if img_path:
            try:
                img = ImageMobject(img_path)
                img.height = 2.3
                img.move_to(RIGHT * 3.7 + DOWN * 0.5)
                frame = RoundedRectangle(width=img.width + 0.3, height=img.height + 0.3,
                                         corner_radius=0.12, stroke_color="#8b9bb4",
                                         stroke_width=2, fill_opacity=0)
                frame.move_to(img.get_center())
                lock = VGroup(
                    RoundedRectangle(width=1.1, height=0.8, corner_radius=0.12,
                                     stroke_color=C_SEC, stroke_width=3,
                                     fill_color=C_SEC, fill_opacity=0.2),
                    T("LOCKED", size=20, color=C_SEC),
                )
                lock[1].move_to(lock[0].get_center())
                lock.move_to(img.get_center())
                self.play(FadeIn(frame), FadeIn(lock), run_time=0.5)
                self.play(grid.animate.move_to(frame.get_left() + LEFT * 0.3),
                          run_time=0.85)
                self.play(FadeOut(lock, scale=0.5), FadeIn(img, scale=0.92), run_time=0.85)
                ok = T("recovered", size=24, color=C_RESULT).next_to(frame, DOWN, buff=0.2)
                self.play(FadeIn(ok), run_time=0.4)
            except Exception:
                pass

        self.wait(0.9)
        self.play(FadeOut(t), run_time=0.4)
