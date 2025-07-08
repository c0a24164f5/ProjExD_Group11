import pygame
import csv
import time
import sys
import os

# Pygameの初期化
pygame.init()
pygame.mixer.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Rhythm Game (最終版)")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255) # 判定強化表示用

# フォントの設定
font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 36)

# ゲーム設定
LANE_COUNT = 4
LANE_WIDTH = 100
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)

NOTE_SPEED = 5
NOTE_HEIGHT = 20

JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30 # 通常のPERFECT/GOOD判定の許容範囲

FALL_TIME_MS = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED * (1000 / 60)

# 各レーンに対応するキーと色、表示用の文字
lane_keys = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}
key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys.items()}
lane_idx_to_key_char = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# 譜面ファイルと音楽ファイルのパス設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = BASE_DIR

BEATMAP_FILE_NAME = 'beatmap.csv' # 必要であれば 'ex5_beatmap.csv' などに書き換える
MUSIC_FILE_NAME = 'maou_short_14_shining_star.mp3' # 必要であれば 'ex5.mp3' などに書き換える

BEATMAP_FULL_PATH = os.path.join(ASSET_DIR, BEATMAP_FILE_NAME)
MUSIC_FULL_PATH = os.path.join(ASSET_DIR, MUSIC_FILE_NAME)

BEATMAP = []
try:
    if not os.path.exists(BEATMAP_FULL_PATH):
        raise FileNotFoundError(f"'{BEATMAP_FULL_PATH}' が見つかりません。")

    with open(BEATMAP_FULL_PATH, 'r') as f:
        reader = csv.reader(f)
        BEATMAP = [[int(row[0]), int(row[1])] for row in reader]
except FileNotFoundError as e:
    print(f"エラー: 譜面ファイルが見つかりません。{e}")
    print("ゲームスクリプトと同じディレクトリに 'beatmap.csv' があるか確認してください。")
    print("または 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
    print(f"期待される譜面パス: {BEATMAP_FULL_PATH}")
    pygame.quit()
    sys.exit()

beatmap_index = 0
notes = []

score = 0
combo = 0
max_combo = 0

MAX_HP = 500
current_hp = MAX_HP
HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 20
HP_LOSS_PER_MISS = 10 # 通常のミスで減るHP量

# 判定強化設定
JUDGEMENT_BOOST_COMBO_THRESHOLD = 10 # 判定強化が発動するコンボの倍数
JUDGEMENT_BOOST_DURATION_FRAMES = 60 * 5 # 判定強化の持続時間 (3秒 = 60FPS * 3秒)
judgement_boost_active = False # 判定強化が現在有効か
judgement_boost_timer = 0 # 判定強化の残り時間（フレーム数）

judgement_effect_timer = 0
judgement_message = ""
judgement_color = WHITE

# 音楽のロード
try:
    if not os.path.exists(MUSIC_FULL_PATH):
        raise FileNotFoundError(f"'{MUSIC_FULL_PATH}' が見つかりません。")
        
    pygame.mixer.music.load(MUSIC_FULL_PATH)
except pygame.error as e:
    print(f"警告: 音楽ファイルをロードできませんでした。{e}")
    print(f"期待される音楽パス: {MUSIC_FULL_PATH}")
except FileNotFoundError as e:
    print(f"警告: 音楽ファイルが見つかりません。{e}")
    print(f"期待される音楽パス: {MUSIC_FULL_PATH}")

running = True
clock = pygame.time.Clock()
game_started = False
game_start_time = 0
game_over = False

# メインのゲームループ
while running:
    # ゲーム開始条件: 音楽がロードされており、まだゲームが開始されていない場合、かつゲームオーバーでない
    if not game_started and pygame.mixer.get_init() and BEATMAP and not game_over:
        if not pygame.mixer.music.get_busy(): # 音楽が再生中でない場合のみ開始
            pygame.mixer.music.play()
            game_start_time = time.time()
            game_started = True

    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # ゲームオーバー時のリスタート処理 (Rキー)
        if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            # ゲーム状態をリセット
            score = 0
            combo = 0
            max_combo = 0
            current_hp = MAX_HP
            notes.clear()
            beatmap_index = 0
            game_started = False
            game_start_time = 0
            game_over = False
            judgement_effect_timer = 0
            judgement_message = ""
            judgement_color = WHITE
            judgement_boost_active = False # リスタート時にリセット
            judgement_boost_timer = 0 # リスタート時にリセット
            
            # 音楽を停止してリセット
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.load(MUSIC_FULL_PATH)
                except (pygame.error, FileNotFoundError) as e:
                    print(f"警告: 音楽ファイルを再ロードできませんでした。{e}")
        # キー入力処理
        if event.type == pygame.KEYDOWN:
            # ゲームが開始していて、かつゲームオーバーでない場合のみキー入力を処理
            if game_started and not game_over and event.key in lane_keys:
                pressed_lane_idx = key_to_lane_idx[event.key]
                hit_found = False
                for note in reversed(notes): # 最も手前のノーツから判定
                    if note['lane'] == pressed_lane_idx and not note['hit']:
                        # ノーツが判定範囲（GOOD以上）に入っているかチェック
                        if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                            score += 100
                            combo += 1
                            max_combo = max(max_combo, combo)
                            notes.remove(note)
                            
                            # 判定強化が有効な場合、またはPERFECTの範囲内の場合、PERFECTにする
                            if judgement_boost_active or abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW / 2:
                                judgement_message = "PERFECT!"
                            else:
                                judgement_message = "GOOD!" # 判定強化がなければGOODのまま
                            
                            judgement_color = GREEN
                            judgement_effect_timer = 30
                            hit_found = True
                            
                            # コンボが3の倍数でHP回復
                            if combo > 0 and combo % 3 == 0:
                                hp_recovered = min(10, MAX_HP - current_hp)
                                current_hp += hp_recovered
                                if hp_recovered > 0:
                                    judgement_message += f" (+{hp_recovered} HP!)"
                            
                            # 判定強化の発動チェック
                            if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                                judgement_boost_active = True
                                judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                                judgement_message += " (BOOST!)" # 判定メッセージにBOOST発動を追加
                            
                            break # ヒットが見つかったらこのレーンでの処理は終了
                
                if not hit_found: # キーが押されたが、有効なノーツに当たらなかった場合 (MISS)
                    combo = 0 # コンボリセット
                    judgement_message = "MISS!"
                    judgement_color = RED
                    judgement_effect_timer = 30
                    current_hp -= HP_LOSS_PER_MISS # HP減少
                    if current_hp <= 0:
                        current_hp = 0
                        game_over = True
                        if pygame.mixer.get_init():
                            pygame.mixer.music.stop()

    # ゲームの状態更新 (ゲームオーバーでない場合のみ)
    if not game_over:
        # 譜面からノーツを生成 (ゲーム開始済みの場合のみ)
        if game_started:
            current_game_time_ms = (time.time() - game_start_time) * 1000

            # BEATMAP[beatmap_index][0] はノーツが判定ラインに到達すべき時間
            # FALL_TIME_MS はノーツが画面上端から判定ラインまで落ちるのにかかる時間
            # この条件が、ノーツが生成されるべきタイミング。
            while beatmap_index < len(BEATMAP) and current_game_time_ms >= BEATMAP[beatmap_index][0] - FALL_TIME_MS:
                note_data = BEATMAP[beatmap_index]
                target_lane = note_data[1]

                # 新しいノーツを作成 (画面上端に隠れる位置からスタート)
                lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)
                new_note_rect = pygame.Rect(lane_x_start, -NOTE_HEIGHT, LANE_WIDTH, NOTE_HEIGHT)
                
                notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
                
                beatmap_index += 1 # 次のノーツへ

        # ノーツの移動と判定外れチェック
        for note in notes[:]: # リストをコピーして要素削除時にエラーを防ぐ
            note['rect'].y += NOTE_SPEED
            # ノーツが判定ラインを完全に通り過ぎてしまった場合 (TOO LATE! / Missed Note)
            if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW and not note['hit']:
                notes.remove(note)
                note['hit'] = True # 既に処理済みとしてマーク

                if judgement_boost_active:
                    # 判定強化中はTOO LATEもPERFECTに昇格
                    score += 100 # スコア加算
                    combo += 1 # コンボ継続
                    max_combo = max(max_combo, combo)
                    judgement_message = "PERFECT! (Boosted)" # BOOSTによるPERFECTであることを示す
                    judgement_color = GREEN
                    judgement_effect_timer = 30
                    
                    # HP回復のチェックもここで行う (TOO LATEがPERFECTになった場合)
                    if combo > 0 and combo % 3 == 0:
                        hp_recovered = min(10, MAX_HP - current_hp)
                        current_hp += hp_recovered
                        if hp_recovered > 0:
                            judgement_message += f" (+{hp_recovered} HP!)"

                    # 判定強化の発動チェック (BOOST中のBOOST発動は意味ないが、タイマーリセットのため)
                    if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                        judgement_boost_active = True
                        judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                        judgement_message += " (BOOST!)" # BOOST発動メッセージも追加
                else:
                    # 判定強化中でない場合は通常のTOO LATE (コンボリセット & HP減少)
                    combo = 0 # コンボをリセット
                    judgement_message = "TOO LATE!" # 遅すぎた場合もMISS扱い
                    judgement_color = RED
                    judgement_effect_timer = 30
                    current_hp -= HP_LOSS_PER_MISS # HP減少
                    if current_hp <= 0: # HPがゼロになったらゲームオーバー
                        current_hp = 0
                        game_over = True
                        if pygame.mixer.get_init():
                            pygame.mixer.music.stop()

    # 判定強化タイマーの更新
    if judgement_boost_active:
        judgement_boost_timer -= 1
        if judgement_boost_timer <= 0:
            judgement_boost_active = False
            judgement_boost_timer = 0

    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

    # 描画
    screen.fill(BLACK)
    for i in range(LANE_COUNT):
        lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
        pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2) # レーンの枠
        # レーンの下に対応するキーを表示
        key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
        screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
    pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0) # 判定ラインの背景
    pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3) # 判定ライン

    # ノーツの描画
    for note in notes:
        # レーンの色でノーツを描画
        pygame.draw.rect(screen, lane_keys[list(lane_keys.keys())[note['lane']]]['color'], note['rect'])

    # スコア、コンボ、最高コンボの表示
    score_text = font.render(f"Score: {score}", True, WHITE)
    combo_text = font.render(f"Combo: {combo}", True, WHITE)
    max_combo_text = small_font.render(f"Max Combo: {max_combo}", True, WHITE)
    
    screen.blit(score_text, (10, 10))
    screen.blit(combo_text, (10, 50))
    screen.blit(max_combo_text, (SCREEN_WIDTH - max_combo_text.get_width() - 10, 10))

    # HPバーの描画
    hp_bar_x = (SCREEN_WIDTH - HP_BAR_WIDTH) // 2
    hp_bar_y = 10
    hp_bar_fill_width = int(HP_BAR_WIDTH * (current_hp / MAX_HP))
    
    pygame.draw.rect(screen, GRAY, (hp_bar_x, hp_bar_y, HP_BAR_WIDTH, HP_BAR_HEIGHT), 2) # HPバーの枠
    hp_fill_color = GREEN if current_hp > MAX_HP / 3 else RED # HPに応じて色を変える
    pygame.draw.rect(screen, hp_fill_color, (hp_bar_x, hp_bar_y, hp_bar_fill_width, HP_BAR_HEIGHT)) # HPの量
    
    hp_text = small_font.render(f"HP: {current_hp}/{MAX_HP}", True, WHITE)
    screen.blit(hp_text, (hp_bar_x + HP_BAR_WIDTH + 10, hp_bar_y)) # HPの数値

    # 判定強化の残り時間を表示
    if judgement_boost_active:
        boost_text = small_font.render(f"Boost: {judgement_boost_timer // 60 + 1}s", True, CYAN) # シアン色で表示
        screen.blit(boost_text, (SCREEN_WIDTH - boost_text.get_width() - 10, 50))

    # 判定メッセージの表示 (PERFECT!, GOOD!, MISS!, TOO LATE!)
    if judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)
    
    # ゲームオーバー時の表示
    if game_over:
        game_over_text = font.render("GAME OVER!", True, RED)
        final_score_text = small_font.render(f"Final Score: {score}", True, WHITE)
        max_combo_final_text = small_font.render(f"Max Combo: {max_combo}", True, WHITE)
        
        go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        fs_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        mc_rect = max_combo_final_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

        screen.blit(game_over_text, go_rect)
        screen.blit(final_score_text, fs_rect)
        screen.blit(max_combo_final_text, mc_rect)
        
        restart_text = small_font.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(restart_text, restart_rect)

    # 画面の更新
    pygame.display.flip()
    # フレームレートを60FPSに固定
    clock.tick(60)

pygame.quit()