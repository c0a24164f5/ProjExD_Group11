import pygame
import csv
import time
import sys

# Pygameの初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Rhythm Game")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)

# フォントの設定
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 36)
finish_font = pygame.font.Font(None, 100)

# ゲーム設定
LANE_COUNT = 4
LANE_WIDTH = 100
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)
NOTE_SPEED = 5
NOTE_HEIGHT = 20
JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30

# 各レーンに対応するキーと色、表示用の文字
lane_keys = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}
key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys.items()}
lane_idx_to_key_char = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# 譜面ファイルの読み込み
BEATMAP_FILE = 'beatmap.csv'
BEATMAP = []
try:
    with open(BEATMAP_FILE, 'r') as f:
        reader = csv.reader(f)
        BEATMAP = [[int(row[0]), int(row[1])] for row in reader]
except FileNotFoundError:
    print(f"エラー: '{BEATMAP_FILE}' が見つかりません。")
    print("先に 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
    pygame.quit()
    sys.exit()

beatmap_index = 0
notes = []
score = 0
combo = 0
max_combo = 0
judgement_effect_timer = 0
judgement_message = ""
judgement_color = WHITE

# 音楽のロードと再生
try:
    pygame.mixer.music.load('maou_short_14_shining_star.mp3')
except pygame.error:
    print("警告: 音楽ファイルをロードできませんでした。")

# ゲームループのフラグとクロック
running = True
clock = pygame.time.Clock()
game_started = False
game_start_time = 0

# -------- メインのゲームループ --------
while running:
    if not game_started and BEATMAP:
        pygame.mixer.music.play()
        game_start_time = time.time()
        game_started = True

    # --- 1. イベント処理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- ▼▼▼ ここから判定ロジックを修正 ▼▼▼ ---
        if event.type == pygame.KEYDOWN:
            if event.key in lane_keys:
                pressed_lane_idx = key_to_lane_idx[event.key]
                
                # 押されたレーンに、判定ライン付近のノーツがあるかを探す
                note_to_judge = None
                for note in notes:
                    if note['lane'] == pressed_lane_idx:
                        # 判定ライン付近にある一番近いノーツを候補とする
                        if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW * 2: #少し広めに探す
                           note_to_judge = note
                           break # 候補が見つかったら探すのをやめる
                
                if note_to_judge:
                    # 叩くべきノーツが近くにあった場合の処理
                    hit_found = False
                    # タイミングが合っているかチェック
                    if abs(note_to_judge['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                        # ヒット成功！
                        score += 100
                        combo += 1
                        max_combo = max(max_combo, combo)
                        notes.remove(note_to_judge) # ヒットしたノーツを削除
                        
                        # PERFECT / GOOD の判定
                        if abs(note_to_judge['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW / 2:
                            judgement_message = "PERFECT!"
                        else:
                            judgement_message = "GOOD!"
                        judgement_color = GREEN
                        judgement_effect_timer = 30
                        hit_found = True
                    
                    if not hit_found:
                        # ノーツはあったが、タイミングが早すぎる/遅すぎる場合 (MISS)
                        combo = 0
                        judgement_message = "MISS!"
                        judgement_color = RED
                        judgement_effect_timer = 30
                # else:
                #   note_to_judge が None の場合、つまり近くに叩くべきノーツが何もない時
                #   何もしないので、空打ちしてもMISSにならない

    # --- ▲▲▲ ここまで判定ロジックを修正 ▲▲▲ ---

    # --- 2. ゲームの状態更新 ---
    if game_started:
        current_game_time_ms = (time.time() - game_start_time) * 1000
        while beatmap_index < len(BEATMAP):
            note_data = BEATMAP[beatmap_index]
            target_time_ms = note_data[0]
            if current_game_time_ms >= target_time_ms:
                target_lane = note_data[1]
                lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)
                new_note_rect = pygame.Rect(lane_x_start, 0, LANE_WIDTH, NOTE_HEIGHT)
                notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False, 'spawn_time_ms': target_time_ms})
                beatmap_index += 1
            else:
                break

    for note in notes[:]:
        note['rect'].y += NOTE_SPEED
        if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW and not note['hit']:
            notes.remove(note)
            combo = 0
            judgement_message = "TOO LATE!"
            judgement_color = RED
            judgement_effect_timer = 30

    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

    # --- 3. 描画 ---
    screen.fill(BLACK)
    for i in range(LANE_COUNT):
        lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
        pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)
        key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
        screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
    pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)
    pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

    for note in notes:
        pygame.draw.rect(screen, lane_keys[list(lane_keys.keys())[note['lane']]]['color'], note['rect'])

    score_text = font.render(f"Score: {score}", True, WHITE)
    combo_text = font.render(f"Combo: {combo}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(combo_text, (10, 50))

    if judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)

    if game_started and not pygame.mixer.music.get_busy():
        finish_text_surface = finish_font.render("finish", True, WHITE)
        finish_text_rect = finish_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(finish_text_surface, finish_text_rect)
        pygame.display.flip()
        pygame.time.wait(2000)
        running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()