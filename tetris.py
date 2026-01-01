import sys

# ===== libpng iCCP 경고 숨기기 =====
class _NullWriter:
    def write(self, text): pass
    def flush(self): pass

sys.stderr = _NullWriter()

import pygame
import random
import os
from score_system import TetrisScore
from PIL import Image
import io


# ======================
# 기본 설정
# ======================
GRID_W, GRID_H = 10, 20
BLOCK = 30
SIDE = 180

WIDTH  = GRID_W * BLOCK + SIDE
HEIGHT = GRID_H * BLOCK

BLACK = (30, 30, 30)
WHITE = (255, 255, 255)
GRAY  = (120, 120, 120)


# ======================
# 이미지 로드 (iCCP 제거 안전모드)
# ======================
def load_png_safe(path):
    if not os.path.exists(path):
        print(f"[이미지 없음] {path}")
        return None
    try:
        with Image.open(path) as im:
            data = io.BytesIO()
            im.save(data, format="PNG")  # iCCP 문제 제거
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


# ======================
# 블록 클래스
# ======================
class Piece:
    def __init__(self):
        shape = random.choice(SHAPES)
        self.rotations = self.make_rotations(shape)
        self.rotation = 0
        self.shape = self.rotations[self.rotation]
        self.color = random.choice(COLOR_NAMES)
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
        self.rotation = (self.rotation + 1) % len(self.rotations)
        self.shape = self.rotations[self.rotation]
        if self.collision(grid):
            self.rotation = old
            self.shape = self.rotations[self.rotation]

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

    # 🎵 BGM
    if os.path.exists("sounds/bgm.mp3"):
        pygame.mixer.music.load("sounds/bgm.mp3")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)

    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("파스텔 테트리스")

    font = pygame.font.SysFont("malgungothic", 24)
    clock = pygame.time.Clock()

    land = load_sound("sounds/block_land.wav")
    clear = load_sound("sounds/line_clear.wav")
    over  = load_sound("sounds/gameover.wav")

    grid = [[None]*GRID_W for _ in range(GRID_H)]
    current = Piece()
    next_piece = Piece()
    score = TetrisScore()

    fall_delay = 500
    fall_time = 0
    run = True

    while run:
        dt = clock.tick(60)
        fall_time += dt

        # 🎮 조작
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
            ):
                run = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:
                    current.x -= 1;  current.x += current.collision(grid)
                if e.key == pygame.K_RIGHT:
                    current.x += 1;  current.x -= current.collision(grid)
                if e.key == pygame.K_DOWN:
                    current.y += 1;  current.y -= current.collision(grid)
                if e.key == pygame.K_UP:
                    current.rotate(grid)
                if e.key == pygame.K_SPACE:
                    while not current.collision(grid): current.y += 1
                    current.y -= 1

        # 🧱 자동 낙하
        if fall_time > fall_delay:
            fall_time = 0
            current.y += 1
            if current.collision(grid):
                current.y -= 1
                for yy, row in enumerate(current.shape):
                    for xx, cell in enumerate(row):
                        if cell:
                            grid[current.y+yy][current.x+xx] = current.color

                if land: land.play()
                grid, c = clear_lines(grid)
                score.clear_lines(c)
                if c and clear: clear.play()

                if is_top_blocked(grid): run = False
                else: current, next_piece = next_piece, Piece()

        # 🎨 화면
        win.fill(BLACK)
        draw_grid(win, grid)
        draw_current(win, current)

        win.blit(font.render(f"점수: {score.score}", True, WHITE), (GRID_W*BLOCK + 30, HEIGHT - 80))
        win.blit(font.render(f"레벨: {score.level}", True, WHITE), (GRID_W*BLOCK + 30, HEIGHT - 50))
        draw_next(win, next_piece, font)

        pygame.display.update()

    if over: over.play()
    pygame.time.delay(1500)
    pygame.quit()


# ======================
# 실행
# ======================
if __name__ == "__main__":
    main()
