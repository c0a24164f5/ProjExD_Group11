"""
プロジェクト演習D 音楽ゲーム (osモジュール削除版)

このプログラムは、CSVファイルから譜面を読み込み、
音楽に合わせてノーツが落下するリズムゲームを実行します。
"""
import pygame
import csv
import time
import sys
# import os # <- 削除
from typing import List, Dict, Tuple, Optional

# --- 定数設定 (Constants) ---
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
FPS: int = 60

# 色定義
WHITE: Tuple[int, int, int] = (255, 255, 255)
BLACK: Tuple[int, int, int] = (0, 0, 0)
RED: Tuple[int, int, int] = (255, 0, 0)
GREEN: Tuple[int, int, int] = (0, 255, 0)
GRAY: Tuple[int, int, int] = (100, 100, 100)

# レーン設定
LANE_COUNT: int = 4
LANE_WIDTH: int = 100
LANE_SPACING: int = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)

# ノーツ設定
NOTE_SPEED: float = 5.0
NOTE_HEIGHT: int = 20

# 判定設定
JUDGEMENT_LINE_Y: int = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW_PERFECT: int = 15
JUDGEMENT_WINDOW_GOOD: int = 30

# キー設定
LANE_KEYS: Dict[int, Dict] = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}
KEY_TO_LANE: Dict[int, int] = {key: data["lane_idx"] for key, data in LANE_KEYS.items()}
LANE_TO_CHAR: Dict[int, str] = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# --- ▼▼▼ ここを修正 ▼▼▼ ---
# ファイルパス設定 (ファイル名を直接指定)
BEATMAP_FILE: str = 'beatmap.csv'
MUSIC_FILE: str = 'maou_short_14_shining_star.mp3'
# --- ▲▲▲ ここまで修正 ▲▲▲ ---


class Note:
    """ノーツの情報を管理するクラス。"""
    def __init__(self, lane_idx: int, hit_time_ms: int):
        """Noteオブジェクトを初期化します。"""
        self.lane_idx: int = lane_idx
        self.hit_time_ms: int = hit_time_ms
        self.is_hit: bool = False
        x_pos: int = LANE_SPACING + self.lane_idx * (LANE_WIDTH + LANE_SPACING)
        self.rect: pygame.Rect = pygame.Rect(x_pos, 0, LANE_WIDTH, NOTE_HEIGHT)

    def update(self) -> None:
        """毎フレーム呼び出され、ノーツの位置を更新します。"""
        self.rect.y += NOTE_SPEED

    def draw(self, surface: pygame.Surface) -> None:
        """ノーツを指定されたサーフェスに描画します。"""
        key = list(LANE_KEYS.keys())[self.lane_idx]
        color = LANE_KEYS[key]["color"]
        pygame.draw.rect(surface, color, self.rect)


class Game:
    """ゲーム全体の進行を管理するクラス。"""
    def __init__(self):
        """Gameオブジェクトを初期化し、必要なリソースをセットアップします。"""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("My Rhythm Game")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        self.font: pygame.font.Font = pygame.font.Font(None, 48)
        self.small_font: pygame.font.Font = pygame.font.Font(None, 36)
        self.finish_font: pygame.font.Font = pygame.font.Font(None, 100)

        self.beatmap: List[List[int]] = self._load_beatmap()
        self._load_music()

        self.running: bool = True
        self.game_started: bool = False
        self.game_start_time: float = 0.0
        self.beatmap_index: int = 0
        self.notes: List[Note] = []
        self.score: int = 0
        self.combo: int = 0
        self.max_combo: int = 0
        self.judgement_text: str = ""
        self.judgement_color: Tuple[int, int, int] = WHITE
        self.judgement_timer: int = 0

    def _load_beatmap(self) -> List[List[int]]:
        """beatmap.csvファイルを読み込みます。"""
        try:
            with open(BEATMAP_FILE, 'r') as f:
                reader = csv.reader(f)
                return [[int(row[0]), int(row[1])] for row in reader]
        except FileNotFoundError:
            print(f"エラー: '{BEATMAP_FILE}' が見つかりません。")
            print("先に 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
            pygame.quit()
            sys.exit()

    def _load_music(self) -> None:
        """音楽ファイルを読み込みます。"""
        try:
            pygame.mixer.music.load(MUSIC_FILE)
        except pygame.error:
            print(f"警告: '{MUSIC_FILE}' をロードできませんでした。")

    def run(self) -> None:
        """メインゲームループを実行します。"""
        while self.running:
            self._handle_events()
            self._update_state()
            self._draw_elements()
            self.clock.tick(FPS)
        pygame.quit()

    def _handle_events(self) -> None:
        """イベントを処理します。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key in KEY_TO_LANE:
                    self._judge_hit(KEY_TO_LANE[event.key])

    def _update_state(self) -> None:
        """ゲームの状態を更新します。"""
        if not self.beatmap: return

        if not self.game_started:
            pygame.mixer.music.play()
            self.game_start_time = time.time()
            self.game_started = True

        current_game_time_ms: float = (time.time() - self.game_start_time) * 1000

        while self.beatmap_index < len(self.beatmap):
            hit_time, lane = self.beatmap[self.beatmap_index]
            if current_game_time_ms >= hit_time:
                self.notes.append(Note(lane_idx=lane, hit_time_ms=hit_time))
                self.beatmap_index += 1
            else:
                break

        for note in self.notes[:]:
            note.update()
            if note.rect.top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW_GOOD:
                self.notes.remove(note)
                self._set_judgement("TOO LATE!", RED)
                self.combo = 0

        if self.judgement_timer > 0:
            self.judgement_timer -= 1

        if self.game_started and not pygame.mixer.music.get_busy() and not self.notes:
            self.judgement_text = "finish"
            self._draw_elements()
            pygame.time.wait(2000)
            self.running = False

    def _judge_hit(self, pressed_lane_idx: int) -> None:
        """キー入力に対する判定を行います。"""
        note_to_judge: Optional[Note] = None
        for note in self.notes:
            if note.lane_idx == pressed_lane_idx:
                if abs(note.rect.centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW_GOOD * 2:
                    note_to_judge = note
                    break
        
        if note_to_judge:
            dist: int = abs(note_to_judge.rect.centery - JUDGEMENT_LINE_Y)
            if dist < JUDGEMENT_WINDOW_GOOD:
                self.notes.remove(note_to_judge)
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                if dist < JUDGEMENT_WINDOW_PERFECT:
                    self.score += 200
                    self._set_judgement("PERFECT!", GREEN)
                else:
                    self.score += 100
                    self._set_judgement("GOOD!", GREEN)
            else:
                self.combo = 0
                self._set_judgement("MISS!", RED)

    def _set_judgement(self, text: str, color: Tuple[int, int, int]) -> None:
        """判定結果のテキストを設定します。"""
        self.judgement_text = text
        self.judgement_color = color
        self.judgement_timer = 30

    def _draw_elements(self) -> None:
        """画面の要素を描画します。"""
        self.screen.fill(BLACK)
        self._draw_lanes()
        for note in self.notes:
            note.draw(self.screen)
        self._draw_hud()
        if self.judgement_timer > 0:
            self._draw_judgement()
        pygame.display.flip()

    def _draw_lanes(self) -> None:
        """レーンと判定ラインを描画します。"""
        for i in range(LANE_COUNT):
            x = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
            pygame.draw.rect(self.screen, GRAY, (x, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)
            key_char = self.small_font.render(LANE_TO_CHAR[i], True, WHITE)
            self.screen.blit(key_char, (x + (LANE_WIDTH - key_char.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
        pygame.draw.line(self.screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

    def _draw_hud(self) -> None:
        """スコアやコンボを描画します。"""
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        combo_surf = self.font.render(f"Combo: {self.combo}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(combo_surf, (10, 50))

    def _draw_judgement(self) -> None:
        """判定テキストを描画します。"""
        font = self.finish_font if self.judgement_text == "finish" else self.font
        judgement_surf = font.render(self.judgement_text, True, self.judgement_color)
        judgement_rect = judgement_surf.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        self.screen.blit(judgement_surf, judgement_rect)


if __name__ == '__main__':
    game = Game()
    game.run()