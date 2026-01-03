import sys

# ===== libpng iCCP 경고 숨기기 =====
class _NullWriter:
    def write(self, text): pass
    def flush(self): pass

sys.stderr = _NullWriter()

import pygame
import random
import math
import os
from score_system import TetrisScore
from PIL import Image, PngImagePlugin
import io


# ======================
# 기본 설정
# ======================
GRID_W, GRID_H = 10, 20
BLOCK = 30
SIDE = 240

WIDTH  = GRID_W * BLOCK + SIDE
HEIGHT = GRID_H * BLOCK

BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
GRAY  = (120, 120, 120)

SFX_ENABLED = False

# ======================
# 이미지 로드 (iCCP 제거 안전모드)
# ======================
def load_png_safe(path):
    if not os.path.exists(path):
        print(f"[이미지 없음] {path}")
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            im.info.pop("icc_profile", None)
            im.info.pop("srgb", None)
            data = io.BytesIO()
            im.save(data, format="PNG", pnginfo=PngImagePlugin.PngInfo())
            data.seek(0)
            return pygame.image.load(data)
    except Exception as e:
        print(f"[로드 실패] {path} -> {e}")
        return None


# 블록 이미지 로드
BLOCK_DIR = "assets/blocks"
COLOR_NAMES = [
    "blue", "green", "red", "orange",
    "purple", "pink", "lightblue"
]

ALL_COLORS = COLOR_NAMES + ["gray", "darkgray", "white"]

BLOCK_IMAGES = {}
for name in ALL_COLORS:
    img = load_png_safe(os.path.join(BLOCK_DIR, f"{name}.png"))
    if img:
        BLOCK_IMAGES[name] = pygame.transform.scale(img, (BLOCK, BLOCK))
    else:
        BLOCK_IMAGES[name] = None


# ======================
# 테트로미노
# ======================
SHAPES = [
    [[1,1,1,1]],
    [[1,1],[1,1]],
    [[0,1,0],[1,1,1]],
    [[1,0,0],[1,1,1]],
    [[0,0,1],[1,1,1]],
    [[0,1,1],[1,1,0]],
    [[1,1,0],[0,1,1]]
]

SHAPE_COLORS = [
    "lightblue",  # I
    "pink",       # O
    "purple",     # T
    "blue",       # J
    "orange",     # L
    "green",      # S
    "red"         # Z
]


# ======================
# 블록 클래스
# ======================
class Piece:
    def __init__(self):
        shape_index = random.randrange(len(SHAPES))
        shape = SHAPES[shape_index]
        self.rotations = self.make_rotations(shape)
        self.rotation = 0
        self.shape = self.rotations[self.rotation]
        self.color = SHAPE_COLORS[shape_index]
        self.x = GRID_W // 2 - len(self.shape[0]) // 2
        self.y = 0

    def make_rotations(self, shape):
        rots, cur = [], shape
        for _ in range(4):
            if cur not in rots:
                rots.append(cur)
            cur = [list(row) for row in zip(*cur[::-1])]
        return rots

    def rotate(self, grid):
        old = self.rotation
        old_x = self.x
        self.rotation = (self.rotation + 1) % len(self.rotations)
        self.shape = self.rotations[self.rotation]
        if self.collision(grid):
            # Simple wall kick to allow rotation near edges.
            for dx in (-1, 1, -2, 2):
                self.x = old_x + dx
                if not self.collision(grid):
                    return
            self.rotation = old
            self.shape = self.rotations[self.rotation]
            self.x = old_x

    def collision(self, grid):
        for y, row in enumerate(self.shape):
            for x, cell in enumerate(row):
                if cell:
                    px, py = self.x + x, self.y + y
                    if px < 0 or px >= GRID_W or py >= GRID_H:
                        return True
                    if py >= 0 and grid[py][px] is not None:
                        return True
        return False


# ======================
# 유틸
# ======================
def load_sound(path):
    return pygame.mixer.Sound(path) if os.path.exists(path) else None

def load_high_score(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().strip()
        return max(0, int(data)) if data else 0
    except (FileNotFoundError, ValueError, OSError):
        return 0

def save_high_score(path, score_value):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(score_value))
    except OSError:
        pass

def clear_lines(grid):
    new = [row for row in grid if None in row]
    cleared = GRID_H - len(new)
    for _ in range(cleared):
        new.insert(0, [None]*GRID_W)
    return new, cleared


# ======================
# 그리기
# ======================
def draw_grid(win, grid):
    for y in range(GRID_H):
        for x in range(GRID_W):
            cell = grid[y][x]
            if cell and BLOCK_IMAGES[cell]:
                win.blit(BLOCK_IMAGES[cell], (x*BLOCK, y*BLOCK))
            pygame.draw.rect(win, GRAY, (x*BLOCK, y*BLOCK, BLOCK, BLOCK), 1)

def draw_next(win, piece, font):
    win.blit(font.render("NEXT", True, WHITE), (GRID_W*BLOCK + 40, 30))
    for y, row in enumerate(piece.shape):
        for x, cell in enumerate(row):
            if cell:
                win.blit(
                    BLOCK_IMAGES[piece.color],
                    (GRID_W*BLOCK + 40 + x*BLOCK, 70 + y*BLOCK)
                )

def draw_current(win, current):
    for y, row in enumerate(current.shape):
        for x, cell in enumerate(row):
            if cell:
                px, py = current.x + x, current.y + y
                if 0 <= px < GRID_W and 0 <= py < GRID_H:
                    win.blit(BLOCK_IMAGES[current.color], (px*BLOCK, py*BLOCK))
                    pygame.draw.rect(win, GRAY, (px*BLOCK, py*BLOCK, BLOCK, BLOCK), 1)

def is_top_blocked(grid):
    return any(cell is not None for cell in grid[0])


# ======================
# 메인
# ======================
def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    pygame.key.set_repeat(220, 90)

    # 🎵 BGM
    bgm_loaded = False
    if os.path.exists("sounds/bgm.mp3"):
        pygame.mixer.music.load("sounds/bgm.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
        bgm_loaded = True

    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("파스텔 테트리스")

    font = pygame.font.SysFont("malgungothic", 24)
    level_font = pygame.font.SysFont("malgungothic", 48)
    bonus_font = pygame.font.SysFont("malgungothic", 64)
    info_font = pygame.font.SysFont("malgungothic", 20)
    clock = pygame.time.Clock()

    land = load_sound("sounds/block_land.wav") if SFX_ENABLED else None
    clear = load_sound("sounds/line_clear.wav") if SFX_ENABLED else None
    over  = load_sound("sounds/gameover.wav") if SFX_ENABLED else None

    high_score_path = "high_score.txt"
    high_score = load_high_score(high_score_path)

    base_fall_delay = 500
    level_pause_ms = 1200
    flash_duration = 200
    bonus_duration = 1600
    bonus_pos = (GRID_W * BLOCK // 2, HEIGHT // 2 - 40)
    game_over_duration = 5000
    restart_button = pygame.Rect(WIDTH // 2 - 90, HEIGHT // 2 + 80, 180, 48)

    def reset_game_state():
        grid = [[None]*GRID_W for _ in range(GRID_H)]
        current = Piece()
        next_piece = Piece()
        score = TetrisScore()
        fall_time = 0
        pause_until = 0
        flash_timer = 0
        bonus_text = ""
        bonus_timer = 0
        game_over = False
        game_over_until = 0
        game_over_sound_played = False
        game_over_music_stopped = False
        return (
            grid, current, next_piece, score,
            fall_time, pause_until, flash_timer,
            bonus_text, bonus_timer,
            game_over, game_over_until,
            game_over_sound_played, game_over_music_stopped
        )

    (
        grid, current, next_piece, score,
        fall_time, pause_until, flash_timer,
        bonus_text, bonus_timer,
        game_over, game_over_until,
        game_over_sound_played, game_over_music_stopped
    ) = reset_game_state()

    run = True

    while run:
        dt = clock.tick(60)
        now = pygame.time.get_ticks()
        paused = now < pause_until
        if game_over and now >= game_over_until and not game_over_music_stopped:
            if bgm_loaded:
                pygame.mixer.music.stop()
            game_over_music_stopped = True
        if not paused and not game_over:
            fall_time += dt
        if flash_timer > 0:
            flash_timer = max(0, flash_timer - dt)
        if bonus_timer > 0:
            bonus_timer = max(0, bonus_timer - dt)

        # 🎮 조작
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                run = False

            if paused:
                continue
            if game_over:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    (
                        grid, current, next_piece, score,
                        fall_time, pause_until, flash_timer,
                        bonus_text, bonus_timer,
                        game_over, game_over_until,
                        game_over_sound_played, game_over_music_stopped
                    ) = reset_game_state()
                    if bgm_loaded:
                        pygame.mixer.music.play(-1)
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if restart_button.collidepoint(e.pos):
                        (
                            grid, current, next_piece, score,
                            fall_time, pause_until, flash_timer,
                            bonus_text, bonus_timer,
                            game_over, game_over_until,
                            game_over_sound_played, game_over_music_stopped
                        ) = reset_game_state()
                        if bgm_loaded:
                            pygame.mixer.music.play(-1)
                continue

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    current.x -= 1;  current.x += current.collision(grid)
                if e.key == pygame.K_RIGHT:
                    current.x += 1;  current.x -= current.collision(grid)
                if e.key == pygame.K_DOWN:
                    current.y += 1
                    if current.collision(grid):
                        current.y -= 1
                    else:
                        score.soft_drop(1)
                if e.key == pygame.K_UP:
                    if not getattr(e, "repeat", False):
                        current.rotate(grid)
                if e.key == pygame.K_SPACE:
                    if getattr(e, "repeat", False):
                        continue
                    drop = 0
                    while True:
                        current.y += 1
                        if current.collision(grid):
                            current.y -= 1
                            break
                        drop += 1
                    if drop:
                        score.hard_drop(drop)

        # 🧱 자동 낙하
        fall_delay = max(80, base_fall_delay - (score.level - 1) * 35)
        if (not paused) and (not game_over) and fall_time > fall_delay:
            fall_time = 0
            current.y += 1
            if current.collision(grid):
                current.y -= 1
                for yy, row in enumerate(current.shape):
                    for xx, cell in enumerate(row):
                        if cell:
                            grid[current.y+yy][current.x+xx] = current.color

                if land: land.play()
                prev_level = score.level
                grid, c = clear_lines(grid)
                is_all_clear = all(cell is None for row in grid for cell in row)
                gained = score.clear_lines(c, is_all_clear=is_all_clear)
                if c and clear: clear.play()
                if c:
                    flash_timer = flash_duration
                    bonus_text = f"+{gained}"
                    bonus_timer = bonus_duration
                if score.level > prev_level:
                    pause_until = now + level_pause_ms

                if is_top_blocked(grid):
                    game_over = True
                    game_over_until = now + game_over_duration
                    if score.score > high_score:
                        high_score = score.score
                        save_high_score(high_score_path, high_score)
                    if over and not game_over_sound_played:
                        over.play()
                        game_over_sound_played = True
                else:
                    current, next_piece = next_piece, Piece()

        # 🎨 화면
        win.fill(BLACK)
        draw_grid(win, grid)
        draw_current(win, current)

        display_high_score = max(high_score, score.score)
        win.blit(font.render(f"최고점수: {display_high_score}", True, WHITE), (GRID_W*BLOCK + 30, HEIGHT - 110))

        win.blit(font.render(f"점수: {score.score}", True, WHITE), (GRID_W*BLOCK + 30, HEIGHT - 80))
        win.blit(font.render(f"레벨: {score.level}", True, WHITE), (GRID_W*BLOCK + 30, HEIGHT - 50))
        draw_next(win, next_piece, font)

        if bonus_timer > 0 and bonus_text:
            t = bonus_timer / bonus_duration
            scale = 1.15 - 0.15 * (1.0 - t)
            alpha = int(255 * min(1.0, t * 2))
            bonus = bonus_font.render(bonus_text, True, (255, 220, 80))
            w, h = bonus.get_size()
            bonus = pygame.transform.smoothscale(
                bonus, (int(w * scale), int(h * scale))
            )
            bonus.set_alpha(alpha)
            win.blit(
                bonus,
                (bonus_pos[0] - bonus.get_width() // 2, bonus_pos[1])
            )

        if flash_timer > 0:
            alpha = int(160 * (flash_timer / flash_duration))
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            win.blit(flash, (0, 0))

        if paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            win.blit(overlay, (0, 0))
            pulse = 1.0 + 0.06 * math.sin((pause_until - now) / 80.0)
            text = level_font.render(f"LEVEL {score.level}", True, (255, 220, 80))
            w, h = text.get_size()
            text = pygame.transform.smoothscale(
                text, (int(w * pulse), int(h * pulse))
            )
            win.blit(
                text,
                (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 60)
            )
            sub = info_font.render("READY?", True, (240, 240, 240))
            win.blit(
                sub,
                (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 10)
            )

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            win.blit(overlay, (0, 0))
            text = level_font.render("게임 종료", True, (255, 90, 90))
            win.blit(
                text,
                (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 40)
            )
            sub = info_font.render(f"점수: {score.score}", True, (240, 240, 240))
            win.blit(
                sub,
                (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20)
            )
            sub2 = info_font.render(f"최고점수: {high_score}", True, (240, 240, 240))
            win.blit(
                sub2,
                (WIDTH // 2 - sub2.get_width() // 2, HEIGHT // 2 + 50)
            )
            mouse_pos = pygame.mouse.get_pos()
            button_hover = restart_button.collidepoint(mouse_pos)
            button_color = (90, 90, 90) if button_hover else (70, 70, 70)
            pygame.draw.rect(win, button_color, restart_button, border_radius=6)
            pygame.draw.rect(win, (140, 140, 140), restart_button, 2, border_radius=6)
            label = info_font.render("다시 시작", True, (240, 240, 240))
            win.blit(
                label,
                (
                    restart_button.centerx - label.get_width() // 2,
                    restart_button.centery - label.get_height() // 2
                )
            )

        pygame.display.update()

    if game_over_sound_played:
        pygame.time.delay(300)
    pygame.quit()


# ======================
# 실행
# ======================
if __name__ == "__main__":
    main()
