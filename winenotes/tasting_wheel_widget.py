"""
Interactive Wine Tasting Aroma & Flavor Wheel Widget.
Custom GTK 4 widget rendered with Cairo, featuring concentric category rings,
smooth hover feedback, and selection toggles for wine descriptors.
"""

from __future__ import annotations
import math
from typing import Set, Optional, Callable, Tuple, List, Dict
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Gdk

from winenotes.aroma_wheel_data import (
    AROMA_CATEGORIES_DATA,
    SUBCATEGORIES,
    DESCRIPTOR_MAP,
    SubcategoryInfo,
    DescriptorInfo,
)


class TastingWheelWidget(Gtk.DrawingArea):
    """
    A circular wine aroma wheel with 3 concentric levels:
    - Tier 1: Main aroma source (Primary, Secondary, Tertiary, Faults)
    - Tier 2: Aroma family (Flower, Citrus, Red Fruit, Oak Aging, etc.)
    - Tier 3: Specific descriptors (Cherry, Lime, Vanilla, etc.)
    """

    def __init__(
        self,
        selected_descriptors: Optional[Set[str]] = None,
        on_toggle: Optional[Callable[[str, bool], None]] = None,
    ):
        super().__init__()
        self.selected_descriptors: Set[str] = set(selected_descriptors or [])
        self.highlighted_descriptors: Set[str] = set()
        self.on_toggle = on_toggle

        # Hover state
        self._hover_tier: Optional[int] = None
        self._hover_name: Optional[str] = None
        self._hover_subcat: Optional[str] = None
        self._hover_tier1: Optional[str] = None

        # Precompute radial layout
        self._layout_items: List[Dict] = []
        self._tier2_items: List[Dict] = []
        self._tier1_items: List[Dict] = []
        self._total_descriptors = sum(len(s.descriptors) for s in SUBCATEGORIES)
        self._init_geometry_data()

        # Visual preferences
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_content_width(520)
        self.set_content_height(520)

        # Set drawing function
        self.set_draw_func(self._on_draw)

        # Event controllers
        self._setup_event_controllers()

    def _init_geometry_data(self):
        """Precalculate angle slices for tiers and descriptors."""
        self._layout_items.clear()
        self._tier2_items.clear()
        self._tier1_items.clear()

        slice_angle = (2.0 * math.pi) / self._total_descriptors
        start_offset = -math.pi / 2.0  # Start at 12 o'clock

        current_angle = start_offset

        # Build Tier 1 & Tier 2 groups
        for t1_group in AROMA_CATEGORIES_DATA:
            t1_name = t1_group["tier1"]
            t1_color = t1_group["tier1_color"]
            t1_start = current_angle
            t1_desc_count = sum(len(sub["descriptors"]) for sub in t1_group["subcategories"])
            t1_angle = t1_desc_count * slice_angle
            t1_end = t1_start + t1_angle

            self._tier1_items.append({
                "name": t1_name,
                "color_hex": t1_color,
                "start_angle": t1_start,
                "end_angle": t1_end,
                "count": t1_desc_count,
            })

            for subcat_data in t1_group["subcategories"]:
                s_name = subcat_data["name"]
                s_color = subcat_data["color"]
                s_start = current_angle
                s_desc_count = len(subcat_data["descriptors"])
                s_angle = s_desc_count * slice_angle
                s_end = s_start + s_angle

                self._tier2_items.append({
                    "name": s_name,
                    "tier1": t1_name,
                    "color_hex": s_color,
                    "start_angle": s_start,
                    "end_angle": s_end,
                    "descriptors": subcat_data["descriptors"],
                })

                for desc in subcat_data["descriptors"]:
                    d_start = current_angle
                    d_end = d_start + slice_angle
                    self._layout_items.append({
                        "name": desc,
                        "subcat": s_name,
                        "tier1": t1_name,
                        "color_hex": s_color,
                        "start_angle": d_start,
                        "end_angle": d_end,
                        "mid_angle": (d_start + d_end) / 2.0,
                    })
                    current_angle += slice_angle

    def _setup_event_controllers(self):
        # Motion controller for hover effects
        motion_ctrl = Gtk.EventControllerMotion.new()
        motion_ctrl.connect("motion", self._on_motion)
        motion_ctrl.connect("leave", self._on_leave)
        self.add_controller(motion_ctrl)

        # Click gesture for selecting descriptors
        click_gesture = Gtk.GestureClick.new()
        click_gesture.connect("pressed", self._on_pressed)
        self.add_controller(click_gesture)

    def set_selected_descriptors(self, descriptors: Set[str]):
        """Update selected descriptors and redraw."""
        self.selected_descriptors = set(descriptors)
        self.queue_draw()

    def set_highlighted_descriptors(self, descriptors: Set[str]):
        """Highlight a subset (e.g., matching a search term)."""
        self.highlighted_descriptors = set(descriptors)
        self.queue_draw()

    def toggle_descriptor(self, name: str):
        """Toggle descriptor selection state."""
        if name in self.selected_descriptors:
            self.selected_descriptors.remove(name)
            is_selected = False
        else:
            self.selected_descriptors.add(name)
            is_selected = True

        if self.on_toggle:
            self.on_toggle(name, is_selected)
        self.queue_draw()

    def _hex_to_rgb(self, hex_code: str) -> Tuple[float, float, float]:
        hex_clean = hex_code.lstrip("#")
        return (
            int(hex_clean[0:2], 16) / 255.0,
            int(hex_clean[2:4], 16) / 255.0,
            int(hex_clean[4:6], 16) / 255.0,
        )

    def _normalize_angle(self, angle: float) -> float:
        """Normalize angle relative to -pi/2 start into [0, 2*pi)."""
        offset = -math.pi / 2.0
        diff = (angle - offset) % (2.0 * math.pi)
        if diff < 0:
            diff += 2.0 * math.pi
        return diff + offset

    def _hit_test(self, x: float, y: float, w: float, h: float) -> Tuple[Optional[int], Optional[str], Optional[str], Optional[str]]:
        """Determine what tier and item is at coordinate (x, y)."""
        cx, cy = w / 2.0, h / 2.0
        dx = x - cx
        dy = y - cy
        dist = math.hypot(dx, dy)
        max_r = min(w, h) / 2.0 - 10.0

        if max_r <= 30:
            return None, None, None, None

        r0 = 0.22 * max_r  # Center hub
        r1 = 0.35 * max_r  # Tier 1 ring
        r2 = 0.52 * max_r  # Tier 2 ring
        r3 = max_r         # Tier 3 outer ring

        if dist < r0:
            return 0, "Center Hub", None, None

        raw_angle = math.atan2(dy, dx)
        # Normalize between [-pi/2, 3*pi/2)
        norm_angle = raw_angle
        while norm_angle < -math.pi / 2.0:
            norm_angle += 2.0 * math.pi
        while norm_angle >= (3.0 * math.pi / 2.0):
            norm_angle -= 2.0 * math.pi

        # Check Tier 1
        if r0 <= dist < r1:
            for item in self._tier1_items:
                if item["start_angle"] <= norm_angle < item["end_angle"]:
                    return 1, item["name"], None, item["name"]

        # Check Tier 2
        elif r1 <= dist < r2:
            for item in self._tier2_items:
                if item["start_angle"] <= norm_angle < item["end_angle"]:
                    return 2, item["name"], item["name"], item["tier1"]

        # Check Tier 3 (Descriptors)
        elif r2 <= dist <= r3:
            for item in self._layout_items:
                if item["start_angle"] <= norm_angle < item["end_angle"]:
                    return 3, item["name"], item["subcat"], item["tier1"]

        return None, None, None, None

    def _on_motion(self, _ctrl, x: float, y: float):
        w = self.get_width()
        h = self.get_height()
        tier, name, subcat, tier1 = self._hit_test(x, y, w, h)

        if (self._hover_tier, self._hover_name) != (tier, name):
            self._hover_tier = tier
            self._hover_name = name
            self._hover_subcat = subcat
            self._hover_tier1 = tier1

            # Update mouse cursor
            if tier == 3:
                self.set_cursor(Gdk.Cursor.new_from_name("pointer"))
            elif tier == 2:
                self.set_cursor(Gdk.Cursor.new_from_name("pointer"))
            else:
                self.set_cursor(None)

            self.queue_draw()

    def _on_leave(self, _ctrl):
        if self._hover_tier is not None:
            self._hover_tier = None
            self._hover_name = None
            self._hover_subcat = None
            self._hover_tier1 = None
            self.set_cursor(None)
            self.queue_draw()

    def _on_pressed(self, _gesture, n_press: int, x: float, y: float):
        w = self.get_width()
        h = self.get_height()
        tier, name, subcat, tier1 = self._hit_test(x, y, w, h)

        if tier == 3 and name:
            self.toggle_descriptor(name)
        elif tier == 2 and name:
            # Clicking a subcategory toggles all its descriptors if none or some selected, or deselects all
            for s in SUBCATEGORIES:
                if s.name == name:
                    descs = s.descriptors
                    all_selected = all(d in self.selected_descriptors for d in descs)
                    if all_selected:
                        for d in descs:
                            if d in self.selected_descriptors:
                                self.selected_descriptors.remove(d)
                                if self.on_toggle:
                                    self.on_toggle(d, False)
                    else:
                        for d in descs:
                            if d not in self.selected_descriptors:
                                self.selected_descriptors.add(d)
                                if self.on_toggle:
                                    self.on_toggle(d, True)
                    self.queue_draw()
                    break

    def _on_draw(self, _area, cr, width, height):
        cx = width / 2.0
        cy = height / 2.0
        max_r = min(width, height) / 2.0 - 10.0

        if max_r < 40:
            return

        r0 = 0.22 * max_r  # Center hub
        r1 = 0.35 * max_r  # Tier 1
        r2 = 0.52 * max_r  # Tier 2 (Family)
        r3 = max_r         # Tier 3 (Descriptors)

        # Clear background with subtle dark or transparent tint
        cr.save()

        # 1. DRAW TIER 3 (Descriptors Outer Ring)
        for item in self._layout_items:
            name = item["name"]
            s_ang = item["start_angle"]
            e_ang = item["end_angle"]
            m_ang = item["mid_angle"]
            r, g, b = self._hex_to_rgb(item["color_hex"])

            is_selected = name in self.selected_descriptors
            is_hovered = (self._hover_tier == 3 and self._hover_name == name)
            is_highlighted = name in self.highlighted_descriptors or not self.highlighted_descriptors

            cr.save()
            cr.new_path()
            cr.arc(cx, cy, r3, s_ang, e_ang)
            cr.arc_negative(cx, cy, r2, e_ang, s_ang)
            cr.close_path()

            # Fill color based on state
            if is_selected:
                cr.set_source_rgba(r, g, b, 0.95)
                cr.fill_preserve()
                # Glowing border for selected slice
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.9)
                cr.set_line_width(2.0)
                cr.stroke()
            elif is_hovered:
                cr.set_source_rgba(r, g, b, 0.75)
                cr.fill_preserve()
                cr.set_source_rgba(1.0, 1.0, 1.0, 0.8)
                cr.set_line_width(1.5)
                cr.stroke()
            else:
                alpha = 0.40 if is_highlighted else 0.12
                cr.set_source_rgba(r, g, b, alpha)
                cr.fill_preserve()
                cr.set_source_rgba(0.2, 0.2, 0.2, 0.25)
                cr.set_line_width(0.7)
                cr.stroke()

            # Text label for descriptor
            cr.save()
            cr.translate(cx, cy)
            cr.rotate(m_ang)

            font_size = max(7.5, min(10.5, max_r * 0.026))
            cr.select_font_face("Sans", cairo_slant_normal := 0, cairo_weight_normal := 0)
            cr.set_font_size(font_size)

            # If angle is on left hemisphere, flip text so it reads upright
            cos_a = math.cos(m_ang)
            if cos_a < 0:
                # Text reads outward to inward on left half
                cr.rotate(math.pi)
                text_x = -(r3 - 6)
                if is_selected:
                    label_str = f"✓ {name}"
                else:
                    label_str = name
            else:
                text_x = r2 + 6
                if is_selected:
                    label_str = f"{name} ✓"
                else:
                    label_str = name

            if is_selected:
                cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
                cr.select_font_face("Sans", 0, 1)  # Bold
            elif is_hovered:
                cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            elif is_highlighted:
                cr.set_source_rgba(0.95, 0.95, 0.95, 0.9)
            else:
                cr.set_source_rgba(0.6, 0.6, 0.6, 0.4)

            extents = cr.text_extents(label_str)
            text_y = extents.height / 2.0

            # Trim text if too wide
            max_text_w = (r3 - r2) - 12
            if extents.width > max_text_w and len(label_str) > 6:
                label_str = label_str[:8] + ".."

            cr.move_to(text_x, text_y)
            cr.show_text(label_str)
            cr.restore()

            cr.restore()

        # 2. DRAW TIER 2 (Subcategories / Aroma Families)
        for item in self._tier2_items:
            name = item["name"]
            s_ang = item["start_angle"]
            e_ang = item["end_angle"]
            m_ang = (s_ang + e_ang) / 2.0
            r, g, b = self._hex_to_rgb(item["color_hex"])

            is_hovered = (self._hover_tier == 2 and self._hover_name == name) or (
                self._hover_tier == 3 and self._hover_subcat == name
            )

            cr.save()
            cr.new_path()
            cr.arc(cx, cy, r2, s_ang, e_ang)
            cr.arc_negative(cx, cy, r1, e_ang, s_ang)
            cr.close_path()

            alpha = 0.95 if is_hovered else 0.85
            cr.set_source_rgba(r, g, b, alpha)
            cr.fill_preserve()

            border_alpha = 0.9 if is_hovered else 0.4
            cr.set_source_rgba(1.0, 1.0, 1.0, border_alpha)
            cr.set_line_width(1.5 if is_hovered else 1.0)
            cr.stroke()

            # Subcategory Text label
            cr.save()
            cr.translate(cx, cy)
            cr.rotate(m_ang)

            cos_a = math.cos(m_ang)
            subcat_font_size = max(8.0, min(11.5, max_r * 0.029))
            cr.select_font_face("Sans", 0, 1)  # Bold
            cr.set_font_size(subcat_font_size)

            display_name = name.upper()
            extents = cr.text_extents(display_name)

            # Center along radius between r1 and r2
            mid_r = (r1 + r2) / 2.0

            if cos_a < 0:
                cr.rotate(math.pi)
                text_x = -mid_r - (extents.width / 2.0)
            else:
                text_x = mid_r - (extents.width / 2.0)

            text_y = extents.height / 2.0
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            cr.move_to(text_x, text_y)
            cr.show_text(display_name)
            cr.restore()

            cr.restore()

        # 3. DRAW TIER 1 (Primary, Secondary, Tertiary, Faults)
        for item in self._tier1_items:
            name = item["name"]
            s_ang = item["start_angle"]
            e_ang = item["end_angle"]
            m_ang = (s_ang + e_ang) / 2.0
            r, g, b = self._hex_to_rgb(item["color_hex"])

            is_hovered = (self._hover_tier == 1 and self._hover_name == name) or (
                self._hover_tier in (2, 3) and self._hover_tier1 == name
            )

            cr.save()
            cr.new_path()
            cr.arc(cx, cy, r1, s_ang, e_ang)
            cr.arc_negative(cx, cy, r0, e_ang, s_ang)
            cr.close_path()

            alpha = 0.85 if is_hovered else 0.70
            cr.set_source_rgba(r, g, b, alpha)
            cr.fill_preserve()

            cr.set_source_rgba(1.0, 1.0, 1.0, 0.4)
            cr.set_line_width(1.0)
            cr.stroke()

            # Text label for Tier 1
            cr.save()
            cr.translate(cx, cy)
            cr.rotate(m_ang)

            cos_a = math.cos(m_ang)
            tier1_font_size = max(7.0, min(10.0, max_r * 0.024))
            cr.select_font_face("Sans", 0, 1)
            cr.set_font_size(tier1_font_size)

            extents = cr.text_extents(name)
            mid_r = (r0 + r1) / 2.0

            if cos_a < 0:
                cr.rotate(math.pi)
                text_x = -mid_r - (extents.width / 2.0)
            else:
                text_x = mid_r - (extents.width / 2.0)

            text_y = extents.height / 2.0
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
            cr.move_to(text_x, text_y)
            cr.show_text(name)
            cr.restore()

            cr.restore()

        # 4. DRAW CENTER HUB
        cr.save()
        cr.new_path()
        cr.arc(cx, cy, r0, 0, 2 * math.pi)
        cr.set_source_rgba(0.12, 0.12, 0.14, 0.95)
        cr.fill_preserve()
        cr.set_source_rgba(0.85, 0.25, 0.35, 0.8)
        cr.set_line_width(3.0)
        cr.stroke()

        # Inner ring subtle line
        cr.arc(cx, cy, r0 - 6, 0, 2 * math.pi)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.15)
        cr.set_line_width(1.0)
        cr.stroke()

        # Center content
        if self._hover_tier == 3 and self._hover_name:
            # Active hover on descriptor
            subcat = self._hover_subcat or ""
            desc = self._hover_name

            # Subcat header
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(max(8.0, r0 * 0.16))
            cr.set_source_rgba(0.85, 0.85, 0.85, 0.8)
            ext = cr.text_extents(subcat.upper())
            cr.move_to(cx - ext.width / 2.0, cy - r0 * 0.32)
            cr.show_text(subcat.upper())

            # Descriptor Title
            cr.select_font_face("Sans", 0, 1)
            cr.set_font_size(max(10.0, r0 * 0.23))
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ext = cr.text_extents(desc)
            cr.move_to(cx - ext.width / 2.0, cy + ext.height / 3.0)
            cr.show_text(desc)

            # Subtitle hint
            is_sel = desc in self.selected_descriptors
            hint = "✓ Selected" if is_sel else "+ Click to Add"
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(max(7.5, r0 * 0.14))
            if is_sel:
                cr.set_source_rgba(0.3, 0.9, 0.5, 0.9)
            else:
                cr.set_source_rgba(0.7, 0.8, 1.0, 0.8)
            ext = cr.text_extents(hint)
            cr.move_to(cx - ext.width / 2.0, cy + r0 * 0.42)
            cr.show_text(hint)

        elif self._hover_tier == 2 and self._hover_name:
            # Hover on subcategory
            subcat = self._hover_name
            tier1 = self._hover_tier1 or ""

            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(max(8.0, r0 * 0.16))
            cr.set_source_rgba(0.85, 0.85, 0.85, 0.8)
            ext = cr.text_extents(tier1)
            cr.move_to(cx - ext.width / 2.0, cy - r0 * 0.30)
            cr.show_text(tier1)

            cr.select_font_face("Sans", 0, 1)
            cr.set_font_size(max(10.0, r0 * 0.22))
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
            ext = cr.text_extents(subcat)
            cr.move_to(cx - ext.width / 2.0, cy + ext.height / 3.0)
            cr.show_text(subcat)

            hint = "Click to toggle group"
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(max(7.5, r0 * 0.13))
            cr.set_source_rgba(0.8, 0.8, 0.8, 0.7)
            ext = cr.text_extents(hint)
            cr.move_to(cx - ext.width / 2.0, cy + r0 * 0.40)
            cr.show_text(hint)

        else:
            # Default state: Logo / Title and selected count
            cr.select_font_face("Sans", 0, 1)
            cr.set_font_size(max(9.0, r0 * 0.18))
            cr.set_source_rgba(0.95, 0.25, 0.35, 1.0)
            title1 = "WINE AROMA"
            ext = cr.text_extents(title1)
            cr.move_to(cx - ext.width / 2.0, cy - r0 * 0.28)
            cr.show_text(title1)

            title2 = "WHEEL"
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
            ext = cr.text_extents(title2)
            cr.move_to(cx - ext.width / 2.0, cy - r0 * 0.05)
            cr.show_text(title2)

            count = len(self.selected_descriptors)
            status_text = f"{count} Selected" if count > 0 else "Hover to Explore"
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(max(7.5, r0 * 0.15))
            if count > 0:
                cr.set_source_rgba(0.3, 0.9, 0.5, 0.95)
            else:
                cr.set_source_rgba(0.7, 0.7, 0.7, 0.7)
            ext = cr.text_extents(status_text)
            cr.move_to(cx - ext.width / 2.0, cy + r0 * 0.35)
            cr.show_text(status_text)

        cr.restore()
        cr.restore()
