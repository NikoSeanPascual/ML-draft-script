import pygame
import random
import math

pygame.init()
pygame.font.init()
pygame.mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
PLAY_WIDTH = 300
PLAY_HEIGHT = 600
BLOCK_SIZE = 30

TOP_LEFT_X = (SCREEN_WIDTH - PLAY_WIDTH) // 2
TOP_LEFT_Y = SCREEN_HEIGHT - PLAY_HEIGHT - 50

# GLOBAL VOLUME
music_volume = 0.5
sfx_volume = 0.5

# COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (30, 30, 30)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
RED = (255, 50, 50)

SHAPE_COLORS = [
    (0, 255, 255), (0, 0, 255), (255, 165, 0),
    (255, 255, 0), (0, 255, 0), (128, 0, 128), (255, 0, 0)
]

# ASSET LOADING & AUDIO LAYERING
FONTS = {}

BLOOM_CACHE = {}


def pre_render_bloom_effects():
    for color in SHAPE_COLORS:
        BLOOM_CACHE[color] = []
        for i in range(3, 0, -1):
            padding = i * 4
            bloom_size = BLOCK_SIZE + (padding * 2)
            bloom_surf = pygame.Surface((bloom_size, bloom_size), pygame.SRCALPHA).convert_alpha()
            bloom_alpha = int(35 / i)

            pygame.draw.rect(bloom_surf, (*color, bloom_alpha), (0, 0, bloom_size, bloom_size), border_radius=6)
            BLOOM_CACHE[color].append((padding, bloom_surf))


def get_font(size):
    if size not in FONTS:
        try:
            FONTS[size] = pygame.font.Font("DS-DIGIB.TTF", size)
        except (IOError, FileNotFoundError):
            try:
                FONTS[size] = pygame.font.Font("DS-DIGIB.ttf", size)
            except (IOError, FileNotFoundError):
                FONTS[size] = pygame.font.SysFont('arial', size, bold=True)
    return FONTS[size]


def load_sound(path):
    try:
        return pygame.mixer.Sound(path)
    except:
        class DummySound:
            def play(self): pass

            def set_volume(self, v): pass

        return DummySound()


sound_place = load_sound("sound_effects/place_obj.wav")
sound_clear = load_sound("sound_effects/row_destroyed.wav")
sound_gameover = load_sound("sound_effects/game_over.wav")
sound_move = load_sound("sound_effects/move.wav")
sound_rotate = load_sound("sound_effects/rotate.wav")
sound_combo = load_sound("sound_effects/combo.wav")
sound_explosion = load_sound("sound_effects/explosion.wav")


def update_sfx_volumes():
    all_sfx_effects = [
        sound_place,
        sound_clear,
        sound_gameover,
        sound_move,
        sound_rotate,
        sound_combo,
        sound_explosion
    ]

    for sfx in all_sfx_effects:
        if hasattr(sfx, 'set_volume') and sfx.__class__.__name__ != 'DummySound':
            sfx.set_volume(sfx_volume)


class MusicManager:
    def __init__(self):
        self.current_track = None

    def update_soundtrack(self, score, force_track=None):
        # OVERRIDE TRACKING IF FORCED BY THE SETTINGS MENU SLIDER
        if force_track:
            target_track = force_track
        else:
            target_track = "sound_effects/soft_bg_music.wav"
            if score >= 5000:
                target_track = "sound_effects/hard_bg_music.wav"
            elif score >= 1000:
                target_track = "sound_effects/midgame_bg_music.wav"
        if self.current_track != target_track:
            self.current_track = target_track
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(500)
                pygame.mixer.music.load(target_track)
                pygame.mixer.music.set_volume(music_volume)
                pygame.mixer.music.play(-1, fade_ms=500)
            except (pygame.error, FileNotFoundError):
                pass
        else:
            pygame.mixer.music.set_volume(music_volume)


music_tracker = MusicManager()

# SHADER EFFECTS
CRT_SURFACE = None


def draw_crt_overlay(surface):
    global CRT_SURFACE
    if CRT_SURFACE is None:
        CRT_SURFACE = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 3):
            pygame.draw.line(CRT_SURFACE, (0, 0, 0, 40), (0, y), (SCREEN_WIDTH, y))
    surface.blit(CRT_SURFACE, (0, 0))


# UI INTERACTIVE COMPONENTS
class Button:
    def __init__(self, text, x, y, w, h, font_size=32):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.font_size = font_size
        self.is_hovered = False

    def draw(self, surface):
        # INTERACTIVE GLOW SHIFT ON HOVER
        border_color = CYAN if not self.is_hovered else WHITE
        bg_alpha = 40 if self.is_hovered else 15

        # DRAW BACKGROUND PANEL
        bg_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        bg_surf.fill((*CYAN, bg_alpha))
        surface.blit(bg_surf, (self.rect.x, self.rect.y))

        # CYBER CHROMATIC ABERRATION OUTLINE BORDER
        pygame.draw.rect(surface, (255, 0, 0, 150), (self.rect.x - 2, self.rect.y, self.rect.width, self.rect.height),
                         2)
        pygame.draw.rect(surface, (0, 0, 255, 150), (self.rect.x + 2, self.rect.y, self.rect.width, self.rect.height),
                         2)
        pygame.draw.rect(surface, border_color, self.rect, 2)
        font = get_font(self.font_size)
        text_color = WHITE if self.is_hovered else CYAN
        label = font.render(self.text, True, text_color)
        surface.blit(label, (self.rect.x + (self.rect.width - label.get_width()) // 2,
                             self.rect.y + (self.rect.height - label.get_height()) // 2))

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                if sound_move: sound_move.play()
                return True
        return False


class Slider:
    def __init__(self, x, y, w, initial_val=0.5):
        self.rect = pygame.Rect(x, y, w, 10)
        self.val = initial_val
        self.handle_radius = 12
        self.is_dragging = False
        self.handle_x = self.rect.x + int(self.val * self.rect.width)

    def draw(self, surface):
        # DRAW TARGE SLOT LINE
        pygame.draw.rect(surface, DARK_GRAY, self.rect, border_radius=4)
        pygame.draw.rect(surface, CYAN, (self.rect.x, self.rect.y, self.handle_x - self.rect.x, self.rect.height),
                         border_radius=4)

        # DRAW HANDLE NODES
        pygame.draw.circle(surface, RED, (self.handle_x - 2, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, CYAN, (self.handle_x, self.rect.centery), self.handle_radius)
        pygame.draw.circle(surface, WHITE, (self.handle_x, self.rect.centery), self.handle_radius - 4)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_rect = pygame.Rect(self.handle_x - self.handle_radius, self.rect.centery - self.handle_radius,
                                      self.handle_radius * 2, self.handle_radius * 2)
            if handle_rect.collidepoint(mouse_pos) or self.rect.collidepoint(mouse_pos):
                self.is_dragging = True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        if self.is_dragging:
            self.handle_x = max(self.rect.x, min(mouse_pos[0], self.rect.x + self.rect.width))
            self.val = (self.handle_x - self.rect.x) / self.rect.width
            return True
        return False


# SHAPE FORMATS
S = [['.....', '.....', '..00.', '.00..', '.....'], ['.....', '..0..', '..00.', '...0.', '.....']]
Z = [['.....', '.....', '.00..', '..00.', '.....'], ['.....', '...0.', '..00.', '..0..', '.....']]
I = [['..0..', '..0..', '..0..', '..0..', '.....'], ['.....', '0000.', '.....', '.....', '.....']]
O = [['.....', '.....', '.00..', '.00..', '.....']]
J = [['.....', '.0...', '.000.', '.....', '.....'], ['.....', '..00.', '..0..', '..0..', '.....'],
     ['.....', '.....', '.000.', '...0.', '.....'], ['.....', '..0..', '..0..', '.00..', '.....']]
L = [['.....', '...0.', '.000.', '.....', '.....'], ['.....', '..0..', '..0..', '..00.', '.....'],
     ['.....', '.....', '.000.', '.0...', '.....'], ['.....', '.00..', '..0..', '..0..', '.....']]
T = [['.....', '..0..', '.000.', '.....', '.....'], ['.....', '..0..', '..00.', '..0..', '.....'],
     ['.....', '.....', '.000.', '..0..', '.....'], ['.....', '..0..', '.00..', '..0..', '.....']]

SHAPES = [I, J, L, O, S, T, Z]


class PIECES:
    def __init__(self, x, y, shape):
        self.shape = shape
        self.color = SHAPE_COLORS[SHAPES.index(shape)]
        self.x = x
        self.y = y
        self.rotation = 0
        self.visual_x = float(x)
        self.visual_y = float(y)
        self.spawn_progress = 0.0

    def reset_position(self):
        self.x = 5
        self.y = 0
        self.rotation = 0
        self.visual_x = 5.0
        self.visual_y = 0.0
        self.spawn_progress = 0.0

    def update_visuals(self, dt):
        self.visual_x += (self.x - self.visual_x) * 15.0 * dt
        self.visual_y += (self.y - self.visual_y) * 15.0 * dt
        if self.spawn_progress < 1.0:
            self.spawn_progress = min(1.0, self.spawn_progress + 4.0 * dt)


class FloatingText:
    def __init__(self, text, x, y, color, size=36, is_action=False):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.vy = -120.0
        self.alpha = 255
        self.life = 1.2
        self.is_action = is_action
        self.time_alive = 0.0

    def update(self, dt):
        self.y += self.vy * dt
        self.time_alive += dt
        if self.time_alive > 0.4:
            self.alpha = max(0, self.alpha - int(800 * dt))
        self.life -= dt

    def draw(self, surface):
        if self.alpha <= 0: return
        current_size = self.size
        if self.is_action and self.time_alive < 0.2:
            scale = max(1.0, 1.4 - (self.time_alive * 2.0))
            current_size = int(self.size * scale)

        font = get_font(current_size)
        label = font.render(self.text, True, self.color)

        txt_surf = pygame.Surface(label.get_size(), pygame.SRCALPHA)
        txt_surf.fill((255, 255, 255, 0))
        txt_surf.blit(label, (0, 0))

        alpha_surface = pygame.Surface(label.get_size(), pygame.SRCALPHA)
        alpha_surface.set_alpha(self.alpha)
        alpha_surface.blit(txt_surf, (0, 0))
        surface.blit(alpha_surface, (self.x - label.get_width() // 2, self.y - label.get_height() // 2))


class Afterimage:
    def __init__(self, positions, color):
        self.positions = positions
        self.color = color
        self.alpha = 160

    def update(self, dt):
        self.alpha = max(0, self.alpha - int(1000 * dt))

    def draw(self, surface, ox=0, oy=0):
        if self.alpha <= 0: return
        for pos in self.positions:
            x, y = pos
            if y > -1:
                rx = TOP_LEFT_X + x * BLOCK_SIZE + ox
                ry = TOP_LEFT_Y + y * BLOCK_SIZE + oy
                surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
                surf.fill((*self.color, self.alpha // 4))
                pygame.draw.rect(surf, (*self.color, self.alpha), (0, 0, BLOCK_SIZE, BLOCK_SIZE), 2)
                surface.blit(surf, (rx, ry))


class PARTICLES:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(100, 500)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 150
        self.life = 1.0
        self.size = random.uniform(6, 12)
        self.rotation = random.uniform(0, 360)
        self.spin = random.uniform(-400, 400)
        self.gravity = 900
        self.drag = 2.5

    def update(self, dt):
        self.vx -= self.vx * self.drag * dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.spin * dt
        self.life -= dt
        self.size = max(0, self.size - 8.0 * dt)

    def draw(self, surface, ox=0, oy=0):
        if self.life > 0 and self.size > 0:
            surf = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
            surf.fill((*self.color, int(255 * self.life)))
            rotated_surf = pygame.transform.rotate(surf, self.rotation)
            surface.blit(rotated_surf, (
                int(self.x) + ox - rotated_surf.get_width() // 2,
                int(self.y) + oy - rotated_surf.get_height() // 2
            ))


def create_grid(locked_pos={}):
    grid = [[BLACK for _ in range(10)] for _ in range(20)]
    for i in range(20):
        for j in range(10):
            if (j, i) in locked_pos:
                grid[i][j] = locked_pos[(j, i)]
    return grid


def convert_shape_format(shape, use_visual=False):
    positions = []
    format = shape.shape[shape.rotation % len(shape.shape)]
    base_x = shape.visual_x if use_visual else shape.x
    base_y = shape.visual_y if use_visual else shape.y

    for i, line in enumerate(format):
        row = list(line)
        for j, column in enumerate(row):
            if column == '0':
                positions.append((base_x + j, base_y + i))
    for i, pos in enumerate(positions):
        positions[i] = (pos[0] - 2, pos[1] - 4)
    return positions


def valid_space(shape, grid):
    accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == BLACK] for i in range(20)]
    accepted_pos = [j for sub in accepted_pos for j in sub]
    formatted = convert_shape_format(shape, use_visual=False)

    for pos in formatted:
        if pos not in accepted_pos:
            if pos[1] > -1:
                return False
            if pos[0] < 0 or pos[0] >= 10:
                return False
    return True


def check_lost(positions):
    for pos in positions:
        x, y = pos
        if y < 1:
            return True
    return False


def get_shape():
    return PIECES(5, 0, random.choice(SHAPES))


def draw_text_middle(surface, text, size, color, y_offset=0, ox=0, oy=0):
    font = get_font(size)
    label = font.render(text, 1, color)
    surface.blit(label, (TOP_LEFT_X + PLAY_WIDTH / 2 - (label.get_width() / 2) + ox,
                         TOP_LEFT_Y + PLAY_HEIGHT / 2 - label.get_height() / 2 + y_offset + oy))


def draw_grid(surface, ox=0, oy=0):
    for i in range(20):
        pygame.draw.line(surface, DARK_GRAY, (TOP_LEFT_X + ox, TOP_LEFT_Y + i * BLOCK_SIZE + oy),
                         (TOP_LEFT_X + PLAY_WIDTH + ox, TOP_LEFT_Y + i * BLOCK_SIZE + oy))
    for j in range(10):
        pygame.draw.line(surface, DARK_GRAY, (TOP_LEFT_X + j * BLOCK_SIZE + ox, TOP_LEFT_Y + oy),
                         (TOP_LEFT_X + j * BLOCK_SIZE + ox, TOP_LEFT_Y + PLAY_HEIGHT + oy))


def draw_block(surface, color, x, y, size, ox=0, oy=0, alpha=255, draw_bloom=True):
    rx, ry = int(x + ox), int(y + oy)

    if draw_bloom and alpha == 255 and color in BLOOM_CACHE:
        for padding, bloom_surf in BLOOM_CACHE[color]:
            surface.blit(bloom_surf, (rx - padding, ry - padding))

    elif draw_bloom and alpha > 0:
        for i in range(3, 0, -1):
            padding = i * 4
            bloom_size = size + (padding * 2)
            bloom_surf = pygame.Surface((bloom_size, bloom_size), pygame.SRCALPHA).convert_alpha()
            bloom_alpha = int((35 / i) * (alpha / 255.0))
            pygame.draw.rect(bloom_surf, (*color, bloom_alpha), (0, 0, bloom_size, bloom_size), border_radius=6)
            surface.blit(bloom_surf, (rx - padding, ry - padding))

    if alpha < 255:
        block_surf = pygame.Surface((size, size), pygame.SRCALPHA).convert_alpha()
        pygame.draw.rect(block_surf, (*color, alpha), (0, 0, size, size), 0)

        lighter = (min(color[0] + 70, 255), min(color[1] + 70, 255), min(color[2] + 70, 255), alpha)
        darker = (max(color[0] - 70, 0), max(color[1] - 70, 0), max(color[2] - 70, 0), alpha)

        pygame.draw.line(block_surf, lighter, (0, 0), (size - 1, 0), 2)
        pygame.draw.line(block_surf, lighter, (0, 0), (0, size - 1), 2)
        pygame.draw.line(block_surf, darker, (0, size - 1), (size - 1, size - 1), 2)
        pygame.draw.line(block_surf, darker, (size - 1, 0), (size - 1, size - 1), 2)
        surface.blit(block_surf, (rx, ry))
    else:
        pygame.draw.rect(surface, color, (rx, ry, size, size), 0)

        lighter = (min(color[0] + 70, 255), min(color[1] + 70, 255), min(color[2] + 70, 255))
        darker = (max(color[0] - 70, 0), max(color[1] - 70, 0), max(color[2] - 70, 0))

        pygame.draw.line(surface, lighter, (rx, ry), (rx + size - 1, ry), 2)
        pygame.draw.line(surface, lighter, (rx, ry), (rx, ry + size - 1), 2)
        pygame.draw.line(surface, darker, (rx, ry + size - 1), (rx + size - 1, ry + size - 1), 2)
        pygame.draw.line(surface, darker, (rx + size - 1, ry), (rx + size - 1, ry + size - 1), 2)
        pygame.draw.rect(surface, BLACK, (rx, ry, size, size), 1)


def clear_rows(grid, locked):
    cleared = 0
    rows_to_clear = []
    for i in range(len(grid) - 1, -1, -1):
        if BLACK not in grid[i]:
            rows_to_clear.append(i)

    if rows_to_clear:
        cleared = len(rows_to_clear)
        for row in rows_to_clear:
            for col in range(10):
                if (col, row) in locked:
                    del locked[(col, row)]

        for key in sorted(list(locked), key=lambda x: x[1], reverse=True):
            x, y = key
            shift = sum(1 for row in rows_to_clear if y < row)
            if shift > 0:
                locked[(x, y + shift)] = locked.pop(key)

    return cleared, rows_to_clear


def draw_ui_panel(surface, x, y, w, h, title, ox=0, oy=0, border_color=(0, 255, 255), text_color=(255, 255, 255),
                  glow1=(255, 50, 50), glow2=(50, 50, 255)):
    pygame.draw.rect(surface, (*glow1, 150), (x + ox - 2, y + oy, w, h), 2, border_radius=4)
    pygame.draw.rect(surface, (*glow2, 150), (x + ox + 2, y + oy, w, h), 2, border_radius=4)
    pygame.draw.rect(surface, border_color, (x + ox, y + oy, w, h), 2, border_radius=4)

    font = get_font(30)
    label_r = font.render(title, 1, glow1)
    label_b = font.render(title, 1, glow2)
    label = font.render(title, 1, text_color)

    surface.blit(label_r, (x + (w / 2 - label.get_width() / 2) - 2 + ox, y + 10 + oy))
    surface.blit(label_b, (x + (w / 2 - label.get_width() / 2) + 2 + ox, y + 10 + oy))
    surface.blit(label, (x + (w / 2 - label.get_width() / 2) + ox, y + 10 + oy))


def draw_stats_panel(surface, level, lines, ox=0, oy=0, border_color=(0, 255, 255), text_color=(255, 255, 255),
                     glow1=(255, 50, 50), glow2=(50, 50, 255)):
    sx = TOP_LEFT_X + PLAY_WIDTH + 40
    sy = TOP_LEFT_Y + 230
    draw_ui_panel(surface, sx, sy, 150, 150, "STATS", ox, oy, border_color, text_color, glow1, glow2)

    font = get_font(20)
    lvl_label = font.render(f"LVL: {level}", 1, text_color)
    lines_label = font.render(f"LINES: {lines}", 1, text_color)
    surface.blit(lvl_label, (sx + 20 + ox, sy + 60 + oy))
    surface.blit(lines_label, (sx + 20 + ox, sy + 100 + oy))


def draw_window(surface, grid, score, level, total_lines, ox=0, oy=0, animating_clear=False, clear_anim_time=0.0,
                flash_rows=[], border_color=(0, 255, 255), bg_color=(5, 5, 5), text_color=(255, 255, 255),
                text_glow1=(255, 50, 50), text_glow2=(50, 50, 255)):
    surface.fill(bg_color)

    for i in range(1, 6):
        glow_surf = pygame.Surface((PLAY_WIDTH + i * 16, PLAY_HEIGHT + i * 16), pygame.SRCALPHA)
        alpha = int(30 / i)
        pygame.draw.rect(glow_surf, (*text_glow1, alpha), (-2, 0, glow_surf.get_width(), glow_surf.get_height()), 4,
                         border_radius=8)
        pygame.draw.rect(glow_surf, (*text_glow2, alpha), (2, 0, glow_surf.get_width(), glow_surf.get_height()), 4,
                         border_radius=8)
        pygame.draw.rect(glow_surf, (*border_color, alpha), (0, 0, glow_surf.get_width(), glow_surf.get_height()), 4,
                         border_radius=8)
        surface.blit(glow_surf, (TOP_LEFT_X - (i * 8) + ox, TOP_LEFT_Y - (i * 8) + oy))

    font = get_font(65)
    title_text = "NIKO'S TETRIS"
    label = font.render(title_text, 1, text_color)
    label_r = font.render(title_text, 1, text_glow1)
    label_b = font.render(title_text, 1, text_glow2)
    surface.blit(label_r, (SCREEN_WIDTH / 2 - label.get_width() / 2 - 3, 35))
    surface.blit(label_b, (SCREEN_WIDTH / 2 - label.get_width() / 2 + 3, 35))
    surface.blit(label, (SCREEN_WIDTH / 2 - label.get_width() / 2, 35))

    # 3. SCORE UI PANEL SETUP
    sx = TOP_LEFT_X - 190
    sy = TOP_LEFT_Y + 40
    draw_ui_panel(surface, sx, sy, 150, 150, "SCORE", ox, oy, border_color, text_color, text_glow1, text_glow2)

    score_font = get_font(40)
    score_label = score_font.render(str(score), 1, text_color)
    surface.blit(score_label, (sx + 75 - score_label.get_width() / 2 + ox, sy + 55 + oy))

    # 4. DRAW MATRIX GRID BACKGROUND BOX (Slightly darker shade of the current theme)
    matrix_bg = (max(0, bg_color[0] - 4), max(0, bg_color[1] - 4), max(0, bg_color[2] - 4))
    pygame.draw.rect(surface, matrix_bg, (TOP_LEFT_X + ox, TOP_LEFT_Y + oy, PLAY_WIDTH, PLAY_HEIGHT), 0)

    # 5. DRAW PLAYFIELD GRID BLOCKS & CLEAR ANIMATIONS
    for i in range(20):
        if animating_clear and i in flash_rows:
            progress = max(0.0, clear_anim_time) / 0.4
            center_x = TOP_LEFT_X + PLAY_WIDTH / 2
            for j in range(10):
                if grid[i][j] != BLACK:
                    orig_x = TOP_LEFT_X + j * BLOCK_SIZE
                    orig_y = TOP_LEFT_Y + i * BLOCK_SIZE
                    anim_x = center_x + (orig_x - center_x) * (1.0 - progress)
                    current_size = int(BLOCK_SIZE * (1.0 - progress))
                    render_x = anim_x + (BLOCK_SIZE - current_size) / 2
                    render_y = orig_y + (BLOCK_SIZE - current_size) / 2
                    if current_size > 0:
                        draw_block(surface, grid[i][j], render_x, render_y, current_size, 0, 0,
                                   alpha=int(255 * (1.0 - progress)), draw_bloom=False)
            continue

        for j in range(10):
            if grid[i][j] != BLACK:
                draw_block(surface, grid[i][j], TOP_LEFT_X + j * BLOCK_SIZE, TOP_LEFT_Y + i * BLOCK_SIZE, BLOCK_SIZE,
                           ox, oy, draw_bloom=True)

    # 6. DRAW PLAYFIELD SHARP OUTLINE BORDERS
    pygame.draw.rect(surface, (*text_glow1, 150), (TOP_LEFT_X + ox - 2, TOP_LEFT_Y + oy, PLAY_WIDTH, PLAY_HEIGHT), 2)
    pygame.draw.rect(surface, (*text_glow2, 150), (TOP_LEFT_X + ox + 2, TOP_LEFT_Y + oy, PLAY_WIDTH, PLAY_HEIGHT), 2)
    pygame.draw.rect(surface, border_color, (TOP_LEFT_X + ox, TOP_LEFT_Y + oy, PLAY_WIDTH, PLAY_HEIGHT), 4)

    # 7. DRAW FOREGROUND MATRIX LINES
    draw_grid(surface, ox, oy)


def draw_preview_panel(surface, shape, title, sx, sy, ox=0, oy=0, border_color=(0, 255, 255),
                       text_color=(255, 255, 255),
                       glow1=(255, 50, 50), glow2=(50, 50, 255)):
    draw_ui_panel(surface, sx, sy, 150, 150, title, ox, oy, border_color, text_color, glow1, glow2)

    if shape:
        shape_pos = convert_shape_format(shape, use_visual=True)

        min_x = min([p[0] for p in shape_pos])
        max_x = max([p[0] for p in shape_pos])
        min_y = min([p[1] for p in shape_pos])
        max_y = max([p[1] for p in shape_pos])

        shape_width = (max_x - min_x + 1) * BLOCK_SIZE
        shape_height = (max_y - min_y + 1) * BLOCK_SIZE

        center_x = sx + (150 / 2) - (shape_width / 2)
        center_y = sy + (150 / 2) - (shape_height / 2) + 15

        for pos in shape_pos:
            block_x = center_x + (pos[0] - min_x) * BLOCK_SIZE
            block_y = center_y + (pos[1] - min_y) * BLOCK_SIZE

            draw_block(surface, shape.color, block_x, block_y, BLOCK_SIZE, ox, oy, draw_bloom=True)


def spawn_particles(rows, particles):
    for row in rows:
        for col in range(10):
            x = TOP_LEFT_X + col * BLOCK_SIZE + BLOCK_SIZE // 2
            y = TOP_LEFT_Y + row * BLOCK_SIZE + BLOCK_SIZE // 2
            color = random.choice(SHAPE_COLORS)
            for _ in range(6):
                particles.append(PARTICLES(x, y, color))


def main(win):
    music_tracker.update_soundtrack(0)

    current_border_color = pygame.Color(*CYAN)
    current_bg_color = pygame.Color(5, 5, 12)
    current_text_color = pygame.Color(255, 255, 255)
    current_glow1_color = pygame.Color(255, 50, 50)
    current_glow2_color = pygame.Color(50, 50, 255)

    target_border = pygame.Color(*CYAN)
    target_bg = pygame.Color(5, 5, 12)
    target_text = pygame.Color(255, 255, 255)
    target_glow1 = pygame.Color(255, 50, 50)
    target_glow2 = pygame.Color(50, 50, 255)

    score = 0
    current_level = 1
    total_lines_cleared = 0
    locked_positions = {}
    grid = create_grid(locked_positions)
    change_piece = False
    run = True
    current_piece = get_shape()
    next_piece = get_shape()
    clock = pygame.time.Clock()

    hold_piece = None
    has_swapped = False

    fall_time = 0.0
    fall_speed = 0.27
    level_time = 0.0

    particles = []
    afterimages = []
    floating_texts = []

    lock_delay_counter = -1
    LOCK_DELAY_MAX = 0.5

    combo_count = -1
    animating_clear = False
    clear_anim_time = 0.0
    cleared_rows_list = []
    pending_score_addition = 0
    shake_intensity = 0.0

    pygame.key.set_repeat(200, 50)

    game_over_active = False
    btn_retry = Button("PLAY AGAIN", SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 + 30, 200, 50, font_size=24)
    btn_menu = Button("QUIT", SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 30, 200, 50, font_size=24)

    while run:
        dt = clock.tick(60) / 1000.0
        if dt > 0.1: dt = 0.1
        mouse_pos = pygame.mouse.get_pos()

        lerp_amount = min(1.0, 3.5 * dt)
        current_border_color = current_border_color.lerp(target_border, lerp_amount)
        current_bg_color = current_bg_color.lerp(target_bg, lerp_amount)
        current_text_color = current_text_color.lerp(target_text, lerp_amount)
        current_glow1_color = current_glow1_color.lerp(target_glow1, lerp_amount)
        current_glow2_color = current_glow2_color.lerp(target_glow2, lerp_amount)

        c_border = tuple(current_border_color)[:3]
        c_bg = tuple(current_bg_color)[:3]
        c_text = tuple(current_text_color)[:3]
        c_glow1 = tuple(current_glow1_color)[:3]
        c_glow2 = tuple(current_glow2_color)[:3]

        if not animating_clear and not game_over_active:
            fall_time += dt
            level_time += dt

        if level_time > 10.0 and not game_over_active:
            level_time = 0
            if fall_speed > 0.12:
                fall_speed -= 0.005

        if not game_over_active:
            current_piece.update_visuals(dt)

        if fall_time > fall_speed and not animating_clear and not game_over_active:
            fall_time = 0.0
            current_piece.y += 1
            if not (valid_space(current_piece, grid)) and current_piece.y > 0:
                current_piece.y -= 1
                if lock_delay_counter == -1:
                    lock_delay_counter = LOCK_DELAY_MAX

        down_test_piece = PIECES(current_piece.x, current_piece.y + 1, current_piece.shape)
        down_test_piece.rotation = current_piece.rotation
        if not valid_space(down_test_piece, grid) and not animating_clear and not game_over_active:
            if lock_delay_counter == -1:
                lock_delay_counter = LOCK_DELAY_MAX
            else:
                lock_delay_counter -= dt
                if lock_delay_counter <= 0:
                    change_piece = True
                    lock_delay_counter = -1
        else:
            # FIX: If the piece is in the air (slid off a ledge), completely wipe the lock delay!
            lock_delay_counter = -1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if game_over_active:
                btn_retry.handle_event(event)
                btn_menu.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_retry.is_hovered:
                        return True
                    if btn_menu.is_hovered:
                        return False
                continue

            if event.type == pygame.KEYDOWN and not animating_clear and not game_over_active:
                if event.key == pygame.K_g:
                    score += 150

                if event.key == pygame.K_LEFT:
                    current_piece.x -= 1
                    if not valid_space(current_piece, grid):
                        current_piece.x += 1
                    elif sound_move:
                        sound_move.play()
                if event.key == pygame.K_RIGHT:
                    current_piece.x += 1
                    if not valid_space(current_piece, grid):
                        current_piece.x -= 1
                    elif sound_move:
                        sound_move.play()
                if event.key == pygame.K_DOWN:
                    current_piece.y += 1
                    if not valid_space(current_piece, grid):
                        current_piece.y -= 1
                    elif sound_move:
                        sound_move.play()

                if event.key == pygame.K_c or event.key == pygame.K_LSHIFT:
                    if not has_swapped:
                        if hold_piece is None:
                            hold_piece = current_piece
                            current_piece = next_piece
                            next_piece = get_shape()
                        else:
                            hold_piece, current_piece = current_piece, hold_piece

                        hold_piece.reset_position()
                        current_piece.reset_position()
                        has_swapped = True
                        if sound_move: sound_move.play()

                if event.key == pygame.K_UP:
                    old_rotation = current_piece.rotation
                    current_piece.rotation += 1
                    kick_offsets = [(0, 0), (-1, 0), (1, 0), (0, -1), (-1, -1), (1, -1), (-2, 0), (2, 0)]
                    rotated_successfully = False

                    for dx, dy in kick_offsets:
                        current_piece.x += dx
                        current_piece.y += dy
                        if valid_space(current_piece, grid):
                            rotated_successfully = True
                            if sound_rotate: sound_rotate.play()
                            break
                        current_piece.x -= dx
                        current_piece.y -= dy

                    if not rotated_successfully:
                        current_piece.rotation = old_rotation

                if event.key == pygame.K_SPACE:
                    trail_positions = []
                    while valid_space(current_piece, grid):
                        trail_positions.append(convert_shape_format(current_piece))
                        current_piece.y += 1
                    current_piece.y -= 1

                    for snapshot in trail_positions:
                        afterimages.append(Afterimage(snapshot, current_piece.color))

                    change_piece = True
                    lock_delay_counter = -1

        ox, oy = 0, 0
        if shake_intensity > 0 and not game_over_active:
            ox = random.randint(int(-shake_intensity), int(shake_intensity))
            oy = random.randint(int(-shake_intensity), int(shake_intensity))
            shake_intensity = max(0, shake_intensity - 40 * dt)

        if change_piece and not animating_clear and not game_over_active:
            shape_pos = convert_shape_format(current_piece)
            for pos in shape_pos:
                if pos[1] > -1:
                    locked_positions[(pos[0], pos[1])] = current_piece.color

            grid = create_grid(locked_positions)
            lines_cleared, cleared_rows = clear_rows(grid, locked_positions)

            if lines_cleared > 0:
                combo_count += 1
                total_lines_cleared += lines_cleared

                scoring_brackets = {1: 100, 2: 300, 3: 600, 4: 1200}
                base_award = scoring_brackets.get(lines_cleared, lines_cleared * 100)
                combo_bonus = combo_count * 50
                pending_score_addition = base_award + combo_bonus

                action_strings = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE", 4: "TETRIS!"}
                action_text = action_strings.get(lines_cleared, "CLEAR!")

                floating_texts.append(
                    FloatingText(action_text, TOP_LEFT_X + PLAY_WIDTH // 2, TOP_LEFT_Y + 220, CYAN, size=45,
                                 is_action=True))
                if combo_count > 0:
                    floating_texts.append(
                        FloatingText(f"COMBO x{combo_count}", TOP_LEFT_X + PLAY_WIDTH // 2, TOP_LEFT_Y + 270, GOLD,
                                     size=38, is_action=True))
                    if sound_combo:
                        sound_combo.set_volume(min(1.0, 0.3 + (combo_count * 0.15)))
                        sound_combo.play()

                floating_texts.append(
                    FloatingText(f"+{pending_score_addition}", TOP_LEFT_X + PLAY_WIDTH // 2, TOP_LEFT_Y + 160, WHITE,
                                 size=32))

                animating_clear = True
                clear_anim_time = 0.4
                cleared_rows_list = cleared_rows
                shake_intensity = lines_cleared * 8.0
                spawn_particles(cleared_rows, particles)

                if lines_cleared >= 4 and sound_explosion:
                    sound_explosion.play()
                elif sound_clear:
                    sound_clear.play()
            else:
                combo_count = -1
                if sound_place: sound_place.play()

            current_piece = next_piece
            next_piece = get_shape()
            change_piece = False
            has_swapped = False

        if animating_clear:
            clear_anim_time -= dt
            if clear_anim_time <= 0:
                animating_clear = False
                score += pending_score_addition
                pending_score_addition = 0
                grid = create_grid(locked_positions)

        if score < 1000:
            current_level = 1
            target_border = pygame.Color(*CYAN)
            target_bg = pygame.Color(5, 5, 12)
            target_text = pygame.Color(255, 255, 255)
            target_glow1 = pygame.Color(255, 50, 50)
            target_glow2 = pygame.Color(50, 50, 255)
        elif score < 5000:
            current_level = 2
            target_border = pygame.Color(0, 255, 100)
            target_bg = pygame.Color(8, 25, 12)
            target_text = pygame.Color(170, 255, 170)
            target_glow1 = pygame.Color(0, 140, 30)
            target_glow2 = pygame.Color(20, 80, 40)
        else:
            current_level = 3 + ((score - 500) // 100)
            target_border = pygame.Color(255, 30, 0)
            target_bg = pygame.Color(24, 6, 6)
            target_text = pygame.Color(255, 165, 0)
            target_glow1 = pygame.Color(220, 0, 0)
            target_glow2 = pygame.Color(110, 0, 0)

        if change_piece == False and animating_clear == False and clear_anim_time <= 0:
            music_tracker.update_soundtrack(score)

        ghost_piece = PIECES(current_piece.x, current_piece.y, current_piece.shape)
        ghost_piece.rotation = current_piece.rotation
        while valid_space(ghost_piece, grid):
            ghost_piece.y += 1
        ghost_piece.y -= 1

        draw_window(win, grid, score, current_level, total_lines_cleared, ox, oy, animating_clear, clear_anim_time,
                    cleared_rows_list, border_color=c_border, bg_color=c_bg, text_color=c_text,
                    text_glow1=c_glow1, text_glow2=c_glow2)

        for ai in reversed(afterimages):
            ai.update(dt)
            ai.draw(win, ox, oy)
            if ai.alpha <= 0: afterimages.remove(ai)

        ghost_pos = convert_shape_format(ghost_piece, use_visual=False)
        for pos in ghost_pos:
            if pos[1] > -1 and not game_over_active:
                rect = (TOP_LEFT_X + pos[0] * BLOCK_SIZE + ox, TOP_LEFT_Y + pos[1] * BLOCK_SIZE + oy, BLOCK_SIZE,
                        BLOCK_SIZE)
                pygame.draw.rect(win, current_piece.color, rect, 2)

        if not change_piece and not game_over_active:
            t = current_piece.spawn_progress
            scale_factor = 0.8 + 0.2 * t + 0.15 * math.sin(t * math.pi)
            shape_pos_vis = convert_shape_format(current_piece, use_visual=True)

            for pos in shape_pos_vis:
                if pos[1] > -1:
                    orig_bx = TOP_LEFT_X + pos[0] * BLOCK_SIZE
                    orig_by = TOP_LEFT_Y + pos[1] * BLOCK_SIZE
                    cx = orig_bx + BLOCK_SIZE / 2
                    cy = orig_by + BLOCK_SIZE / 2
                    dyn_size = int(BLOCK_SIZE * scale_factor)

                    shadow_surf = pygame.Surface((dyn_size, dyn_size), pygame.SRCALPHA)
                    pygame.draw.rect(shadow_surf, (0, 0, 0, 160), (0, 0, dyn_size, dyn_size), border_radius=4)
                    win.blit(shadow_surf, (cx - dyn_size / 2 + 10 + ox, cy - dyn_size / 2 + 10 + oy))

            for pos in shape_pos_vis:
                if pos[1] > -1:
                    orig_bx = TOP_LEFT_X + pos[0] * BLOCK_SIZE
                    orig_by = TOP_LEFT_Y + pos[1] * BLOCK_SIZE
                    cx = orig_bx + BLOCK_SIZE / 2
                    cy = orig_by + BLOCK_SIZE / 2
                    dyn_size = int(BLOCK_SIZE * scale_factor)
                    draw_block(win, current_piece.color, cx - dyn_size / 2, cy - dyn_size / 2, dyn_size, ox, oy,
                               alpha=int(255 * min(1.0, t * 1.5)), draw_bloom=True)

        next_px = TOP_LEFT_X + PLAY_WIDTH + 40
        next_py = TOP_LEFT_Y + 40
        draw_preview_panel(win, next_piece, "NEXT", next_px, next_py, ox, oy, c_border, c_text, c_glow1, c_glow2)

        hold_px = TOP_LEFT_X - 190
        hold_py = TOP_LEFT_Y + 230
        draw_preview_panel(win, hold_piece, "HOLD", hold_px, hold_py, ox, oy, c_border, c_text, c_glow1, c_glow2)

        draw_stats_panel(win, current_level, total_lines_cleared, ox, oy, c_border, c_text, c_glow1, c_glow2)

        for p in reversed(particles):
            p.update(dt)
            p.draw(win, ox, oy)
            if p.life <= 0: particles.remove(p)

        for ft in reversed(floating_texts):
            ft.update(dt)
            ft.draw(win)
            if ft.life <= 0: floating_texts.remove(ft)

        if check_lost(locked_positions):
            if not game_over_active:
                game_over_active = True
                if sound_gameover: sound_gameover.play()

            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            win.blit(overlay, (0, 0))

            draw_text_middle(win, "GAME OVER!", 65, RED, -60)

            btn_retry.update(mouse_pos)
            btn_menu.update(mouse_pos)
            btn_retry.draw(win)
            btn_menu.draw(win)

        draw_crt_overlay(win)
        pygame.display.update()


def main_menu(win):
    global music_volume, sfx_volume
    track_list = [
        "sound_effects/soft_bg_music.wav",
        "sound_effects/midgame_bg_music.wav",
        "sound_effects/hard_bg_music.wav"
    ]

    STATE_MAIN = 0
    STATE_SETTINGS = 1
    current_state = STATE_MAIN

    # CONSTRUCT INTERACTIVE MAIN MENU BUTTONS
    btn_play = Button("PLAY", SCREEN_WIDTH // 2 - 125, 320, 250, 55, font_size=32)
    btn_settings = Button("SETTINGS", SCREEN_WIDTH // 2 - 125, 410, 250, 55, font_size=32)
    btn_quit = Button("QUIT", SCREEN_WIDTH // 2 - 125, 500, 250, 55, font_size=32)

    # CONSTRUCT SETTINGS CONFIGURATION COMPONENTS
    slider_music = Slider(320, 250, 300, initial_val=music_volume)
    slider_sfx = Slider(320, 320, 300, initial_val=sfx_volume)
    btn_back = Button("GO BACK", SCREEN_WIDTH // 2 - 100, 640, 200, 50, font_size=28)

    # PRE-RENDER CREDIT TEXT SURFACES USING THE DIGIB FONT LOADER
    font_author = get_font(24)
    author_text = font_author.render("by Niko Sean Pascual", True, (140, 140, 140))
    author_rect = author_text.get_rect(center=(SCREEN_WIDTH // 2, 225))  # Slipped down slightly to give the titles room

    font_comm = get_font(18)
    comm_text = font_comm.render("commissioned by Aron", True, (100, 100, 100))
    comm_rect = comm_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 35))

    music_tracker.update_soundtrack(0, force_track=track_list[0])

    run = True
    while run:
        win.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        # RENDER GLITCH/RGB CHROMATIC ABERRATION TITLE PANEL EFFECTS
        font = get_font(80)
        title_text = "NIKO'S TETRIS"
        label = font.render(title_text, 1, CYAN)
        label_r = font.render(title_text, 1, (255, 0, 0))
        label_b = font.render(title_text, 1, (0, 0, 255))

        y_pos = 120
        win.blit(label_r, (SCREEN_WIDTH / 2 - label.get_width() / 2 - 4, y_pos))
        win.blit(label_b, (SCREEN_WIDTH / 2 - label.get_width() / 2 + 4, y_pos))
        win.blit(label, (SCREEN_WIDTH / 2 - label.get_width() / 2, y_pos))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if current_state == STATE_MAIN:
                btn_play.handle_event(event)
                btn_settings.handle_event(event)
                btn_quit.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_play.is_hovered:
                        game_active = True
                        while game_active:
                            game_active = main(win)
                        music_tracker.update_soundtrack(0, force_track=track_list[0])
                    elif btn_settings.is_hovered:
                        current_state = STATE_SETTINGS
                    elif btn_quit.is_hovered:
                        run = False

            elif current_state == STATE_SETTINGS:
                btn_back.handle_event(event)

                if slider_music.handle_event(event, mouse_pos):
                    music_volume = slider_music.val
                    track_index = min(int(music_volume * 3), 2)
                    music_tracker.update_soundtrack(0, force_track=track_list[track_index])

                if slider_sfx.handle_event(event, mouse_pos):
                    sfx_volume = slider_sfx.val
                    update_sfx_volumes()
                    if event.type == pygame.MOUSEBUTTONDOWN and sound_move:
                        sound_move.play()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_back.is_hovered:
                        current_state = STATE_MAIN

        if current_state == STATE_MAIN:
            win.blit(author_text, author_rect)

            btn_play.update(mouse_pos)
            btn_settings.update(mouse_pos)
            btn_quit.update(mouse_pos)

            btn_play.draw(win)
            btn_settings.draw(win)
            btn_quit.draw(win)

            win.blit(comm_text, comm_rect)

        elif current_state == STATE_SETTINGS:
            pygame.draw.rect(win, (15, 15, 15), (100, 210, 600, 490), 0)
            pygame.draw.rect(win, CYAN, (100, 210, 600, 490), 2)

            font_ui = get_font(32)

            lbl_m = font_ui.render("MUSIC:", True, CYAN)
            win.blit(lbl_m, (140, 240))
            slider_music.draw(win)

            lbl_s = font_ui.render("SFX:", True, CYAN)
            win.blit(lbl_s, (140, 310))
            slider_sfx.draw(win)

            lbl_c = font_ui.render("CONTROLS GUIDE", True, GOLD)
            win.blit(lbl_c, (SCREEN_WIDTH // 2 - lbl_c.get_width() // 2, 380))

            font_ctrl = get_font(24)
            controls_lines = [
                "LEFT / RIGHT ARROWS : MOVE PIECE",
                "UP ARROW                    : ROTATE PIECE ",
                "DOWN ARROW                : SOFT DROP",
                "SPACEBAR                   : HARD DROP",
                "C / LEFT SHIFT           : HOLD PIECE MECHANIC"
            ]

            for index, line in enumerate(controls_lines):
                lbl_line = font_ctrl.render(line, True, WHITE)
                win.blit(lbl_line, (140, 430 + (index * 35)))

            btn_back.update(mouse_pos)
            btn_back.draw(win)

        draw_crt_overlay(win)
        pygame.display.update()

    pygame.quit()


if __name__ == '__main__':
    win = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Niko's Tetris")

    pre_render_bloom_effects()

    main_menu(win)
