# display/renderer.py — layout JSON → framebuffer
#
# The renderer owns the screen list and current screen index.
# It calls only HAL primitives and components — never touches SPI or registers.
#
# Screen types handled:
#   A1  Ambient/Idle    — clock, date, streak
#   A2  Morning Brief   — top task + non-negotiables checklist
#   A3  Active Nudge    — full-screen message
#   A4  Goal Progress   — progress ring + pct + label
#   A5  Weekly Heatmap  — 7-day habit grid
#   A7  Wind-down       — lights-out time + tomorrow task

import utime
from display.hal import COLOR_BG, COLOR_FG, WIDTH, HEIGHT
from display import components as comp

_CX = WIDTH  // 2
_CY = HEIGHT // 2


class Renderer:

    def __init__(self, hal):
        self._hal     = hal
        self._screens = []      # list of {"type": "A1", "data": {...}}
        self._index   = 0       # current screen index
        self._nudge   = None    # active nudge data or None
        self._prev_index = 0    # screen to return to after nudge dismiss

    # ── Layout loading ────────────────────────────────────────────────────────

    def load_layout(self, layout_dict):
        """Accept a parsed layout dict (from cache or WS LAYOUT_UPDATE)."""
        screens = layout_dict.get("screens", [])
        if not screens:
            print("[renderer] layout has no screens")
            return
        self._screens = screens
        self._index   = 0
        print(f"[renderer] loaded {len(screens)} screens, direction={layout_dict.get('direction')}")
        self.render_current()

    def get_screens(self):
        return self._screens

    def current_screen(self):
        if not self._screens:
            return None
        return self._screens[self._index]

    # ── Navigation ────────────────────────────────────────────────────────────

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
        """Push a nudge screen (A3) on top of the current screen."""
        self._prev_index = self._index
        self._nudge      = nudge_data
        self._render_A3(nudge_data)
        self._hal.show()

    def dismiss_nudge(self):
        """Return to the screen that was showing before the nudge."""
        self._nudge = None
        self._index = self._prev_index
        self.render_current()

    def is_nudge_active(self):
        return self._nudge is not None

    # ── Render dispatch ───────────────────────────────────────────────────────

    def render_current(self):
        screen = self.current_screen()
        if screen is None:
            self._render_boot("NO DATA")
            return
        stype = screen.get("type", "")
        data  = screen.get("data", {})
        self._hal.clear()
        fn = {
            "A1": self._render_A1,
            "A2": self._render_A2,
            "A3": self._render_A3,
            "A4": self._render_A4,
            "A5": self._render_A5,
            "A7": self._render_A7,
        }.get(stype)
        if fn:
            fn(data)
        else:
            print(f"[renderer] unknown screen type: {stype}")
            comp.draw_text_centred(self._hal, stype, _CY - 20, scale=2)
        comp.apply_circle_mask(self._hal)
        self._hal.show()

    def render_boot(self, line2="CONNECTING..."):
        self._render_boot(line2)
        comp.apply_circle_mask(self._hal)
        self._hal.show()

    # ── Screen implementations ────────────────────────────────────────────────

    def _render_boot(self, line2):
        self._hal.clear()
        comp.draw_text_centred(self._hal, "GRAVITY", _CY - 24, scale=3)
        comp.draw_text_centred(self._hal, line2,     _CY + 12, scale=1)

    def _render_A1(self, data):
        """Ambient / Idle — clock, date, streak."""
        # Time
        t = utime.localtime()
        time_str  = "{:02d}:{:02d}".format(t[3], t[4])
        date_str  = "{:04d}-{:02d}-{:02d}".format(t[0], t[1], t[2])
        streak    = data.get("streak", 0)

        # Large clock in centre
        comp.draw_text_centred(self._hal, time_str, _CY - 40, scale=4)

        # Date below
        comp.draw_text_centred(self._hal, date_str, _CY + 20, scale=1)

        # Streak at bottom
        streak_text = f"streak {streak}"
        comp.draw_text_centred(self._hal, streak_text, _CY + 60, scale=2)

    def _render_A2(self, data):
        """Morning Brief — top task + non-negotiables checklist."""
        task      = data.get("task", "")
        nonneg    = data.get("nonneg", [])
        completed = set(data.get("nonneg_completed", []))

        # Top task — large, centred, wrapped to 2 lines if needed
        words = task.upper().split()
        line1, line2 = _wrap_words(words, max_chars=12)
        y = 90
        if line2:
            comp.draw_text_centred(self._hal, line1, y,      scale=2)
            comp.draw_text_centred(self._hal, line2, y + 24, scale=2)
            y += 58
        else:
            comp.draw_text_centred(self._hal, line1, y, scale=2)
            y += 36

        comp.draw_divider(self._hal, y, margin=60)
        y += 10

        # Checklist
        left_x = 80
        for item in nonneg:
            if y > HEIGHT - 60:
                break
            done = item in completed
            y = comp.draw_checklist_item(self._hal, left_x, y, item, done, scale=1)

    def _render_A3(self, data):
        """Active Nudge — full-screen message."""
        self._hal.clear()
        message  = data.get("message", "")
        nudge_id = data.get("nudge_id", "")

        # Wrap message into lines of ~16 chars
        words = message.split()
        lines = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 > 16:
                if current:
                    lines.append(current.strip())
                current = w + " "
            else:
                current += w + " "
        if current.strip():
            lines.append(current.strip())

        n = len(lines)
        y_start = _CY - (n * 20) // 2
        for i, line in enumerate(lines):
            comp.draw_text_centred(self._hal, line.upper(), y_start + i * 20, scale=2)

        comp.draw_text_centred(self._hal, "TAP TO DISMISS", HEIGHT - 90, scale=1)
        comp.apply_circle_mask(self._hal)

    def _render_A4(self, data):
        """Goal Progress — progress ring + percentage + label + days."""
        pct        = data.get("pct", 0.0)
        label      = data.get("label", "GOAL").upper()
        days_left  = data.get("days_left", 0)
        milestones = data.get("milestones", [])

        # Outer progress ring
        comp.draw_progress_ring(self._hal, _CX, _CY, radius=200, pct=pct, thickness=14)

        # Inner ring border
        comp.draw_arc(self._hal, _CX, _CY, 182, 0, 360, thickness=2)

        # Large percentage in centre
        pct_str = f"{int(pct*100)}%"
        comp.draw_text_centred(self._hal, pct_str, _CY - 30, scale=4)

        # Goal label
        comp.draw_text_centred(self._hal, label, _CY + 28, scale=1)

        # Days remaining
        comp.draw_text_centred(self._hal, f"{days_left}d left", _CY + 46, scale=1)

        # Milestones as small text at bottom
        if milestones:
            ms_text = " / ".join(milestones[:3])
            comp.draw_text_centred(self._hal, ms_text, _CY + 80, scale=1)

    def _render_A5(self, data):
        """Weekly Heatmap — 7-column habit completion grid from cache."""
        import cache
        habits = cache.get_habit_history()
        if not habits:
            comp.draw_text_centred(self._hal, "NO HABIT DATA", _CY, scale=1)
            return

        comp.draw_text_centred(self._hal, "THIS WEEK", 80, scale=1)

        # Day-of-week headers: M T W T F S S
        headers = ["M", "T", "W", "T", "F", "S", "S"]
        cell_total = 24
        grid_w     = 7 * cell_total - 4
        hx = _CX - grid_w // 2
        for i, h in enumerate(headers):
            comp.draw_text(self._hal, hx + i * cell_total + 8, 110, h, scale=1)

        comp.draw_heatmap(self._hal, habits, cx=_CX, cy=_CY + 20, cell_size=20, gap=4)

        # Legend
        comp.draw_text_centred(self._hal, "filled = done", HEIGHT - 90, scale=1)

    def _render_A7(self, data):
        """Wind-down — lights-out time and tomorrow's task."""
        lights_out     = data.get("lights_out", "23:00")
        tomorrow_task  = data.get("tomorrow_task", "")

        comp.draw_text_centred(self._hal, "LIGHTS OUT", _CY - 60, scale=2)
        comp.draw_text_centred(self._hal, lights_out,   _CY - 20, scale=4)

        comp.draw_divider(self._hal, _CY + 40, margin=80)

        comp.draw_text_centred(self._hal, "TOMORROW", _CY + 60, scale=1)
        comp.draw_text_centred(self._hal, tomorrow_task.upper(), _CY + 80, scale=2)


# ── Utility ───────────────────────────────────────────────────────────────────

def _wrap_words(words, max_chars):
    """Split word list into two lines with at most max_chars per line."""
    line1 = ""
    for i, w in enumerate(words):
        test = (line1 + " " + w).strip()
        if len(test) <= max_chars:
            line1 = test
        else:
            line2 = " ".join(words[i:])
            return line1, line2
    return line1, ""
