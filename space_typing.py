import pygame
import random
import math
import sys
import time
import asyncio

pygame.init()

# ============================================================
#  SCREEN & COLORS
# ============================================================
WIDTH, HEIGHT = 900, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Typing Shooter")

BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255,  60,  60)
GREEN   = (50,  255, 100)
BLUE    = (50,  150, 255)
YELLOW  = (255, 230,  50)
ORANGE  = (255, 140,  0)
CYAN    = (0,   220, 255)
PURPLE  = (180,  50, 255)
PINK    = (255,  80, 200)
GRAY    = (100, 100, 100)
DARK    = (8,    8,  12)
NEON_G  = (57,  255, 20)

# Minimal palette
LIGHT   = (200, 200, 200)
DIM     = (60,   60,  65)
ACCENT  = (255, 255, 255)
HIT_COL = (255,  60,  60)

clock = pygame.time.Clock()
FPS   = 60

# ============================================================
#  FONTS
# ============================================================
font_big    = pygame.font.SysFont("consolas", 48, bold=True)
font_med    = pygame.font.SysFont("consolas", 28, bold=True)
font_small  = pygame.font.SysFont("consolas", 20)
font_tiny   = pygame.font.SysFont("consolas", 16)
font_input  = pygame.font.SysFont("consolas", 26, bold=True)

# ============================================================
#  WORD LISTS PER LEVEL GROUP
# ============================================================
WORDS = {
    "easy":   ["cat","dog","run","fly","gun","hit","zap","pop","sun","map",
                "cup","bat","net","fog","ice","ant","bee","cap","den","elf"],
    "medium": ["alien","laser","comet","orbit","pilot","radar","robot","space",
                "probe","boost","craft","flare","hyper","lunar","nexus","ozone",
                "pluto","quark","realm","sigma"],
    "hard":   ["asteroid","blackhole","cosmonaut","destroyer","explosion",
                "federation","galactic","hyperspace","interstellar","jetpropel",
                "kingplanet","lasercannon","meteorite","navigation","observatory",
                "planetarium","quantumleap","rocketlaunch","supernova","teleporter"],
    "boss_small": ["fire","zap","hit","bang","boom","shot","kill","burn","doom","nuke"],
}

BOSS_WORDS = {
    1:  ["invasion","starship","moonwalk"],
    2:  ["blackstar","meteoroid","spacedock"],
    3:  ["alienfleet","cosmicblast","starcluster"],
    4:  ["photontorpedo","quantumfield","darkmatrix"],
    5:  ["nebulastrike","gravitywarp","sunblazer"],
    6:  ["hyperdrivecore","plasmacannon","ionicstorm"],
    7:  ["interstellarwar","cosmicdetonation","galaxybreaker"],
    8:  ["universalchaos","dimensionrift","spacetimedrift"],
    9:  ["apocalypticblast","cosmicannihilator","stellarexplosion"],
    10: ["universalannihilation","cosmicdevastationcore","intergalacticmeltdown",
         "quantumsingularityblast","hyperdimensionalrift"],
}

# Level config: (word_pool, enemy_count_normal, speed, boss_hp)
LEVEL_CONFIG = {
    1:  ("easy",   3, 0.6,  3),
    2:  ("easy",   4, 0.7,  4),
    3:  ("easy",   4, 0.8,  4),
    4:  ("medium", 4, 0.9,  5),
    5:  ("medium", 5, 1.0,  5),
    6:  ("medium", 5, 1.1,  6),
    7:  ("hard",   5, 1.2,  7),
    8:  ("hard",   6, 1.3,  8),
    9:  ("hard",   6, 1.4,  9),
    10: ("hard",   6, 1.6, 15),
}

LEVEL_TIME = 60  # 1 minute

# Combo tracking
combo_count = 0
max_combo = 0

# ============================================================
#  STARS (background)
# ============================================================
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
          random.uniform(0.3, 1.5)) for _ in range(200)]

def draw_stars():
    for sx, sy, sp in stars:
        brightness = int(80 + sp * 60)
        pygame.draw.circle(screen, (brightness, brightness, brightness),
                           (int(sx), int(sy)), int(sp))

def scroll_stars():
    global stars
    stars = [((sx - sp * 0.5) % WIDTH, sy, sp) for sx, sy, sp in stars]

# ============================================================
#  PARTICLE SYSTEM
# ============================================================
particles = []

def spawn_particles(x, y, color, count=18):
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(20, 40),
            "color": color,
            "size": random.randint(2, 5),
        })

def update_particles():
    global particles
    alive = []
    for p in particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
        p["vx"] *= 0.92
        p["vy"] *= 0.92
        r = min(255, p["color"][0])
        g = min(255, p["color"][1])
        b = min(255, p["color"][2])
        if p["life"] > 0:
            pygame.draw.circle(screen, (r, g, b), (int(p["x"]), int(p["y"])), p["size"])
            alive.append(p)
    particles[:] = alive

# ============================================================
#  LETTER BULLET (real projectile that flies to target)
# ============================================================
class LetterBullet:
    """A real bullet projectile that flies from player to enemy/boss.
    When it reaches the target it confirms the hit (letter turns red)."""
    def __init__(self, sx, sy, target, letter_idx, is_last=False, is_boss=False):
        self.x = float(sx)
        self.y = float(sy)
        self.target = target        # Enemy or Boss object
        self.letter_idx = letter_idx
        self.is_last = is_last      # True if this is the final letter
        self.is_boss = is_boss
        self.speed = 16             # pixels per frame
        self.alive = True
        self.trail = []             # trail positions

    def update(self):
        # Track target's current position (homing bullet)
        tx, ty = float(self.target.x), float(self.target.y)
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)

        if dist < 18:  # arrived!
            self.alive = False
            spawn_particles(tx, ty, WHITE, 6)
            if self.is_boss:
                self.target.shake = 8
                if self.is_last:
                    spawn_particles(tx, ty, WHITE, 25)
                    spawn_particles(tx, ty, LIGHT, 20)
            else:
                self.target.confirm_letter_hit(self.letter_idx, self.is_last)
            return

        # Save trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)

        # Move toward target
        self.x += dx / dist * self.speed
        self.y += dy / dist * self.speed

        if self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50:
            self.alive = False

    def draw(self):
        # Trail (fading dots)
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / max(1, len(self.trail))  # 0..1
            size = max(1, int(2 * t))
            v = int(180 * t)
            pygame.draw.circle(screen, (v, v, v), (int(tx), int(ty)), size)
        # Main bullet
        pygame.draw.circle(screen, LIGHT, (int(self.x), int(self.y)), 5)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 2)

flying_bullets = []   # global list of active letter bullets

def fire_letter_bullet(player_x, player_y, target, letter_idx,
                       is_last=False, is_boss=False):
    """Fire a real bullet from player toward target."""
    flying_bullets.append(
        LetterBullet(player_x, player_y - 30, target, letter_idx,
                     is_last, is_boss)
    )

def update_flying_bullets():
    global flying_bullets
    for b in flying_bullets:
        b.update()
    flying_bullets = [b for b in flying_bullets if b.alive]

def draw_flying_bullets():
    for b in flying_bullets:
        b.draw()

# ============================================================
#  PLAYER BULLET (enemy attack)
# ============================================================
class EnemyBullet:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vy = 3.5
        self.alive = True

    def update(self):
        self.y += self.vy
        if self.y > HEIGHT:
            self.alive = False

    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(screen, (180, 40, 40), (int(self.x), int(self.y)), 2)

# ============================================================
#  NORMAL ENEMY (alien)
# ============================================================
class Enemy:
    def __init__(self, word, speed):
        self.word = word
        self.x = random.randint(80, WIDTH - 80)
        self.y = random.randint(-60, -20)
        self.speed = speed
        self.alive = True
        self.color = LIGHT
        self.size = 26
        self.shake = 0
        self.confirmed_hits = 0  # letters whose bullets have arrived (shown RED)
        self.typed_count = 0     # letters the player has typed (bullets in-flight)
        self.dying = False
        self.death_timer = 0

    def update(self):
        if self.dying:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.alive = False
            return
        self.y += self.speed
        if self.shake > 0:
            self.shake -= 1
        if self.y > HEIGHT + 40:
            self.alive = False

    def confirm_letter_hit(self, letter_idx, is_last):
        """Called when a bullet arrives at this enemy."""
        self.confirmed_hits = max(self.confirmed_hits, letter_idx + 1)
        self.shake = 6
        if is_last:
            self.dying = True
            self.death_timer = 18
            self.speed = 0
            spawn_particles(self.x, self.y, WHITE, 25)
            spawn_particles(self.x, self.y, LIGHT, 15)

    def hit(self):
        self.alive = False

    def draw(self, typed_so_far=""):
        cx, cy = int(self.x), int(self.y)
        sx = cx + random.randint(-3, 3) if self.shake else cx

        # Death animation: flash, shrink
        if self.dying:
            flash = self.death_timer % 3 == 0
            shrink = max(0.2, self.death_timer / 18)
            col = WHITE if flash else GRAY
            sz = int(22 * shrink)
            pygame.draw.ellipse(screen, col, (sx - sz, cy - sz//2, sz*2, sz))
            ring_r = int(40 * (1 - shrink) + 8)
            pygame.draw.circle(screen, LIGHT, (sx, cy), ring_r, 1)
            return

        # Alien body (minimal)
        pygame.draw.ellipse(screen, DIM, (sx-20, cy-12, 40, 24))
        pygame.draw.ellipse(screen, LIGHT, (sx-20, cy-12, 40, 24), 1)
        pygame.draw.ellipse(screen, GRAY, (sx-8, cy-20, 16, 12))
        # Eyes
        pygame.draw.circle(screen, WHITE, (sx-6, cy-14), 3)
        pygame.draw.circle(screen, WHITE, (sx+6, cy-14), 3)
        pygame.draw.circle(screen, BLACK, (sx-6, cy-14), 1)
        pygame.draw.circle(screen, BLACK, (sx+6, cy-14), 1)
        # Legs
        for lx in [-14, -5, 5, 14]:
            pygame.draw.line(screen, GRAY, (sx+lx, cy+10), (sx+lx, cy+20), 1)

        # Word display — 3 states per letter
        confirmed = self.confirmed_hits   # bullet arrived = RED
        typed = self.typed_count          # typed but in-flight = ORANGE pulse
        letter_surfs = []
        total_w = 0
        for i, ch in enumerate(self.word):
            if i < confirmed:
                s = font_small.render(ch, True, RED)
            elif i < typed:
                s = font_small.render(ch, True, GRAY)
            else:
                s = font_small.render(ch, True, WHITE)
            letter_surfs.append(s)
            total_w += s.get_width()

        wx = cx - total_w // 2
        wy = cy + 28

        # Background box
        bg_surf = pygame.Surface((total_w + 8, 22), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 160))
        screen.blit(bg_surf, (wx - 4, wy - 2))

        # Border
        border_col = DIM
        if confirmed > 0:
            progress = confirmed / len(self.word)
            v = int(100 + 155 * progress)
            border_col = (v, int(60 * (1 - progress)), int(60 * (1 - progress)))
        pygame.draw.rect(screen, border_col,
                         (wx - 4, wy - 2, total_w + 8, 22), 1, border_radius=4)

        # Draw letters
        cur_x = wx
        for s in letter_surfs:
            screen.blit(s, (cur_x, wy))
            cur_x += s.get_width()

        # RED damage line under confirmed letters
        if confirmed > 0:
            done_w = sum(letter_surfs[i].get_width() for i in range(confirmed))
            pygame.draw.line(screen, RED, (wx, wy + 18), (wx + done_w, wy + 18), 2)

# ============================================================
#  BOSS
# ============================================================
class Boss:
    def __init__(self, level, word_pool):
        self.level = level
        self.words = BOSS_WORDS.get(level, ["supernova", "blackhole"])
        self.small_words = WORDS["boss_small"]
        self.x = float(WIDTH // 2)
        self.y = 130.0
        self.hp = LEVEL_CONFIG[level][3]
        self.max_hp = self.hp
        self.alive = True
        self.move_dir = 1
        self.speed = 1.8 + level * 0.15
        self.current_word_idx = 0
        self.shoot_timer = 0
        self.shoot_interval = max(90, 200 - level * 15)
        self.enemy_bullets = []
        self.phase = "word"  # "word" or "small"
        self.small_word_queue = []
        self.small_timer = 0
        self.shake = 0
        self.color = DIM if level < 10 else GRAY
        self.size = 55 + level * 3
        self.confirmed_letters = 0  # for per-letter bullet visual

    @property
    def current_word(self):
        if self.phase == "word":
            return self.words[self.current_word_idx % len(self.words)]
        elif self.small_word_queue:
            return self.small_word_queue[0]
        return ""

    def next_word(self):
        if self.phase == "word":
            self.current_word_idx += 1
            self.hp -= 1
            spawn_particles(self.x, self.y, WHITE, 25)
            if self.hp <= 0:
                self.alive = False

    def hit_small(self):
        if self.small_word_queue:
            self.small_word_queue.pop(0)
        if not self.small_word_queue:
            self.phase = "word"

    def update(self):
        # Move left-right
        self.x += self.speed * self.move_dir
        if self.x > WIDTH - 80 or self.x < 80:
            self.move_dir *= -1

        if self.shake > 0:
            self.shake -= 1

        # Shoot small bullets
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            self.enemy_bullets.append(EnemyBullet(self.x, self.y + self.size // 2))
            # switch to small word attack
            if self.phase == "word" and random.random() < 0.5:
                self.phase = "small"
                count = random.randint(2, 4)
                self.small_word_queue = random.choices(self.small_words, k=count)

        # Update enemy bullets
        for b in self.enemy_bullets:
            b.update()
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

    def draw(self, typed_so_far=""):
        cx, cy = int(self.x), int(self.y)
        sx = cx + random.randint(-3, 3) if self.shake else cx

        s = self.size
        col = self.color

        # Main body (minimal)
        pygame.draw.ellipse(screen, col, (sx - s, cy - s//2, s*2, s))
        pygame.draw.ellipse(screen, LIGHT, (sx - s, cy - s//2, s*2, s), 2)
        pygame.draw.ellipse(screen, GRAY, (sx - s//2, cy - s, s, s//2))
        pygame.draw.ellipse(screen, LIGHT, (sx - s//2, cy - s, s, s//2), 1)

        # Eyes
        for ex in [-18, 18]:
            pygame.draw.circle(screen, WHITE, (sx+ex, cy-10), 8)
            pygame.draw.circle(screen, BLACK, (sx+ex, cy-10), 4)
            pygame.draw.circle(screen, RED,   (sx+ex, cy-10), 2)

        # Mouth
        pygame.draw.arc(screen, LIGHT, (sx-20, cy, 40, 20), math.pi, 2*math.pi, 2)

        # Cannons
        for cx2 in [-s+10, s-10]:
            pygame.draw.rect(screen, GRAY, (sx+cx2-5, cy+s//2-5, 10, 25), border_radius=3)
            pygame.draw.rect(screen, LIGHT, (sx+cx2-5, cy+s//2-5, 10, 25), 1, border_radius=3)

        # HP bar
        bar_w = 250
        bar_x = sx - bar_w // 2
        bar_y = cy - s - 30
        pygame.draw.rect(screen, DIM, (bar_x, bar_y, bar_w, 10), border_radius=4)
        fill = int(bar_w * self.hp / self.max_hp)
        hp_col = WHITE if self.hp > self.max_hp * 0.5 else LIGHT if self.hp > self.max_hp * 0.25 else RED
        pygame.draw.rect(screen, hp_col, (bar_x, bar_y, fill, 10), border_radius=4)
        pygame.draw.rect(screen, GRAY, (bar_x, bar_y, bar_w, 10), 1, border_radius=4)
        hp_txt = font_tiny.render(f"HP {self.hp}/{self.max_hp}", True, LIGHT)
        screen.blit(hp_txt, (bar_x + bar_w//2 - hp_txt.get_width()//2, bar_y - 16))

        # Current word — letters turn RED as bullets arrive
        word = self.current_word
        typed_len = len(typed_so_far)
        confirmed = getattr(self, 'confirmed_letters', 0)
        # Render letter by letter
        word_letters = []
        total_w = 0
        for i, ch in enumerate(word):
            if i < confirmed:
                ls = font_med.render(ch, True, RED)
            elif i < typed_len:
                ls = font_med.render(ch, True, GRAY)
            else:
                ls = font_med.render(ch, True, WHITE)
            word_letters.append(ls)
            total_w += ls.get_width()
        wx = sx - total_w // 2
        wy = cy + s + 15
        pygame.draw.rect(screen, BLACK, (wx-6, wy-4, total_w+12, 34), border_radius=5)
        pygame.draw.rect(screen, GRAY, (wx-6, wy-4, total_w+12, 34), 1, border_radius=5)
        cur_x = wx
        for ls in word_letters:
            screen.blit(ls, (cur_x, wy))
            cur_x += ls.get_width()

        if self.phase == "small" and len(self.small_word_queue) > 1:
            info = font_tiny.render(f"+ {len(self.small_word_queue)-1} more", True, GRAY)
            screen.blit(info, (sx - info.get_width()//2, wy + 36))

        # Enemy bullets
        for b in self.enemy_bullets:
            b.draw()

# ============================================================
#  PLAYER
# ============================================================
class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 70
        self.hp = 5
        self.max_hp = 5
        self.invincible = 0
        self.aim_angle = -math.pi / 2  # pointing up by default
        self.target_angle = -math.pi / 2
        self.aim_x = None  # target position for aim line
        self.aim_y = None

    def set_target(self, tx, ty):
        """Set the target position for auto-aim."""
        self.aim_x = tx
        self.aim_y = ty
        dx = tx - self.x
        dy = ty - self.y
        self.target_angle = math.atan2(dy, dx)

    def clear_target(self):
        self.aim_x = None
        self.aim_y = None
        self.target_angle = -math.pi / 2

    def take_damage(self):
        if self.invincible <= 0:
            self.hp -= 1
            self.invincible = 90
            spawn_particles(self.x, self.y, LIGHT, 15)

    def update(self):
        if self.invincible > 0:
            self.invincible -= 1
        # Smoothly rotate toward target
        diff = self.target_angle - self.aim_angle
        # Normalize to [-pi, pi]
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        self.aim_angle += diff * 0.2  # smooth rotation speed

    def draw(self):
        cx, cy = self.x, self.y
        blink = self.invincible > 0 and (self.invincible // 8) % 2 == 0
        if blink:
            return

        angle = self.aim_angle

        # --- Aim line (faint dotted line to target) ---
        if self.aim_x is not None and self.aim_y is not None:
            dx = self.aim_x - cx
            dy = self.aim_y - cy
            dist = math.hypot(dx, dy)
            if dist > 0:
                steps = int(dist / 14)
                for i in range(steps):
                    t = i / max(1, steps)
                    px = cx + dx * t
                    py = cy + dy * t
                    if i % 3 == 0:
                        v = int(40 * (1 - t))
                        pygame.draw.circle(screen, (v, v, v),
                                           (int(px), int(py)), 1)
            # Crosshair at target (minimal)
            tx, ty = int(self.aim_x), int(self.aim_y)
            cr_size = 8
            pygame.draw.circle(screen, GRAY, (tx, ty), cr_size, 1)
            pygame.draw.line(screen, GRAY, (tx - cr_size - 2, ty),
                             (tx + cr_size + 2, ty), 1)
            pygame.draw.line(screen, GRAY, (tx, ty - cr_size - 2),
                             (tx, ty + cr_size + 2), 1)

        # --- Ship body (rotated) ---
        # Ship points (triangle) rotated by aim_angle
        # Base angle offset: -pi/2 means "up"
        cos_a = math.cos(angle + math.pi / 2)
        sin_a = math.sin(angle + math.pi / 2)

        def rot(px, py):
            """Rotate point around (0,0)."""
            return (cx + px * cos_a - py * sin_a,
                    cy + px * sin_a + py * cos_a)

        # Outer hull
        p1 = rot(0, -30)
        p2 = rot(-22, 20)
        p3 = rot(22, 20)
        pygame.draw.polygon(screen, DIM, [p1, p2, p3])
        pygame.draw.polygon(screen, LIGHT, [p1, p2, p3], 1)

        # Inner hull
        p4 = rot(0, -20)
        p5 = rot(-12, 15)
        p6 = rot(12, 15)
        pygame.draw.polygon(screen, GRAY, [p4, p5, p6])

        # Engine glow
        eng = rot(0, 22)
        pygame.draw.circle(screen, LIGHT, (int(eng[0]), int(eng[1])), 4)
        pygame.draw.circle(screen, WHITE, (int(eng[0]), int(eng[1])), 2)

        # Cockpit
        cock = rot(0, -12)
        pygame.draw.circle(screen, WHITE, (int(cock[0]), int(cock[1])), 4)
        pygame.draw.circle(screen, GRAY,  (int(cock[0]), int(cock[1])), 2)

        # Muzzle flash when firing
        if self.aim_x is not None:
            nose = rot(0, -32)
            pygame.draw.circle(screen, WHITE, (int(nose[0]), int(nose[1])), 2)

        # HP hearts (minimal bars instead)
        for i in range(self.max_hp):
            col = WHITE if i < self.hp else DIM
            hx = 10 + i * 18
            hy = HEIGHT - 20
            pygame.draw.rect(screen, col, (hx, hy, 12, 8), border_radius=2)

# ============================================================
#  HELPER: draw HUD
# ============================================================
def draw_hud(level, timer_left, score, typed_text, target_word):
    # Top bar
    pygame.draw.rect(screen, (12, 12, 16), (0, 0, WIDTH, 36))
    pygame.draw.line(screen, DIM, (0, 36), (WIDTH, 36), 1)

    lv_txt = font_small.render(f"LV {level}", True, LIGHT)
    screen.blit(lv_txt, (10, 8))

    sc_txt = font_small.render(f"SCORE {score}", True, WHITE)
    screen.blit(sc_txt, (WIDTH//2 - sc_txt.get_width()//2, 8))

    # Combo display
    if combo_count > 1:
        combo_txt = font_tiny.render(f"x{combo_count}", True, LIGHT)
        screen.blit(combo_txt, (WIDTH//2 - combo_txt.get_width()//2, 28))

    mins = int(timer_left) // 60
    secs = int(timer_left) % 60
    tcol = RED if timer_left < 15 else LIGHT
    tm_txt = font_small.render(f"{mins:01d}:{secs:02d}", True, tcol)
    screen.blit(tm_txt, (WIDTH - tm_txt.get_width() - 10, 8))

    # Input box (compact)
    box_y = HEIGHT - 28
    pygame.draw.rect(screen, (12, 12, 16), (0, box_y - 2, WIDTH, 30))
    pygame.draw.line(screen, DIM, (0, box_y - 2), (WIDTH, box_y - 2), 1)

    # Color typed text
    if target_word:
        correct = target_word.startswith(typed_text)
        inp_col = WHITE if correct else RED
    else:
        inp_col = LIGHT

    typed_surf = font_tiny.render(typed_text + "_", True, inp_col)
    screen.blit(typed_surf, (10, box_y + 4))

    if target_word:
        tw = font_tiny.render(target_word, True, GRAY)
        screen.blit(tw, (WIDTH - tw.get_width() - 10, box_y + 4))

# ============================================================
#  SCREEN: TITLE
# ============================================================
async def title_screen():
    anim = 0
    while True:
        await asyncio.sleep(0)
        screen.fill(DARK)
        draw_stars()
        scroll_stars()
        anim += 1

        t = font_big.render("SPACE TYPING", True, WHITE)
        t2 = font_big.render("SHOOTER", True, LIGHT)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 130))
        screen.blit(t2, (WIDTH//2 - t2.get_width()//2, 185))

        desc = [
            "Type the word to destroy aliens.",
            "Each letter fires a bullet.",
            "Survive 1 minute, then BOSS.",
            "TAB to pause.",
        ]
        for i, d in enumerate(desc):
            ds = font_small.render(d, True, GRAY)
            screen.blit(ds, (WIDTH//2 - ds.get_width()//2, 300 + i * 30))

        blink = (anim // 30) % 2 == 0
        if blink:
            st = font_med.render("ENTER to Start", True, WHITE)
            screen.blit(st, (WIDTH//2 - st.get_width()//2, 450))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

        pygame.display.flip()
        clock.tick(FPS)

# ============================================================
#  SCREEN: LEVEL INTRO
# ============================================================
async def level_intro(level):
    timer = 120
    while timer > 0:
        await asyncio.sleep(0)
        screen.fill(DARK)
        draw_stars()
        scroll_stars()

        t = font_big.render(f"LEVEL {level}", True, WHITE)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 220))

        pool_name = LEVEL_CONFIG[level][0]
        diff = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
        d = font_med.render(diff[pool_name], True, LIGHT)
        screen.blit(d, (WIDTH//2 - d.get_width()//2, 290))

        hint = font_small.render("Get ready...", True, DIM)
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, 350))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return

        timer -= 1
        pygame.display.flip()
        clock.tick(FPS)

# ============================================================
#  SCREEN: BOSS INTRO
# ============================================================
async def boss_intro(level):
    timer = 100
    while timer > 0:
        await asyncio.sleep(0)
        screen.fill((15, 0, 0))
        draw_stars()

        t = font_big.render("BOSS", True, WHITE)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 250))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        timer -= 1
        pygame.display.flip()
        clock.tick(FPS)

# ============================================================
#  SCREEN: GAME OVER / WIN
# ============================================================
async def end_screen(won, score):
    while True:
        await asyncio.sleep(0)
        screen.fill(DARK)
        draw_stars()

        if won:
            t = font_big.render("YOU WIN", True, WHITE)
        else:
            t = font_big.render("GAME OVER", True, WHITE)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 220))

        sc = font_med.render(f"Score: {score}", True, LIGHT)
        screen.blit(sc, (WIDTH//2 - sc.get_width()//2, 300))

        combo_info = font_small.render(f"Max Combo: {max_combo}", True, GRAY)
        screen.blit(combo_info, (WIDTH//2 - combo_info.get_width()//2, 340))

        info = font_small.render("R - Restart  |  Q - Quit", True, DIM)
        screen.blit(info, (WIDTH//2 - info.get_width()//2, 390))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                if event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(FPS)

# ============================================================
#  FIND BEST MATCH ENEMY
# ============================================================
def find_target(typed, enemies):
    """Return the closest enemy (highest y) whose word starts with typed."""
    best = None
    best_y = -1
    for e in enemies:
        if e.alive and not e.dying and e.word.startswith(typed) and e.y > best_y:
            best = e
            best_y = e.y
    return best

# ============================================================
#  MAIN GAME LOOP
# ============================================================
async def play_level(level, score, player):
    global combo_count, max_combo
    pool_name, max_enemies, speed, boss_hp = LEVEL_CONFIG[level]
    word_pool = WORDS[pool_name]

    enemies = []
    spawn_timer = 0
    spawn_interval = max(60, 150 - level * 8)

    typed_text = ""
    target_enemy = None
    boss = None
    boss_mode = False

    level_timer = LEVEL_TIME * FPS  # frames
    phase = "normal"  # "normal" or "boss"

    def spawn_enemy():
        if len(enemies) < max_enemies:
            w = random.choice(word_pool)
            enemies.append(Enemy(w, speed + random.uniform(-0.2, 0.3)))

    # Initial spawn
    for _ in range(2):
        spawn_enemy()

    running = True
    while running:
        await asyncio.sleep(0)
        dt = clock.tick(FPS)
        screen.fill(DARK)
        draw_stars()
        scroll_stars()
        update_particles()
        update_flying_bullets()

        # ---- Events ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit", score
                elif event.key == pygame.K_TAB:
                    # PAUSE
                    paused = True
                    pause_txt = font_big.render("PAUSED", True, WHITE)
                    pause_hint = font_small.render("TAB to resume", True, DIM)
                    screen.blit(pause_txt, (WIDTH//2 - pause_txt.get_width()//2, HEIGHT//2 - 40))
                    screen.blit(pause_hint, (WIDTH//2 - pause_hint.get_width()//2, HEIGHT//2 + 20))
                    pygame.display.flip()
                    while paused:
                        await asyncio.sleep(0)
                        for pe in pygame.event.get():
                            if pe.type == pygame.QUIT:
                                pygame.quit(); sys.exit()
                            if pe.type == pygame.KEYDOWN and pe.key == pygame.K_TAB:
                                paused = False
                        clock.tick(30)
                elif event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]
                    if not typed_text:
                        target_enemy = None
                elif event.key == pygame.K_RETURN:
                    typed_text = ""
                    target_enemy = None
                else:
                    ch = event.unicode.lower()
                    if ch.isalpha():
                        typed_text += ch

                        # --- BOSS MODE ---
                        if boss_mode and boss and boss.alive:
                            bw = boss.current_word
                            if bw.startswith(typed_text):
                                # Fire bullet per letter!
                                is_last = (typed_text == bw)
                                letter_idx = len(typed_text) - 1
                                fire_letter_bullet(player.x, player.y,
                                                   boss, letter_idx,
                                                   is_last, is_boss=True)
                                if is_last:
                                    combo_count += 1
                                    if combo_count > max_combo:
                                        max_combo = combo_count
                                    if boss.phase == "word":
                                        boss.next_word()
                                    else:
                                        boss.hit_small()
                                    boss.confirmed_letters = 0
                                    typed_text = ""
                                else:
                                    boss.confirmed_letters = getattr(boss, 'confirmed_letters', 0)
                            else:
                                typed_text = ch  # reset on wrong
                                combo_count = 0
                                boss.confirmed_letters = 0

                        # --- NORMAL MODE ---
                        else:
                            if target_enemy is None or not target_enemy.alive or target_enemy.dying:
                                target_enemy = find_target(typed_text, enemies)

                            if target_enemy and target_enemy.alive and not target_enemy.dying:
                                if target_enemy.word.startswith(typed_text):
                                    # Fire REAL bullet per letter!
                                    letter_idx = len(typed_text) - 1
                                    is_last = (typed_text == target_enemy.word)
                                    fire_letter_bullet(player.x, player.y,
                                                       target_enemy, letter_idx,
                                                       is_last, is_boss=False)
                                    target_enemy.typed_count = len(typed_text)

                                    if is_last:
                                        # Score on type, destruction on bullet arrival
                                        combo_count += 1
                                        if combo_count > max_combo:
                                            max_combo = combo_count
                                        combo_bonus = combo_count * 5
                                        score += len(target_enemy.word) * 10 + combo_bonus
                                        typed_text = ""
                                        target_enemy = None
                                else:
                                    # Wrong letter — reset
                                    typed_text = ch
                                    target_enemy = find_target(typed_text, enemies)
                            else:
                                target_enemy = find_target(typed_text, enemies)

        # ---- Timer ----
        if phase == "normal":
            level_timer -= 1
            if level_timer <= 0:
                # Switch to boss
                phase = "boss"
                boss_mode = True
                enemies.clear()
                typed_text = ""
                target_enemy = None
                await boss_intro(level)
                boss = Boss(level, pool_name)

        # ---- Spawn enemies ----
        if phase == "normal":
            spawn_timer += 1
            if spawn_timer >= spawn_interval:
                spawn_timer = 0
                spawn_enemy()

        # ---- Update enemies ----
        for e in enemies:
            e.update()
            # Check if reached player
            if e.y > HEIGHT - 80 and e.alive:
                e.alive = False
                player.take_damage()
                combo_count = 0  # Reset combo on damage
                spawn_particles(player.x, player.y, LIGHT, 12)

        enemies = [e for e in enemies if e.alive]

        # ---- Update boss ----
        if boss_mode and boss:
            boss.update()
            # Boss bullets hit player
            for b in boss.enemy_bullets:
                if b.alive:
                    dist = math.hypot(b.x - player.x, b.y - player.y)
                    if dist < 28:
                        b.alive = False
                        player.take_damage()
                        combo_count = 0

            if not boss.alive:
                spawn_particles(boss.x, boss.y, WHITE, 60)
                score += 500 * level
                return "next", score

        # ---- Update player aim ----
        # Auto-aim toward current target
        if boss_mode and boss and boss.alive:
            player.set_target(boss.x, boss.y)
        elif target_enemy and target_enemy.alive and not target_enemy.dying:
            player.set_target(target_enemy.x, target_enemy.y)
        else:
            player.clear_target()

        # ---- Update player ----
        player.update()

        # ---- Player dead ----
        if player.hp <= 0:
            return "dead", score

        # ---- Draw ----
        # Enemies
        for e in enemies:
            e.draw()

        # Boss
        if boss_mode and boss and boss.alive:
            boss.draw(typed_text)

        # Flying bullets (draw on top of enemies)
        draw_flying_bullets()

        # Player
        player.draw()

        # HUD
        timer_left = level_timer / FPS if phase == "normal" else 0
        current_target_word = ""
        if boss_mode and boss:
            current_target_word = boss.current_word
        elif target_enemy and target_enemy.alive:
            current_target_word = target_enemy.word

        if phase == "boss":
            phase_label = font_small.render("BOSS", True, WHITE)
            screen.blit(phase_label, (WIDTH//2 - phase_label.get_width()//2, 48))
            timer_left = 0
        else:
            timer_left = level_timer / FPS

        draw_hud(level, timer_left, score, typed_text, current_target_word)

        pygame.display.flip()

    return "quit", score

# ============================================================
#  MAIN
# ============================================================
async def main():
    global combo_count, max_combo
    while True:
        await title_screen()
        score = 0
        combo_count = 0
        max_combo = 0
        player = Player()

        for level in range(1, 11):
            await level_intro(level)
            result, score = await play_level(level, score, player)

            if result == "dead":
                r = await end_screen(False, score)
                if r == "restart":
                    break
            elif result == "quit":
                pygame.quit(); sys.exit()
            elif result == "next":
                if level == 10:
                    await end_screen(True, score)
                    break
                # Small heal between levels
                if player.hp < player.max_hp:
                    player.hp = min(player.max_hp, player.hp + 1)

asyncio.run(main())
