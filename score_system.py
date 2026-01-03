# score_system.py
print("### score_system.py LOADED ###")

class TetrisScore:
    LINE_CLEAR_SCORES = {
        1: 100,
        2: 300,
        3: 500,
        4: 800
    }

    def __init__(self):
        self.score = 0
        self.level = 1
        self.total_lines = 0
        self.combo = -1
        self.back_to_back = False

    def _update_level(self):
        # Level up a bit faster to keep the pace exciting.
        self.level = (self.total_lines // 8) + 1

    def clear_lines(self, lines, is_all_clear=False):
        """
        lines: 한 번에 지운 줄 수 (0~4)
        반환값: 이번에 추가된 점수
        """
        if lines == 0:
            self.combo = -1
            self.back_to_back = False
            return 0

        self.combo += 1

        base = self.LINE_CLEAR_SCORES.get(lines, 0)
        gained = base * self.level

        # Back-to-back Tetris (4 lines) bonus.
        b2b_bonus = 0
        if lines == 4 and self.back_to_back:
            b2b_bonus = int(gained * 0.5)
        self.back_to_back = (lines == 4)

        combo_bonus = 0
        if self.combo > 0:
            combo_bonus = 50 * self.combo * self.level

        all_clear_bonus = 0
        if is_all_clear:
            all_clear_bonus = 1000 * self.level

        gained += combo_bonus + b2b_bonus + all_clear_bonus

        self.score += gained
        self.total_lines += lines
        self._update_level()

        return gained

    def soft_drop(self, cells):
        self.score += cells

    def hard_drop(self, cells):
        self.score += cells * 2
