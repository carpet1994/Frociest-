import random
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty, StringProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.vector import Vector
from kivy.lang import Builder

Builder.load_file('menu.kv')
Builder.load_file('fighter.kv')

ARENAS = [
    {'name': 'Il CAF',      'preview': 'Images/Arena/wallpaper.png', 'bg': 'Images/Arena/wallpaper.png'},
    {'name': 'Frociest HQ', 'preview': 'Images/Arena/HQ.png',        'bg': 'Images/Arena/HQ.png'},
]

CHARACTERS = [
    {
        'name':        'Jules',
        'preview':     'PG/Preview/Giuse_preview.png',
        'fullbody':    'PG/Preview/Jules_fullbody.png',
        'idle':        'PG/Jules/Jules_idle.gif',
        'walk':        'PG/Jules/Jules_walk.gif',
        'jump':        'PG/Jules/Jules_jump.gif',
        'punch':       'PG/Jules/Jules_punch.gif',
        'kick':        'PG/Jules/Jules_kick.gif',
        'mirror':      False,
        'placeholder': False,
        'placeholder_color': None,
    },
    {
        'name':        'Poz',
        'preview':     'PG/Preview/Poz_preview.png',
        'fullbody':    'PG/Preview/Poz_fullbody.png',
        'idle':        'PG/Poz/poz_idle.gif',
        'walk':        'PG/Poz/poz_walk.gif',
        'jump':        'PG/Poz/poz_jump.gif',
        'punch':       'PG/Poz/poz_punch.gif',
        'kick':        'PG/Poz/poz_kick.gif',
        'mirror':      True,
        'placeholder': False,
        'placeholder_color': None,
    },
    {
        'name':        'Ruben',
        'preview':     'PG/Preview/Ruben_preview.png',
        'fullbody':    'PG/Preview/Ruben_fullbody.png',
        'idle':        'PG/Ruben/Ruben_idle.gif',
        'walk':        'PG/Ruben/Ruben_walk.gif',
        'jump':        'PG/Ruben/Ruben_jump.gif',
        'punch':       'PG/Ruben/Ruben_punch.gif',
        'kick':        'PG/Ruben/Ruben_kick.gif',
        'mirror':      False,
        'placeholder': False,
        'placeholder_color': None,
    },
    {'name': '???', 'placeholder': True, 'placeholder_color': [0.9, 0.7, 0.1,  1], 'fullbody': '', 'preview': '', 'idle': '', 'walk': '', 'jump': '', 'punch': '', 'kick': '', 'mirror': False},
    {'name': '???', 'placeholder': True, 'placeholder_color': [0.8, 0.3, 0.9,  1], 'fullbody': '', 'preview': '', 'idle': '', 'walk': '', 'jump': '', 'punch': '', 'kick': '', 'mirror': False},
    {'name': '???', 'placeholder': True, 'placeholder_color': [0.1, 0.8, 0.8,  1], 'fullbody': '', 'preview': '', 'idle': '', 'walk': '', 'jump': '', 'punch': '', 'kick': '', 'mirror': False},
    {'name': '???', 'placeholder': True, 'placeholder_color': [0.95, 0.5, 0.1, 1], 'fullbody': '', 'preview': '', 'idle': '', 'walk': '', 'jump': '', 'punch': '', 'kick': '', 'mirror': False},
    {'name': '???', 'placeholder': True, 'placeholder_color': [0.5, 0.5, 0.5,  1], 'fullbody': '', 'preview': '', 'idle': '', 'walk': '', 'jump': '', 'punch': '', 'kick': '', 'mirror': False},
]

# Impostazioni globali del gioco
GAME_SETTINGS = {
    'music_on': True,
    'timer':    90,    # 60 / 90 / 120
    'rounds':   3,     # 3 o 5  (alla meglio di X => vince chi fa ceil(X/2))
}

def pick_enemy(player_index):
    choices = [i for i in range(len(CHARACTERS)) if i != player_index and not CHARACTERS[i]['placeholder']]
    return random.choice(choices)

class RoundButton(Widget):
    text = StringProperty('')
    font_size = NumericProperty(24)
    btn_color = ListProperty([1, 1, 1, 0.3])

class Joystick(Widget):
    knob_pos = ListProperty([0, 0])
    background_pos = ListProperty([0, 0])
    active = BooleanProperty(False)
    dir_x = NumericProperty(0)

    def on_touch_down(self, touch):
        if touch.x < Window.width / 2:
            self.active = True
            self.background_pos = [touch.x - 100, touch.y - 100]
            self.knob_pos = touch.pos
            return True
        return False

    def on_touch_move(self, touch):
        if self.active:
            center = Vector(self.background_pos) + Vector(100, 100)
            diff = Vector(touch.pos) - center
            radius = 100
            distance = min(diff.length(), radius)
            direction = diff.normalize() if diff.length() > 0 else Vector(0, 0)
            self.knob_pos = center + direction * distance
            if diff.x > 30:    self.dir_x = 1
            elif diff.x < -30: self.dir_x = -1
            else:               self.dir_x = 0
            return True

    def on_touch_up(self, touch):
        if self.active:
            self.active = False
            self.dir_x = 0
            return True

class Fighter(Widget):
    hp = NumericProperty(250)
    vel_x = NumericProperty(0)
    vel_y = NumericProperty(0)
    is_crouching = BooleanProperty(False)
    is_attacking = BooleanProperty(False)
    attack_type = ObjectProperty(None, allownone=True)

    current_source = StringProperty('')
    facing_left = BooleanProperty(False)
    mirror_default = BooleanProperty(False)
    scale_x = NumericProperty(1)

    anim_idle = StringProperty('')
    anim_walk = StringProperty('')
    anim_jump = StringProperty('')
    anim_punch = StringProperty('')
    anim_kick  = StringProperty('')

    shadow_y = NumericProperty(35)

    def _update_scale(self, *args):
        if not self.mirror_default:
            self.scale_x = -1 if self.facing_left else 1
        else:
            self.scale_x = -1 if not self.facing_left else 1

    def on_facing_left(self, *args):
        self._update_scale()

    def on_mirror_default(self, *args):
        self._update_scale()

    speed = 12
    jump_force = 32
    gravity = 1.6
    ground_y = 50

    def jump(self):
        if self.y <= self.ground_y:
            self.vel_y = self.jump_force

    def apply_physics(self, input_dir, opponent_x=None):
        if self.is_attacking:
            new_source = self.anim_punch if self.attack_type == "punch" else self.anim_kick
        elif self.y > self.ground_y:
            new_source = self.anim_jump
        elif not self.is_crouching:
            new_source = self.anim_walk if input_dir != 0 else self.anim_idle
        else:
            new_source = self.anim_idle

        # Orientamento: se in movimento segue input_dir,
        # altrimenti (idle/crouch/jump) guarda verso l'avversario se fornito
        if input_dir > 0:
            self.facing_left = False
        elif input_dir < 0:
            self.facing_left = True
        elif opponent_x is not None:
            self.facing_left = opponent_x < self.center_x

        if self.current_source != new_source:
            self.current_source = new_source

        if self.y <= self.ground_y:
            self.vel_x = 0 if self.is_crouching else input_dir * self.speed
        else:
            self.vel_x = (self.vel_x * 0.9) + (input_dir * 2)

        self.x += self.vel_x
        self.y += self.vel_y

        if self.y > self.ground_y:
            self.vel_y -= self.gravity
        else:
            self.y = self.ground_y
            self.vel_y = 0


class FighterGame(Widget):
    player   = ObjectProperty(None)
    enemy    = ObjectProperty(None)
    joystick = ObjectProperty(None)
    hitbox   = ObjectProperty(None)

    timer_text      = StringProperty('90')
    bg_source       = StringProperty('Images/Arena/wallpaper.png')
    countdown_image = StringProperty('')

    winner_image = StringProperty('')

    player_wins  = NumericProperty(0)
    enemy_wins   = NumericProperty(0)
    wins_needed  = NumericProperty(2)
    max_dots     = NumericProperty(2)

    selected_char = NumericProperty(0)
    enemy_char    = NumericProperty(0)

    enemy_is_placeholder    = BooleanProperty(True)
    enemy_placeholder_color = ListProperty([0.5, 0.5, 0.5, 1])
    enemy_source            = StringProperty('')
    enemy_mirror            = BooleanProperty(False)
    enemy_punch_source      = StringProperty('')
    enemy_kick_source       = StringProperty('')

    paused = BooleanProperty(False)

    player_x = NumericProperty(200)
    enemy_x  = NumericProperty(600)

    _time_left      = 90.0
    _round_duration = 90
    _round_active   = False
    _round_ending   = False

    _player_name = ''
    _enemy_name  = ''

    def on_kv_post(self, base_widget):
        self.ids.player_id.bind(x=lambda inst, val: setattr(self, 'player_x', val))
        self.ids.enemy_id.bind(x=lambda inst, val: setattr(self, 'enemy_x', val))
        self.ids.enemy_id.bind(
            is_attacking=self._update_enemy_source,
            attack_type=self._update_enemy_source,
            current_source=lambda inst, val: setattr(self, 'enemy_source', val) if not inst.is_attacking else None,
        )
        self.player_x = self.ids.player_id.x
        self.enemy_x  = self.ids.enemy_id.x
        self.ids.btn_jump.bind(on_touch_down=self._btn_up_down)
        self.ids.btn_punch.bind(on_touch_down=self._btn_a_down)
        self.ids.btn_kick.bind(on_touch_down=self._btn_b_down)
        self.ids.btn_crouch.bind(on_touch_down=self._btn_down_down)
        self.ids.btn_crouch.bind(on_touch_up=self._btn_down_up)
        self.ids.btn_pause.bind(on_touch_down=self._btn_pause_down)
        self.ids.btn_resume.bind(on_touch_down=self._btn_resume_down)
        self.ids.btn_pause_menu.bind(on_touch_down=self._btn_pause_menu_down)
        self.ids.btn_pause_quit.bind(on_touch_down=self._btn_pause_quit_down)

    def _setup_player(self):
        char = CHARACTERS[self.selected_char]
        self.player.anim_idle      = char['idle']
        self.player.anim_walk      = char['walk']
        self.player.anim_jump      = char['jump']
        self.player.anim_punch     = char.get('punch', '')
        self.player.anim_kick      = char.get('kick', '')
        self.player.current_source = char['idle']
        self.player.mirror_default = char['mirror']
        self.player.facing_left    = False
        self._player_name = char['name']

    def _setup_enemy(self):
        char = CHARACTERS[self.enemy_char]
        e = self.ids.enemy_id
        if char['placeholder']:
            self.enemy_is_placeholder    = True
            self.enemy_placeholder_color = char['placeholder_color']
            self.enemy_source            = ''
            self.enemy_mirror            = False
            self.enemy_punch_source      = ''
            self.enemy_kick_source       = ''
            self._enemy_idle_source      = ''
            e.anim_idle  = ''
            e.anim_walk  = ''
            e.anim_jump  = ''
            e.anim_punch = ''
            e.anim_kick  = ''
        else:
            self.enemy_is_placeholder    = False
            self.enemy_source            = char['idle']
            self.enemy_mirror            = not char['mirror']
            self.enemy_punch_source      = char.get('punch', '')
            self.enemy_kick_source       = char.get('kick', '')
            self._enemy_idle_source      = char['idle']
            e.anim_idle    = char['idle']
            e.anim_walk    = char['walk']
            e.anim_jump    = char['jump']
            e.anim_punch   = char.get('punch', '')
            e.anim_kick    = char.get('kick', '')
            e.current_source = char['idle']
            e.mirror_default = char['mirror']
            e.facing_left    = True
        self._enemy_name = char['name']

        self._round_duration = GAME_SETTINGS['timer']
        self._time_left      = float(self._round_duration)
        self.timer_text      = str(self._round_duration)
        rounds = GAME_SETTINGS['rounds']
        self.wins_needed = (rounds // 2) + 1
        self.max_dots    = self.wins_needed

    def _update_enemy_source(self, *args):
        e = self.ids.enemy_id
        if e.is_attacking:
            if e.attack_type == "punch" and self.enemy_punch_source:
                self.enemy_source = self.enemy_punch_source
            elif e.attack_type == "kick" and self.enemy_kick_source:
                self.enemy_source = self.enemy_kick_source
        else:
            if hasattr(self, '_enemy_idle_source'):
                self.enemy_source = self._enemy_idle_source

    def _start_countdown(self):
        self._round_active   = False
        self._round_ending   = False
        self.winner_image    = ''
        self.countdown_image = 'Images/3.png'
        Clock.schedule_once(lambda dt: self._cd2(), 1)

    def _cd2(self, *a):
        self.countdown_image = 'Images/2.png'
        Clock.schedule_once(lambda dt: self._cd1(), 1)

    def _cd1(self, *a):
        self.countdown_image = 'Images/1.png'
        Clock.schedule_once(lambda dt: self._cd_fight(), 1)

    def _cd_fight(self, *a):
        self.countdown_image = 'Images/fight.png'
        self._round_active = True
        Clock.schedule_once(lambda dt: self._hide_countdown(), 0.8)

    def _hide_countdown(self, *a):
        self.countdown_image = ''

    def _show_winner(self, winner):
        name = self._player_name if winner == 'player' else self._enemy_name
        self.winner_image = f'Images/{name}_wins.png'

    def _reset_round(self):
        self.player.hp = 250
        self.enemy.hp  = 250
        self.player.x  = 200
        self.player.y  = self.player.ground_y
        self.player.vel_x = 0
        self.player.vel_y = 0
        self.player.is_crouching = False
        self.player.height = 500
        self.player.facing_left = False
        self.enemy.x  = self.width - 700
        self.enemy.y  = self.enemy.ground_y
        self.enemy.vel_x = 0
        self.enemy.vel_y = 0
        self._time_left = float(self._round_duration)
        self.timer_text = str(self._round_duration)
        self._ai_timer        = 0.0
        self._ai_action_timer = 0.0
        self._ai_dir          = 0
        self._ai_crouch_timer = 0.0
        self._start_countdown()

    def _end_round(self, winner):
        if self._round_ending:
            return
        self._round_ending = True
        self._round_active = False
        if winner == 'player':
            self.player_wins += 1
        else:
            self.enemy_wins += 1
        self._show_winner(winner)
        if self.player_wins >= self.wins_needed or self.enemy_wins >= self.wins_needed:
            Clock.schedule_once(lambda dt: self._go_to_menu(), 2.5)
        else:
            Clock.schedule_once(lambda dt: self._reset_round(), 2.5)

    def _go_to_menu(self, *a):
        self.paused = False
        App.get_running_app().root.current = 'menu'

    def _btn_up_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self._round_active and not self.paused:
            self.player.jump()

    def _btn_a_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self._round_active and not self.paused:
            self.do_attack("punch")

    def _btn_b_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self._round_active and not self.paused:
            self.do_attack("kick")

    def _btn_down_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self._round_active and not self.paused:
            self.player.is_crouching = True
            self.player.height = 300

    def _btn_down_up(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.player.is_crouching = False
            self.player.height = 500

    def _btn_pause_down(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.paused = True
            self._round_active = False

    def _btn_resume_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.paused:
            self.paused = False
            self._round_active = True

    def _btn_pause_menu_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.paused:
            self._go_to_menu()

    def _btn_pause_quit_down(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.paused:
            App.get_running_app().stop()

    def update(self, dt):
        if not self._round_active or self.paused:
            return
        if self._time_left > 0:
            self._time_left -= dt
            if self._time_left <= 0:
                self._time_left = 0
                self.timer_text = '0'
                player_pct = self.player.hp / 250.0
                enemy_pct  = self.enemy.hp  / 250.0
                if player_pct >= enemy_pct:
                    self._end_round('player')
                else:
                    self._end_round('enemy')
                return
            self.timer_text = str(int(self._time_left) + 1)

        if self.player:
            self.player.apply_physics(self.joystick.dir_x, opponent_x=self.enemy.center_x)
            if self.player.x < 0:             self.player.x = 0
            if self.player.right > self.width: self.player.right = self.width

        self._update_ai(dt)
        self.check_collisions()

        if self.player.hp <= 0:
            self._end_round('enemy')
        elif self.enemy.hp <= 0:
            self._end_round('player')

    def check_collisions(self):
        if not self.player or not self.enemy:
            return
        p = self.player
        e = self.enemy

        if p.is_attacking:
            p_left  = p.x
            p_right = p.x + p.width
            p_bot   = p.y
            p_top   = p.y + p.height

            margin_x = e.width * 0.30
            e_left   = e.x + margin_x
            e_right  = e.x + e.width - margin_x
            e_bot    = e.y
            e_top    = e.y + e.height * 0.85

            overlap_x = p_left < e_right and p_right > e_left
            overlap_y = p_bot   < e_top   and p_top   > e_bot

            if overlap_x and overlap_y:
                if p.attack_type == "punch":
                    if not e.is_crouching:
                        e.hp -= 1
                elif p.attack_type == "kick":
                    if e.y <= e.ground_y:
                        e.hp -= 1

        if e.is_attacking:
            margin_x = p.width * 0.30
            p_left   = p.x + margin_x
            p_right  = p.x + p.width - margin_x
            p_bot    = p.y
            p_top    = p.y + p.height * 0.85

            e_left  = e.x
            e_right = e.x + e.width
            e_bot   = e.y
            e_top   = e.y + e.height

            overlap_x = e_left < p_right and e_right > p_left
            overlap_y = e_bot   < p_top   and e_top   > p_bot

            if overlap_x and overlap_y:
                if e.attack_type == "punch":
                    if not p.is_crouching:
                        p.hp -= 1
                elif e.attack_type == "kick":
                    if p.y <= p.ground_y:
                        p.hp -= 1

    # ── IA NEMICA ───────────────────────────────────────────────
    _ai_timer        = 0.0
    _ai_action_timer = 0.0
    _ai_dir          = 0
    _ai_crouch_timer = 0.0

    def _update_ai(self, dt):
        if not self._round_active or self.paused:
            return
        p = self.player
        e = self.enemy
        if not p or not e:
            return

        self._ai_timer        += dt
        self._ai_action_timer += dt
        self._ai_crouch_timer += dt

        dist = p.x - e.x

        if abs(dist) > 350:
            self._ai_dir = 1 if dist > 0 else -1
        elif abs(dist) < 120:
            self._ai_dir = -1 if dist > 0 else 1
        else:
            self._ai_dir = 0

        e.apply_physics(self._ai_dir, opponent_x=p.center_x)
        if e.x < 0:            e.x = 0
        if e.right > self.width: e.right = self.width

        if self._ai_action_timer >= 0.8:
            self._ai_action_timer = 0.0
            roll = random.random()

            if abs(dist) < 420 and not e.is_attacking:
                if roll < 0.35:
                    atype = random.choice(["punch", "kick"])
                    self._do_enemy_attack(atype)
                elif roll < 0.55:
                    e.jump()
                elif roll < 0.70:
                    e.is_crouching = True
                    e.height = 300
                    self._ai_crouch_timer = 0.0

        if e.is_crouching and self._ai_crouch_timer >= 0.4:
            e.is_crouching = False
            e.height = 500

    def _do_enemy_attack(self, atype):
        e = self.enemy
        if e and not e.is_attacking:
            e.is_attacking = True
            e.attack_type  = atype
            Clock.schedule_once(self._reset_enemy_attack, 0.3)

    def _reset_enemy_attack(self, dt):
        e = self.enemy
        if e:
            e.is_attacking = False
            e.attack_type  = None

    def do_attack(self, atype):
        if self.player and not self.player.is_attacking:
            self.player.is_attacking = True
            self.player.attack_type  = atype
            Clock.schedule_once(self.reset_attack, 0.3)

    def reset_attack(self, dt):
        if self.player:
            self.player.is_attacking = False
            self.player.attack_type  = None


class SplashScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self._go_to_menu, 5)

    def _go_to_menu(self, dt):
        App.get_running_app().start_music()
        self.manager.current = 'menu'


class MenuScreen(Screen):
    def on_kv_post(self, base_widget):
        self.ids.btn_start.bind(on_touch_down=self._go_charselect)
        self.ids.btn_options.bind(on_touch_down=self._go_options)
        self.ids.btn_quit.bind(on_touch_down=self._quit_game)

    def _go_charselect(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.manager.current = 'charselect'

    def _go_options(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.manager.current = 'options'

    def _quit_game(self, widget, touch):
        if widget.collide_point(*touch.pos):
            App.get_running_app().stop()


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
        self.ids.btn_music_toggle.bind(on_touch_down=self._toggle_music_on)
        self.ids.btn_music_toggle_off.bind(on_touch_down=self._toggle_music_off)
        self.ids.btn_timer_10.bind(on_touch_down=lambda w, t: self._set_timer(w, t, 10))
        self.ids.btn_timer_60.bind(on_touch_down=lambda w, t: self._set_timer(w, t, 60))
        self.ids.btn_timer_90.bind(on_touch_down=lambda w, t: self._set_timer(w, t, 90))
        self.ids.btn_timer_120.bind(on_touch_down=lambda w, t: self._set_timer(w, t, 120))
        self.ids.btn_rounds_3.bind(on_touch_down=lambda w, t: self._set_rounds(w, t, 3))
        self.ids.btn_rounds_5.bind(on_touch_down=lambda w, t: self._set_rounds(w, t, 5))
        self.ids.btn_save.bind(on_touch_down=self._save)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        self.ids.btn_confirm_save.bind(on_touch_down=self._confirm_save_and_back)
        self.ids.btn_confirm_discard.bind(on_touch_down=self._confirm_discard)

    def _has_unsaved_changes(self):
        return (self.tmp_music_on != GAME_SETTINGS['music_on'] or
                self.tmp_timer    != GAME_SETTINGS['timer'] or
                self.tmp_rounds   != GAME_SETTINGS['rounds'])

    def _toggle_music_on(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            self.tmp_music_on = True

    def _toggle_music_off(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            self.tmp_music_on = False

    def _set_timer(self, widget, touch, value):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            self.tmp_timer = value

    def _set_rounds(self, widget, touch, value):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            self.tmp_rounds = value

    def _apply_settings(self):
        GAME_SETTINGS['music_on'] = self.tmp_music_on
        GAME_SETTINGS['timer']    = self.tmp_timer
        GAME_SETTINGS['rounds']   = self.tmp_rounds
        app = App.get_running_app()
        if app._music:
            if self.tmp_music_on:
                if app._music.state != 'play':
                    app._music.play()
            else:
                app._music.stop()

    def _save(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            self._apply_settings()
            self.manager.current = 'menu'

    def _go_back(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self.show_confirm:
            if self._has_unsaved_changes():
                self.show_confirm = True
            else:
                self.manager.current = 'menu'

    def _confirm_save_and_back(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.show_confirm:
            self._apply_settings()
            self.show_confirm = False
            self.manager.current = 'menu'

    def _confirm_discard(self, widget, touch):
        if widget.collide_point(*touch.pos) and self.show_confirm:
            self.show_confirm = False
            self.manager.current = 'menu'


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
    _timer_event            = None
    _roulette_event         = None
    _roulette_step          = 0
    _roulette_target        = 0

    _char_ids = ['char_0', 'char_1', 'char_2', 'char_3',
                 'char_4', 'char_5', 'char_6', 'char_7']

    def on_kv_post(self, base_widget):
        for cid in self._char_ids:
            self.ids[cid].bind(on_touch_down=self._on_char_touch)
        self.ids.btn_fight.bind(on_touch_down=self._confirm)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        Clock.schedule_once(lambda dt: self._update_selection(), 0)

    def on_leave(self):
        self._cancel_roulette()
        if self._timer_event:
            self._timer_event.cancel()
            self._timer_event = None
        self._confirmed            = False
        self.enemy_idle_source     = ''
        self.enemy_fullbody_source = ''
        self.enemy_placeholder     = False
        if 'enemy_border' in self.ids:
            self.ids.enemy_border.opacity = 0

    def _on_char_touch(self, widget, touch):
        if self._confirmed:
            return
        if widget.collide_point(*touch.pos):
            for i, cid in enumerate(self._char_ids):
                if self.ids[cid] == widget:
                    self.selected = i
                    self._update_selection()

    def _update_selection(self):
        if 'char_name_label' not in self.ids:
            return
        char = CHARACTERS[self.selected]
        if not char['placeholder']:
            self.ids.char_name_label.text = char['name']
            self.idle_source              = char['idle']
            self.idle_mirror              = char['mirror']
            self.fullbody_source          = char['fullbody']
        else:
            self.ids.char_name_label.text = '???'
            self.idle_source              = ''
            self.idle_mirror              = False
            self.fullbody_source          = ''

    def _cancel_roulette(self):
        if self._roulette_event:
            self._roulette_event.cancel()
            self._roulette_event = None

    def _confirm(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self._confirmed:
            self._confirmed = True
            self._roulette_target = pick_enemy(self.selected)
            self._roulette_step = 0
            self.ids.enemy_border.opacity = 1
            self._roulette_event = Clock.schedule_interval(self._roulette_tick, 0.08)
            Clock.schedule_once(self._roulette_end, 1.5)

    def _roulette_tick(self, dt):
        idx = self._roulette_step % len(self._char_ids)
        self._roulette_step += 1
        target = self.ids[self._char_ids[idx]]
        self.ids.enemy_border.pos = (target.x - 4, target.y - 4)

    def _roulette_end(self, dt):
        self._cancel_roulette()
        enemy_idx = self._roulette_target
        self._enemy_idx = enemy_idx
        target = self.ids[self._char_ids[enemy_idx]]
        self.ids.enemy_border.pos = (target.x - 4, target.y - 4)
        enemy = CHARACTERS[enemy_idx]
        if enemy['placeholder']:
            self.enemy_placeholder        = True
            self.enemy_placeholder_color  = enemy['placeholder_color']
            self.enemy_idle_source        = ''
            self.enemy_idle_mirror        = False
            self.enemy_fullbody_source    = ''
        else:
            self.enemy_placeholder        = False
            self.enemy_idle_source        = enemy['idle']
            self.enemy_idle_mirror        = not enemy['mirror']
            self.enemy_fullbody_source    = enemy['fullbody']
        self._timer_event = Clock.schedule_once(self._go_arenaselect, 0.5)

    def _go_arenaselect(self, *args):
        self.manager.get_screen('arenaselect').selected_char = self.selected
        self.manager.get_screen('arenaselect').enemy_char    = self._enemy_idx
        self.manager.current = 'arenaselect'

    def _go_back(self, widget, touch):
        if widget.collide_point(*touch.pos) and not self._confirmed:
            self.manager.current = 'menu'


class ArenaSelectScreen(Screen):
    selected      = NumericProperty(0)
    selected_char = NumericProperty(0)
    enemy_char    = NumericProperty(0)

    _arena_ids = ['arena_0', 'arena_1']

    def on_kv_post(self, base_widget):
        for aid in self._arena_ids:
            self.ids[aid].bind(on_touch_down=self._on_arena_touch)
        self.ids.btn_fight.bind(on_touch_down=self._go_fight)
        self.ids.btn_back.bind(on_touch_down=self._go_back)
        self._update_selection()

    def _on_arena_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            for i, aid in enumerate(self._arena_ids):
                if self.ids[aid] == widget:
                    self.selected = i
                    self._update_selection()

    def _update_selection(self):
        self.ids.arena_preview.source = ARENAS[self.selected]['preview']
        target = self.ids[self._arena_ids[self.selected]]
        self.ids.arena_border.pos = (target.x - 3, target.y - 3)

    def _go_fight(self, widget, touch):
        if widget.collide_point(*touch.pos):
            game = self.manager.get_screen('game')
            game.selected_char = self.selected_char
            game.enemy_char    = self.enemy_char
            game.bg_source     = ARENAS[self.selected]['bg']
            self.manager.current = 'game'

    def _go_back(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self.manager.current = 'charselect'


class GameScreen(Screen):
    selected_char = NumericProperty(0)
    enemy_char    = NumericProperty(0)
    bg_source     = StringProperty('Images/Arena/wallpaper.png')

    _update_event = None

    def on_enter(self):
        game = self.ids.game_widget
        game.selected_char = self.selected_char
        game.enemy_char    = self.enemy_char
        game.bg_source     = self.bg_source
        game.paused        = False
        game.player_wins   = 0
        game.enemy_wins    = 0
        game.winner_image    = ''
        game.countdown_image = ''
        game._round_active   = False
        game._round_ending   = False
        game._setup_player()
        game._setup_enemy()
        game.player.hp = 250
        game.player.x  = 200
        game.player.y  = game.player.ground_y
        game.player.vel_x = 0
        game.player.vel_y = 0
        game.player.is_crouching = False
        game.player.height = 500
        game.player.facing_left = False
        game.player.is_attacking = False
        game.player.attack_type  = None
        game.enemy.hp  = 250
        game.enemy.x   = game.width - 700
        game.enemy.y   = game.enemy.ground_y
        game.enemy.vel_x = 0
        game.enemy.vel_y = 0
        self._update_event = Clock.schedule_interval(game.update, 1.0 / 60.0)
        Clock.schedule_once(lambda dt: game._start_countdown(), 0.3)
        App.get_running_app().start_combat_music()

    def on_leave(self):
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None
        App.get_running_app().stop_combat_music()


class GameApp(App):
    kv_file = None
    _music  = None
    _combat = None

    def start_music(self):
        if self._music:
            if self._music.state != 'play' and GAME_SETTINGS['music_on']:
                self._music.play()
            return
        for filename in ('Audio/jingle.ogg', 'Audio/jingle.mp3'):
            try:
                sound = SoundLoader.load(filename)
                if sound:
                    sound.loop = True
                    if GAME_SETTINGS['music_on']:
                        sound.play()
                    self._music = sound
                    return
            except Exception:
                continue

    def start_combat_music(self):
        if self._music and self._music.state == 'play':
            self._music.stop()
        if not self._combat:
            try:
                sound = SoundLoader.load('Audio/combat.ogg')
                if sound:
                    sound.loop = True
                    self._combat = sound
            except Exception:
                return
        if self._combat and self._combat.state != 'play':
            self._combat.play()

    def stop_combat_music(self):
        if self._combat and self._combat.state == 'play':
            self._combat.stop()
        if self._music and GAME_SETTINGS['music_on']:
            self._music.play()

    def build(self):
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(OptionsScreen(name='options'))
        sm.add_widget(CharSelectScreen(name='charselect'))
        sm.add_widget(ArenaSelectScreen(name='arenaselect'))
        sm.add_widget(GameScreen(name='game'))
        sm.current = 'splash'
        return sm


if __name__ == '__main__':
    GameApp().run()
