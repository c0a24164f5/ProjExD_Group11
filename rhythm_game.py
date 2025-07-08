import pygame
import csv
import time
import sys
import os

# Pygameの初期化
pygame.init()
pygame.mixer.init()

# --- 定数と初期設定 ---
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
YELLOW = (255, 255, 0) # フィーバー時のコンボ色

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

# ノーツが画面上端から判定ラインまで落ちるのにかかる時間 (ミリ秒)
# 60FPSを想定して計算
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
ASSET_DIR = BASE_DIR # この例ではスクリプトと同じディレクトリをアセットディレクトリとする

BEATMAP_FILE_NAME = 'beatmap.csv' # 必要であれば 'ex5_beatmap.csv' などに書き換える
MUSIC_FILE_NAME = 'maou_short_14_shining_star.mp3' # 必要であれば 'ex5.mp3' などに書き換える

BEATMAP_FULL_PATH = os.path.join(ASSET_DIR, BEATMAP_FILE_NAME)
MUSIC_FULL_PATH = os.path.join(ASSET_DIR, MUSIC_FILE_NAME)

# --- HPバーのサイズ定義 ---
HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 20

# --- グローバル変数 (ゲームの状態を保持) ---
# これらの変数は複数の関数でアクセス・更新されるため、グローバルとして定義
score = 0
combo = 0
max_combo = 0

MAX_HP = 500
current_hp = MAX_HP
HP_LOSS_PER_MISS = 10 # 通常のミスで減るHP量

# 判定強化設定
JUDGEMENT_BOOST_COMBO_THRESHOLD = 10 # 判定強化が発動するコンボの倍数
JUDGEMENT_BOOST_DURATION_FRAMES = 60 * 5 # 判定強化の持続時間 (5秒 = 60FPS * 5秒)
judgement_boost_active = False # 判定強化が現在有効か
judgement_boost_timer = 0 # 判定強化の残り時間（フレーム数）

# フィーバー演出設定
FEVER_COMBO_THRESHOLD = 50 # フィーバーが発動するコンボ数
fever_active = False # フィーバーが現在有効か (コンボ数で継続)
fever_flash_color_timer = 0 # 色を点滅させるためのタイマー
FEVER_FLASH_INTERVAL = 10 # 色が点滅する間隔 (フレーム数)

judgement_effect_timer = 0
judgement_message = ""
judgement_color = WHITE

beatmap_index = 0
notes = [] # 現在画面に表示されているノーツのリスト

game_started = False
game_start_time = 0
game_over = False

# --- ファイル読み込み処理 (関数化) ---
def load_beatmap(path: str) -> list[list[int]]:
    """
    譜面ファイルを読み込み、ノーツデータ（時間、レーン）のリストを返します。
    ファイルが見つからない場合はエラーメッセージを表示し、ゲームを終了します。
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' が見つかりません。")

        with open(path, 'r') as f:
            reader = csv.reader(f)
            # 各行を整数に変換してリストに追加
            beatmap_data = [[int(row[0]), int(row[1])] for row in reader]
        return beatmap_data
    except FileNotFoundError as e:
        print(f"エラー: 譜面ファイルが見つかりません。{e}")
        print("ゲームスクリプトと同じディレクトリに 'beatmap.csv' があるか確認してください。")
        print("または 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
        print(f"期待される譜面パス: {path}")
        pygame.quit()
        sys.exit()

def load_music(path: str) -> None:
    """
    音楽ファイルを読み込みます。ファイルが見つからない場合やロードに失敗した場合は警告を表示します。
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' が見つかりません。")
        pygame.mixer.music.load(path)
    except pygame.error as e:
        print(f"警告: 音楽ファイルをロードできませんでした。{e}")
        print(f"期待される音楽パス: {path}")
    except FileNotFoundError as e:
        print(f"警告: 音楽ファイルが見つかりません。{e}")
        print(f"期待される音楽パス: {path}")

# 譜面と音楽のロードを実行
BEATMAP = load_beatmap(BEATMAP_FULL_PATH)
load_music(MUSIC_FULL_PATH)

# --- ゲームの状態をリセットする関数 (リスタート用) ---
def reset_game_state() -> None:
    """ゲームの全状態を初期値にリセットします。"""
    global score, combo, max_combo, current_hp, notes, beatmap_index
    global game_started, game_start_time, game_over
    global judgement_effect_timer, judgement_message, judgement_color
    global judgement_boost_active, judgement_boost_timer
    global fever_active, fever_flash_color_timer

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
    judgement_boost_active = False
    judgement_boost_timer = 0
    fever_active = False
    fever_flash_color_timer = 0

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(MUSIC_FULL_PATH)
        except (pygame.error, FileNotFoundError) as e:
            print(f"警告: 音楽ファイルを再ロードできませんでした。{e}")

# --- イベント処理の関数群 ---
def handle_quit_event(event: pygame.event.Event) -> bool:
    """QUITイベントを処理します。ゲームループを終了するかどうかを返します。"""
    if event.type == pygame.QUIT:
        return False # runningをFalseにする
    return True # runningをTrueのままにする

def handle_restart_event(event: pygame.event.Event, is_game_over: bool) -> None:
    """
    ゲームオーバー時にRキーが押された際のリスタート処理を行います。
    is_game_overがTrueでRキーが押された場合のみゲーム状態をリセットします。
    """
    if is_game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
        reset_game_state()

def process_key_press(event: pygame.event.Event) -> None:
    """
    キーが押された際のノーツ判定処理を行います。
    score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgement_boost_active, judgement_boost_timer,
    fever_active, fever_flash_color_timer, notes グローバル変数を更新します。
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes

    # ゲームが開始していて、かつゲームオーバーでない場合のみキー入力を処理
    if game_started and not game_over and event.key in lane_keys:
        pressed_lane_idx = key_to_lane_idx[event.key]
        hit_found = False
        # 最も手前のノーツから判定
        for note in reversed(notes):
            if note['lane'] == pressed_lane_idx and not note['hit']:
                # ノーツが判定範囲（GOOD以上）に入っているかチェック
                if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                    score += 100
                    combo += 1
                    max_combo = max(max_combo, combo)
                    notes.remove(note) # 判定済みのノーツを削除
                    
                    # 判定強化が有効な場合、または通常のPERFECT判定範囲内の場合、PERFECTにする
                    # 通常PERFECTの範囲は JUDGEMENT_WINDOW / 2
                    if judgement_boost_active or abs(note['rect'].centery - JUDGEMENT_LINE_Y) < (JUDGEMENT_WINDOW / 2):
                        judgement_message = "PERFECT!"
                    else:
                        judgement_message = "GOOD!"
                    
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
                    
                    # フィーバーの発動チェック (コンボが閾値以上になったら有効化)
                    if combo >= FEVER_COMBO_THRESHOLD:
                        if not fever_active: # 初めてフィーバーに入った時だけタイマーをリセット
                            fever_flash_color_timer = FEVER_FLASH_INTERVAL
                        fever_active = True
                    
                    break # ヒットが見つかったらこのレーンでの処理は終了
        
        if not hit_found: # キーが押されたが、有効なノーツに当たらなかった場合 (MISS)
            combo = 0 # コンボリセット
            judgement_message = "MISS!"
            judgement_color = RED
            judgement_effect_timer = 30
            current_hp -= HP_LOSS_PER_MISS # HP減少
            check_game_over() # HPチェックとゲームオーバー判定を呼び出す
            
            # コンボがリセットされたらフィーバーも解除
            fever_active = False
            fever_flash_color_timer = 0


# --- ゲーム状態更新の関数群 ---
def check_game_start() -> None:
    """ゲーム開始条件をチェックし、ゲームを開始します。音楽の再生も行います。"""
    global game_started, game_start_time
    # 音楽がロードされており、まだゲームが開始されていない場合、かつゲームオーバーでない
    if not game_started and pygame.mixer.get_init() and BEATMAP and not game_over:
        if not pygame.mixer.music.get_busy(): # 音楽が再生中でない場合のみ開始
            pygame.mixer.music.play()
            game_start_time = time.time()
            game_started = True

def generate_notes() -> None:
    """譜面データに基づいてノーツを生成し、notesリストに追加します。"""
    global beatmap_index, notes
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

def update_notes_position() -> None:
    """
    画面上のノーツの位置を更新し、判定ラインを完全に過ぎてしまったノーツを処理します。
    (TOO LATE! / Missed Note の判定と処理を含みます)
    score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgement_boost_active, judgement_boost_timer,
    fever_active, fever_flash_color_timer グローバル変数を更新します。
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes

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
                check_game_over() # HPチェックとゲームオーバー判定を呼び出す
                
                # コンボがリセットされたらフィーバーも解除
                fever_active = False
                fever_flash_color_timer = 0
    
    # ノーツが消えた（叩き損ねた）ことでコンボがフィーバー閾値未満になったらフィーバー解除
    if combo < FEVER_COMBO_THRESHOLD and fever_active:
        fever_active = False
        fever_flash_color_timer = 0

def update_timers() -> None:
    """各種タイマー（判定エフェクト、判定強化、フィーバー点滅）を更新します。"""
    global judgement_effect_timer, judgement_boost_timer, judgement_boost_active
    global fever_flash_color_timer, fever_active

    # 判定強化タイマーの更新
    if judgement_boost_active:
        judgement_boost_timer -= 1
        if judgement_boost_timer <= 0:
            judgement_boost_active = False
            judgement_boost_timer = 0

    # フィーバー演出の点滅タイマーを更新
    if fever_active:
        fever_flash_color_timer -= 1
        if fever_flash_color_timer <= 0:
            fever_flash_color_timer = FEVER_FLASH_INTERVAL # 次の点滅タイミングを設定

    # 判定メッセージ表示タイマーの更新
    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

def check_game_over() -> None:
    """HPが0以下になった場合にゲームオーバー状態を設定し、音楽を停止します。"""
    global current_hp, game_over
    if current_hp <= 0:
        current_hp = 0
        game_over = True
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

# --- 描画処理の関数群 ---
def draw_background() -> None:
    """ゲームの背景（レーン枠、判定ライン、対応キー）を描画します。フィーバー中は背景色を点滅させます。"""
    # フィーバー中は背景を点滅させる
    if fever_active and (fever_flash_color_timer > FEVER_FLASH_INTERVAL / 2):
        screen.fill((50, 50, 0)) # 暗い黄色のような色で点滅
    else:
        screen.fill(BLACK) # 通常の背景色

    for i in range(LANE_COUNT):
        lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
        pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2) # レーンの枠
        # レーンの下に対応するキーを表示
        key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
        screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
    
    # 判定ラインの背景とライン自体を描画
    pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)
    pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

def draw_notes() -> None:
    """現在画面に表示されているノーツを描画します。"""
    for note in notes:
        # レーンの色でノーツを描画
        pygame.draw.rect(screen, lane_keys[list(lane_keys.keys())[note['lane']]]['color'], note['rect'])

def draw_info_panel() -> None:
    """スコア、コンボ、最高コンボ、HPバー、判定強化の残り時間を描画します。"""
    # スコア、コンボ、最高コンボの表示
    score_text = font.render(f"Score: {score}", True, WHITE)
    # フィーバー中はコンボ文字を黄色にする
    combo_color = YELLOW if fever_active else WHITE
    combo_text = font.render(f"Combo: {combo}", True, combo_color)
    max_combo_text = small_font.render(f"Max Combo: {max_combo}", True, WHITE)
    
    screen.blit(score_text, (10, 10))
    screen.blit(combo_text, (10, 50))
    # マックスコンボのY座標を調整してHPバーと重ならないようにする
    screen.blit(max_combo_text, (SCREEN_WIDTH - max_combo_text.get_width() - 10, 40)) # 調整後のY座標

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
        screen.blit(boost_text, (SCREEN_WIDTH - boost_text.get_width() - 10, 70)) # この位置も調整したよ

def draw_judgement_message() -> None:
    """判定メッセージ（PERFECT!, GOOD!, MISS!, TOO LATE!）を表示します。"""
    if judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)
    
def draw_game_over_screen() -> None:
    """ゲームオーバー時の画面（メッセージ、最終スコア、リスタート指示）を描画します。"""
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


# --- メインのゲームループ ---
running = True
clock = pygame.time.Clock()

while running:
    # 音楽再生とゲーム開始のチェック
    check_game_start()

    # イベント処理
    for event in pygame.event.get():
        running = handle_quit_event(event) # QUITイベントを処理
        handle_restart_event(event, game_over) # ゲームオーバー時のリスタート処理

        # KEYDOWNイベントの場合のみ process_key_press を呼び出す
        if event.type == pygame.KEYDOWN:
            process_key_press(event) # キー入力処理

    # ゲームの状態更新 (ゲームオーバーでない場合のみ)
    if not game_over:
        generate_notes() # 譜面からノーツを生成
        update_notes_position() # ノーツの移動と判定外れチェック
        update_timers() # 各種タイマーの更新
        # HPが0になったらゲームオーバーにする最終チェック
        check_game_over() 

    # 描画
    draw_background() # 背景とレーン枠、判定ライン、キーの描画
    draw_notes() # ノーツの描画
    draw_info_panel() # スコア、コンボ、HPバーなどの描画
    draw_judgement_message() # 判定メッセージの描画
    draw_game_over_screen() # ゲームオーバー画面の描画

    # 画面の更新とフレームレート固定
    pygame.display.flip()
    clock.tick(60)

pygame.quit()