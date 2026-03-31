import random
import os
import time

# ── Orientamento forzato su Android (PRIMA di Kivy) ──────────────────────────
from kivy.utils import platform

if platform == 'android':
    try:
        from android.runnable import run_on_ui_thread  # type: ignore
        from jnius import autoclass                    # type: ignore

        ActivityInfo = autoclass('android.content.pm.ActivityInfo')

        _PythonActivity = None
        for _ns in ('org.kivy.android.PythonActivity',
                    'org.pygame.android.PythonActivity',
                    'org.beeware.android.MainActivity'):
            try:
                _PythonActivity = autoclass(_ns)
                break
            except Exception:
                pass

        if _PythonActivity is not None:
            @run_on_ui_thread
            def _force_landscape():
                _PythonActivity.mActivity.setRequestedOrientation(
                    ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE)
            _force_landscape()
            time.sleep(0.4)
    except Exception:
        pass
# ─────────────────────────────────────────────────────────────────────────────

from kivy.config import Config
Config.set('graphics', 'orientation', 'landscape')
Config.set('kivy', 'log_level', 'warning')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.properties import (NumericProperty, ObjectProperty,
                              BooleanProperty, ListProperty, StringProperty)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.vector import Vector
from kivy.lang import Builder
from kivy.graphics import Rectangle, Color as GColor
from kivy.core.image import Image as _CoreImg

import json as _json

_BASE = os.path.dirname(os.path.abspath(__file__))

def _p(rel):
    return os.path.join(_BASE, rel)

# ── Sprite sheet metadata ─────────────────────────────────────────────────────
_SHEET_META = {}

def _load_sheet_meta():
    global _SHEET_META
    if _SHEET_META:
        return
    meta_path = _p('PG/anim_meta.json')
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as f:
                _SHEET_META = _json.load(f)
        except Exception:
            pass

# ── SheetAnimImage ────────────────────────────────────────────────────────────
# Widget che anima frame da sprite sheet PNG.
# Non usa ffpyplayer (incompatibile con Cython 3).
# Supporta flip orizzontale tramite scale_x = -1.

class SheetAnimImage(Widget):
    source  = StringProperty('')
    scale_x = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._frames   = []
        self._idx      = 0
        self._delay    = 0.1
        self._event    = None
        self._last_src = ''
        self.bind(source=self._on_source, pos=self._redraw, size=self._redraw,
                  scale_x=self._redraw)

    def _on_source(self, *_):
        src = self.source
        if src == self._last_src:
            return
        self._last_src = src
        self._stop_anim()
        self._frames = []
        self._idx    = 0
        if not src or not os.path.exists(src):
            self.canvas.clear()
            return
        self._load_frames(src)
        if self._frames:
            self._start_anim()
        self._redraw()

    def _load_frames(self, gif_path):
        _load_sheet_meta()
        anim_name  = os.path.splitext(os.path.basename(gif_path))[0]
        sheet_path = gif_path.replace('.gif', '_sheet.png')
        # Crouch non ha gif: il path è già un .gif fittizio, lo sheet è il PNG diretto
        if not sheet_path.endswith('_sheet.png'):
            sheet_path = gif_path  # fallback
        meta = _SHEET_META.get(anim_name)

        if os.path.exists(sheet_path) and meta:
            try:
                img    = _CoreImg(sheet_path, keep_data=True)
                tex    = img.texture
                fw, fh = meta['frame_w'], meta['frame_h']
                n      = meta['n_frames']
                self._delay = meta['delay_ms'] / 1000.0
                sheet_h = tex.height
                for i in range(n):
                    x   = i * fw
                    y   = sheet_h - fh
                    sub = tex.get_region(x, y, fw, fh)
                    self._frames.append(sub)
                return
            except Exception:
                self._frames = []

        # Fallback: prova il PNG direttamente (es. crouch = singolo frame PNG)
        png_direct = gif_path  # potrebbe già essere un path a _sheet.png
        if os.path.exists(png_direct):
            try:
                img = _CoreImg(png_direct, keep_data=True)
                self._frames = [img.texture]
                self._delay  = 0.2
                return
            except Exception:
                pass

    def _start_anim(self):
        if self._event:
            self._event.cancel()
        if len(self._frames) > 1:
            self._event = Clock.schedule_interval(self._next_frame, self._delay)

    def _stop_anim(self):
        if self._event:
            self._event.cancel()
            self._event = None

    def _next_frame(self, dt):
        if not self._frames:
            return
        self._idx = (self._idx + 1) % len(self._frames)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        if not self._frames:
            return
        tex = self._frames[self._idx]
        with self.canvas:
            GColor(1, 1, 1, 1)
            if self.scale_x < 0:
                # Flip orizzontale tramite tex_coords (compatibile con OpenGL ES / Android)
                Rectangle(texture=tex,
                           pos=self.pos, size=self.size,
                           tex_coords=(1, 0, 0, 0, 0, 1, 1, 1))
            else:
                Rectangle(texture=tex, pos=self.pos, size=self.size)

    def on_parent(self, *_):
        if self.parent and self._frames and not self._event:
            self._start_anim()
        elif not self.parent:
            self._stop_anim()

# ── KV files ──────────────────────────────────────────────────────────────────
Builder.load_file(_p('menu.kv'))
Builder.load_file(_p('fighter.kv'))

# ── Arene e personaggi ────────────────────────────────────────────────────────
ARENAS = [
    {'name': 'Il CAF',      'preview': _p('Images/Arena/wallpaper.png'), 'bg': _p('Images/Arena/wallpaper.png')},
    {'name': 'Frociest HQ', 'preview': _p('Images/Arena/HQ.png'),        'bg': _p('Images/Arena/HQ.png')},
]

def _char(name, folder, prefix, mirror, preview_name=None):
    pv = preview_name or f'{name}_preview'
    return {
        'name':        name,
        'preview':     _p(f'PG/Preview/{pv}.png'),
        'fullbody':    _p(f'PG/Preview/{name}_fullbody.png'),
        'idle':        _p(f'PG/{folder}/{prefix}_idle.gif'),
        'walk':        _p(f'PG/{folder}/{prefix}_walk.gif'),
        'jump':        _p(f'PG/{folder}/{prefix}_jump.gif'),
        'punch':       _p(f'PG/{folder}/{prefix}_punch.gif'),
        'kick':        _p(f'PG/{folder}/{prefix}_kick.gif'),
        # crouch: punta direttamente al PNG sheet (frame singolo)
        'crouch':      _p(f'PG/{folder}/{prefix}_crouch_sheet.png'),
        'mirror':      mirror,
        'placeholder': False,
        'placeholder_color': None,
    }

def _ph(color):
    return {'name':'???','placeholder':True,'placeholder_color':color,
            'fullbody':'','preview':'','idle':'','walk':'','jump':'',
            'punch':'','kick':'','crouch':'','mirror':False}

CHARACTERS = [
    _char('Jules', 'Jules', 'Jules', False, preview_name='Giuse_preview'),
    _char('Poz',   'Poz',   'Poz',   True),
    _char('Ruben', 'Ruben', 'Ruben', False),
    _ph([0.9, 0.7, 0.1, 1]), _ph([0.8, 0.3, 0.9, 1]),
    _ph([0.1, 0.8, 0.8, 1]), _ph([0.95,0.5, 0.1, 1]),
    _ph([0.5, 0.5, 0.5, 1]),
]

GAME_SETTINGS = {'music_on': True, 'timer': 90, 'rounds': 3}


def pick_enemy(player_index):
    choices = [i for i in range(len(CHARACTERS))
               if i != player_index and not CHARACTERS[i]['placeholder']]
    return random.choice(choices)


# ── Widget UI ─────────────────────────────────────────────────────────────────
class RoundButton(Widget):
    text      = StringProperty('')
    font_size = NumericProperty(24)
    btn_color = ListProperty([1, 1, 1, 0.3])


class Joystick(Widget):
    knob_pos       = ListProperty([0, 0])
    background_pos = ListProperty([0, 0])
    active         = BooleanProperty(False)
    dir_x          = NumericProperty(0)

    def on_touch_down(self, touch):
        if touch.x < Window.width / 2:
            self.active         = True
            self.background_pos = [touch.x - 100, touch.y - 100]
            self.knob_pos       = list(touch.pos)
            touch.ud['joystick'] = True
            return True
        return False

    def on_touch_move(self, touch):
        if touch.ud.get('joystick') and self.active:
            center    = Vector(self.background_pos) + Vector(100, 100)
            diff      = Vector(touch.pos) - center
            dist      = min(diff.length(), 100)
            direction = diff.normalize() if diff.length() > 0 else Vector(0, 0)
            self.knob_pos = list(center + direction * dist)
            self.dir_x = (1 if diff.x > 30 else -1 if diff.x < -30 else 0)
            return True

    def on_touch_up(self, touch):
        if touch.ud.get('joystick') and self.active:
            self.active = False
            self.dir_x  = 0
            return True


# ── Fighter ───────────────────────────────────────────────────────────────────
class Fighter(Widget):
    hp             = NumericProperty(250)
    vel_x          = NumericProperty(0)
    vel_y          = NumericProperty(0)
    is_crouching   = BooleanProperty(False)
    is_attacking   = BooleanProperty(False)
    attack_type    = ObjectProperty(None, allownone=True)
    current_source = StringProperty('')
    facing_left    = BooleanProperty(False)
    mirror_default = BooleanProperty(False)
    scale_x        = NumericProperty(1)
    anim_idle      = StringProperty('')
    anim_walk      = StringProperty('')
    anim_jump      = StringProperty('')
    anim_punch     = StringProperty('')
    anim_kick      = StringProperty('')
    anim_crouch    = StringProperty('')   # ← nuovo: animazione accovacciamento

    speed = 12; jump_force = 32; gravity = 1.6; ground_y = 50

    def _update_scale(self, *_):
        self.scale_x = (-1 if self.facing_left else 1) if not self.mirror_default \
                  else (-1 if not self.facing_left else 1)

    def on_facing_left(self, *_):    self._update_scale()
    def on_mirror_default(self, *_): self._update_scale()

    def jump(self):
        if self.y <= self.ground_y:
            self.vel_y = self.jump_force

    def apply_physics(self, input_dir, opponent_x=None):
        if self.is_attacking:
            new_src = self.anim_punch if self.attack_type == 'punch' else self.anim_kick
        elif self.y > self.ground_y:
            new_src = self.anim_jump
        elif self.is_crouching:
            # Usa animazione crouch dedicata se disponibile, altrimenti idle
            new_src = self.anim_crouch if self.anim_crouch and os.path.exists(self.anim_crouch) \
                      else self.anim_idle
        else:
            new_src = self.anim_walk if input_dir != 0 else self.anim_idle

        if input_dir > 0:       self.facing_left = False
        elif input_dir < 0:     self.facing_left = True
        elif opponent_x is not None:
            self.facing_left = opponent_x < self.center_x

        if self.current_source != new_src:
            self.current_source = new_src

        # Accovacciato: fermo
        if self.y <= self.ground_y:
            self.vel_x = 0 if self.is_crouching else input_dir * self.speed
        else:
            self.vel_x = self.vel_x * 0.9 + input_dir * 2

        self.x += self.vel_x
        self.y += self.vel_y
        if self.y > self.ground_y:
            self.vel_y -= self.gravity
        else:
            self.y = self.ground_y; self.vel_y = 0


# ── FighterGame ───────────────────────────────────────────────────────────────
class FighterGame(Widget):
    player   = ObjectProperty(None)
    enemy    = ObjectProperty(None)
    joystick = ObjectProperty(None)
    hitbox   = ObjectProperty(None)

    timer_text      = StringProperty('90')
    bg_source       = StringProperty('')
    countdown_image = StringProperty('')
    winner_image    = StringProperty('')
    player_wins     = NumericProperty(0)
    enemy_wins      = NumericProperty(0)
    wins_needed     = NumericProperty(2)
    max_dots        = NumericProperty(2)
    selected_char   = NumericProperty(0)
    enemy_char      = NumericProperty(0)

    enemy_is_placeholder    = BooleanProperty(True)
    enemy_placeholder_color = ListProperty([0.5, 0.5, 0.5, 1])
    enemy_source            = StringProperty('')
    enemy_punch_source      = StringProperty('')
    enemy_kick_source       = StringProperty('')
    enemy_crouch_source     = StringProperty('')   # ← nuovo
    paused   = BooleanProperty(False)
    player_x = NumericProperty(200)
    enemy_x  = NumericProperty(600)

    _time_left = 90.0; _round_duration = 90
    _round_active = False; _round_ending = False
    _player_name = ''; _enemy_name = ''
    _enemy_idle_source = ''

    def on_kv_post(self, base_widget):
        p = self.ids.player_id; e = self.ids.enemy_id
        p.bind(x=lambda i,v: setattr(self,'player_x',v))
        e.bind(x=lambda i,v: setattr(self,'enemy_x',v))
        e.bind(is_attacking=self._update_enemy_source,
               attack_type=self._update_enemy_source,
               is_crouching=self._update_enemy_source,
               current_source=lambda i,v: setattr(self,'enemy_source',v) if not i.is_attacking else None)
        self.player_x = p.x; self.enemy_x = e.x
        self.ids.btn_jump.bind(on_touch_down=self._btn_up_down)
        self.ids.btn_punch.bind(on_touch_down=self._btn_a_down)
        self.ids.btn_kick.bind(on_touch_down=self._btn_b_down)
        self.ids.btn_crouch.bind(on_touch_down=self._btn_down_down, on_touch_up=self._btn_down_up)
        self.ids.btn_pause.bind(on_touch_down=self._btn_pause_down)
        self.ids.btn_resume.bind(on_touch_down=self._btn_resume_down)
        self.ids.btn_pause_menu.bind(on_touch_down=self._btn_pause_menu_down)
        self.ids.btn_pause_quit.bind(on_touch_down=self._btn_pause_quit_down)

    def _setup_player(self):
        char = CHARACTERS[self.selected_char]; p = self.ids.player_id
        p.anim_idle   = char['idle']
        p.anim_walk   = char['walk']
        p.anim_jump   = char['jump']
        p.anim_punch  = char['punch']
        p.anim_kick   = char['kick']
        p.anim_crouch = char.get('crouch', '')
        p.current_source   = char['idle']
        p.mirror_default   = char['mirror']
        p.facing_left      = False
        self._player_name  = char['name']

    def _setup_enemy(self):
        char = CHARACTERS[self.enemy_char]; e = self.ids.enemy_id
        if char['placeholder']:
            self.enemy_is_placeholder    = True
            self.enemy_placeholder_color = char['placeholder_color']
            self.enemy_source = self.enemy_punch_source = self.enemy_kick_source = ''
            self.enemy_crouch_source = ''
            self._enemy_idle_source  = ''
            e.anim_idle = e.anim_walk = e.anim_jump = e.anim_punch = e.anim_kick = e.anim_crouch = ''
        else:
            self.enemy_is_placeholder = False
            self.enemy_source         = char['idle']
            self.enemy_punch_source   = char['punch']
            self.enemy_kick_source    = char['kick']
            self.enemy_crouch_source  = char.get('crouch', '')
            self._enemy_idle_source   = char['idle']
            e.anim_idle   = char['idle']
            e.anim_walk   = char['walk']
            e.anim_jump   = char['jump']
            e.anim_punch  = char['punch']
            e.anim_kick   = char['kick']
            e.anim_crouch = char.get('crouch', '')
            e.current_source   = char['idle']
            e.mirror_default   = char['mirror']
            e.facing_left      = True
        self._enemy_name     = char['name']
        self._round_duration = GAME_SETTINGS['timer']
        self._time_left      = float(self._round_duration)
        self.timer_text      = str(self._round_duration)
        rounds = GAME_SETTINGS['rounds']
        self.wins_needed = (rounds // 2) + 1
        self.max_dots    = self.wins_needed

    def _update_enemy_source(self, *_):
        e = self.ids.enemy_id
        if e.is_attacking:
            src = self.enemy_punch_source if e.attack_type == 'punch' else self.enemy_kick_source
            if src: self.enemy_source = src
        elif e.is_crouching and self.enemy_crouch_source:
            self.enemy_source = self.enemy_crouch_source
        else:
            self.enemy_source = self._enemy_idle_source

    def _start_countdown(self):
        self._round_active = False; self._round_ending = False
        self.winner_image  = ''; self.countdown_image = _p('Images/3.png')
        Clock.schedule_once(lambda dt: self._cd(2), 1)

    def _cd(self, n, *_):
        if n > 0:
            self.countdown_image = _p(f'Images/{n}.png')
            Clock.schedule_once(lambda dt: self._cd(n-1), 1)
        else:
            self.countdown_image = _p('Images/fight.png')
            self._round_active   = True
            Clock.schedule_once(lambda dt: setattr(self,'countdown_image',''), 0.8)

    def _show_winner(self, winner):
        name = self._player_name if winner == 'player' else self._enemy_name
        self.winner_image = _p(f'Images/{name}_wins.png')

    def _reset_round(self):
        p = self.ids.player_id; e = self.ids.enemy_id
        p.hp = e.hp = 250
        p.x = 200; p.y = p.ground_y; p.vel_x = p.vel_y = 0
        p.is_crouching = False; p.height = 500; p.facing_left = False
        e.x = self.width - 700; e.y = e.ground_y; e.vel_x = e.vel_y = 0
        self._time_left = float(self._round_duration)
        self.timer_text = str(self._round_duration)
        self._ai_timer = self._ai_action_timer = self._ai_crouch_timer = 0.0
        self._ai_dir = 0
        self._start_countdown()

    def _end_round(self, winner):
        if self._round_ending: return
        self._round_ending = True; self._round_active = False
        if winner == 'player': self.player_wins += 1
        else: self.enemy_wins += 1
        self._show_winner(winner)
        if self.player_wins >= self.wins_needed or self.enemy_wins >= self.wins_needed:
            Clock.schedule_once(lambda dt: self._go_to_menu(), 2.5)
        else:
            Clock.schedule_once(lambda dt: self._reset_round(), 2.5)

    def _go_to_menu(self, *_):
        self.paused = False; App.get_running_app().root.current = 'menu'

    def _btn_up_down(self, w, t):
        if w.collide_point(*t.pos) and self._round_active and not self.paused:
            self.ids.player_id.jump()

    def _btn_a_down(self, w, t):
        if w.collide_point(*t.pos) and self._round_active and not self.paused:
            self._do_attack(self.ids.player_id, 'punch')

    def _btn_b_down(self, w, t):
        if w.collide_point(*t.pos) and self._round_active and not self.paused:
            self._do_attack(self.ids.player_id, 'kick')

    def _btn_down_down(self, w, t):
        if w.collide_point(*t.pos) and self._round_active and not self.paused:
            p = self.ids.player_id
            p.is_crouching = True
            # Non ridimensionare più il widget: l'animazione crouch gestisce la posa

    def _btn_down_up(self, w, t):
        if w.collide_point(*t.pos):
            p = self.ids.player_id
            p.is_crouching = False

    def _btn_pause_down(self, w, t):
        if w.collide_point(*t.pos): self.paused = True; self._round_active = False

    def _btn_resume_down(self, w, t):
        if w.collide_point(*t.pos) and self.paused: self.paused = False; self._round_active = True

    def _btn_pause_menu_down(self, w, t):
        if w.collide_point(*t.pos) and self.paused: self._go_to_menu()

    def _btn_pause_quit_down(self, w, t):
        if w.collide_point(*t.pos) and self.paused: App.get_running_app().stop()

    def _do_attack(self, fighter, atype):
        if not fighter.is_attacking:
            fighter.is_attacking = True; fighter.attack_type = atype
            Clock.schedule_once(lambda dt: self._reset_atk(fighter), 0.35)

    def _reset_atk(self, fighter):
        fighter.is_attacking = False; fighter.attack_type = None

    def update(self, dt):
        if not self._round_active or self.paused: return
        p = self.ids.player_id; e = self.ids.enemy_id
        self._time_left -= dt
        if self._time_left <= 0:
            self._time_left = 0; self.timer_text = '0'
            self._end_round('player' if p.hp / 250.0 >= e.hp / 250.0 else 'enemy')
            return
        self.timer_text = str(int(self._time_left) + 1)
        p.apply_physics(self.ids.joystick_id.dir_x, opponent_x=e.center_x)
        p.x = max(0, min(p.x, self.width - p.width))
        self._update_ai(dt)
        self._check_collisions()
        if p.hp <= 0: self._end_round('enemy')
        elif e.hp <= 0: self._end_round('player')

    def _check_collisions(self):
        p = self.ids.player_id; e = self.ids.enemy_id
        if p.is_attacking:
            mx = e.width * 0.30
            if (p.x < e.x + e.width - mx and p.x + p.width > e.x + mx
                    and p.y < e.y + e.height * 0.85 and p.y + p.height > e.y):
                if p.attack_type == 'punch' and not e.is_crouching: e.hp = max(0, e.hp - 1)
                elif p.attack_type == 'kick' and e.y <= e.ground_y:  e.hp = max(0, e.hp - 1)
        if e.is_attacking:
            mx = p.width * 0.30
            if (e.x < p.x + p.width - mx and e.x + e.width > p.x + mx
                    and e.y < p.y + p.height * 0.85 and e.y + e.height > p.y):
                if e.attack_type == 'punch' and not p.is_crouching: p.hp = max(0, p.hp - 1)
                elif e.attack_type == 'kick' and p.y <= p.ground_y:  p.hp = max(0, p.hp - 1)

    _ai_timer = 0.0; _ai_action_timer = 0.0; _ai_dir = 0; _ai_crouch_timer = 0.0

    def _update_ai(self, dt):
        p = self.ids.player_id; e = self.ids.enemy_id
        self._ai_action_timer += dt; self._ai_crouch_timer += dt
        dist = p.x - e.x
        if abs(dist) > 350:   self._ai_dir = 1 if dist > 0 else -1
        elif abs(dist) < 120: self._ai_dir = -1 if dist > 0 else 1
        else:                  self._ai_dir = 0
        e.apply_physics(self._ai_dir, opponent_x=p.center_x)
        e.x = max(0, min(e.x, self.width - e.width))
        if self._ai_action_timer >= 0.8:
            self._ai_action_timer = 0.0
            if abs(dist) < 420 and not e.is_attacking:
                roll = random.random()
                if   roll < 0.35: self._do_attack(e, random.choice(['punch', 'kick']))
                elif roll < 0.55: e.jump()
                elif roll < 0.70: e.is_crouching = True; self._ai_crouch_timer = 0.0
        if e.is_crouching and self._ai_crouch_timer >= 0.4:
            e.is_crouching = False


# ── Schermate ─────────────────────────────────────────────────────────────────
class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self._go_to_menu, 5)
    def _go_to_menu(self, dt):
        App.get_running_app().start_music()
        self.manager.current = 'menu'


class MenuScreen(Screen):
    def on_kv_post(self, base_widget):
        self.ids.btn_start.bind(on_touch_down=lambda w,t: self.manager.__setattr__('current','charselect') if w.collide_point(*t.pos) else None)
        self.ids.btn_options.bind(on_touch_down=lambda w,t: self.manager.__setattr__('current','options') if w.collide_point(*t.pos) else None)
        self.ids.btn_quit.bind(on_touch_down=lambda w,t: App.get_running_app().stop() if w.collide_point(*t.pos) else None)


class OptionsScreen(Screen):
    tmp_music_on = BooleanProperty(True)
    tmp_timer    = NumericProperty(90)
    tmp_rounds   = NumericProperty(3)
    show_confirm = BooleanProperty(False)

    def on_enter(self):
        self.tmp_music_on = GAME_SETTINGS['music_on']
        self.tmp_timer    = GAME_SETTINGS['timer']
        self.tmp_rounds   = GAME_SETTINGS['rounds']
        self.show_confirm = False

    def on_kv_post(self, base_widget):
        self.ids.btn_music_toggle.bind(on_touch_down=lambda w,t: setattr(self,'tmp_music_on',True) if w.collide_point(*t.pos) and not self.show_confirm else None)
        self.ids.btn_music_toggle_off.bind(on_touch_down=lambda w,t: setattr(self,'tmp_music_on',False) if w.collide_point(*t.pos) and not self.show_confirm else None)
        for v in (10, 60, 90, 120):
            self.ids[f'btn_timer_{v}'].bind(on_touch_down=lambda w,t,val=v: setattr(self,'tmp_timer',val) if w.collide_point(*t.pos) and not self.show_confirm else None)
        for v in (3, 5):
            self.ids[f'btn_rounds_{v}'].bind(on_touch_down=lambda w,t,val=v: setattr(self,'tmp_rounds',val) if w.collide_point(*t.pos) and not self.show_confirm else None)
        self.ids.btn_save.bind(on_touch_down=self._save)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        self.ids.btn_confirm_save.bind(on_touch_down=self._confirm_save_and_back)
        self.ids.btn_confirm_discard.bind(on_touch_down=self._confirm_discard)

    def _apply(self):
        GAME_SETTINGS['music_on'] = self.tmp_music_on
        GAME_SETTINGS['timer']    = self.tmp_timer
        GAME_SETTINGS['rounds']   = self.tmp_rounds
        app = App.get_running_app()
        if app._music:
            if self.tmp_music_on and app._music.state != 'play': app._music.play()
            elif not self.tmp_music_on: app._music.stop()

    def _save(self, w, t):
        if w.collide_point(*t.pos) and not self.show_confirm:
            self._apply(); self.manager.current = 'menu'

    def _go_back(self, w, t):
        if w.collide_point(*t.pos) and not self.show_confirm:
            changed = (self.tmp_music_on != GAME_SETTINGS['music_on'] or
                       self.tmp_timer    != GAME_SETTINGS['timer']    or
                       self.tmp_rounds   != GAME_SETTINGS['rounds'])
            if changed: self.show_confirm = True
            else: self.manager.current = 'menu'

    def _confirm_save_and_back(self, w, t):
        if w.collide_point(*t.pos) and self.show_confirm:
            self._apply(); self.show_confirm = False; self.manager.current = 'menu'

    def _confirm_discard(self, w, t):
        if w.collide_point(*t.pos) and self.show_confirm:
            self.show_confirm = False; self.manager.current = 'menu'


class CharSelectScreen(Screen):
    selected                = NumericProperty(0)
    idle_source             = StringProperty('')
    idle_mirror             = BooleanProperty(False)
    fullbody_source         = StringProperty('')
    enemy_idle_source       = StringProperty('')
    enemy_idle_mirror       = BooleanProperty(False)
    enemy_fullbody_source   = StringProperty('')
    enemy_placeholder       = BooleanProperty(False)
    enemy_placeholder_color = ListProperty([0.5, 0.5, 0.5, 1])
    _confirmed              = BooleanProperty(False)
    _enemy_idx              = NumericProperty(-1)
    _timer_event = None; _roulette_event = None
    _roulette_step = 0;  _roulette_target = 0
    _char_ids = ['char_0','char_1','char_2','char_3','char_4','char_5','char_6','char_7']

    def on_kv_post(self, base_widget):
        for cid in self._char_ids:
            self.ids[cid].bind(on_touch_down=self._on_char_touch)
        self.ids.btn_fight.bind(on_touch_down=self._confirm)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        Clock.schedule_once(lambda dt: self._update_selection(), 0)

    def on_leave(self):
        self._cancel_roulette()
        if self._timer_event: self._timer_event.cancel(); self._timer_event = None
        self._confirmed = False
        self.enemy_idle_source = self.enemy_fullbody_source = ''
        self.enemy_placeholder = False
        if 'enemy_border' in self.ids: self.ids.enemy_border.opacity = 0

    def _on_char_touch(self, widget, touch):
        if self._confirmed or not widget.collide_point(*touch.pos): return
        for i, cid in enumerate(self._char_ids):
            if self.ids[cid] == widget: self.selected = i; self._update_selection()

    def _update_selection(self):
        if 'char_name_label' not in self.ids: return
        char = CHARACTERS[self.selected]
        if not char['placeholder']:
            self.ids.char_name_label.text = char['name']
            self.idle_source    = char['idle']
            self.idle_mirror    = char['mirror']
            self.fullbody_source = char['fullbody']
        else:
            self.ids.char_name_label.text = '???'
            self.idle_source = ''; self.idle_mirror = False; self.fullbody_source = ''

    def _cancel_roulette(self):
        if self._roulette_event: self._roulette_event.cancel(); self._roulette_event = None

    def _confirm(self, w, t):
        if w.collide_point(*t.pos) and not self._confirmed:
            self._confirmed      = True
            self._roulette_target = pick_enemy(self.selected)
            self._roulette_step  = 0
            self.ids.enemy_border.opacity = 1
            self._roulette_event = Clock.schedule_interval(self._roulette_tick, 0.08)
            Clock.schedule_once(self._roulette_end, 1.5)

    def _roulette_tick(self, dt):
        idx = self._roulette_step % len(self._char_ids); self._roulette_step += 1
        target = self.ids[self._char_ids[idx]]
        self.ids.enemy_border.pos = (target.x - 4, target.y - 4)

    def _roulette_end(self, dt):
        self._cancel_roulette()
        ei = self._roulette_target; self._enemy_idx = ei
        target = self.ids[self._char_ids[ei]]
        self.ids.enemy_border.pos = (target.x - 4, target.y - 4)
        enemy = CHARACTERS[ei]
        if enemy['placeholder']:
            self.enemy_placeholder       = True
            self.enemy_placeholder_color = enemy['placeholder_color']
            self.enemy_idle_source = self.enemy_fullbody_source = ''
            self.enemy_idle_mirror = False
        else:
            self.enemy_placeholder    = False
            self.enemy_idle_source    = enemy['idle']
            self.enemy_idle_mirror    = not enemy['mirror']
            self.enemy_fullbody_source = enemy['fullbody']
        self._timer_event = Clock.schedule_once(self._go_arenaselect, 0.5)

    def _go_arenaselect(self, *_):
        s = self.manager.get_screen('arenaselect')
        s.selected_char = self.selected; s.enemy_char = self._enemy_idx
        self.manager.current = 'arenaselect'

    def _go_back(self, w, t):
        if w.collide_point(*t.pos) and not self._confirmed:
            self.manager.current = 'menu'


class ArenaSelectScreen(Screen):
    selected = NumericProperty(0); selected_char = NumericProperty(0); enemy_char = NumericProperty(0)
    _arena_ids = ['arena_0', 'arena_1']

    def on_kv_post(self, base_widget):
        for aid in self._arena_ids: self.ids[aid].bind(on_touch_down=self._on_arena_touch)
        self.ids.btn_fight.bind(on_touch_down=self._go_fight)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        self._update_selection()

    def _on_arena_touch(self, widget, touch):
        if not widget.collide_point(*touch.pos): return
        for i, aid in enumerate(self._arena_ids):
            if self.ids[aid] == widget: self.selected = i; self._update_selection()

    def _update_selection(self):
        self.ids.arena_preview.source = ARENAS[self.selected]['preview']
        target = self.ids[self._arena_ids[self.selected]]
        self.ids.arena_border.pos = (target.x - 3, target.y - 3)

    def _go_fight(self, w, t):
        if w.collide_point(*t.pos):
            game = self.manager.get_screen('game')
            game.selected_char = self.selected_char; game.enemy_char = self.enemy_char
            game.bg_source     = ARENAS[self.selected]['bg']
            self.manager.current = 'game'

    def _go_back(self, w, t):
        if w.collide_point(*t.pos): self.manager.current = 'charselect'


class GameScreen(Screen):
    selected_char = NumericProperty(0); enemy_char = NumericProperty(0)
    bg_source = StringProperty(''); _update_event = None

    def on_enter(self):
        game = self.ids.game_widget
        game.selected_char = self.selected_char; game.enemy_char = self.enemy_char
        game.bg_source = self.bg_source; game.paused = False
        game.player_wins = game.enemy_wins = 0
        game.winner_image = game.countdown_image = ''
        game._round_active = game._round_ending = False
        game._setup_player(); game._setup_enemy()
        p = game.ids.player_id; e = game.ids.enemy_id
        p.hp = e.hp = 250
        p.x = 200; p.y = p.ground_y; p.vel_x = p.vel_y = 0
        p.is_crouching = p.is_attacking = False; p.attack_type = None
        p.height = 500; p.facing_left = False
        e.x = game.width - 700; e.y = e.ground_y; e.vel_x = e.vel_y = 0
        self._update_event = Clock.schedule_interval(game.update, 1.0 / 60.0)
        Clock.schedule_once(lambda dt: game._start_countdown(), 0.3)
        App.get_running_app().start_combat_music()

    def on_leave(self):
        if self._update_event: self._update_event.cancel(); self._update_event = None
        App.get_running_app().stop_combat_music()


class GameApp(App):
    kv_file = None; _music = None; _combat = None

    def _load_sound(self, *paths):
        for p in paths:
            full = _p(p)
            if os.path.exists(full):
                try:
                    s = SoundLoader.load(full)
                    if s: return s
                except Exception: pass
        return None

    def start_music(self):
        if self._music:
            if self._music.state != 'play' and GAME_SETTINGS['music_on']: self._music.play()
            return
        s = self._load_sound('Audio/jingle.ogg', 'Audio/jingle.mp3')
        if s: s.loop = True; (s.play() if GAME_SETTINGS['music_on'] else None); self._music = s

    def start_combat_music(self):
        if self._music and self._music.state == 'play': self._music.stop()
        if not self._combat:
            self._combat = self._load_sound('Audio/combat.ogg', 'Audio/combat.mp3')
            if self._combat: self._combat.loop = True
        if self._combat and self._combat.state != 'play': self._combat.play()

    def stop_combat_music(self):
        if self._combat and self._combat.state == 'play': self._combat.stop()
        if self._music and GAME_SETTINGS['music_on']: self._music.play()

    def on_pause(self): return True
    def on_resume(self): pass

    def build(self):
        sm = ScreenManager(transition=NoTransition())
        for name, cls in [('splash', SplashScreen), ('menu', MenuScreen),
                          ('options', OptionsScreen), ('charselect', CharSelectScreen),
                          ('arenaselect', ArenaSelectScreen), ('game', GameScreen)]:
            sm.add_widget(cls(name=name))
        sm.current = 'splash'
        return sm

if __name__ == '__main__':
    GameApp().run()
