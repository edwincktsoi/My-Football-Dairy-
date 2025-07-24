import json
import math
from datetime import date, datetime
import os

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDRectangleFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.toast import toast
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker, MDTimePicker

# Kivy imports
from kivy.uix.widget import Widget
from kivy.uix.label import Label as KivyLabel
from kivy.graphics import Color, Ellipse, Line, Rectangle, InstructionGroup, Triangle
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView

# --- Data for Formations and Roles (Inspired by FM24) ---

# Coordinates are (rel_x, rel_y) from 0.0 to 1.0, where (0,0) is bottom-left
FORMATION_DATA = {
    "4-4-2": {
        "GK": (0.5, 0.08),
        "RB": (0.85, 0.22), "RCB": (0.65, 0.2), "LCB": (0.35, 0.2), "LB": (0.15, 0.22),
        "RM": (0.8, 0.5), "RCM": (0.6, 0.5), "LCM": (0.4, 0.5), "LM": (0.2, 0.5),
        "RS": (0.6, 0.8), "LS": (0.4, 0.8)
    },
    "4-3-3": {
        "GK": (0.5, 0.08),
        "RB": (0.85, 0.25), "RCB": (0.65, 0.2), "LCB": (0.35, 0.2), "LB": (0.15, 0.25),
        "DM": (0.5, 0.35), "RCM": (0.7, 0.55), "LCM": (0.3, 0.55),
        "RW": (0.8, 0.78), "ST": (0.5, 0.82), "LW": (0.2, 0.78)
    },
    "3-5-2": {
        "GK": (0.5, 0.08),
        "RCB": (0.7, 0.2), "CB": (0.5, 0.2), "LCB": (0.3, 0.2),
        "RWB": (0.85, 0.45), "RCM": (0.65, 0.5), "CDM": (0.5, 0.38), "LCM": (0.35, 0.5), "LWB": (0.15, 0.45),
        "RS": (0.6, 0.8), "LS": (0.4, 0.8)
    },
    "5-3-2": {
        "GK": (0.5, 0.08),
        "RWB": (0.9, 0.35), "RCB": (0.7, 0.2), "CB": (0.5, 0.2), "LCB": (0.3, 0.2), "LWB": (0.1, 0.35),
        "RCM": (0.65, 0.55), "CM": (0.5, 0.5), "LCM": (0.35, 0.55),
        "RS": (0.6, 0.8), "LS": (0.4, 0.8)
    }
}

# Maps a generic position type to a list of available roles
POSITION_ROLES = {
    "GK": ["Goalkeeper", "Sweeper Keeper", "Other"],
    "FB": ["Full-Back", "Wing-Back", "Inverted Wing-Back", "Other"],
    "CB": ["Central Defender", "Ball-Playing Defender", "No-Nonsense Centre-Back", "Other"],
    "DM": ["Defensive Midfielder", "Deep Lying Playmaker", "Anchor Man", "Half-Back", "Other"],
    "CM": ["Central Midfielder", "Box-to-Box Midfielder", "Advanced Playmaker", "Roaming Playmaker", "Mezzala", "Other"],
    "WM": ["Winger", "Inverted Winger", "Wide Playmaker","Inside Forward","Raumdeuter", "Other"],
    "AM": ["Attacking Midfielder", "Advanced Playmaker", "Trequartista", "Shadow Striker", "Other"],
    "ST": ["Deep Lying Forward", "Advanced Forward", "Poacher", "Complete Forward", "Target Man", "False Nine","Pressing Forward", "Other"]
}

# Maps a specific position name from FORMATION_DATA to a generic role type from POSITION_ROLES
POSITION_TO_ROLE_TYPE_MAP = {
    "GK": "GK",
    "RB": "FB", "LB": "FB", "RWB": "FB", "LWB": "FB",
    "CB": "CB", "RCB": "CB", "LCB": "CB",
    "DM": "DM", "CDM": "DM",
    "CM": "CM", "RCM": "CM", "LCM": "CM",
    "RM": "WM", "LM": "WM",
    "RW": "WM", "LW": "WM",
    "AM": "AM",
    "ST": "ST", "RS": "ST", "LS": "ST"
}

class FullPitchPositionWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_position_name = None
        self.current_formation = "4-4-2"
        self.position_nodes = InstructionGroup()
        self.canvas.add(self.position_nodes)
        self.parent_screen = None
        self.pitch_x, self.pitch_y, self.pitch_w, self.pitch_h = 0, 0, 0, 0

        with self.canvas.before:
            self.pitch_graphics = InstructionGroup()

        self.bind(size=self._update_pitch_graphics, pos=self._update_pitch_graphics)
        self._update_pitch_graphics()

    def set_formation(self, formation_name):
        if formation_name in FORMATION_DATA:
            self.current_formation = formation_name
            self.selected_position_name = None
            if self.parent_screen:
                self.parent_screen.set_position_from_pitch(None)
            self._update_pitch_graphics()

    def _update_pitch_graphics(self, *args):
        self.pitch_graphics.clear()
        pitch_aspect_ratio = 105 / 68
        if self.width / self.height > pitch_aspect_ratio:
            self.pitch_h = self.height
            self.pitch_w = self.height * pitch_aspect_ratio
        else:
            self.pitch_w = self.width
            self.pitch_h = self.width / pitch_aspect_ratio
        self.pitch_x = self.x + (self.width - self.pitch_w) / 2
        self.pitch_y = self.y + (self.height - self.pitch_h) / 2
        w, h, x, y = self.pitch_w, self.pitch_h, self.pitch_x, self.pitch_y

        self._draw_grass_pattern(x, y, w, h)

        self.pitch_graphics.add(Color(0.9, 0.9, 0.9, 0.9))
        line_width = dp(1.2)

        def add_line(*points):
            self.pitch_graphics.add(Line(points=points, width=line_width))

        center_x, center_y = x + w / 2, y + h / 2

        # Outer lines and center line
        add_line(x, y, x + w, y)
        add_line(x, y, x, y + h)
        add_line(x + w, y, x + w, y + h)
        add_line(x, y + h, x + w, y + h)
        add_line(x, center_y, x + w, center_y)

        # Center circle (now unfilled)
        center_circle_radius = w * (9.15 / 105.0)
        self.pitch_graphics.add(Line(circle=(center_x, center_y, center_circle_radius), width=line_width))

        # Kickoff spot
        self.pitch_graphics.add(Ellipse(
            pos=(center_x - dp(2), center_y - dp(2)),
            size=(dp(4), dp(4))
        ))

        # Penalty areas
        pen_area_depth = h * (16.5 / 68.0)
        pen_area_width = w * (40.32 / 105.0)
        pa_x1 = center_x - pen_area_width / 2
        pa_x2 = center_x + pen_area_width / 2

        pa_y_bottom = y + pen_area_depth
        add_line(pa_x1, y, pa_x1, pa_y_bottom)
        add_line(pa_x2, y, pa_x2, pa_y_bottom)
        add_line(pa_x1, pa_y_bottom, pa_x2, pa_y_bottom)

        pa_y_top = y + h - pen_area_depth
        add_line(pa_x1, y + h, pa_x1, pa_y_top)
        add_line(pa_x2, y + h, pa_x2, pa_y_top)
        add_line(pa_x1, pa_y_top, pa_x2, pa_y_top)

        self.canvas.before.add(self.pitch_graphics)
        self.redraw_position_nodes()

    def _draw_grass_pattern(self, x, y, w, h):
        color1, color2 = (0.13, 0.55, 0.13, 1), (0.14, 0.58, 0.14, 1)
        num_stripes = 14
        stripe_h = h / num_stripes
        for i in range(num_stripes):
            self.pitch_graphics.add(Color(*(color1 if i % 2 == 0 else color2)))
            self.pitch_graphics.add(Rectangle(pos=(x, y + i * stripe_h), size=(w, stripe_h)))

    def on_touch_down(self, touch):
        if self.pitch_x <= touch.x <= self.pitch_x + self.pitch_w and self.pitch_y <= touch.y <= self.pitch_y + self.pitch_h:
            min_dist_sq, closest_pos_name = float('inf'), None
            formation_nodes = FORMATION_DATA.get(self.current_formation, {})
            for name, (rel_x, rel_y) in formation_nodes.items():
                abs_x = self.pitch_x + rel_x * self.pitch_w
                abs_y = self.pitch_y + rel_y * self.pitch_h
                dist_sq = (touch.x - abs_x)**2 + (touch.y - abs_y)**2
                if dist_sq < min_dist_sq and dist_sq < (dp(20))**2:
                    min_dist_sq = dist_sq
                    closest_pos_name = name
            if closest_pos_name:
                self.selected_position_name = closest_pos_name
                self.redraw_position_nodes()
                if self.parent_screen:
                    self.parent_screen.set_position_from_pitch(self.selected_position_name)
                return True
        return super().on_touch_down(touch)

    def redraw_position_nodes(self):
        self.position_nodes.clear()
        formation_nodes = FORMATION_DATA.get(self.current_formation, {})
        for name, (rel_x, rel_y) in formation_nodes.items():
            abs_x = self.pitch_x + rel_x * self.pitch_w
            abs_y = self.pitch_y + rel_y * self.pitch_h
            marker_size = dp(16)
            is_selected = (name == self.selected_position_name)

            if is_selected:
                # Outer white glow
                self.position_nodes.add(Color(1, 1, 1, 1))
                self.position_nodes.add(Ellipse(
                    pos=(abs_x - marker_size/2 - dp(2), abs_y - marker_size/2 - dp(2)),
                    size=(marker_size + dp(4), marker_size + dp(4))
                ))
                # Inner blue fill
                self.position_nodes.add(Color(0.1, 0.5, 1, 1))
                self.position_nodes.add(Ellipse(
                    pos=(abs_x - marker_size/2, abs_y - marker_size/2),
                    size=(marker_size, marker_size)
                ))
            else:
                # Filled white circle
                self.position_nodes.add(Color(1, 1, 1, 0.9))
                self.position_nodes.add(Ellipse(
                    pos=(abs_x - marker_size/2, abs_y - marker_size/2),
                    size=(marker_size, marker_size)
                ))

class HalfPitchWidget(Widget):
    """
    Custom widget for drawing a realistic football half-pitch.
    Handles responsive drawing of markers and a single info display box.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markers_data = []
        self.marker_instructions = InstructionGroup()
        self.canvas.add(self.marker_instructions)
        self.current_marker_type = 'shot_on'
        self.parent_screen = None
        self.drawing_direction_marker = None
        self.direction_preview_line = InstructionGroup()
        self.pitch_x, self.pitch_y, self.pitch_w, self.pitch_h = 0, 0, 0, 0
        with self.canvas.before:
            self.pitch_graphics = InstructionGroup()
        self.canvas.add(self.direction_preview_line)
        self.info_label = KivyLabel(text="xG/xA: --", font_size='10sp', size_hint=(None, None), size=(dp(65), dp(25)), color=(1, 1, 1, 0.9))
        with self.info_label.canvas.before:
            Color(0.2, 0.2, 0.2, 0.7)
            self.info_label_bg = Rectangle(size=self.info_label.size, pos=self.info_label.pos)
        self.add_widget(self.info_label)
        self.bind(size=self._update_pitch_graphics, pos=self._update_pitch_graphics)
        self._update_pitch_graphics()

    def _update_pitch_graphics(self, *args):
        self.pitch_graphics.clear()
        pitch_aspect_ratio = 68 / 52.5
        if self.width / self.height > pitch_aspect_ratio:
            self.pitch_h = self.height; self.pitch_w = self.height * pitch_aspect_ratio
        else:
            self.pitch_w = self.width; self.pitch_h = self.width / pitch_aspect_ratio
        self.pitch_x = self.x + (self.width - self.pitch_w) / 2; self.pitch_y = self.y + (self.height - self.pitch_h) / 2
        w, h, x, y = self.pitch_w, self.pitch_h, self.pitch_x, self.pitch_y
        self._draw_grass_pattern(x, y, w, h)
        self.pitch_graphics.add(Color(0.9, 0.9, 0.9, 0.9)); line_width = dp(1.5)
        def add_line(*points): self.pitch_graphics.add(Line(points=points, width=line_width))
        center_x = x + w / 2
        add_line(x, y, x + w, y); add_line(x, y, x, y + h); add_line(x + w, y, x + w, y + h); add_line(x, y + h, x + w, y + h)
        
        # Center Circle Arc
        center_circle_radius = w * (9.15 / 68.0)
        arc_points = []
        num_segments = 20
        for i in range(num_segments + 1):
            angle = math.pi + (math.pi * i / num_segments)
            arc_x = center_x + center_circle_radius * math.cos(angle)
            arc_y = y + h + center_circle_radius * math.sin(angle)
            arc_points.extend([arc_x, arc_y])
        if len(arc_points) > 2:
            self.pitch_graphics.add(Line(points=arc_points, width=line_width))
        self.pitch_graphics.add(Ellipse(pos=(center_x - dp(2), y + h - dp(2)), size=(dp(4), dp(4))))
        
        goal_width = w * (7.32 / 68.0); goal_depth = dp(8); goal_x1, goal_x2 = center_x - goal_width / 2, center_x + goal_width / 2
        add_line(goal_x1, y, goal_x1, y - goal_depth); add_line(goal_x2, y, goal_x2, y - goal_depth); add_line(goal_x1, y - goal_depth, goal_x2, y - goal_depth)
        pen_area_depth = h * (16.5 / 52.5); pen_area_width = w * (40.32 / 68.0); pa_x1, pa_x2 = center_x - pen_area_width / 2, center_x + pen_area_width / 2; pa_y = y + pen_area_depth
        add_line(pa_x1, y, pa_x1, pa_y); add_line(pa_x2, y, pa_x2, pa_y); add_line(pa_x1, pa_y, pa_x2, pa_y)
        goal_area_depth = h * (5.5 / 52.5); goal_area_width = w * (18.32 / 68.0); ga_x1, ga_x2 = center_x - goal_area_width / 2, center_x + goal_area_width / 2; ga_y = y + goal_area_depth
        add_line(ga_x1, y, ga_x1, ga_y); add_line(ga_x2, y, ga_x2, ga_y); add_line(ga_x1, ga_y, ga_x2, ga_y)
        
        # Penalty Spot and Arc
        penalty_spot_y = y + h * (11.0 / 52.5)
        self.pitch_graphics.add(Ellipse(pos=(center_x - dp(2.5), penalty_spot_y - dp(2.5)), size=(dp(5), dp(5))))
        arc_radius = w * (9.15 / 68.0)
        arc_points_pen = []
        start_angle_rad, end_angle_rad = math.radians(35), math.radians(145)
        angle_range = end_angle_rad - start_angle_rad
        for i in range(num_segments + 1):
            angle = start_angle_rad + (angle_range * i / num_segments)
            arc_x = center_x + arc_radius * math.cos(angle)
            arc_y = penalty_spot_y + arc_radius * math.sin(angle)
            arc_points_pen.extend([arc_x, arc_y])
        if len(arc_points_pen) > 2:
            self.pitch_graphics.add(Line(points=arc_points_pen, width=line_width))
        self.info_label.pos = (
            self.pitch_x + self.pitch_w - self.info_label.width - dp(5),
            self.pitch_y + self.pitch_h - self.info_label.height - dp(5)
        )
        self.info_label_bg.pos = self.info_label.pos
        
        # Redraw markers
        self.redraw_all_markers()

    def _draw_grass_pattern(self, x, y, w, h):
        color1, color2 = (0.13, 0.55, 0.13, 1), (0.14, 0.58, 0.14, 1)
        num_stripes, stripe_h = 9, h / 9
        for i in range(num_stripes):
            self.pitch_graphics.add(Color(*(color1 if i % 2 == 0 else color2)))
            self.pitch_graphics.add(Rectangle(pos=(x, y + i * stripe_h), size=(w, stripe_h)))

    def get_xg_value(self, rel_pos):
        rel_x, rel_y = rel_pos
        if rel_y <= 0.01: return 0.99
        shot_x_m = (rel_x - 0.5) * 68.0
        shot_y_m = rel_y * 52.5
        distance_m = math.sqrt(shot_x_m**2 + shot_y_m**2)
        dist_to_post1_sq = (shot_x_m - (-7.32 / 2))**2 + shot_y_m**2
        dist_to_post2_sq = (shot_x_m - (7.32 / 2))**2 + shot_y_m**2
        if dist_to_post1_sq == 0 or dist_to_post2_sq == 0: return 0.95
        cos_angle = max(-1.0, min(1.0, (dist_to_post1_sq + dist_to_post2_sq - 7.32**2) / (2 * math.sqrt(dist_to_post1_sq * dist_to_post2_sq))))
        angle_rad = math.acos(cos_angle)
        final_xg = (0.8 * math.exp(-distance_m / 8)) * ((angle_rad / 0.7) ** 0.7)
        return min(final_xg, 0.99)

    def get_xa_value(self, rel_pos):
        rel_x, rel_y = rel_pos; x_m = (rel_x - 0.5) * 68.0; y_m = rel_y * 52.5
        if y_m < 10 and abs(x_m) > (7.32 / 2): return 0.15 + (10 - y_m) * 0.02
        if 16.5 < y_m < 30 and abs(x_m) < 12: return 0.08 + (30 - y_m) * 0.007
        return min(0.12 * math.exp(-math.sqrt(x_m**2 + y_m**2) / 20), 0.15)

    def on_touch_down(self, touch):
        if self.drawing_direction_marker is None and self.pitch_x <= touch.x <= self.pitch_x + self.pitch_w and self.pitch_y <= touch.y <= self.pitch_y + self.pitch_h:
            rel_pos = ((touch.x - self.pitch_x) / self.pitch_w, (touch.y - self.pitch_y) / self.pitch_h)
            marker_data = {
                'rel_pos': rel_pos, 'rel_end_pos': None, 'type': self.current_marker_type,
                'xg': self.get_xg_value(rel_pos), 'xa': self.get_xa_value(rel_pos)
            }
            self.markers_data.append(marker_data)
            self.update_info_label(marker_data)
            self.redraw_all_markers()
            self.drawing_direction_marker = marker_data
            if self.parent_screen: self.parent_screen.update_summary()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.drawing_direction_marker:
            self.direction_preview_line.clear()
            start_pos = self.drawing_direction_marker['pos']
            end_pos = touch.pos
            self.direction_preview_line.add(Color(1, 1, 0, 0.8))
            self.direction_preview_line.add(Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=dp(1.5), dash_length=dp(5), dash_offset=dp(5)))
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.drawing_direction_marker:
            if self.pitch_x <= touch.x <= self.pitch_x + self.pitch_w and self.pitch_y <= touch.y <= self.pitch_y + self.pitch_h:
                self.drawing_direction_marker['rel_end_pos'] = ((touch.x - self.pitch_x) / self.pitch_w, (touch.y - self.pitch_y) / self.pitch_h)
            self.direction_preview_line.clear()
            self.drawing_direction_marker = None
            self.redraw_all_markers()
            return True
        return super().on_touch_up(touch)

    def update_info_label(self, marker_data):
        if not marker_data: self.info_label.text = "xG/xA: --"; return
        marker_type = marker_data['type']
        if marker_type in ['shot_on', 'shot_off', 'goal']: self.info_label.text = f"xG: {marker_data['xg']:.2f}"
        elif marker_type == 'assist': self.info_label.text = f"xA: {marker_data['xa']:.2f}"
        else: self.info_label.text = "xG/xA: --"

    def draw_marker_graphic(self, marker_data):
        pos, marker_type = marker_data['pos'], marker_data['type']
        if marker_data.get('rel_end_pos'):
            start_pos = marker_data['pos']
            end_pos = (self.pitch_x + marker_data['rel_end_pos'][0] * self.pitch_w, self.pitch_y + marker_data['rel_end_pos'][1] * self.pitch_h)
            if start_pos != end_pos:
                self.marker_instructions.add(Color(1, 1, 1, 0.7))
                self.marker_instructions.add(Line(points=[start_pos[0], start_pos[1], end_pos[0], end_pos[1]], width=dp(1.2)))
                dx, dy = end_pos[0] - start_pos[0], end_pos[1] - start_pos[1]
                angle = math.atan2(dy, dx); arrow_len = dp(8); arrow_angle = math.pi / 6
                p1 = (end_pos[0] - arrow_len * math.cos(angle - arrow_angle), end_pos[1] - arrow_len * math.sin(angle - arrow_angle))
                p2 = (end_pos[0] - arrow_len * math.cos(angle + arrow_angle), end_pos[1] - arrow_len * math.sin(angle + arrow_angle))
                self.marker_instructions.add(Triangle(points=[end_pos[0], end_pos[1], p1[0], p1[1], p2[0], p2[1]]))
        center_x, center_y = pos[0], pos[1]
        if marker_type == 'goal':
            d = dp(19); self.marker_instructions.add(Color(1, 0.84, 0, 1)); outer_radius = d / 2; inner_radius = outer_radius * 0.4
            points = []
            for i in range(10):
                radius = outer_radius if i % 2 == 0 else inner_radius
                angle = math.pi / 2 + (2 * math.pi / 10) * i
                points.extend([center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)])
            for i in range(10):
                p1_idx, p2_idx = i * 2, ((i + 1) % 10) * 2
                self.marker_instructions.add(Triangle(points=[center_x, center_y, points[p1_idx], points[p1_idx+1], points[p2_idx], points[p2_idx+1]]))
        elif marker_type == 'shot_on':
            d = dp(10); self.marker_instructions.add(Color(0.2, 0.8, 0.2, 1)); self.marker_instructions.add(Ellipse(pos=(center_x - d/2, center_y - d/2), size=(d, d)))
        elif marker_type == 'shot_off':
            d = dp(10); self.marker_instructions.add(Color(0.9, 0.1, 0.1, 1)); size = d; half_size = size / 2; x_width = dp(2)
            self.marker_instructions.add(Line(points=[center_x - half_size, center_y - half_size, center_x + half_size, center_y + half_size], width=x_width))
            self.marker_instructions.add(Line(points=[center_x - half_size, center_y + half_size, center_x + half_size, center_y - half_size], width=x_width))
        elif marker_type == 'assist':
            d = dp(10); self.marker_instructions.add(Color(0.1, 0.7, 1, 1)); size = d
            self.marker_instructions.add(Rectangle(pos=(center_x - size/2, center_y - size/2), size=(size, size)))

    def redraw_all_markers(self):
        self.marker_instructions.clear()
        for marker in self.markers_data:
            marker['pos'] = (self.pitch_x + marker['rel_pos'][0] * self.pitch_w, self.pitch_y + marker['rel_pos'][1] * self.pitch_h)
            self.draw_marker_graphic(marker)

    def clear_markers(self):
        self.markers_data.clear()
        self.update_info_label(None)
        self.redraw_all_markers()

    def undo_last_marker(self):
        if self.drawing_direction_marker:
            self.markers_data.pop()
            self.drawing_direction_marker = None
            self.direction_preview_line.clear()
            self.redraw_all_markers()
            self.update_info_label(self.markers_data[-1] if self.markers_data else None)
            return True
        elif self.markers_data:
            self.markers_data.pop()
            self.redraw_all_markers()
            self.update_info_label(self.markers_data[-1] if self.markers_data else None)
            return True
        return False

class AddStatScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None
        self.selected_game_type = "Match"
        self.selected_position = "N/A"
        self.selected_role = "N/A"
        self.selected_date = date.today()
        self.selected_time = datetime.now().time()
        self.performance_rating = 6.0

        self.root_scroll = ScrollView(do_scroll_x=False)
        main_layout = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12), size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        main_layout.add_widget(MDLabel(text="Attacking Stats Tracker", font_style="H5", halign="center", theme_text_color="Primary", adaptive_height=True))

        # --- Define Widgets for Session and Position ---
        # It's good practice to define interactive widgets here before assigning them to layouts.
        self.date_button = MDRectangleFlatButton(text=self.selected_date.strftime('%Y-%m-%d'), on_release=self.show_date_picker)
        self.time_button = MDRectangleFlatButton(text=self.selected_time.strftime('%H:%M'), on_release=self.show_time_picker)
        self.game_type_button = MDRectangleFlatButton(text=self.selected_game_type)
        game_type_items = [{"text": gt, "on_release": lambda x=gt: self.set_game_type(x)} for gt in ["Fun Game", "Training", "Match"]]
        self.game_type_menu = MDDropdownMenu(caller=self.game_type_button, items=game_type_items, width_mult=4)
        self.game_type_button.on_release = self.game_type_menu.open
        self.formation_button = MDRectangleFlatButton(text="4-4-2")
        formation_items = [{"text": ft, "on_release": lambda x=ft: self.set_formation(x)} for ft in FORMATION_DATA.keys()]
        self.formation_menu = MDDropdownMenu(caller=self.formation_button, items=formation_items, width_mult=4)
        self.formation_button.on_release = self.formation_menu.open
        self.position_button = MDRectangleFlatButton(text=self.selected_position, disabled=True)
        self.role_button = MDRectangleFlatButton(text=self.selected_role, on_release=lambda x: self.role_menu.open(), disabled=True)
        self.role_menu = MDDropdownMenu(caller=self.role_button, items=[], width_mult=4)

        # --- Session Info Card (Simplified) ---
        session_card = MDCard(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None, adaptive_height=True, elevation=2, style="elevated")
        session_card.add_widget(MDLabel(text="Session Details", font_style="H6", halign="center", adaptive_height=True))
        form_grid = MDGridLayout(cols=2, spacing=dp(15), adaptive_height=True, padding=(0, dp(10)))
        
        def add_form_row(label_text, widget):
            form_grid.add_widget(MDLabel(text=label_text, adaptive_height=True, halign="right", theme_text_color="Secondary"))
            form_grid.add_widget(widget)

        add_form_row("Date:", self.date_button)
        add_form_row("Time:", self.time_button)
        add_form_row("Game Type:", self.game_type_button)
        session_card.add_widget(form_grid)
        main_layout.add_widget(session_card)

        # --- Position Selection Card (Updated) ---
        pos_card = MDCard(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None, adaptive_height=True, elevation=2, style="elevated")
        pos_card.add_widget(MDLabel(text="Select Formation & Position", font_style="H6", halign="center", adaptive_height=True))
        
        # New horizontal layout for Formation, Position, and Role
        controls_grid = MDGridLayout(cols=3, spacing=dp(10), adaptive_height=True)
        controls_grid.add_widget(self.formation_button)
        controls_grid.add_widget(self.position_button)
        controls_grid.add_widget(self.role_button)
        pos_card.add_widget(controls_grid)

        # Add the pitch widget below the new controls
        self.position_pitch_widget = FullPitchPositionWidget(size_hint_y=None, height=dp(280))
        self.position_pitch_widget.parent_screen = self
        pos_card.add_widget(self.position_pitch_widget)
        main_layout.add_widget(pos_card)

        # --- Pitch and Events Card ---
        pitch_card = MDCard(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint_y=None, height=dp(460), elevation=3, style="elevated")
        pitch_header = MDBoxLayout(orientation='horizontal', adaptive_height=True, spacing=dp(10))
        pitch_header.add_widget(MDLabel(text="Events", font_style="H6", size_hint_x=0.7, adaptive_height=True))
        self.undo_button = MDIconButton(icon="undo-variant", on_release=self.undo_last)
        pitch_header.add_widget(self.undo_button)
        pitch_card.add_widget(pitch_header)
        btn_layout = MDGridLayout(cols=4, spacing=dp(8), adaptive_height=True, padding=(dp(10), 0))
        event_buttons_def = {'shot_on': "Shot On", 'shot_off': "Shot Off", 'goal': "Goal", 'assist': "Assist"}
        self.event_buttons = {}
        for key, text in event_buttons_def.items():
            btn = MDRectangleFlatButton(text=text, on_release=lambda x, k=key: self.select_marker_type(k), font_size="12sp")
            self.event_buttons[key] = btn
            btn_layout.add_widget(btn)
        pitch_card.add_widget(btn_layout)
        self.pitch_widget = HalfPitchWidget(size_hint_y=1)
        self.pitch_widget.parent_screen = self
        pitch_card.add_widget(self.pitch_widget)
        main_layout.add_widget(pitch_card)

        # --- Summary Card ---
        summary_card = MDCard(orientation='vertical', padding=dp(15), spacing=dp(12), size_hint_y=None, adaptive_height=True, elevation=2, style="elevated")
        summary_card.add_widget(MDLabel(text="Session Summary", font_style="H6", halign="center", adaptive_height=True))
        self.summary_content_box = MDBoxLayout(orientation='vertical', adaptive_height=True, padding=(dp(10), 0))
        summary_card.add_widget(self.summary_content_box)
        main_layout.add_widget(summary_card)

        # --- Action Buttons ---
        action_layout = MDBoxLayout(orientation='horizontal', spacing=dp(15), adaptive_height=True, padding=(dp(20), 0))
        action_layout.add_widget(MDFlatButton(text="Clear All", on_release=self.confirm_clear_all, theme_text_color="Error"))
        action_layout.add_widget(MDRaisedButton(text="Save Session", on_release=self.save_stat, elevation=2, size_hint_x=0.6))
        main_layout.add_widget(action_layout)

        self.root_scroll.add_widget(main_layout)
        self.add_widget(self.root_scroll)
        self.select_marker_type('shot_on')
        self.update_summary()

    def show_date_picker(self, *args):
        date_dialog = MDDatePicker(year=self.selected_date.year, month=self.selected_date.month, day=self.selected_date.day)
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()
    def on_date_save(self, instance, value, date_range):
        self.selected_date = value; self.date_button.text = self.selected_date.strftime('%Y-%m-%d')
    def show_time_picker(self, *args):
        time_dialog = MDTimePicker(); time_dialog.set_time(self.selected_time)
        time_dialog.bind(on_save=self.on_time_save)
        time_dialog.open()
    def on_time_save(self, instance, time):
        self.selected_time = time; self.time_button.text = self.selected_time.strftime('%H:%M')

    def set_game_type(self, game_type):
        self.selected_game_type = game_type; self.game_type_button.text = game_type; self.game_type_menu.dismiss()

    def set_formation(self, formation_name):
        self.formation_button.text = formation_name
        self.position_pitch_widget.set_formation(formation_name)
        self.formation_menu.dismiss()

    def set_position_from_pitch(self, position_name):
        if position_name is None:
            self.selected_position, self.selected_role = "N/A", "N/A"
            self.position_button.text, self.role_button.text = self.selected_position, self.selected_role
            self.role_button.disabled, self.role_menu.items = True, []
            return
        self.selected_position = position_name
        self.position_button.text = position_name
        roles = POSITION_ROLES.get(POSITION_TO_ROLE_TYPE_MAP.get(position_name), [])
        if roles:
            self.role_button.disabled = False
            self.role_menu.items = [{"text": r, "on_release": lambda x=r: self.set_role(x)} for r in roles]
            self.set_role(roles[0])
        else:
            self.set_role("N/A"); self.role_button.disabled = True; self.role_menu.items = []

    def set_role(self, role_name):
        self.selected_role = role_name; self.role_button.text = role_name
        if self.role_menu: self.role_menu.dismiss()

    def select_marker_type(self, marker_type):
        self.pitch_widget.current_marker_type = marker_type
        for key, button in self.event_buttons.items():
            is_selected = (key == marker_type)
            button.md_bg_color = self.theme_cls.primary_color if is_selected else (0,0,0,0)
            button.text_color = "white" if is_selected else self.theme_cls.primary_color

    def update_summary(self):
        self.summary_content_box.clear_widgets()
        markers = self.pitch_widget.markers_data
        if not markers:
            self.summary_content_box.add_widget(MDLabel(text="No events recorded yet.", halign="center", theme_text_color="Secondary", adaptive_height=True))
        else:
            stats = {"Goals": 0, "Assists": 0, "Shots On": 0, "Shots Off": 0, "xG": 0.0, "xA": 0.0}
            for m in markers:
                if m['type'] in ['shot_on', 'shot_off', 'goal']: stats['xG'] += m.get('xg', 0)
                if m['type'] == 'assist': stats['xA'] += m.get('xa', 0)
                if m['type'] == 'goal': stats["Goals"] += 1; stats["Shots On"] += 1
                elif m['type'] == 'assist': stats["Assists"] += 1
                elif m['type'] == 'shot_on': stats["Shots On"] += 1
                elif m['type'] == 'shot_off': stats["Shots Off"] += 1
            
            summary_grid = MDGridLayout(cols=2, adaptive_height=True, spacing=dp(10))
            def add_stat_row(name, value):
                summary_grid.add_widget(MDLabel(text=name, halign='left', adaptive_height=True))
                summary_grid.add_widget(MDLabel(text=value, halign='right', adaptive_height=True, bold=True))
            
            add_stat_row("Goals:", str(stats["Goals"]))
            add_stat_row("Assists:", str(stats["Assists"]))
            add_stat_row("Total Shots:", str(stats["Shots On"] + stats["Shots Off"]))
            add_stat_row("Expected Goals (xG):", f"{stats['xG']:.2f}")
            add_stat_row("Expected Assists (xA):", f"{stats['xA']:.2f}")
            self.summary_content_box.add_widget(summary_grid)
        self.undo_button.disabled = not bool(markers)

    def undo_last(self, instance):
        if self.pitch_widget.undo_last_marker():
            toast("Last event removed"); self.update_summary()
        else:
            toast("Nothing to undo")

    def confirm_clear_all(self, instance):
        if not self.dialog:
            self.dialog = MDDialog(title="Clear All Data?", text="This action cannot be undone.", buttons=[MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text="Clear All", md_bg_color="red", on_release=self.clear_all)])
        self.dialog.open()

    def clear_all(self, instance):
        if self.dialog: self.dialog.dismiss()
        self.pitch_widget.clear_markers()
        self.update_summary()
        toast("All data cleared")

    def save_stat(self, instance):
        app = MDApp.get_running_app()
        username = getattr(app, "current_user", "default_user")
        folder_path = os.path.join("data", "matches_history", username)
        os.makedirs(folder_path, exist_ok=True)
        session_dt = datetime.combine(self.selected_date, self.selected_time)
        filename = f"session_{session_dt.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(folder_path, filename)

        markers = self.pitch_widget.markers_data
        events_to_save = [{'rel_pos': m['rel_pos'], 'rel_end_pos': m.get('rel_end_pos'), 'type': m['type'], 'xg': m.get('xg'), 'xa': m.get('xa')} for m in markers]
        
        data = {
            "session_info": {
                "game_type": self.selected_game_type,
                "formation": self.formation_button.text,
                "position": self.selected_position,
                "role": self.selected_role,
                "date": self.selected_date.isoformat(),
                "time": self.selected_time.strftime("%H:%M:%S"),
            },
            "stats": {
                "goals": sum(1 for m in markers if m['type'] == 'goal'),
                "assists": sum(1 for m in markers if m['type'] == 'assist'),
                "shots_on_target": sum(1 for m in markers if m['type'] in ['shot_on', 'goal']),
                "shots_off_target": sum(1 for m in markers if m['type'] == 'shot_off'),
                "total_xg": sum(m.get('xg', 0) for m in markers if m['type'] in ['shot_on', 'shot_off', 'goal']),
                "total_xa": sum(m.get('xa', 0) for m in markers if m['type'] == 'assist'),
            },
            "events": events_to_save
        }

        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            toast(f"Stats saved to {filename}")
        except Exception as e:
            toast(f"Error saving file: {e}")