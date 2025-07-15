import pygame
import csv # 譜面ファイルの読み込み用
import time # ゲーム開始時間の記録用
import sys

# 初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Rhythm Game")

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# フォント
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 36)

# ノーツ/レーン設定
LANE_COUNT = 4
LANE_WIDTH = 100
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)
NOTE_SPEED = 5
NOTE_HEIGHT = 20
JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30

# キー定義
lane_keys = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}
key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys.items()}
lane_idx_to_key_char = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# 譜面読み込み
BEATMAP_FILE = 'beatmap.csv'
try:
    with open(BEATMAP_FILE, 'r') as f:
        reader = csv.reader(f)
        BEATMAP = [[int(row[0]), int(row[1])] for row in reader]
except FileNotFoundError:
    print("Error: beatmap.csv not found.")
    pygame.quit()
    sys.exit()

# -------- Scene 基底クラス --------
class Scene:
    """
    各画面での基底クラス定義
    操作に応じて実行
    状態の更新
    画面の更新
    """
    def handle_events(self, events): pass
    def update(self): pass
    def draw(self): pass

# -------- タイトル画面 --------
class TitleScene(Scene):
    """
    タイトル画面を表示
    spaceキーでPlayScene(プレイ中の画面)に移動
    """

    def __init__(self, game):
        self.game = game

    def handle_events(self, events):

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.game.change_scene(PlayScene(self.game))

    def draw(self):
        screen.fill(BLACK)
        text = font.render("Press SPACE to Start", True, WHITE)
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

# -------- リザルト画面 --------
class ResultScene(Scene):
    """
    リザルトの表示
    Ｒキーでタイトル画面に移動
    """
    def __init__(self, game):
        self.game = game

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.game.change_scene(TitleScene(self.game))

    def draw(self):
        if self.game.notes_count == 0:
            self.game.notes_count = 1  # ゼロ割り防止（0%表示）
        else:
            self.notes_count = self.game.notes_count
        screen.fill(BLACK)
        screen.blit(font.render("RESULT", True, WHITE), (300, 100))
        screen.blit(font.render(f"Score: {self.game.score}", True, WHITE), (300, 200))
        screen.blit(font.render(f"Max Combo: {self.game.max_combo}", True, WHITE), (300, 250))
        screen.blit(font.render(f"Perfect: {self.game.perfect} , {self.game.perfect*100//self.game.notes_count}%", True, WHITE), (300, 300))
        screen.blit(font.render(f"Good FAST : {self.game.good_fast} , {self.game.good_fast*100//self.game.notes_count}%", True, WHITE), (300, 350))
        screen.blit(font.render(f"Good LATE : {self.game.good_late} , {self.game.good_late*100//self.game.notes_count}%", True, WHITE), (300, 400))
        screen.blit(font.render(f"Miss : {self.game.miss} , {self.game.miss*100//self.game.notes_count}%", True, WHITE), (300, 450))
        screen.blit(small_font.render("Press R to Restart", True, WHITE), (250, 500))

# -------- プレイ画面 --------
class PlayScene(Scene):
    """
    キーが押されたとき、ジャッジラインから±15px 以内でperfect、15px ～ 30px の範囲でgood、それ以上ズレるか、判定タイミングを過ぎるとmiss
    ノーツがすべて生成され、画面からノーツがなくなったら曲を止めリザルト画面へ移動
    """
    def __init__(self, game):
        self.game = game
        self.game.reset_score()  # ゲーム開始時にスコア関連を初期化
        self.notes = []
        self.beatmap_index = 0
        self.start_time = time.time()
        self.judgement_message = ""
        self.judgement_color = WHITE
        self.judgement_effect_timer = 0
        pygame.mixer.music.load('maou_short_14_shining_star.mp3')
        pygame.mixer.music.play()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in key_to_lane_idx:
                lane = key_to_lane_idx[event.key]
                for note in self.notes[:]:
                    if note['lane'] == lane and abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                        self.notes.remove(note)
                        self.game.score += 100
                        self.game.combo += 1
                        if  self.game.combo > self.game.max_combo:
                            self.game.max_combo = self.game.combo
                        if abs(note['rect'].centery - JUDGEMENT_LINE_Y) <= JUDGEMENT_WINDOW / 2:
                            self.judgement_message = "PERFECT!"
                            self.game.perfect += 1
                            self.game.notes_count += 1
                        elif abs(note['rect'].centery - JUDGEMENT_LINE_Y) > JUDGEMENT_WINDOW / 2:
                            if note['rect'].centery < JUDGEMENT_LINE_Y:
                                self.judgement_message = "GOOD FAST"
                                self.game.good_fast += 1
                                self.game.notes_count += 1
                            else :
                                self.judgement_message = "GOOD LATE"
                                self.game.good_late += 1
                                self.game.notes_count += 1
                        self.judgement_color = GREEN
                        self.judgement_effect_timer = 30
                        self.hit_found = True
                        break

    def update(self):
        current_time = (time.time() - self.start_time) * 1000
        while self.beatmap_index < len(BEATMAP) and current_time >= BEATMAP[self.beatmap_index][0]:
            lane = BEATMAP[self.beatmap_index][1]
            x = LANE_SPACING + lane * (LANE_WIDTH + LANE_SPACING)
            y = -NOTE_HEIGHT - (JUDGEMENT_LINE_Y + NOTE_HEIGHT)
            rect = pygame.Rect(x, y, LANE_WIDTH, NOTE_HEIGHT)
            self.notes.append({'rect': rect, 'lane': lane})
            self.beatmap_index += 1

        for note in self.notes[:]:
            note['rect'].y += NOTE_SPEED
            if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW:
                self.notes.remove(note)
                self.game.combo = 0
                self.game.miss += 1  # Miss数を加算
                self.game.notes_count += 1  # 総ノーツ数にもカウント
                self.judgement_message = "MISS"
                self.judgement_color = RED
                self.judgement_effect_timer = 30

        if self.beatmap_index >= len(BEATMAP) and not self.notes:
            pygame.mixer.music.stop()
            self.game.change_scene(ResultScene(self.game))
        
        
    def draw(self):
        screen.fill(BLACK)
        for i in range(LANE_COUNT):
            x = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
            pygame.draw.rect(screen, GRAY, (x, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)
            key_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
            screen.blit(key_text, (x + (LANE_WIDTH - key_text.get_width()) // 2, JUDGEMENT_LINE_Y + 40))
        pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

        for note in self.notes:
            color = lane_keys[list(lane_keys.keys())[note['lane']]]['color']
            pygame.draw.rect(screen, color, note['rect'])

        # 画面左上にスコアとコンボ数を表示
        screen.blit(font.render(f"Score: {self.game.score}", True, WHITE), (10, 10))
        screen.blit(font.render(f"Combo: {self.game.combo}", True, WHITE), (10, 60))

        # 判定エフェクトタイマーがあるときエフェクトを表示
        if self.judgement_effect_timer > 0:
            self.judgement_display = font.render(self.judgement_message, True, self.judgement_color)
            self.judgement_rect = self.judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
            screen.blit(self.judgement_display, self.judgement_rect)
            self.judgement_effect_timer -= 1

# -------- ゲーム本体 --------
class Game:
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfect = 0
        self.good_fast = 0
        self.good_late = 0
        self.miss = 0
        self.notes_count = self.perfect+self.good_fast+self.good_late+self.miss
        self.current_scene = TitleScene(self)
    
    def reset_score(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfect = 0
        self.good_fast = 0
        self.good_late = 0
        self.miss = 0
        self.notes_count = 0

    def change_scene(self, new_scene):
        self.current_scene = new_scene

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

            self.current_scene.handle_events(events)
            self.current_scene.update()
            self.current_scene.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

# -------- 起動 --------
if __name__ == "__main__":
    Game().run()