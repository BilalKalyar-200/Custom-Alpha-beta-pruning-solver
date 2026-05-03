import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import math
import time
import random

# ─── Color Theme ────────────────────────────────────────────────────────────
BG        = "#1e1e2e"
BG2       = "#2a2a3d"
BG3       = "#16213e"
ACCENT    = "#7c3aed"
ACCENT2   = "#a855f7"
MAX_COL   = "#3b82f6"
MIN_COL   = "#ef4444"
LEAF_COL  = "#10b981"
PRUNED_BG = "#374151"
PRUNED_FG = "#6b7280"
BEST_COL  = "#f59e0b"
ACTIVE_COL= "#8b5cf6"
TEXT      = "#e2e8f0"
TEXT2     = "#94a3b8"
BORDER    = "#334155"
GREEN     = "#22c55e"
RED       = "#ef4444"
PANEL_BG  = "#0f172a"

# ─── Node ────────────────────────────────────────────────────────────────────
_id_counter = 0
def new_id():
    global _id_counter
    _id_counter += 1
    return _id_counter

class Node:
    def __init__(self, is_max=True, depth=0, value=None):
        self.id       = new_id()
        self.is_max   = is_max
        self.depth    = depth
        self.value    = value          # int if leaf, else None until evaluated
        self.children = []
        # algorithm state
        self.alpha    = -math.inf
        self.beta     =  math.inf
        self.result   = None
        self.state    = "idle"         # idle | active | evaluated | pruned | best
        self.best_child_id = None
        # canvas
        self.cx = 0
        self.cy = 0

    def is_leaf(self):
        return len(self.children) == 0

    def add_child(self, root_is_max):
        child_is_max = not self.is_max
        child_depth  = self.depth + 1
        c = Node(is_max=child_is_max, depth=child_depth,
                 value=random.randint(-9, 9))
        self.children.append(c)
        return c

    def remove_child(self):
        if self.children:
            self.children.pop()

    def reset_algo_state(self):
        self.alpha    = -math.inf
        self.beta     =  math.inf
        self.result   = None
        self.state    = "idle"
        self.best_child_id = None
        for c in self.children:
            c.reset_algo_state()


# ─── Tree Builder ─────────────────────────────────────────────────────────────
def build_tree(depth, branch, is_max=True, current_depth=0):
    n = Node(is_max=is_max, depth=current_depth)
    if current_depth < depth:
        for _ in range(branch):
            child = build_tree(depth, branch, not is_max, current_depth+1)
            n.children.append(child)
    else:
        n.value = random.randint(-9, 9)
    return n


# ─── Alpha-Beta Step Generator ────────────────────────────────────────────────
def generate_steps(root):
    steps = []

    def ab(node, alpha, beta):
        steps.append({"type": "visit", "id": node.id,
                       "alpha": alpha, "beta": beta,
                       "msg": f"{'MAX' if node.is_max else 'MIN'} node (depth {node.depth}) — visiting  |  α={'−∞' if alpha==-math.inf else alpha}  β={'+∞' if beta==math.inf else beta}"})
        if node.is_leaf():
            steps.append({"type": "leaf", "id": node.id, "val": node.value,
                           "msg": f"Leaf node → returns {node.value}"})
            return node.value

        best       = -math.inf if node.is_max else math.inf
        best_cid   = None
        local_a, local_b = alpha, beta

        for i, child in enumerate(node.children):
            val = ab(child, local_a, local_b)
            if node.is_max:
                if val > best:
                    best, best_cid = val, child.id
                local_a = max(local_a, best)
            else:
                if val < best:
                    best, best_cid = val, child.id
                local_b = min(local_b, best)

            steps.append({"type": "update", "id": node.id,
                           "val": best, "alpha": local_a, "beta": local_b,
                           "best_cid": best_cid,
                           "msg": f"{'MAX' if node.is_max else 'MIN'} updates value to {best}  |  α={'−∞' if local_a==-math.inf else local_a}  β={'+∞' if local_b==math.inf else local_b}"})

            if local_b <= local_a:
                remaining = node.children[i+1:]
                for rem in remaining:
                    _mark_prune(rem, steps)
                steps.append({"type": "cutoff", "id": node.id,
                               "msg": f"✂ Alpha-Beta cutoff! α={local_a}  β={local_b} — pruning {len(remaining)} subtree(s)"})
                break

        steps.append({"type": "done", "id": node.id, "val": best,
                       "best_cid": best_cid,
                       "msg": f"{'MAX' if node.is_max else 'MIN'} node complete → returns {best}"})
        return best

    ab(root, -math.inf, math.inf)
    return steps


def _mark_prune(node, steps):
    steps.append({"type": "prune", "id": node.id,
                   "msg": f"Subtree pruned (not explored)"})
    for c in node.children:
        _mark_prune(c, steps)


# ─── Main App ─────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Alpha-Beta Minimax Simulator")
        self.configure(bg=BG)
        self.minsize(1100, 700)
        self.state("zoomed")  # start maximized

        self.root_node  = None
        self.steps      = []
        self.step_idx   = -1
        self.node_map   = {}
        self.anim_id    = None
        self.selected   = None   # selected node id

        self._build_ui()
        self._new_tree()
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self._zoom_scale = getattr(self, '_zoom_scale', 1.0) * factor
        self._zoom_scale = max(0.3, min(3.0, self._zoom_scale))
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        self.canvas.scale("all", cx, cy, factor, factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _pan_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _pan_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # ── top bar ──
        top = tk.Frame(self, bg=BG3, pady=8)
        top.pack(fill=tk.X)

        tk.Label(top, text="⬡  Alpha-Beta Minimax", bg=BG3,
                 fg=ACCENT2, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=16)

        # controls
        ctrl = tk.Frame(top, bg=BG3)
        ctrl.pack(side=tk.LEFT, padx=20)

        def lbl(t): return tk.Label(ctrl, text=t, bg=BG3, fg=TEXT2, font=("Segoe UI", 10))
        def spin(var, lo, hi, w=4):
            s = tk.Spinbox(ctrl, textvariable=var, from_=lo, to=hi, width=w,
                           bg=BG2, fg=TEXT, insertbackground=TEXT,
                           buttonbackground=BG2, relief="flat",
                           font=("Segoe UI", 10), highlightbackground=BORDER,
                           highlightthickness=1)
            return s

        self.v_depth  = tk.IntVar(value=3)
        self.v_branch = tk.IntVar(value=3)
        self.v_root   = tk.StringVar(value="MAX")

        lbl("Depth").pack(side=tk.LEFT, padx=(0,2))
        spin(self.v_depth, 1, 4).pack(side=tk.LEFT, padx=(0,10))
        lbl("Branch").pack(side=tk.LEFT, padx=(0,2))
        spin(self.v_branch, 2, 5).pack(side=tk.LEFT, padx=(0,10))
        lbl("Root").pack(side=tk.LEFT, padx=(0,2))
        om = ttk.OptionMenu(ctrl, self.v_root, "MAX", "MAX", "MIN")
        om.config(width=4)
        om.pack(side=tk.LEFT, padx=(0,10))

        def btn(parent, text, cmd, color=ACCENT, fg=TEXT, w=14):
            b = tk.Button(parent, text=text, command=cmd,
                          bg=color, fg=fg, relief="flat",
                          font=("Segoe UI", 10, "bold"),
                          padx=8, pady=4, cursor="hand2",
                          activebackground=ACCENT2, activeforeground=TEXT,
                          width=w)
            return b

        btn(ctrl, "🌲 New Tree", self._new_tree, ACCENT).pack(side=tk.LEFT, padx=3)
        btn(ctrl, "🎲 Randomize", self._randomize, "#0f766e").pack(side=tk.LEFT, padx=3)
        btn(ctrl, "↺ Reset", self._reset_algo, "#7c3aed").pack(side=tk.LEFT, padx=3)

        # right side buttons
        right = tk.Frame(top, bg=BG3)
        right.pack(side=tk.RIGHT, padx=16)

        self.btn_instant = btn(right, "⚡ Show Result", self._run_instant, "#b45309", w=14)
        self.btn_instant.pack(side=tk.LEFT, padx=4)
        self.btn_step = btn(right, "▶ Step by Step", self._start_step, GREEN, w=14)
        self.btn_step.pack(side=tk.LEFT, padx=4)

        # ── main area ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        # canvas pane
        canvas_frame = tk.Frame(main, bg=BG)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=PANEL_BG, highlightthickness=0)
        hbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL,   command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_zoom)
        self.canvas.bind("<ButtonPress-2>", self._pan_start)
        self.canvas.bind("<B2-Motion>", self._pan_move)

        # right panel
        rp = tk.Frame(main, bg=BG2, width=310, padx=12, pady=12)
        rp.pack(side=tk.RIGHT, fill=tk.Y)
        rp.pack_propagate(False)

        tk.Label(rp, text="Step Log", bg=BG2, fg=ACCENT2,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")

        self.log_box = tk.Text(rp, bg=BG3, fg=TEXT, font=("Consolas", 10),
                               relief="flat", wrap=tk.WORD, state=tk.DISABLED,
                               highlightthickness=0)
        log_scroll = tk.Scrollbar(rp, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=(6,10))

        # step controls
        sc = tk.Frame(rp, bg=BG2)
        sc.pack(fill=tk.X, pady=4)
        self.btn_prev = btn(sc, "◀ Prev", self._prev_step, BG3, TEXT2, w=8)
        self.btn_prev.pack(side=tk.LEFT, padx=(0,4))
        self.btn_next = btn(sc, "Next ▶", self._next_step, GREEN, TEXT, w=8)
        self.btn_next.pack(side=tk.LEFT)

        self.step_label = tk.Label(rp, text="", bg=BG2, fg=TEXT2,
                                    font=("Segoe UI", 10))
        self.step_label.pack(anchor="w", pady=2)

        # node editor
        tk.Frame(rp, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
        tk.Label(rp, text="Node Editor", bg=BG2, fg=ACCENT2,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")

        self.editor_frame = tk.Frame(rp, bg=BG2)
        self.editor_frame.pack(fill=tk.X, pady=6)

        tk.Label(self.editor_frame, text="Click a node on the tree\nto edit it here.",
                 bg=BG2, fg=TEXT2, font=("Segoe UI", 10), justify="left").pack(anchor="w")

        # legend
        tk.Frame(rp, bg=BORDER, height=1).pack(fill=tk.X, pady=8)
        tk.Label(rp, text="Legend", bg=BG2, fg=ACCENT2,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0,4))
        for col, lbl in [(MAX_COL,"MAX node"), (MIN_COL,"MIN node"),
                          (LEAF_COL,"Leaf (idle)"), (BEST_COL,"Best path"),
                          (ACTIVE_COL,"Currently active"),
                          (PRUNED_FG,"Pruned (skipped)"), (GREEN,"Evaluated")]:
            row = tk.Frame(rp, bg=BG2)
            row.pack(anchor="w", pady=1)
            tk.Canvas(row, bg=BG2, width=14, height=14,
                      highlightthickness=0).pack(side=tk.LEFT, padx=(0,6))
            c2 = row.winfo_children()[0]
            c2.create_oval(2,2,13,13, fill=col, outline="")
            tk.Label(row, text=lbl, bg=BG2, fg=TEXT2,
                     font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # style ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TMenubutton", background=BG2, foreground=TEXT,
                         relief="flat", font=("Segoe UI",10))

    # ── Tree Actions ──────────────────────────────────────────────────────────
    def _new_tree(self):
        if self.anim_id:
            self.after_cancel(self.anim_id); self.anim_id=None
        d = self.v_depth.get()
        b = self.v_branch.get()
        r = self.v_root.get() == "MAX"
        self.root_node = build_tree(d, b, r)
        self.node_map  = {}
        self._collect_nodes(self.root_node)
        self.steps   = []
        self.step_idx = -1
        self._draw()
        self._log_clear()
        self._log("🌲 New tree built. Click a node to select/edit it.\n"
                  "Use ⚡ Show Result for instant answer\nor ▶ Step by Step to walk through.")
        self.step_label.config(text="")

    def _collect_nodes(self, n):
        self.node_map[n.id] = n
        for c in n.children:
            self._collect_nodes(c)

    def _randomize(self):
        def rnd(n):
            if n.is_leaf(): n.value = random.randint(-9, 9)
            for c in n.children: rnd(c)
        rnd(self.root_node)
        self.steps=[]; self.step_idx=-1
        self.root_node.reset_algo_state()
        self._draw()
        self._log_clear()
        self._log("🎲 Leaf values randomized.")

    def _reset_algo(self):
        if self.anim_id: self.after_cancel(self.anim_id); self.anim_id=None
        self.steps=[]; self.step_idx=-1
        self.root_node.reset_algo_state()
        self._draw()
        self._log_clear()
        self._log("↺ Algorithm state reset.")
        self.step_label.config(text="")

    # ── Algorithm ─────────────────────────────────────────────────────────────
    def _ensure_steps(self):
        if not self.steps:
            self.root_node.reset_algo_state()
            self.steps = generate_steps(self.root_node)

    def _run_instant(self):
        self._ensure_steps()
        self.step_idx = len(self.steps)-1
        msg = self._apply_steps(self.step_idx)
        self._draw()
        self._log_clear()
        for i, s in enumerate(self.steps):
            self._log(f"[{i+1:03d}] {s['msg']}\n")
        self._log(f"\n✅ Optimal value: {self.root_node.result}")
        self.step_label.config(text=f"All {len(self.steps)} steps shown")

    def _start_step(self):
        self._ensure_steps()
        self.step_idx = -1
        self.root_node.reset_algo_state()
        self._draw()
        self._log_clear()
        self._log("▶ Step-by-step mode. Use 'Next ▶' to advance.\n")
        self.step_label.config(text=f"Step 0 / {len(self.steps)}")

    def _next_step(self):
        self._ensure_steps()
        if self.step_idx < len(self.steps)-1:
            self.step_idx += 1
            self._apply_steps(self.step_idx)
            self._draw()
            s = self.steps[self.step_idx]
            self._log(f"[{self.step_idx+1:03d}] {s['msg']}\n")
            self.step_label.config(text=f"Step {self.step_idx+1} / {len(self.steps)}")

    def _prev_step(self):
        if self.step_idx > 0:
            self.step_idx -= 1
            self.root_node.reset_algo_state()
            self._apply_steps(self.step_idx)
            self._draw()
            s = self.steps[self.step_idx]
            self._log_clear()
            for i in range(self.step_idx+1):
                self._log(f"[{i+1:03d}] {self.steps[i]['msg']}\n")
            self.step_label.config(text=f"Step {self.step_idx+1} / {len(self.steps)}")
        elif self.step_idx == 0:
            self.step_idx = -1
            self.root_node.reset_algo_state()
            self._draw()
            self._log_clear()
            self._log("↺ Back to start.")
            self.step_label.config(text=f"Step 0 / {len(self.steps)}")

    def _apply_steps(self, up_to):
        pruned_ids, best_ids, eval_ids, active_id = set(), set(), set(), None
        for i in range(up_to+1):
            s = self.steps[i]
            n = self.node_map.get(s["id"])
            if not n: continue
            t = s["type"]
            if t == "visit":
                n.alpha = s["alpha"]; n.beta = s["beta"]
                active_id = n.id
            elif t == "leaf":
                n.result = s["val"]; eval_ids.add(n.id)
            elif t == "update":
                n.result = s["val"]; n.alpha = s["alpha"]; n.beta = s["beta"]
                n.best_child_id = s.get("best_cid")
                if n.best_child_id: best_ids.add(n.best_child_id)
            elif t == "prune":
                pruned_ids.add(n.id)
            elif t == "done":
                n.result = s["val"]; eval_ids.add(n.id)
                if s.get("best_cid"): best_ids.add(s["best_cid"])
        # apply states
        def apply_state(node):
            if node.id in pruned_ids: node.state = "pruned"
            elif node.id == active_id: node.state = "active"
            elif node.id in best_ids and node.id not in pruned_ids: node.state = "best"
            elif node.id in eval_ids: node.state = "evaluated"
            else: node.state = "idle"
            for c in node.children: apply_state(c)
        apply_state(self.root_node)
        return self.steps[up_to]["msg"] if 0 <= up_to < len(self.steps) else ""

    # ── Drawing ───────────────────────────────────────────────────────────────
    NW, NH = 64, 40
    HGAP, VGAP = 16, 70

    def _draw(self):
        self.canvas.delete("all")
        self.canvas._buttons = []
        w = self._subtree_width(self.root_node)
        total_w = max(w + 60, 900)
        depth = self._tree_depth(self.root_node)
        total_h = (depth+1)*(self.NH+self.VGAP)+80
        self.canvas.config(scrollregion=(0,0,total_w,total_h))
        self._assign_pos(self.root_node, 30, total_w-30, 40)
        self._draw_edges(self.root_node)
        self._draw_nodes(self.root_node)

    def _subtree_width(self, n):
        if n.is_leaf(): return self.NW + self.HGAP
        return sum(self._subtree_width(c) for c in n.children)

    def _tree_depth(self, n):
        if n.is_leaf(): return 0
        return 1 + max(self._tree_depth(c) for c in n.children)

    def _assign_pos(self, n, left, right, y):
        n.cx = (left+right)/2
        n.cy = y + self.NH/2
        if n.is_leaf(): return
        w = (right-left)/len(n.children)
        for i, c in enumerate(n.children):
            self._assign_pos(c, left+i*w, left+(i+1)*w, y+self.NH+self.VGAP)

    def _draw_edges(self, n):
        for c in n.children:
            if c.state == "pruned":
                color, dash, width = PRUNED_FG, (6,4), 1
            elif c.state in ("best",):
                color, dash, width = BEST_COL, (), 3
            else:
                color, dash, width = "#475569", (), 1.5
            self.canvas.create_line(n.cx, n.cy+self.NH/2,
                                    c.cx, c.cy-self.NH/2,
                                    fill=color, width=width, dash=dash, smooth=True)
            self._draw_edges(c)

    def _draw_nodes(self, n):
        x, y = n.cx - self.NW/2, n.cy - self.NH/2
        nw, nh = self.NW, self.NH

        # background & border color
        state = n.state
        if state == "pruned":
            bg, border, lw = PRUNED_BG, PRUNED_FG, 1
        elif state == "active":
            bg, border, lw = "#1e1b4b", ACTIVE_COL, 3
        elif state == "best":
            bg, border, lw = "#1c1917", BEST_COL, 3
        elif state == "evaluated":
            bg, border, lw = "#052e16", GREEN, 2
        elif n.is_leaf():
            bg, border, lw = "#022c22", LEAF_COL, 1.5
        else:
            bg, border, lw = BG2, MAX_COL if n.is_max else MIN_COL, 1.5

        if n.id == self.selected:
            border, lw = "#e2e8f0", 3

        self.canvas.create_rectangle(x, y, x+nw, y+nh,
                                     fill=bg, outline=border,
                                     width=lw, tags=f"node_{n.id}")

        # type badge
        badge_col = MAX_COL if n.is_max else MIN_COL
        self.canvas.create_oval(x+4, y+4, x+14, y+14, fill=badge_col, outline="")
        self.canvas.create_text(x+9, y+9, text="▲" if n.is_max else "▼",
                                 font=("Segoe UI",6), fill="white")

        # main label
        if n.is_leaf():
            disp = str(n.value) if n.value is not None else "?"
            col  = TEXT
        elif n.result is not None:
            disp = str(n.result)
            col  = BEST_COL if state == "best" else GREEN
        else:
            disp = "MAX" if n.is_max else "MIN"
            col  = TEXT2

        self.canvas.create_text(n.cx+4, n.cy-2, text=disp,
                                  font=("Segoe UI",13,"bold"), fill=col)

        # alpha/beta under node (only when algo running)
        if not n.is_leaf() and n.alpha > -math.inf:
            ab_str = f"α={n.alpha}  β={'+∞' if n.beta==math.inf else n.beta}"
            self.canvas.create_text(n.cx, n.cy+nh/2+10, text=ab_str,
                                     font=("Consolas",8), fill=TEXT2)

        # +/- buttons for branch nodes
        if not n.is_leaf():
            self._draw_btn(x-18, n.cy-10, 16, 20, "+", n.id, "add")
            self._draw_btn(x-18, n.cy+2,  16, 20, "−", n.id, "rem")

        # pruned X
        if state == "pruned":
            self.canvas.create_line(x+2, y+2, x+nw-2, y+nh-2,
                                     fill=PRUNED_FG, width=1.5, dash=(3,2))
            self.canvas.create_line(x+nw-2, y+2, x+2, y+nh-2,
                                     fill=PRUNED_FG, width=1.5, dash=(3,2))

        for c in n.children:
            self._draw_nodes(c)

    def _draw_btn(self, x, y, w, h, label, nid, action):
        rx, ry = x, y
        btn_id = self.canvas.create_rectangle(rx, ry, rx+w, ry+h,
                                               fill="#334155", outline="#475569",
                                               width=1, tags=f"btn_{nid}_{action}")
        self.canvas.create_text(rx+w/2, ry+h/2, text=label,
                                  font=("Segoe UI",11,"bold"), fill=TEXT)
        self.canvas._buttons.append((rx, ry, rx+w, ry+h, nid, action))

    # ── Click Handling ────────────────────────────────────────────────────────
    def _on_canvas_click(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        # check buttons first
        for (x1,y1,x2,y2, nid, action) in self.canvas._buttons:
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                self._handle_btn(nid, action)
                return

        # check node click
        hit = self._hit_test(self.root_node, cx, cy)
        if hit:
            self.selected = hit.id
            self._show_editor(hit)
            self._draw()

    def _hit_test(self, n, cx, cy):
        if abs(n.cx - cx) < self.NW/2 and abs(n.cy - cy) < self.NH/2:
            return n
        for c in n.children:
            r = self._hit_test(c, cx, cy)
            if r: return r
        return None

    def _handle_btn(self, nid, action):
        n = self.node_map.get(nid)
        if not n: return
        if action == "add":
            new_c = n.add_child(self.root_node.is_max)
            self.node_map[new_c.id] = new_c
        elif action == "rem":
            if len(n.children) > 1:
                removed = n.children[-1]
                n.remove_child()
                # clean node_map
                def remove_ids(nd):
                    self.node_map.pop(nd.id, None)
                    for c in nd.children: remove_ids(c)
                remove_ids(removed)
        self.steps = []; self.step_idx = -1
        self.root_node.reset_algo_state()
        self._draw()

    # ── Node Editor Panel ─────────────────────────────────────────────────────
    def _show_editor(self, node):
        for w in self.editor_frame.winfo_children():
            w.destroy()

        def lbl(t, col=TEXT2):
            tk.Label(self.editor_frame, text=t, bg=BG2, fg=col,
                     font=("Segoe UI",10)).pack(anchor="w", pady=1)

        lbl(f"Node ID: {node.id}", ACCENT2)
        lbl(f"Type: {'MAX' if node.is_max else 'MIN'}")
        lbl(f"Depth: {node.depth}")
        lbl(f"Leaf: {'Yes' if node.is_leaf() else 'No'}")

        if node.is_leaf():
            tk.Frame(self.editor_frame, bg=BORDER, height=1).pack(fill=tk.X, pady=6)
            tk.Label(self.editor_frame, text="Leaf Value:", bg=BG2, fg=TEXT,
                     font=("Segoe UI",10,"bold")).pack(anchor="w")
            val_var = tk.StringVar(value=str(node.value) if node.value is not None else "0")
            entry = tk.Entry(self.editor_frame, textvariable=val_var,
                             bg=BG3, fg=TEXT, insertbackground=TEXT,
                             font=("Segoe UI",14,"bold"), relief="flat",
                             highlightbackground=ACCENT, highlightthickness=2,
                             width=8, justify="center")
            entry.pack(pady=4)
            entry.focus_set()
            entry.select_range(0, tk.END)

            def save_val(*_):
                try:
                    v = int(val_var.get())
                    node.value = v
                    self.steps=[]; self.step_idx=-1
                    self.root_node.reset_algo_state()
                    self._draw()
                    lbl_saved.config(text="✓ Saved", fg=GREEN)
                    self.editor_frame.after(1500, lambda: lbl_saved.config(text=""))
                except ValueError:
                    lbl_saved.config(text="✗ Integer only", fg=RED)

            entry.bind("<Return>", save_val)
            entry.bind("<FocusOut>", save_val)

            tk.Button(self.editor_frame, text="Set Value", command=save_val,
                      bg=ACCENT, fg=TEXT, relief="flat",
                      font=("Segoe UI",10,"bold"), padx=8, pady=3,
                      cursor="hand2").pack(pady=4)
            lbl_saved = tk.Label(self.editor_frame, text="", bg=BG2, fg=GREEN,
                                  font=("Segoe UI",9))
            lbl_saved.pack()

            # quick value slider
            tk.Label(self.editor_frame, text="Quick set (−20 to 20):", bg=BG2, fg=TEXT2,
                     font=("Segoe UI",9)).pack(anchor="w", pady=(6,0))
            slider = tk.Scale(self.editor_frame, from_=-20, to=20, orient=tk.HORIZONTAL,
                               variable=val_var, bg=BG2, fg=TEXT, troughcolor=BG3,
                               highlightthickness=0, relief="flat",
                               command=lambda v: (setattr(node,'value',int(float(v))),
                                                  [setattr(self,'steps',[]),
                                                   setattr(self,'step_idx',-1),
                                                   self.root_node.reset_algo_state(),
                                                   self._draw()]))
            try: slider.set(node.value or 0)
            except: pass
            slider.pack(fill=tk.X)

        else:
            tk.Frame(self.editor_frame, bg=BORDER, height=1).pack(fill=tk.X, pady=6)
            tk.Label(self.editor_frame, text="Children:", bg=BG2, fg=TEXT,
                     font=("Segoe UI",10,"bold")).pack(anchor="w")
            tk.Label(self.editor_frame, text=f"{len(node.children)} children",
                     bg=BG2, fg=TEXT2, font=("Segoe UI",10)).pack(anchor="w")

            row = tk.Frame(self.editor_frame, bg=BG2)
            row.pack(pady=6)

            def add_child():
                new_c = node.add_child(self.root_node.is_max)
                self.node_map[new_c.id] = new_c
                self.steps=[]; self.step_idx=-1
                self.root_node.reset_algo_state()
                self._draw(); self._show_editor(node)

            def rem_child():
                if len(node.children) > 1:
                    removed = node.children[-1]
                    node.remove_child()
                    def rm(nd): self.node_map.pop(nd.id,None); [rm(c) for c in nd.children]
                    rm(removed)
                    self.steps=[]; self.step_idx=-1
                    self.root_node.reset_algo_state()
                    self._draw(); self._show_editor(node)

            tk.Button(row, text="+ Add child", command=add_child,
                      bg="#065f46", fg=TEXT, relief="flat",
                      font=("Segoe UI",10,"bold"), padx=8, pady=4,
                      cursor="hand2").pack(side=tk.LEFT, padx=(0,6))
            tk.Button(row, text="− Remove", command=rem_child,
                      bg="#7f1d1d", fg=TEXT, relief="flat",
                      font=("Segoe UI",10,"bold"), padx=8, pady=4,
                      cursor="hand2").pack(side=tk.LEFT)

            # flip max/min
            def toggle_type():
                node.is_max = not node.is_max
                def flip_children(nd):
                    for c in nd.children:
                        c.is_max = not nd.is_max
                        flip_children(c)
                flip_children(node)
                self.steps=[]; self.step_idx=-1
                self.root_node.reset_algo_state()
                self._draw(); self._show_editor(node)

            tk.Button(self.editor_frame, text="⇄ Flip MAX/MIN",
                      command=toggle_type,
                      bg="#4c1d95", fg=TEXT, relief="flat",
                      font=("Segoe UI",10,"bold"), padx=8, pady=4,
                      cursor="hand2").pack(pady=4, anchor="w")

        if node.result is not None:
            tk.Frame(self.editor_frame, bg=BORDER, height=1).pack(fill=tk.X, pady=4)
            tk.Label(self.editor_frame, text=f"Algorithm result: {node.result}",
                     bg=BG2, fg=BEST_COL, font=("Segoe UI",10,"bold")).pack(anchor="w")
        if node.alpha > -math.inf:
            tk.Label(self.editor_frame, text=f"α = {node.alpha}", bg=BG2,
                     fg=MAX_COL, font=("Consolas",10)).pack(anchor="w")
        if node.beta < math.inf:
            tk.Label(self.editor_frame, text=f"β = {node.beta}", bg=BG2,
                     fg=MIN_COL, font=("Consolas",10)).pack(anchor="w")

    # ── Log ───────────────────────────────────────────────────────────────────
    def _log(self, msg):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.insert(tk.END, msg)
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    def _log_clear(self):
        self.log_box.config(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state=tk.DISABLED)


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
