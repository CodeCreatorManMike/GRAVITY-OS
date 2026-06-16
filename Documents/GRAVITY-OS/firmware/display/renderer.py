# display/renderer.py — layout JSON → round display
#
# Handles the 5 new face types (Tier 1 schema):
#   goal_arc        — perimeter progress ring, pct, days left
#   task_list       — up to 6 tasks with ring checkboxes
#   habit_heatmap   — 7-day completion grid per habit
#   timer           — depleting arc countdown
#   study_progress  — module completion ring
#
# Also handles legacy A3 (nudge) and offline badge.
#
# Layout dict accepted formats:
#   NEW: {"faces": [{"type": "goal_arc", ...flat fields...}], "generated_at": "..."}
#   OLD: {"screens": [{"type": "A1", "data": {...}}]}   ← backwards compat only

import utime
from display.hal import COLOR_BG, COLOR_FG, WIDTH, HEIGHT
from display import components as comp

_CX = WIDTH  // 2   # 240
_CY = HEIGHT // 2   # 240


class Renderer:

    def __init__(self, hal):
        self._hal        = hal
        self._screens    = []   # normalised list of face dicts (flat, type field present)
        self._index      = 0
        self._nudge      = None
        self._prev_index = 0
        self._offline    = False   # draw offline badge when True

    # ── Layout loading ─────────────────────────────────────────────────────────

    def load_layout(self, layout_dict, offline=False):
        """Accept layout from WS LAYOUT_UPDATE or flash cache."""
        self._offline = offline

        # Accept both "faces" (new) and "screens" (legacy) keys
        faces = layout_dict.get("faces") or layout_dict.get("screens") or []
        if not faces:
            print("[renderer] layout has no faces")
            return

        # Normalise legacy {"type": "A1", "data": {...}} into flat dict
        normalised = []
        for f in faces:
            if "data" in f and isinstance(f["data"], dict):
                flat = dict(f["data"])
                flat["type"] = f.get("type", "")
                normalised.append(flat)
            else:
                normalised.append(f)

        self._screens = normalised
        self._index   = 0
        print(f"[renderer] loaded {len(normalised)} faces")
        self.render_current()

    def get_screens(self):
        return self._screens

    def current_screen(self):
        if not self._screens:
            return None
        return self._screens[self._index]

    def set_offline(self, offline):
        self._offline = offline

    # ── Navigation ─────────────────────────────────────────────────────────────

    def next_screen(self):
        if not self._screens:
            return
        self._index = (self._index + 1) % len(self._screens)
        self.render_current()

    def prev_screen(self):
        if not self._screens:
            return
        self._index = (self._index - 1) % len(self._screens)
        self.render_current()

    def show_nudge(self, nudge_data):
        """Overlay nudge on current screen."""
        self._prev_index = self._index
        self._nudge      = nudge_data
        self._hal.clear()
        self._render_nudge(nudge_data)
        comp.apply_circle_mask(self._hal)
        self._hal.show()

    def dismiss_nudge(self):
        self._nudge = None
        self._index = self._prev_index
        self.render_current()

    def is_nudge_active(self):
        return self._nudge is not None

    # ── Render dispatch ────────────────────────────────────────────────────────

    def render_current(self):
        face = self.current_screen()
        if face is None:
            self._render_boot("NO DATA")
            comp.apply_circle_mask(self._hal)
            self._hal.show()
            return

        ftype = face.get("type", "")
        self._hal.clear()

        dispatch = {
            "goal_arc":       self._render_goal_arc,
            "task_list":      self._render_task_list,
            "habit_heatmap":  self._render_habit_heatmap,
            "timer":          self._render_timer,
            "study_progress": self._render_study_progress,
            # Legacy nudge (pushed separately via show_nudge in normal flow)
            "A3":             self._render_nudge,
        }
        fn = dispatch.get(ftype)
        if fn:
            fn(face)
        else:
            print(f"[renderer] unknown face type: {ftype}")
            comp.draw_text_centred(self._hal, ftype or "?", _CY, scale=2)

        comp.apply_circle_mask(self._hal)

        # Offline badge — small dot + "OFFLINE" at bottom of circle
        if self._offline:
            self._draw_offline_badge()

        # Dot pagination indicator (bottom arc)
        self._draw_dots()

        self._hal.show()

    def render_boot(self, line2="CONNECTING..."):
        self._hal.clear()
        self._render_boot(line2)
        comp.apply_circle_mask(self._hal)
        self._hal.show()

    # ── Boot screen ────────────────────────────────────────────────────────────

    def _render_boot(self, line2):
        comp.draw_text_centred(self._hal, "GRAVITY", _CY - 24, scale=3)
        comp.draw_text_centred(self._hal, line2,     _CY + 12, scale=1)

    # ── Offline badge ──────────────────────────────────────────────────────────

    def _draw_offline_badge(self):
        comp.draw_text_centred(self._hal, "OFFLINE", HEIGHT - 72, scale=1)

    # ── Dot pagination ─────────────────────────────────────────────────────────

    def _draw_dots(self):
        n = len(self._screens)
        if n <= 1:
            return
        dot_size   = 4
        dot_gap    = 8
        total_w    = n * dot_size + (n - 1) * dot_gap
        x0         = _CX - total_w // 2
        y          = HEIGHT - 52
        for i in range(n):
            x = x0 + i * (dot_size + dot_gap)
            if i == self._index:
                self._hal.fill_rect(x, y, dot_size, dot_size, COLOR_FG)
            else:
                self._hal.draw_hline(x, y, dot_size, COLOR_FG)
                self._hal.draw_hline(x, y + dot_size - 1, dot_size, COLOR_FG)
                self._hal.draw_vline(x, y, dot_size, COLOR_FG)
                self._hal.draw_vline(x + dot_size - 1, y, dot_size, COLOR_FG)

    # ══════════════════════════════════════════════════════════════════════════
    # Face renderers
    # ══════════════════════════════════════════════════════════════════════════

    def _render_goal_arc(self, face):
        """
        goal_arc — perimeter progress ring filling from top, pct in centre.
        JSON: {type, label, pct, days_left, on_track, sub_label}
        """
        pct       = float(face.get("pct", 0.0))
        label     = str(face.get("label", "GOAL")).upper()
        days_left = int(face.get("days_left", 0))
        on_track  = face.get("on_track", True)
        sub_label = str(face.get("sub_label", "")).upper()

        # Outer progress ring (radius 210, thickness 18 — near display edge)
        comp.draw_progress_ring(self._hal, _CX, _CY, radius=210, pct=pct, thickness=18)

        # Second inner border ring
        comp.draw_arc(self._hal, _CX, _CY, 192, 0, 360, thickness=2)

        # Large pct in centre
        pct_str = f"{int(pct * 100)}%"
        comp.draw_text_centred(self._hal, pct_str, _CY - 36, scale=4)

        # Goal label
        label_w = comp.text_width(label, scale=1)
        if label_w > 200:
            label = label[:18] + "..."
        comp.draw_text_centred(self._hal, label, _CY + 20, scale=1)

        # Days left + on-track indicator
        days_str = f"{days_left}d left"
        if not on_track:
            days_str += " !"
        comp.draw_text_centred(self._hal, days_str, _CY + 38, scale=1)

        # Sub-label (sub-goal or milestone)
        if sub_label:
            comp.draw_text_centred(self._hal, sub_label[:20], _CY + 58, scale=1)

    def _render_task_list(self, face):
        """
        task_list — up to 6 tasks with checkboxes.
        JSON: {type, tasks: [{id, title, done}], done_count, total_count, next_label}
        """
        tasks      = face.get("tasks", [])[:6]
        done_count = int(face.get("done_count", 0))
        total      = int(face.get("total_count", len(tasks)))
        next_label = str(face.get("next_label", "")).upper()

        # Header: count
        header = f"{done_count}/{total} DONE"
        comp.draw_text_centred(self._hal, header, 76, scale=1)

        # "NEXT" label if all tasks not done
        if next_label and done_count < total:
            nl = next_label[:18]
            comp.draw_text_centred(self._hal, nl, 94, scale=1)

        comp.draw_divider(self._hal, 112, margin=80)

        # Task rows — centred column, 6 tasks max
        n = len(tasks)
        row_h = 28
        y_start = 124
        left_x  = 80

        for i, task in enumerate(tasks):
            y    = y_start + i * row_h
            if y > HEIGHT - 80:
                break
            done  = bool(task.get("done", False))
            title = str(task.get("title", "")).upper()[:16]
            comp.draw_checklist_item(self._hal, left_x, y, title, done, scale=1)

    def _render_habit_heatmap(self, face):
        """
        habit_heatmap — 7-day grid per habit, streak at bottom.
        JSON: {type, habits: [{name, days: [bool x 7]}], streak, week_label}
        """
        habits_list = face.get("habits", [])
        streak      = int(face.get("streak", 0))
        week_label  = str(face.get("week_label", "THIS WEEK")).upper()

        # Convert list to dict for draw_heatmap
        habits_dict = {}
        for h in habits_list[:5]:   # max 5 habits
            name = str(h.get("name", ""))[:10]
            days = h.get("days", [False] * 7)
            habits_dict[name] = days

        if not habits_dict:
            comp.draw_text_centred(self._hal, "NO HABITS", _CY, scale=2)
            return

        comp.draw_text_centred(self._hal, week_label, 80, scale=1)

        # Day headers
        headers    = ["M", "T", "W", "T", "F", "S", "S"]
        cell_total = 24
        grid_w     = 7 * cell_total - 4
        hx         = _CX - grid_w // 2
        for i, h in enumerate(headers):
            comp.draw_text(self._hal, hx + i * cell_total + 8, 100, h, scale=1)

        comp.draw_heatmap(self._hal, habits_dict, cx=_CX, cy=_CY + 10, cell_size=20, gap=4)

        # Streak
        if streak:
            comp.draw_text_centred(self._hal, f"{streak} DAY STREAK", HEIGHT - 88, scale=1)

    def _render_timer(self, face):
        """
        timer — depleting arc + large remaining time.
        JSON: {type, label, duration_seconds, remaining_seconds, running}
        """
        label     = str(face.get("label", "FOCUS")).upper()
        duration  = int(face.get("duration_seconds",  25 * 60))
        remaining = int(face.get("remaining_seconds", duration))
        running   = bool(face.get("running", False))

        pct  = remaining / duration if duration > 0 else 0.0
        mins = remaining // 60
        secs = remaining % 60

        # Outer ring — depleting (full = 1.0 at start, 0.0 done)
        comp.draw_progress_ring(self._hal, _CX, _CY, radius=210, pct=pct, thickness=18)
        comp.draw_arc(self._hal, _CX, _CY, 192, 0, 360, thickness=2)

        # Remaining time large centre
        time_str = f"{mins:02d}:{secs:02d}"
        comp.draw_text_centred(self._hal, time_str, _CY - 32, scale=4)

        # Label
        comp.draw_text_centred(self._hal, label, _CY + 24, scale=1)

        # Running indicator
        status = "RUNNING" if running else "PAUSED"
        comp.draw_text_centred(self._hal, status, _CY + 42, scale=1)

    def _render_study_progress(self, face):
        """
        study_progress — module arc + lesson counter + streak.
        JSON: {type, subject, pct, current_lesson, total_lessons, target_grade, streak_days}
        """
        subject       = str(face.get("subject", "STUDY")).upper()
        pct           = float(face.get("pct", 0.0))
        current       = int(face.get("current_lesson", 0))
        total         = int(face.get("total_lessons", 0))
        target_grade  = str(face.get("target_grade", "")).upper()
        streak_days   = int(face.get("streak_days", 0))

        # Outer arc
        comp.draw_progress_ring(self._hal, _CX, _CY, radius=210, pct=pct, thickness=18)
        comp.draw_arc(self._hal, _CX, _CY, 192, 0, 360, thickness=2)

        # Subject name
        subj = subject[:14]
        comp.draw_text_centred(self._hal, subj, _CY - 60, scale=2)

        # Pct
        pct_str = f"{int(pct * 100)}%"
        comp.draw_text_centred(self._hal, pct_str, _CY - 24, scale=4)

        # Lesson counter
        if total > 0:
            lesson_str = f"{current}/{total} LESSONS"
            comp.draw_text_centred(self._hal, lesson_str, _CY + 24, scale=1)

        # Target grade
        if target_grade:
            comp.draw_text_centred(self._hal, f"TARGET {target_grade}", _CY + 42, scale=1)

        # Streak
        if streak_days:
            comp.draw_text_centred(self._hal, f"{streak_days}d STREAK", _CY + 60, scale=1)

    def _render_nudge(self, data):
        """Full-screen nudge message (overlaid on current face or legacy A3)."""
        self._hal.clear()
        message = data.get("message", "")

        # Word-wrap to ~16 chars per line
        words   = message.split()
        lines   = []
        current = ""
        for w in words:
            test = (current + " " + w).strip()
            if len(test) <= 16:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)

        n       = len(lines)
        y_start = _CY - (n * 20) // 2
        for i, line in enumerate(lines):
            comp.draw_text_centred(self._hal, line.upper(), y_start + i * 20, scale=2)

        comp.draw_text_centred(self._hal, "TAP TO DISMISS", HEIGHT - 90, scale=1)
