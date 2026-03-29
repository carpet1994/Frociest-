"""
Frociest Rumble
Android: buildozer con requirements=python3,pygame,android,pyjnius,pillow
Desktop: pip install pygame
"""

import os, sys, random, math
os.environ.setdefault('SDL_AUDIODRIVER', 'openslES')   # Android audio

# ── Android: forza landscape prima di init ────────────────────────────────────
try:
    import android                                      # type: ignore
    from android.runnable import run_on_ui_thread       # type: ignore
    from jnius import autoclass                         # type: ignore
    import time
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    ActivityInfo   = autoclass('android.content.pm.ActivityInfo')
    @run_on_ui_thread
    def _force_landscape():
        PythonActivity.mActivity.setRequestedOrientation(
            ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE)
    _force_landscape()
    time.sleep(0.35)   # attende che Android applichi la rotazione
    ON_ANDROID = True
except Exception:
    ON_ANDROID = False

import pygame
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.init()
pygame.mixer.init()

W, H = 1280, 720
if ON_ANDROID:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    W, H   = screen.get_size()
else:
    screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Frociest Rumble")
clock = pygame.time.Clock()
FPS   = 60

# Recalculate after real dimensions are known
GROUND_Y = H - 80

_BASE = os.path.dirname(os.path.abspath(__file__))
def _p(rel): return os.path.join(_BASE, rel)

# ── Font helpers ──────────────────────────────────────────────────────────────
_font_cache: dict = {}
def font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        _font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _font_cache[key]

def draw_text(surf, text, size, color, cx, cy, bold=False, alpha=255):
    f   = font(size, bold)
    img = f.render(text, True, color)
    if alpha < 255:
        img.set_alpha(alpha)
    r = img.get_rect(center=(cx, cy))
    surf.blit(img, r)

# ── Image / GIF loader ────────────────────────────────────────────────────────
_img_cache: dict = {}

def load_image(path, size=None):
    """Load PNG/JPG; returns Surface or None."""
    if not path or not os.path.exists(path):
        return None
    key = (path, size)
    if key in _img_cache:
        return _img_cache[key]
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        _img_cache[key] = img
        return img
    except Exception:
        return None

# ── Sprite sheet metadata ─────────────────────────────────────────────────────
import json as _json
_SHEET_META: dict = {}

def _load_sheet_meta():
    global _SHEET_META
    if _SHEET_META:
        return
    meta_path = _p('PG/anim_meta.json')
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r') as _f:
                _SHEET_META = _json.load(_f)
        except Exception:
            pass

def load_gif(path):
    """
    Carica animazione da sprite sheet PNG (_sheet.png) se disponibile,
    altrimenti fallback su GIF via Pillow (desktop).
    Ritorna list of (Surface, delay_ms).
    """
    if not path or not os.path.exists(path):
        return []
    key = ('gif', path)
    if key in _img_cache:
        return _img_cache[key]

    _load_sheet_meta()
    frames = []

    # Priorità: sprite sheet PNG (funziona su Android senza Pillow)
    sheet_path = path.replace('.gif', '_sheet.png')
    anim_name  = os.path.splitext(os.path.basename(path))[0]
    meta       = _SHEET_META.get(anim_name)

    if os.path.exists(sheet_path) and meta:
        try:
            sheet = pygame.image.load(sheet_path).convert_alpha()
            fw    = meta['frame_w']
            fh    = meta['frame_h']
            n     = meta['n_frames']
            delay = meta['delay_ms']
            for i in range(n):
                frame = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
                frames.append((frame, delay))
        except Exception:
            frames = []

    # Fallback: GIF via Pillow (solo desktop) o frame singolo
    if not frames:
        try:
            from PIL import Image as PILImage      # type: ignore
            pil = PILImage.open(path)
            try:
                while True:
                    delay = pil.info.get('duration', 80)
                    frame = pil.convert('RGBA')
                    raw   = frame.tobytes()
                    surf  = pygame.image.frombytes(raw, frame.size, 'RGBA').convert_alpha()
                    frames.append((surf, max(delay, 40)))
                    pil.seek(pil.tell() + 1)
            except EOFError:
                pass
        except ImportError:
            try:
                surf = pygame.image.load(path).convert_alpha()
                frames = [(surf, 100)]
            except Exception:
                pass

    _img_cache[key] = frames
    return frames


# ── GIF Animator ─────────────────────────────────────────────────────────────
class GifAnim:
    def __init__(self):
        self.frames   = []
        self.idx      = 0
        self.elapsed  = 0
        self._path    = ''

    def set_gif(self, path):
        if path == self._path:
            return
        self._path   = path
        self.frames  = load_gif(path)
        self.idx     = 0
        self.elapsed = 0

    def update(self, dt_ms):
        if not self.frames:
            return
        self.elapsed += dt_ms
        delay = self.frames[self.idx][1]
        if self.elapsed >= delay:
            self.elapsed -= delay
            self.idx = (self.idx + 1) % len(self.frames)

    def get_frame(self):
        if not self.frames:
            return None
        return self.frames[self.idx][0]

# ── Draw helpers ──────────────────────────────────────────────────────────────
def draw_rect_rounded(surf, color, rect, radius=14, alpha=255):
    if alpha < 255:
        tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surf.blit(tmp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surf, color, rect, border_radius=radius)

def draw_ellipse_a(surf, color, rect, alpha=255):
    if alpha < 255:
        tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, (*color[:3], alpha), (0, 0, rect[2], rect[3]))
        surf.blit(tmp, (rect[0], rect[1]))
    else:
        pygame.draw.ellipse(surf, color, rect)

def draw_image_centered(surf, img, cx, cy, flip_x=False, scale=1.0):
    if img is None: return
    s = img
    if scale != 1.0:
        nw = int(s.get_width()  * scale)
        nh = int(s.get_height() * scale)
        if nw < 1 or nh < 1: return
        s  = pygame.transform.smoothscale(s, (nw, nh))
    if flip_x:
        s = pygame.transform.flip(s, True, False)
    r = s.get_rect(center=(cx, cy))
    surf.blit(s, r)

def draw_image_fit(surf, img, rect, flip_x=False):
    """Blit image scaled to fit rect, preserving aspect ratio."""
    if img is None: return
    iw, ih = img.get_size()
    rw, rh = rect[2], rect[3]
    if rw <= 0 or rh <= 0 or iw <= 0 or ih <= 0: return
    scale = min(rw / iw, rh / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    s = pygame.transform.smoothscale(img, (nw, nh))
    if flip_x:
        s = pygame.transform.flip(s, True, False)
    blit_x = rect[0] + (rw - nw) // 2
    blit_y = rect[1] + (rh - nh) // 2
    surf.blit(s, (blit_x, blit_y))

# ── Sound ─────────────────────────────────────────────────────────────────────
_snd_cache: dict = {}
def load_sound(*paths):
    for p in paths:
        full = _p(p)
        if not os.path.exists(full): continue
        if full in _snd_cache: return _snd_cache[full]
        try:
            s = pygame.mixer.Sound(full)
            _snd_cache[full] = s
            return s
        except Exception:
            pass
    return None

# ── Game data ─────────────────────────────────────────────────────────────────
def _char(name, folder, prefix, mirror, preview_name=None):
    pv = preview_name or f'{name}_preview'
    return {
        'name':    name,
        'preview': _p(f'PG/Preview/{pv}.png'),
        'fullbody':_p(f'PG/Preview/{name}_fullbody.png'),
        'idle':    _p(f'PG/{folder}/{prefix}_idle.gif'),
        'walk':    _p(f'PG/{folder}/{prefix}_walk.gif'),
        'jump':    _p(f'PG/{folder}/{prefix}_jump.gif'),
        'punch':   _p(f'PG/{folder}/{prefix}_punch.gif'),
        'kick':    _p(f'PG/{folder}/{prefix}_kick.gif'),
        'mirror':  mirror,
        'placeholder': False,
        'placeholder_color': None,
    }

def _ph(color):
    return {'name':'???','placeholder':True,'placeholder_color':color,
            'fullbody':'','preview':'','idle':'','walk':'','jump':'',
            'punch':'','kick':'','mirror':False}

CHARACTERS = [
    _char('Jules','Jules','Jules', False, preview_name='Giuse_preview'),
    _char('Poz',  'Poz',  'poz',   True),
    _char('Ruben','Ruben','Ruben', False),
    _ph([230,178,25]), _ph([204,76,229]),
    _ph([25,204,204]), _ph([242,127,25]),
    _ph([127,127,127]),
]

ARENAS = [
    {'name':'Il CAF',      'preview':_p('Images/Arena/wallpaper.png'), 'bg':_p('Images/Arena/wallpaper.png')},
    {'name':'Frociest HQ', 'preview':_p('Images/Arena/HQ.png'),       'bg':_p('Images/Arena/HQ.png')},
]

GAME_SETTINGS = {'music_on': True, 'timer': 90, 'rounds': 3}

def pick_enemy(player_index):
    choices = [i for i in range(len(CHARACTERS))
               if i != player_index and not CHARACTERS[i]['placeholder']]
    return random.choice(choices)

# ── Music ─────────────────────────────────────────────────────────────────────
_music_playing  = None
_combat_channel = None
_combat_snd     = None

def start_menu_music():
    global _music_playing, _combat_channel
    if _combat_channel:
        _combat_channel.stop(); _combat_channel = None
    if not GAME_SETTINGS['music_on']:
        pygame.mixer.music.stop(); _music_playing = None; return
    if _music_playing == 'menu': return
    for p in ('Audio/jingle.ogg','Audio/jingle.mp3'):
        full = _p(p)
        if os.path.exists(full):
            try:
                pygame.mixer.music.load(full)
                pygame.mixer.music.set_volume(0.7)
                pygame.mixer.music.play(-1)
                _music_playing = 'menu'
                return
            except Exception: pass

def start_combat_music():
    global _music_playing, _combat_channel, _combat_snd
    pygame.mixer.music.stop(); _music_playing = None
    if _combat_snd is None:
        _combat_snd = load_sound('Audio/combat.ogg','Audio/combat.mp3')
    if _combat_snd:
        _combat_channel = _combat_snd.play(-1)

def stop_combat_music():
    global _combat_channel
    if _combat_channel:
        _combat_channel.stop(); _combat_channel = None

def set_music(on):
    GAME_SETTINGS['music_on'] = on
    if on:
        if _music_playing != 'menu': start_menu_music()
    else:
        pygame.mixer.music.stop()

# ══════════════════════════════════════════════════════════════════════════════
# Fighter
# ══════════════════════════════════════════════════════════════════════════════
FIGHTER_W = 200
FIGHTER_H = 350

class Fighter:
    SPEED      = 9
    JUMP_FORCE = -22
    GRAVITY    = 1.1

    def __init__(self, x, facing_left, char):
        self.x            = float(x)
        self.y            = float(GROUND_Y)
        self.vel_x        = 0.0
        self.vel_y        = 0.0
        self.hp           = 250
        self.is_crouching = False
        self.is_attacking = False
        self.attack_type  = None
        self.facing_left  = facing_left
        self.mirror_default = char['mirror']
        self.char         = char
        self.anim         = GifAnim()
        self._h           = FIGHTER_H
        self._atk_timer   = 0.0
        self._set_anim('idle')

    @property
    def center_x(self): return self.x + FIGHTER_W / 2

    def _set_anim(self, state):
        if self.char['placeholder']: return
        p = self.char.get(state, '')
        if not p or not os.path.exists(p):
            p = self.char.get('idle', '')
        self.anim.set_gif(p)

    def _choose_anim(self, input_dir):
        if self.is_attacking:
            return 'punch' if self.attack_type == 'punch' else 'kick'
        if self.y < GROUND_Y - 2: return 'jump'
        if self.is_crouching:     return 'idle'
        return 'walk' if input_dir != 0 else 'idle'

    def jump(self):
        if self.y >= GROUND_Y - 2:
            self.vel_y = self.JUMP_FORCE

    def start_attack(self, atype):
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_type  = atype
            self._atk_timer   = 0.35

    def crouch(self, val):
        self.is_crouching = val
        self._h = int(FIGHTER_H * 0.55) if val else FIGHTER_H

    def update(self, dt, input_dir, opponent_x=None):
        if input_dir > 0:   self.facing_left = False
        elif input_dir < 0: self.facing_left = True
        elif opponent_x is not None:
            self.facing_left = opponent_x < self.center_x

        self._set_anim(self._choose_anim(input_dir))
        self.anim.update(dt * 1000)

        if self.is_attacking:
            self._atk_timer -= dt
            if self._atk_timer <= 0:
                self.is_attacking = False
                self.attack_type  = None

        on_ground = self.y >= GROUND_Y - 2
        if on_ground:
            self.vel_x = 0 if self.is_crouching else input_dir * self.SPEED
        else:
            self.vel_x = self.vel_x * 0.9 + input_dir * 1.5

        self.x += self.vel_x
        self.y += self.vel_y
        if not on_ground:
            self.vel_y += self.GRAVITY
        if self.y >= GROUND_Y:
            self.y = GROUND_Y; self.vel_y = 0

    def draw(self, surf):
        dw, dh = FIGHTER_W, self._h
        flip = (not self.facing_left) if self.mirror_default else self.facing_left

        if self.char['placeholder']:
            c = self.char['placeholder_color'][:3]
            pygame.draw.rect(surf, c, (int(self.x), int(self.y) - dh, dw, dh))
        else:
            frame = self.anim.get_frame()
            if frame:
                scaled = pygame.transform.smoothscale(frame, (dw, dh))
                if flip:
                    scaled = pygame.transform.flip(scaled, True, False)
                surf.blit(scaled, (int(self.x), int(self.y) - dh))

# ══════════════════════════════════════════════════════════════════════════════
# Virtual Joystick
# ══════════════════════════════════════════════════════════════════════════════
class VirtualJoystick:
    RADIUS = 90
    KNOB_R = 36

    def __init__(self):
        self.active  = False
        self.cx = self.cy = 0
        self.kx = self.ky = 0
        self.dir_x   = 0
        self._finger = None

    def handle_down(self, x, y, fid):
        if x < W // 2:
            self.active = True
            self.cx, self.cy = x, y
            self.kx, self.ky = x, y
            self._finger = fid
            self.dir_x   = 0
            return True
        return False

    def handle_move(self, x, y, fid):
        if not self.active or fid != self._finger: return
        dx = x - self.cx; dy = y - self.cy
        dist = math.hypot(dx, dy)
        if dist > self.RADIUS:
            dx *= self.RADIUS / dist
            dy *= self.RADIUS / dist
        self.kx = self.cx + dx
        self.ky = self.cy + dy
        self.dir_x = 1 if dx > 25 else (-1 if dx < -25 else 0)

    def handle_up(self, fid):
        if fid == self._finger:
            self.active  = False
            self.dir_x   = 0
            self._finger = None

    def draw(self, surf):
        if not self.active: return
        s = pygame.Surface((self.RADIUS*2+2, self.RADIUS*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,255,255,60), (self.RADIUS+1, self.RADIUS+1), self.RADIUS, 3)
        surf.blit(s, (int(self.cx)-self.RADIUS-1, int(self.cy)-self.RADIUS-1))
        pygame.draw.circle(surf, (255,255,255), (int(self.kx), int(self.ky)), self.KNOB_R)

# ══════════════════════════════════════════════════════════════════════════════
# Buttons
# ══════════════════════════════════════════════════════════════════════════════
class CircleButton:
    def __init__(self, cx, cy, r, label, color):
        self.cx = cx; self.cy = cy; self.r = r
        self.label = label; self.color = color

    def hit(self, x, y): return math.hypot(x-self.cx, y-self.cy) <= self.r

    def draw(self, surf):
        s = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 140), (self.r, self.r), self.r)
        surf.blit(s, (self.cx-self.r, self.cy-self.r))
        draw_text(surf, self.label, 32, (255,255,255), self.cx, self.cy, bold=True)

class RectButton:
    def __init__(self, x, y, w, h, label, color, font_size=36, radius=18):
        self.rect   = pygame.Rect(x, y, w, h)
        self.label  = label; self.color = color
        self.fs     = font_size; self.radius = radius

    def hit(self, x, y): return self.rect.collidepoint(x, y)

    def draw(self, surf, alpha=220):
        draw_rect_rounded(surf, self.color, self.rect, self.radius, alpha)
        draw_text(surf, self.label, self.fs, (255,255,255),
                  self.rect.centerx, self.rect.centery, bold=True)

# ══════════════════════════════════════════════════════════════════════════════
# Touch helper
# ══════════════════════════════════════════════════════════════════════════════
def _touch_pos(ev):
    if ev.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
        # p4a (python-for-android) with pygame: coordinates are normalized 0..1
        # but on some builds they may already be pixel coords — detect by range
        x, y = ev.x, ev.y
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
            return int(x * W), int(y * H)
        return int(x), int(y)
    return ev.pos

# ══════════════════════════════════════════════════════════════════════════════
# Base Screen
# ══════════════════════════════════════════════════════════════════════════════
class Screen:
    def on_enter(self): pass
    def on_leave(self): pass
    def handle_event(self, event): pass
    def update(self, dt): pass
    def draw(self, surf): pass

# ── Splash ────────────────────────────────────────────────────────────────────
class SplashScreen(Screen):
    def on_enter(self):
        self._timer = 5.0
        self._logo  = load_image(_p('Images/dev.png'))

    def update(self, dt):
        self._timer -= dt
        if self._timer <= 0:
            start_menu_music()
            return 'menu'

    def draw(self, surf):
        surf.fill((0,0,0))
        draw_text(surf, "Developed by", 32, (255,255,255), W//2, H//2 - int(H*0.22), bold=True)
        if self._logo:
            size = int(H * 0.55)
            sc = size / self._logo.get_height()
            draw_image_centered(surf, self._logo, W//2, H//2, scale=sc)

# ── Menu ──────────────────────────────────────────────────────────────────────
class MenuScreen(Screen):
    def on_enter(self):
        bw, bh = 320, 90
        cx = W // 2
        self._logo = load_image(_p('Images/game_logo.png'))
        self._btns = [
            RectButton(cx-bw//2, int(H*0.40), bw, bh, "START",   (25,204,76)),
            RectButton(cx-bw//2, int(H*0.24), bw, bh, "OPTIONS", (25,102,229)),
            RectButton(cx-bw//2, int(H*0.08), bw, bh, "QUIT",    (191,25,25)),
        ]

    def handle_event(self, ev):
        if ev.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN): return
        x, y = _touch_pos(ev)
        if self._btns[0].hit(x,y): return 'charselect'
        if self._btns[1].hit(x,y): return 'options'
        if self._btns[2].hit(x,y): return 'quit'

    def draw(self, surf):
        surf.fill((38,38,38))
        if self._logo:
            lh = int(H * 0.42)
            lw = int(lh * self._logo.get_width() / self._logo.get_height())
            lw = min(lw, int(W * 0.75))
            img = pygame.transform.smoothscale(self._logo, (lw, lh))
            surf.blit(img, (W//2 - lw//2, int(H*0.55)))
        for b in self._btns: b.draw(surf)

# ── Options ───────────────────────────────────────────────────────────────────
class OptionsScreen(Screen):
    def on_enter(self):
        self._music_on = GAME_SETTINGS['music_on']
        self._timer    = GAME_SETTINGS['timer']
        self._rounds   = GAME_SETTINGS['rounds']
        self._confirm  = False
        self._build()

    def _build(self):
        hw = (W - 60) // 2
        self._btn_on  = RectButton(30,      int(H*0.71), hw, 72, "ON",  (60,60,70), 30)
        self._btn_off = RectButton(30+hw+6, int(H*0.71), hw, 72, "OFF", (60,60,70), 30)
        tw = (W - 58) // 4
        self._btn_t = [(v, RectButton(30+i*(tw+6), int(H*0.54), tw, 72, str(v), (60,60,70), 28))
                       for i,v in enumerate((10,60,90,120))]
        rw = (W - 52) // 2
        self._btn_r = [(v, RectButton(30+i*(rw+6), int(H*0.37), rw, 72, str(v), (60,60,70), 28))
                       for i,v in enumerate((3,5))]
        self._btn_save = RectButton(30,    int(H*0.12), 280, 80, "SAVE",   (25,178,51))
        self._btn_back = RectButton(W-220, int(H*0.12), 180, 60, "< BACK", (76,76,76), 26)
        self._btn_cs   = RectButton(W//2-170, H//2+10, 160, 70, "SAVE",    (25,178,51))
        self._btn_cd   = RectButton(W//2+10,  H//2+10, 160, 70, "DISCARD", (191,25,25))

    def handle_event(self, ev):
        if ev.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN): return
        x, y = _touch_pos(ev)
        if self._confirm:
            if self._btn_cs.hit(x,y): self._apply(); return 'menu'
            if self._btn_cd.hit(x,y): self._confirm = False
            return
        if self._btn_on.hit(x,y):  self._music_on = True
        if self._btn_off.hit(x,y): self._music_on = False
        for v,b in self._btn_t:
            if b.hit(x,y): self._timer = v
        for v,b in self._btn_r:
            if b.hit(x,y): self._rounds = v
        if self._btn_save.hit(x,y): self._apply(); return 'menu'
        if self._btn_back.hit(x,y):
            changed = (self._music_on != GAME_SETTINGS['music_on'] or
                       self._timer   != GAME_SETTINGS['timer'] or
                       self._rounds  != GAME_SETTINGS['rounds'])
            if changed: self._confirm = True
            else: return 'menu'

    def _apply(self):
        GAME_SETTINGS['music_on'] = self._music_on
        GAME_SETTINGS['timer']    = self._timer
        GAME_SETTINGS['rounds']   = self._rounds
        self._confirm = False
        set_music(self._music_on)

    def draw(self, surf):
        surf.fill((25,25,25))
        draw_text(surf, "OPTIONS", 54, (255,255,255), W//2, int(H*0.90), bold=True)
        draw_text(surf, "Music",            32, (153,153,153), 120, int(H*0.79)+18, bold=True)
        self._btn_on.draw(surf, 220);  self._btn_off.draw(surf, 220)
        pygame.draw.rect(surf, (255,204,25) if self._music_on     else (80,80,80), self._btn_on.rect,  3, border_radius=10)
        pygame.draw.rect(surf, (255,204,25) if not self._music_on else (80,80,80), self._btn_off.rect, 3, border_radius=10)
        draw_text(surf, "Timer (seconds)", 32, (153,153,153), 200, int(H*0.62)+18, bold=True)
        for v,b in self._btn_t:
            b.draw(surf, 220)
            if v == self._timer: pygame.draw.rect(surf, (255,204,25), b.rect, 3, border_radius=10)
        draw_text(surf, "Rounds",          32, (153,153,153), 120, int(H*0.45)+18, bold=True)
        for v,b in self._btn_r:
            b.draw(surf, 220)
            if v == self._rounds: pygame.draw.rect(surf, (255,204,25), b.rect, 3, border_radius=10)
        self._btn_save.draw(surf); self._btn_back.draw(surf)
        if self._confirm:
            ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,170)); surf.blit(ov,(0,0))
            draw_text(surf, "Save changes?", 44, (255,255,255), W//2, H//2-30, bold=True)
            self._btn_cs.draw(surf); self._btn_cd.draw(surf)

# ── Char Select ───────────────────────────────────────────────────────────────
class CharSelectScreen(Screen):
    CS = 130   # char thumbnail size

    def on_enter(self):
        self._selected   = 0
        self._confirmed  = False
        self._enemy_idx  = -1
        self._roulette   = False
        self._rou_step   = 0
        self._rou_target = 0
        self._rou_timer  = 0.0
        self._go_timer   = -1.0
        self._enemy_border_idx = -1
        # Grid
        cols = 4; cs = self.CS; gap = 20
        gw = cols*cs + (cols-1)*gap
        ox = W//2 - gw//2; oy = int(H*0.52)
        self._char_rects = []
        for i in range(len(CHARACTERS)):
            r = i // cols; c = i % cols
            self._char_rects.append(pygame.Rect(ox+c*(cs+gap), oy+r*(cs+gap), cs, cs))
        self._prev_imgs = [
            None if CHARACTERS[i]['placeholder'] else load_image(CHARACTERS[i]['preview'], (cs, cs))
            for i in range(len(CHARACTERS))
        ]
        self._fullbody = [
            None if CHARACTERS[i]['placeholder'] else load_image(CHARACTERS[i]['fullbody'])
            for i in range(len(CHARACTERS))
        ]
        self._btn_fight = RectButton(W-310, int(H*0.02), 280, 80, "NEXT >",  (217,25,25))
        self._btn_back  = RectButton(20,    int(H*0.93), 180, 60, "< BACK",  (76,76,76), 26)

    def handle_event(self, ev):
        if ev.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN): return
        x, y = _touch_pos(ev)
        if self._confirmed: return
        if self._btn_back.hit(x,y):  return 'menu'
        if self._btn_fight.hit(x,y): self._start_confirm(); return
        for i, r in enumerate(self._char_rects):
            if r.collidepoint(x,y): self._selected = i; break

    def _start_confirm(self):
        self._confirmed  = True
        self._roulette   = True
        self._rou_step   = 0
        self._rou_target = pick_enemy(self._selected)
        self._rou_timer  = 0.0

    def update(self, dt):
        if self._roulette:
            self._rou_timer += dt
            self._rou_step = int(self._rou_timer * 12) % len(CHARACTERS)
            if self._rou_timer >= 1.5:
                self._roulette         = False
                self._enemy_idx        = self._rou_target
                self._enemy_border_idx = self._rou_target
                self._go_timer         = 0.5
        if self._go_timer >= 0:
            self._go_timer -= dt
            if self._go_timer < 0:
                return ('arenaselect', self._selected, self._enemy_idx)

    def draw(self, surf):
        surf.fill((25,25,25))
        draw_text(surf, "SELECT CHARACTER", 44, (255,255,255), W//2, int(H*0.88), bold=True)
        fb_w = int(W*0.28); fb_h = int(H*0.65)
        if self._fullbody[self._selected]:
            draw_image_fit(surf, self._fullbody[self._selected], (0, int(H*0.02), fb_w, fb_h))
        ei = self._rou_step if self._roulette else self._enemy_idx
        if ei >= 0 and not CHARACTERS[ei]['placeholder'] and self._fullbody[ei]:
            draw_image_fit(surf, self._fullbody[ei], (W-fb_w, int(H*0.02), fb_w, fb_h), flip_x=True)
        for i, r in enumerate(self._char_rects):
            c = CHARACTERS[i]
            if c['placeholder']:
                col = c['placeholder_color'][:3]
                pygame.draw.rect(surf, col, r, border_radius=12)
            else:
                img = self._prev_imgs[i]
                if img: surf.blit(img, r)
                else:   pygame.draw.rect(surf, (80,80,80), r, border_radius=12)
            if i == self._selected:
                pygame.draw.rect(surf, (255,255,255), r.inflate(8,8), 3, border_radius=16)
            ri = self._rou_step if self._roulette else self._enemy_border_idx
            if ri == i:
                pygame.draw.rect(surf, (255,25,25), r.inflate(8,8), 3, border_radius=16)
        cname = CHARACTERS[self._selected]['name'] if not CHARACTERS[self._selected]['placeholder'] else '???'
        draw_text(surf, cname, 38, (255,255,0), W//2, int(H*0.44), bold=True)
        vs = load_image(_p('Images/vs.png'))
        if vs:
            sc = min(440/vs.get_width(), 220/vs.get_height())
            draw_image_centered(surf, vs, W//2, int(H*0.32), scale=sc)
        self._btn_fight.draw(surf); self._btn_back.draw(surf)

# ── Arena Select ──────────────────────────────────────────────────────────────
class ArenaSelectScreen(Screen):
    def __init__(self):
        self._selected_char = 0
        self._enemy_char    = 0
        self._selected      = 0

    def on_enter(self):
        self._selected = 0
        aw, ah = int(W*0.35), int(H*0.50)
        gap = 40; total = len(ARENAS)*aw + (len(ARENAS)-1)*gap
        ox = W//2 - total//2
        self._arena_rects = [pygame.Rect(ox+i*(aw+gap), int(H*0.35), aw, ah) for i in range(len(ARENAS))]
        self._prev_imgs   = [load_image(a['preview']) for a in ARENAS]
        self._btn_fight   = RectButton(W//2-140, int(H*0.08), 280, 80, "FIGHT!",  (217,25,25))
        self._btn_back    = RectButton(20,        int(H*0.93), 180, 60, "< BACK", (76,76,76), 26)

    def handle_event(self, ev):
        if ev.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN): return
        x, y = _touch_pos(ev)
        if self._btn_back.hit(x,y):  return 'charselect'
        if self._btn_fight.hit(x,y): return ('game', self._selected_char, self._enemy_char, self._selected)
        for i, r in enumerate(self._arena_rects):
            if r.collidepoint(x,y): self._selected = i; break

    def draw(self, surf):
        surf.fill((20,20,20))
        draw_text(surf, "SELECT ARENA", 44, (255,255,255), W//2, int(H*0.90), bold=True)
        for i, r in enumerate(self._arena_rects):
            img = self._prev_imgs[i]
            if img: draw_image_fit(surf, img, r)
            else:   pygame.draw.rect(surf, (60,60,60), r, border_radius=10)
            pygame.draw.rect(surf, (255,255,255) if i==self._selected else (100,100,100), r, 3, border_radius=10)
            draw_text(surf, ARENAS[i]['name'], 28, (255,255,255), r.centerx, r.bottom+24, bold=True)
        self._btn_fight.draw(surf); self._btn_back.draw(surf)

# ── Game ──────────────────────────────────────────────────────────────────────
class GameScreen(Screen):
    def __init__(self):
        self._selected_char = 0
        self._enemy_char    = 0
        self._arena_idx     = 0

    def on_enter(self):
        self._bg = load_image(ARENAS[self._arena_idx]['bg'])
        pc = CHARACTERS[self._selected_char]
        ec = CHARACTERS[self._enemy_char]
        self._player   = Fighter(200, False, pc)
        self._enemy    = Fighter(W - 200 - FIGHTER_W, True, ec)
        self._joystick = VirtualJoystick()
        br = W - 130; bm = H // 2
        self._btns = {
            'jump':  CircleButton(br-80,  bm-120, 52, "Y", (242,216,0)),
            'punch': CircleButton(br-180, bm,     52, "X", (25,76,242)),
            'kick':  CircleButton(br,     bm,     52, "B", (229,25,25)),
            'crouch':CircleButton(br-80,  bm+120, 52, "A", (25,191,25)),
        }
        self._btn_pause      = pygame.Rect(W-95, 15, 80, 80)
        self._btn_resume     = RectButton(W//2-160, int(H*0.55), 320, 90, "RESUME", (25,191,51))
        self._btn_pause_menu = RectButton(W//2-160, int(H*0.40), 320, 90, "MENU",   (25,102,229))
        self._btn_pause_quit = RectButton(W//2-160, int(H*0.25), 320, 90, "QUIT",   (204,25,25))
        rounds = GAME_SETTINGS['rounds']
        self._wins_needed  = rounds // 2 + 1
        self._player_wins  = 0
        self._enemy_wins   = 0
        self._time_left    = float(GAME_SETTINGS['timer'])
        self._paused       = False
        self._round_active = False
        self._round_ending = False
        self._countdown    = 3
        self._cd_timer     = 0.0
        self._winner_text  = ''
        self._winner_timer = 0.0
        self._cd_imgs = {n: load_image(_p(f'Images/{n}.png')) for n in ('3','2','1','fight')}
        self._win_imgs = {c['name']: load_image(_p(f"Images/{c['name']}_wins.png"))
                         for c in CHARACTERS if not c['placeholder']}
        self._crouch_finger = None
        start_combat_music()

    def on_leave(self):
        stop_combat_music()
        start_menu_music()

    def handle_event(self, ev):
        if ev.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            x, y = _touch_pos(ev)
            fid  = getattr(ev, 'finger_id', 0)
            if self._btn_pause.collidepoint(x,y) and not self._paused:
                self._paused = True; self._round_active = False; return
            if self._paused:
                if self._btn_resume.hit(x,y):
                    self._paused = False; self._round_active = True; return
                if self._btn_pause_menu.hit(x,y): return 'menu'
                if self._btn_pause_quit.hit(x,y): return 'quit'
                return
            if not self._round_active: return
            self._joystick.handle_down(x, y, fid)
            if self._btns['jump'].hit(x,y):   self._player.jump()
            if self._btns['punch'].hit(x,y):  self._player.start_attack('punch')
            if self._btns['kick'].hit(x,y):   self._player.start_attack('kick')
            if self._btns['crouch'].hit(x,y):
                self._player.crouch(True); self._crouch_finger = fid

        elif ev.type in (pygame.FINGERMOTION, pygame.MOUSEMOTION):
            fid = getattr(ev, 'finger_id', 0)
            x, y = _touch_pos(ev)
            self._joystick.handle_move(x, y, fid)

        elif ev.type in (pygame.FINGERUP, pygame.MOUSEBUTTONUP):
            fid = getattr(ev, 'finger_id', 0)
            self._joystick.handle_up(fid)
            if fid == self._crouch_finger:
                self._player.crouch(False); self._crouch_finger = None

    # ── AI ───────────────────────────────────────────────────────────────────
    _ai_action_t = 0.0; _ai_crouch_t = 0.0; _ai_dir = 0

    def _update_ai(self, dt):
        p = self._player; e = self._enemy
        dist = p.x - e.x
        if   abs(dist) > 350: self._ai_dir = 1 if dist>0 else -1
        elif abs(dist) < 120: self._ai_dir = -1 if dist>0 else 1
        else:                  self._ai_dir = 0
        e.update(dt, self._ai_dir, opponent_x=p.center_x)
        e.x = max(0, min(e.x, W - FIGHTER_W))
        self._ai_action_t += dt; self._ai_crouch_t += dt
        if self._ai_action_t >= 0.8:
            self._ai_action_t = 0.0
            if abs(dist) < 420 and not e.is_attacking:
                r = random.random()
                if   r < 0.35: e.start_attack(random.choice(['punch','kick']))
                elif r < 0.55: e.jump()
                elif r < 0.70: e.crouch(True); self._ai_crouch_t = 0.0
        if e.is_crouching and self._ai_crouch_t >= 0.4:
            e.crouch(False)

    def _check_collisions(self):
        p = self._player; e = self._enemy
        mx = FIGHTER_W * 0.30
        if p.is_attacking:
            if (p.x < e.x+FIGHTER_W-mx and p.x+FIGHTER_W > e.x+mx and
                    p.y-FIGHTER_H < e.y-FIGHTER_H*0.15 and p.y > e.y-FIGHTER_H):
                if p.attack_type=='punch' and not e.is_crouching: e.hp = max(0, e.hp-1)
                elif p.attack_type=='kick' and e.y >= GROUND_Y-2: e.hp = max(0, e.hp-1)
        if e.is_attacking:
            if (e.x < p.x+FIGHTER_W-mx and e.x+FIGHTER_W > p.x+mx and
                    e.y-FIGHTER_H < p.y-FIGHTER_H*0.15 and e.y > p.y-FIGHTER_H):
                if e.attack_type=='punch' and not p.is_crouching: p.hp = max(0, p.hp-1)
                elif e.attack_type=='kick' and p.y >= GROUND_Y-2: p.hp = max(0, p.hp-1)

    def _end_round(self, winner):
        if self._round_ending: return
        self._round_ending = True; self._round_active = False
        pc = CHARACTERS[self._selected_char]; ec = CHARACTERS[self._enemy_char]
        if winner == 'player': self._player_wins += 1; self._winner_text = pc['name']
        else:                  self._enemy_wins  += 1; self._winner_text = ec['name']
        self._winner_timer = 2.5

    def _reset_round(self):
        self._player.x = 200; self._player.y = GROUND_Y
        self._player.vel_x = self._player.vel_y = 0
        self._player.hp = 250; self._player.crouch(False)
        self._enemy.x = W - 200 - FIGHTER_W; self._enemy.y = GROUND_Y
        self._enemy.vel_x = self._enemy.vel_y = 0; self._enemy.hp = 250
        self._time_left = float(GAME_SETTINGS['timer'])
        self._winner_text = ''
        self._round_ending = False
        self._countdown = 3; self._cd_timer = 0.0

    def update(self, dt):
        # Countdown phase
        if not self._round_active and not self._round_ending:
            self._cd_timer += dt
            if self._countdown > 0 and self._cd_timer >= 1.0:
                self._cd_timer -= 1.0; self._countdown -= 1
            elif self._countdown == 0 and self._cd_timer >= 0.8:
                self._round_active = True; self._countdown = -1
            return

        # Winner display phase
        if self._round_ending:
            self._winner_timer -= dt
            if self._winner_timer <= 0:
                if self._player_wins >= self._wins_needed or self._enemy_wins >= self._wins_needed:
                    return 'menu'
                self._reset_round()
            return

        if self._paused: return

        self._time_left -= dt
        if self._time_left <= 0:
            self._time_left = 0
            self._end_round('player' if self._player.hp >= self._enemy.hp else 'enemy'); return

        p = self._player; e = self._enemy
        p.update(dt, self._joystick.dir_x, opponent_x=e.center_x)
        p.x = max(0, min(p.x, W - FIGHTER_W))
        self._update_ai(dt)
        self._check_collisions()
        if p.hp <= 0: self._end_round('enemy')
        elif e.hp <= 0: self._end_round('player')

    def draw(self, surf):
        # Background
        if self._bg:
            bg = pygame.transform.smoothscale(self._bg, (W, H))
            surf.blit(bg, (0,0))
        else:
            surf.fill((30,30,50))

        # Ground shadow
        for f in (self._player, self._enemy):
            draw_ellipse_a(surf, (0,0,0), (int(f.x+30), GROUND_Y-8, 140, 24), 90)

        self._player.draw(surf)
        self._enemy.draw(surf)

        # HP bars
        bar_w = W//2 - 120; bar_h = 36; bar_y = 20
        for i, (ftr, ox) in enumerate(((self._player, 30), (self._enemy, W//2+90))):
            pygame.draw.rect(surf, (25,25,25), (ox, bar_y, bar_w, bar_h), border_radius=4)
            r = max(0, ftr.hp / 250.0)
            c = (0,217,0) if r>0.5 else ((255,217,0) if r>0.1 else (229,25,25))
            pygame.draw.rect(surf, c, (ox, bar_y, int(bar_w*r), bar_h), border_radius=4)

        # Win dots
        dot_y = bar_y + bar_h + 10; dot_r = 12; dot_gap = 32
        for i in range(self._wins_needed):
            c = (51,204,51) if self._player_wins > i else (76,76,76)
            pygame.draw.circle(surf, c, (30+i*dot_gap+dot_r, dot_y+dot_r), dot_r)
        for i in range(self._wins_needed):
            c = (229,51,51) if self._enemy_wins > i else (76,76,76)
            pygame.draw.circle(surf, c, (W-30-i*dot_gap-dot_r, dot_y+dot_r), dot_r)

        # Timer
        draw_text(surf, str(max(0, int(self._time_left)+1)), 56, (255,255,255), W//2, bar_y+bar_h//2+2, bold=True)

        # Countdown
        if not self._round_active and not self._round_ending and self._countdown >= 0:
            key = str(self._countdown) if self._countdown > 0 else 'fight'
            img = self._cd_imgs.get(key)
            if img:
                sc = min((H*0.45)/img.get_height(), (W*0.35)/img.get_width())
                draw_image_centered(surf, img, W//2, H//2, scale=sc)

        # Winner
        if self._round_ending and self._winner_text:
            img = self._win_imgs.get(self._winner_text)
            if img:
                draw_image_fit(surf, img, (int(W*0.15), int(H*0.36), int(W*0.70), int(H*0.28)))

        # Joystick + buttons
        self._joystick.draw(surf)
        for b in self._btns.values(): b.draw(surf)

        # Pause button
        if not self._paused:
            s = pygame.Surface((80,80), pygame.SRCALPHA)
            pygame.draw.circle(s, (0,0,0,115), (40,40), 40)
            pygame.draw.rect(s, (255,255,255,204), (22,18,12,44), border_radius=3)
            pygame.draw.rect(s, (255,255,255,204), (46,18,12,44), border_radius=3)
            surf.blit(s, (W-95, 15))

        if self._paused:
            ov = pygame.Surface((W,H), pygame.SRCALPHA); ov.fill((0,0,0,166)); surf.blit(ov,(0,0))
            draw_text(surf, "PAUSE", 80, (255,255,0), W//2, int(H*0.72), bold=True)
            self._btn_resume.draw(surf)
            self._btn_pause_menu.draw(surf)
            self._btn_pause_quit.draw(surf)

# ══════════════════════════════════════════════════════════════════════════════
# Main loop
# ══════════════════════════════════════════════════════════════════════════════
def main():
    arenaselect = ArenaSelectScreen()
    game        = GameScreen()
    screens = {
        'splash':     SplashScreen(),
        'menu':       MenuScreen(),
        'options':    OptionsScreen(),
        'charselect': CharSelectScreen(),
        'arenaselect':arenaselect,
        'game':       game,
    }

    current_name = 'splash'
    current      = screens[current_name]
    current.on_enter()

    def switch(name, *args):
        nonlocal current, current_name
        current.on_leave()
        current_name = name
        current      = screens[name]
        if name == 'arenaselect' and len(args) >= 2:
            arenaselect._selected_char = args[0]
            arenaselect._enemy_char    = args[1]
        elif name == 'game' and len(args) >= 3:
            game._selected_char = args[0]
            game._enemy_char    = args[1]
            game._arena_idx     = args[2]
        current.on_enter()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            else:
                result = current.handle_event(event)
                if result:
                    if result == 'quit': running = False
                    elif isinstance(result, tuple): switch(result[0], *result[1:])
                    else: switch(result)

        result = current.update(dt)
        if result:
            if result == 'quit': running = False
            elif isinstance(result, tuple): switch(result[0], *result[1:])
            elif isinstance(result, str):   switch(result)

        screen.fill((0,0,0))
        current.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
