import pygame
import csv
import time
import sys
import os 

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
CYAN: Tuple[int, int, int] = (0, 255, 255) # 判定強化表示用
YELLOW: Tuple[int, int, int] = (255, 255, 0) # フィーバー時のコンボ色
BLUE: Tuple[int, int, int] = (0, 0, 255) # メニュー選択肢用
FEVER_BACKGROUND_COLOR: Tuple[int, int, int] = (40, 40, 0) # 黒に近い、ごく薄い黄土色 (R, G, B)
PURPLE: Tuple[int, int, int] = (128, 0, 128) # HPバーの色として追加

# レーン設定
LANE_COUNT: int = 4
LANE_WIDTH: int = 100
LANE_SPACING: int = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)

# ノーツ設定
NOTE_SPEED: float = 5.0
NOTE_HEIGHT: int = 20 # 単発ノーツの表示高さ

# 判定設定
JUDGEMENT_LINE_Y: int = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW_PERFECT: int = 15 # PERFECT判定の許容範囲 (JUDGEMENT_LINE_Yからの距離)
JUDGEMENT_WINDOW_GOOD: int = 30 # GOOD判定の許容範囲 (JUDGEMENT_LINE_Yからの距離)

# ノーツが画面上端から判定ラインまで落ちるのにかかる時間 (ミリ秒)
FALL_TIME_MS: float = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED * (1000 / FPS)

# 各レーンに対応するキーとレーンインデックス (キー入力判定用)
key_to_lane_idx: Dict[int, int] = {
    pygame.K_a: 0, # Aキーは0番目のレーン
    pygame.K_s: 1, # Sキーは1番目のレーン
    pygame.K_d: 2, # Dキーは2番目のレーン
    pygame.K_f: 3 # Fキーは3番目のレーン
}

# 各レーンに対応する色をリストで定義 (描画用)。レーンインデックスと色が確実に一致する！
lane_colors: List[Tuple[int, int, int]] = [
    (255, 100, 100), # レーン0 (Aキー) の色
    (100, 255, 100), # レーン1 (Sキー) の色
    (100, 100, 255), # レーン2 (Dキー) の色
    (255, 255, 100) # レーン3 (Fキー) の色
]

# レーンインデックスに対応する表示文字
lane_idx_to_key_char: Dict[int, str] = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# 長押しに使うdict (キーが押されている間、レーンに四角いエフェクトを描画するために使用)
lane_keys = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}

# 譜面ファイルと音楽ファイルのパス設定
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR: str = BASE_DIR # この例ではスクリプトと同じディレクトリをアセットディレクトリとする

BEATMAP_FILE_NAME: str = 'beatmap.csv'
MUSIC_FILE_NAME: str = 'maou_short_14_shining_star.mp3'
T_SOUND_FILE_NAME: str = 'T.mp3' # T.mp3のファイル名を追加

BEATMAP_FULL_PATH: str = os.path.join(ASSET_DIR, BEATMAP_FILE_NAME)
MUSIC_FULL_PATH: str = os.path.join(ASSET_DIR, MUSIC_FILE_NAME)
T_SOUND_FULL_PATH: str = os.path.join(ASSET_DIR, T_SOUND_FILE_NAME) # T.mp3のフルパスを定義

# --- HPバーのサイズ定義 ---
HP_BAR_WIDTH: int = 200
HP_BAR_HEIGHT: int = 20

# --- ゲームの状態を管理するEnum (または定数) ---
GAME_STATE_MENU: int = 0
GAME_STATE_PLAYING: int = 1
GAME_STATE_GAME_OVER: int = 2

# --- グローバル変数 (ゲームの状態を保持) ---
score: int = 0
combo: int = 0
max_combo: int = 0

MAX_HP: int = 500
current_hp: int = MAX_HP
HP_LOSS_PER_MISS: int = 10 # 通常のミスで減るHP量

# 判定強化設定
JUDGEMENT_BOOST_COMBO_THRESHOLD: int = 10 # 判定強化が発動するコンボの倍数
JUDGEMENT_BOOST_DURATION_FRAMES: int = FPS * 5 # 判定強化の持続時間 (5秒)
judgement_boost_active: bool = False # 判定強化が現在有効か
judgement_boost_timer: int = 0 # 判定強化の残り時間（フレーム数）

# フィーバー演出設定
FEVER_COMBO_THRESHOLD: int = 10 # フィーバーが発動するコンボ数
fever_active: bool = False # フィーバーが現在有効か (コンボ数で継続)
fever_flash_color_timer: int = 0 # 色を点滅させるためのタイマー (今回は背景には使わないが、他の用途のために残しておく)
FEVER_FLASH_INTERVAL: int = 120 # (今回は背景には使わないが、他の用途のために残しておく)

judgement_effect_timer: int = 0
judgement_message: str = ""
judgement_color: Tuple[int, int, int] = WHITE

beatmap_index: int = 0
# notesリストの各辞書に 'type', 'start_time_ms', 'end_time_ms', 'is_holding', 'is_released' を追加
notes: List[Dict] = [] 

# ゲーム状態の初期値はメニュー
game_state: int = GAME_STATE_MENU
game_start_time: float = 0.0

lane_effects: List[Optional[Tuple[int, int, int]]] = [None] * LANE_COUNT
lane_effect_timers: List[int] = [0] * LANE_COUNT

# --- Pygameの初期化と画面設定 ---
pygame.init()
pygame.mixer.init()
screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("君もシャイニングマスターの道へ") # タイトル名を変更


# --- フォントの設定 ---
font_path: Optional[str] = None
try:
    if sys.platform.startswith('win'): # Windows
        potential_font_paths = [
            "C:/Windows/Fonts/YuGothM.ttc", # 游ゴシック Medium
            "C:/Windows/Fonts/meiryo.ttc", # メイリオ
            "C:/Windows/Fonts/msgothic.ttc" # MS ゴシック
        ]
    elif sys.platform == 'darwin': # macOS
        potential_font_paths = [
            "/System/Library/Fonts/AquaKana.ttc",
            "/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", # ヒラギノ丸ゴシック
            "/System/Library/Fonts/SFCompactText.ttf" # システムフォント
        ]
    else: # Linux (Noto Sans CJK JPの一般的なパス)
        potential_font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
            "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", # IPA Pゴシック
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
        ]

    for path in potential_font_paths:
        if os.path.exists(path):
            font_path = path
            print(f"使用フォント: {font_path}")
            break
    
    if font_path is None:
        print("警告: 適切な日本語フォントが見つかりませんでした。テキストが四角 (□) で表示される可能性があります。")

except Exception as e:
    print(f"フォントの検索中にエラーが発生しました: {e}")
    font_path = None # 問題が発生した場合もデフォルトにフォールバック

font: pygame.font.Font = pygame.font.Font(font_path, 48)
large_font: pygame.font.Font = pygame.font.Font(font_path, 72) # メニュータイトル用
small_font: pygame.font.Font = pygame.font.Font(font_path, 36)

# --- 効果音のロード ---
t_sound: Optional[pygame.mixer.Sound] = None
try:
    t_sound = pygame.mixer.Sound(T_SOUND_FULL_PATH)
except pygame.error:
    print(f"警告: 効果音ファイル '{T_SOUND_FULL_PATH}' を読み込めませんでした。キーを押しても効果音が鳴りません。")
except FileNotFoundError:
    print(f"警告: 効果音ファイル '{T_SOUND_FULL_PATH}' が見つかりません。キーを押しても効果音が鳴りません。")

def play_sound(sound_obj: Optional[pygame.mixer.Sound]) -> None:
    """
    指定されたSoundオブジェクトを再生します。
    SoundオブジェクトがNoneの場合（ロードに失敗した場合など）は何もせず終了します。
    """
    if sound_obj:
        sound_obj.play()

# --- レーンごとの円形エフェクトを描画 ---  
def draw_lane_effect(screen: pygame.Surface, x_center: int, color: Tuple[int, int, int], alpha: int = 100, radius: int = 50) -> None:
    """
    指定された位置に円形のエフェクトを描画します。
    """
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(s, color + (alpha,), (x_center, JUDGEMENT_LINE_Y), radius)
    screen.blit(s, (0, 0))

#***ロングノーツのクラスの追加 (長押しエフェクト用)
class Long_note:
    """
    x座標,y座標,高さ,横幅から四角を作成
    引数1:x座標
    引数2:y座標
    引数3:高さ
    引数4:横幅
    """
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height) 
        self.color = color
            
    def update(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect)

# 「今、どのキーが押され続けているか」を記録するための変数
held_keys = set() 
# 押されているキーのレーンに表示するエフェクト用の四角 (Long_noteクラスを使用)
pressing_notes = {} 
for key, data in lane_keys.items():
    lane_idx = key_to_lane_idx[key]
    color = (100, 100, 100) # 灰色
    lane_x = LANE_SPACING + lane_idx * (LANE_WIDTH + LANE_SPACING)
    pressing_notes[key] = Long_note(lane_x, JUDGEMENT_LINE_Y -5, LANE_WIDTH, 10, color)


# --- ファイル読み込み処理 (関数化) ---
def load_beatmap(path: str) -> List[List[int]]:
    """
    譜面ファイルを読み込み、ノーツデータ（時間、レーン、[終了時間]）のリストを返します。
    ファイルが見つからない場合はエラーメッセージを表示し、ゲームを終了します。
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' not found.")

        beatmap_data = []
        with open(path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 2:
                    # 単発ノーツ: [開始時間, レーン] -> 終了時間を開始時間と同じにする
                    beatmap_data.append([int(row[0]), int(row[1]), int(row[0])]) 
                elif len(row) == 3:
                    # ロングノーツ: [開始時間, レーン, 終了時間]
                    beatmap_data.append([int(row[0]), int(row[1]), int(row[2])])
                else:
                    print(f"警告: 不正な譜面データ形式の行をスキップしました: {row}")
        return beatmap_data
    except FileNotFoundError as e:
        print(f"エラー: 譜面ファイルが見つかりません。{e}")
        print("ゲームスクリプトと同じディレクトリに 'beatmap.csv' があるか確認してください。")
        print("または 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
        print(f"期待される譜面パス: {path}")
        pygame.quit()
        sys.exit()
    except ValueError as e:
        print(f"エラー: 譜面データの内容が不正です。数値に変換できませんでした。{e}")
        print(f"問題の行を確認してください。")
        pygame.quit()
        sys.exit()

def load_music(path: str) -> None:
    """
    音楽ファイルを読み込みます。ファイルが見つからない場合やロードに失敗した場合は警告を表示します。
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' not found.")
        pygame.mixer.music.load(path)
    except pygame.error as e:
        print(f"警告: 音楽ファイルをロードできませんでした。{e}")
        print(f"期待される音楽パス: {path}")
    except FileNotFoundError as e:
        print(f"警告: 音楽ファイルが見つかりません。{e}")
        print(f"期待される音楽パス: {path}")

# 譜面と音楽のロードを実行
BEATMAP: List[List[int]] = load_beatmap(BEATMAP_FULL_PATH)
load_music(MUSIC_FULL_PATH)

# --- ゲームの状態をリセットする関数 (リスタート用) ---
def reset_game_state(activate_boost_initially: bool = False) -> None:
    """ゲームの全状態を初期値にリセットします。
    activate_boost_initially: ゲーム開始時に判定強化を有効にするかどうか。
    """
    global score, combo, max_combo, current_hp, notes, beatmap_index
    global game_state, game_start_time
    global judgement_effect_timer, judgement_message, judgement_color
    global judgement_boost_active, judgement_boost_timer
    global fever_active, fever_flash_color_timer
    global lane_effects, lane_effect_timers # エフェクト関連もリセット
    global held_keys # held_keysもリセット

    score = 0
    combo = 0
    max_combo = 0
    current_hp = MAX_HP
    notes.clear()
    beatmap_index = 0
    game_state = GAME_STATE_PLAYING # ゲーム開始状態に設定
    game_start_time = 0.0 # ゲーム開始時刻をリセット
    judgement_effect_timer = 0
    judgement_message = ""
    judgement_color = WHITE
    judgement_boost_active = activate_boost_initially # ここで初期設定を適用
    judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES if activate_boost_initially else 0
    fever_active = False
    fever_flash_color_timer = 0
    
    # レーンエフェクトもリセット
    lane_effects = [None] * LANE_COUNT
    lane_effect_timers = [0] * LANE_COUNT
    held_keys.clear() # held_keysもリセット

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

def handle_menu_input(event: pygame.event.Event) -> None:
    """メニュー画面でのキー入力を処理します。"""
    global game_state, judgement_boost_active, game_start_time

    if event.type == pygame.KEYDOWN: # メニュー画面から1,2キーで選択
        if event.key == pygame.K_1: # Start without Judgment Boost
            judgement_boost_active = False
            reset_game_state(activate_boost_initially=False)
            pygame.mixer.music.play()
            game_start_time = time.time() # ゲーム開始時刻を設定
        elif event.key == pygame.K_2: # Start with Judgment Boost
            judgement_boost_active = True
            reset_game_state(activate_boost_initially=True)
            pygame.mixer.music.play()
            game_start_time = time.time() # ゲーム開始時刻を設定

def handle_game_over_input(event: pygame.event.Event) -> None:
    """
    ゲームオーバー時にRキーが押された際のリスタート処理を行います。
    """
    global game_state
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r: # rキーが押されたらリスタート
        game_state = GAME_STATE_MENU # Return to menu

def process_key_press(event: pygame.event.Event) -> None:
    """
    キーが押された際のノーツ判定処理を行います。
    単発ノーツのヒット判定と、ロングノーツの押し始め判定を行います。
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes, lane_effects, lane_effect_timers
    
    if game_state == GAME_STATE_PLAYING and event.key in key_to_lane_idx:
        pressed_lane_idx = key_to_lane_idx[event.key]
        play_sound(t_sound) # 効果音を鳴らす
        
        judgement_effect_timer = 30
        lane_effect_timers[pressed_lane_idx] = 10 
        
        hit_note_index = -1
        best_distance = float('inf') # 最も近いノーツを探すための距離

        current_game_time_ms = (time.time() - game_start_time) * 1000

        # まず、押されたレーンのノーツの中から、まだヒットされていないノーツを探す
        # 単発ノーツ、またはロングノーツの開始点が判定ラインの範囲内にあるか
        for i, note in enumerate(notes):
            if note['lane'] == pressed_lane_idx and not note['hit']:
                # ノーツの**下端**が判定ラインにどれだけ近いか
                distance_to_judgement_line = abs(note['rect'].bottom - JUDGEMENT_LINE_Y) # ★修正点: .centery から .bottom へ

                # 判定範囲内かつ、これまで見つけた中で最も近いノーツを探す
                if distance_to_judgement_line <= JUDGEMENT_WINDOW_GOOD and distance_to_judgement_line < best_distance:
                    best_distance = distance_to_judgement_line
                    hit_note_index = i
        
        if hit_note_index != -1:
            hit_note = notes[hit_note_index]
            score_gained = 0

            # 判定ロジック (単発ノーツまたはロングノーツの押し始め)
            if judgement_boost_active and best_distance <= JUDGEMENT_WINDOW_GOOD:
                judgement_message = "PERFECT! (Boosted)"
                judgement_color = GREEN
                score_gained = 100
            elif best_distance <= JUDGEMENT_WINDOW_PERFECT:
                judgement_message = "PERFECT!"
                judgement_color = GREEN
                score_gained = 100
            elif best_distance <= JUDGEMENT_WINDOW_GOOD:
                judgement_message = "GOOD!"
                judgement_color = YELLOW
                score_gained = 50
            
            score += score_gained
            combo += 1
            max_combo = max(max_combo, combo)
            lane_effects[pressed_lane_idx] = judgement_color # エフェクト色を設定
            
            # HP回復 (コンボが3の倍数で回復)
            if combo > 0 and combo % 3 == 0:
                hp_recovered = min(10, MAX_HP - current_hp)
                current_hp += hp_recovered
                if hp_recovered > 0:
                    judgement_message += f" (+{hp_recovered} HP!)"
            
            # 判定強化の発動
            if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                judgement_boost_active = True
                judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                judgement_message = (judgement_message + " (BOOST!)") if "BOOST!" not in judgement_message else judgement_message
            
            # フィーバーの発動
            if combo >= FEVER_COMBO_THRESHOLD:
                if not fever_active:
                    fever_flash_color_timer = FEVER_FLASH_INTERVAL
                fever_active = True

            # ノーツの種類に応じた処理
            if hit_note['type'] == 'single':
                # 単発ノーツはヒットしたら削除
                notes.pop(hit_note_index)
                hit_note['hit'] = True # 処理済みとしてマーク
            elif hit_note['type'] == 'long':
                # ロングノーツは押し始めを判定したら 'is_holding' を True にする
                # リストからは削除しない
                hit_note['is_holding'] = True
                hit_note['hit'] = True # 押し始めをヒット済みとしてマーク

        else: # ノーツが見つからなかった場合 (MISS)
            combo = 0 # コンボリセット
            judgement_message = "MISS!"
            judgement_color = RED
            lane_effects[pressed_lane_idx] = RED # エフェクト色をMISSに設定
            judgement_effect_timer = 30
            current_hp -= HP_LOSS_PER_MISS # HP減少
            check_game_over() # ゲームオーバー判定

            # コンボがリセットされたらフィーバー解除
            fever_active = False
            fever_flash_color_timer = 0


# --- ゲーム状態更新の関数群 ---
def check_game_start() -> None:
    """ゲーム開始条件をチェックし、ゲームを開始します。音楽の再生も行います。"""
    global game_start_time
    if game_state == GAME_STATE_PLAYING and pygame.mixer.get_init() and BEATMAP:
        if not pygame.mixer.music.get_busy() and game_start_time == 0: 
            pygame.mixer.music.play()
            game_start_time = time.time() 

def generate_notes() -> None:
    """譜面データに基づいてノーツを生成し、notesリストに追加します。"""
    global beatmap_index, notes
    if game_state == GAME_STATE_PLAYING:
        current_game_time_ms = (time.time() - game_start_time) * 1000

        while beatmap_index < len(BEATMAP) and current_game_time_ms >= BEATMAP[beatmap_index][0] - FALL_TIME_MS:
            note_data = BEATMAP[beatmap_index] # [開始時間, レーン, 終了時間]
            start_time_ms = note_data[0]
            target_lane = note_data[1]
            end_time_ms = note_data[2] # 譜面から取得した終了時間

            note_type = 'single'
            note_height_to_draw = NOTE_HEIGHT # デフォルトは単発ノーツの高さ
            
            if end_time_ms > start_time_ms:
                # ロングノーツの場合
                note_type = 'long'
                duration_ms = end_time_ms - start_time_ms
                # 継続時間(ms)を落下速度に基づいてピクセル単位の高さに変換
                # (1000.0 / FPS) は1フレームあたりのミリ秒
                note_height_to_draw = int(duration_ms / (1000.0 / FPS) * NOTE_SPEED)
                if note_height_to_draw < NOTE_HEIGHT: # 最低限の高さは確保
                    note_height_to_draw = NOTE_HEIGHT
            
            lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)
            # ノーツのy座標は画面上端から、描画高さは計算された高さ
            new_note_rect = pygame.Rect(lane_x_start, -note_height_to_draw, LANE_WIDTH, note_height_to_draw)
            
            notes.append({
                'rect': new_note_rect,
                'lane': target_lane,
                'hit': False,          # 単発ノーツ用: ヒットしたか (ロングノーツの押し始めにも使用)
                'type': note_type,
                'start_time_ms': start_time_ms,
                'end_time_ms': end_time_ms,
                'is_holding': False,   # ロングノーツ用: 押し始め判定後、現在押されているか
                'is_released': False,  # ロングノーツ用: 押し終わりの判定済みか
                'scored_hold_points': 0 # ロングノーツ用: 加算済みの長押しスコア（任意）
            })
            
            beatmap_index += 1 


def update_notes_position() -> None:
    """
    画面上のノーツの位置を更新し、判定ラインを完全に過ぎてしまったノーツを処理します。
    (TOO LATE! / Missed Note の判定と処理を含みます)
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes, lane_effects, lane_effect_timers

    current_game_time_ms = (time.time() - game_start_time) * 1000

    for note in notes[:]: # リストをコピーして要素削除時にエラーを防ぐ
        # ロングノーツが押下中の場合は、そのrectのy座標は動かさない（描画時に調整）
        # ただし、is_holdingがFalseの通常の落下状態のときは動かす
        if not (note['type'] == 'long' and note['is_holding']):
            note['rect'].y += NOTE_SPEED
        
        if note['type'] == 'single':
            # 単発ノーツが判定ラインを完全に通り過ぎてしまった場合 (TOO LATE! / Missed Note)
            if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW_GOOD and not note['hit']:
                notes.remove(note)
                note['hit'] = True 
                # 以下、MISSの処理
                combo = 0 
                judgement_message = "TOO LATE!" 
                judgement_color = RED
                lane_effects[note['lane']] = RED 
                judgement_effect_timer = 30
                current_hp -= HP_LOSS_PER_MISS 
                check_game_over()
                fever_active = False
                fever_flash_color_timer = 0
                if combo < FEVER_COMBO_THRESHOLD and fever_active:
                    fever_active = False
                    fever_flash_color_timer = 0
        
        elif note['type'] == 'long':
            # ロングノーツが開始時間になっても押されなかった場合 (MISS)
            # ノーツの上端が判定ラインを通り過ぎたのに、まだヒット（押し始め）されていない場合
            if not note['hit'] and note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW_GOOD:
                notes.remove(note)
                note['hit'] = True # 処理済みとしてマーク
                # 以下、MISSの処理
                combo = 0 
                judgement_message = "MISS! (Long Note Start)" 
                judgement_color = RED
                lane_effects[note['lane']] = RED 
                judgement_effect_timer = 30
                current_hp -= HP_LOSS_PER_MISS 
                check_game_over()
                fever_active = False
                fever_flash_color_timer = 0

            # ロングノーツが押し始められていて、まだ終了していないが、
            # 終了時間を大きく過ぎてもキーが離されていない場合 (TOO LATE! for release)
            # is_holdingがTrueで、かつ終了時間 + GOOD判定ウィンドウを過ぎてもまだis_releasedがFalse
            elif note['is_holding'] and not note['is_released'] and \
                 current_game_time_ms > note['end_time_ms'] + JUDGEMENT_WINDOW_GOOD:
                
                # ユーザーが離さなかった場合のMISS
                notes.remove(note)
                note['is_released'] = True # 終了済みマーク
                
                combo = 0 # MISSなのでコンボリセット
                judgement_message = "TOO LATE! (Long Note End)"
                judgement_color = RED
                lane_effects[note['lane']] = RED
                judgement_effect_timer = 30
                current_hp -= HP_LOSS_PER_MISS
                check_game_over()
                fever_active = False
                fever_flash_color_timer = 0
            
            # 画面外に出たロングノーツを削除 (念のため)
            # is_holding == False の通常落下中のロングノーツが画面外に出た場合も含む
            elif note['rect'].top > SCREEN_HEIGHT + 100: # 画面下端を十分に過ぎたら削除
                notes.remove(note)


def update_timers() -> None:
    """各種タイマー（判定エフェクト、判定強化、フィーバー点滅、レーンエフェクト）を更新します。"""
    global judgement_effect_timer, judgement_boost_timer, judgement_boost_active
    global fever_flash_color_timer, fever_active
    global lane_effect_timers

    # 判定強化タイマーの更新
    if judgement_boost_active:
        judgement_boost_timer -= 1
        if judgement_boost_timer <= 0:
            judgement_boost_active = False
            judgement_boost_timer = 0

    # フィーバー演出の点滅タイマーを更新 (背景色には影響しないが、他の要素で使う可能性を考慮して残す)
    if fever_active:
        fever_flash_color_timer -= 1
        if fever_flash_color_timer <= 0:
            fever_flash_color_timer = FEVER_FLASH_INTERVAL
    
    # 判定メッセージ表示タイマーの更新
    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

    # レーンエフェクトタイマーの更新
    for i in range(LANE_COUNT):
        if lane_effect_timers[i] > 0:
            lane_effect_timers[i] -= 1
            if lane_effect_timers[i] == 0:
                lane_effects[i] = None # タイマーが0になったらエフェクトを消す


def check_game_over() -> None:
    """HPが0以下になった場合にゲームオーバー状態を設定し、音楽を停止します。"""
    global current_hp, game_state
    if current_hp <= 0:
        current_hp = 0
        game_state = GAME_STATE_GAME_OVER
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

def check_game_finish() -> None:
    """
    全てのノーツが生成され、画面上に残っているノーツがなくなった場合に
    ゲーム終了状態（ゲームオーバー）に遷移します。
    """
    global game_state, judgement_message
    if game_state == GAME_STATE_PLAYING:
        # 音楽が再生中でなく、かつ全てのノーツが処理された（生成済みかつ画面上に残っていない）場合
        if not pygame.mixer.music.get_busy() and beatmap_index >= len(BEATMAP) and not notes:
            # ゲームオーバー画面へ遷移
            game_state = GAME_STATE_GAME_OVER
            judgement_message = "FINISH!" # ゲーム終了を示すメッセージ

# --- 描画処理の関数群 ---
def draw_background() -> None:
    """ゲームの背景（レーン枠、判定ライン、対応キー）を描画します。フィーバー中は背景色を特別な色にします。"""
    if fever_active and game_state == GAME_STATE_PLAYING: # プレイ中のみフィーバー背景
        screen.fill(FEVER_BACKGROUND_COLOR) # フィーバー中はごく薄い黄色の背景
    else:
        screen.fill(BLACK) # 通常の背景は黒

    if game_state == GAME_STATE_PLAYING:
        # レーンの描画
        for i in range(LANE_COUNT):
            lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
            pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2) # レーンの枠

            # レーンエフェクトの描画
            if lane_effects[i]:
                draw_lane_effect(screen, lane_x_start + LANE_WIDTH // 2, lane_effects[i], alpha=100)

            # レーンの下に対応するキーを表示
            key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
            screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
        
        # 判定ラインの背景とライン自体を描画
        pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)
        pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

def draw_notes() -> None:
    """現在画面に表示されているノーツを描画します。"""
    if game_state == GAME_STATE_PLAYING:
        current_game_time_ms = (time.time() - game_start_time) * 1000 # 現在のゲーム時間を取得

        for note in notes:
            draw_rect = note['rect'].copy() # 描画用の一時的なRectオブジェクトを作成

            if note['type'] == 'long' and note['is_holding'] and not note['is_released']:
                # 押されているロングノーツの描画
                # 判定ラインに下端を合わせ、上方向に縮むように描画する
                
                # 経過時間（開始判定からの時間）
                elapsed_hold_time_ms = current_game_time_ms - note['start_time_ms']
                # ロングノーツの総時間
                total_duration_ms = note['end_time_ms'] - note['start_time_ms']

                # 残りの描画するべき高さ
                # 総時間に対する残りの時間の比率で高さを計算
                # 落下速度基準で計算された元の高さを利用
                original_total_height = int(total_duration_ms / (1000.0 / FPS) * NOTE_SPEED)
                
                # 進行度合いに応じた縮小される高さ
                played_height = int(elapsed_hold_time_ms / (1000.0 / FPS) * NOTE_SPEED)
                
                # 現在の描画高さ
                current_draw_height = original_total_height - played_height
                
                # 最低限の高さは確保 (例: NOTE_HEIGHT)
                if current_draw_height < NOTE_HEIGHT:
                    current_draw_height = NOTE_HEIGHT

                # 描画Rectのy座標と高さを調整
                # 下端を判定ラインに合わせる (JUDGEMENT_LINE_Yはノーツの下端が来るべき位置)
                draw_rect.height = current_draw_height
                draw_rect.y = JUDGEMENT_LINE_Y - current_draw_height # 判定ラインのYから高さを引いてY座標を決定

                # 押下中の色 (例: 元の色の半分)
                active_color = (lane_colors[note['lane']][0] // 2, lane_colors[note['lane']][1] // 2, lane_colors[note['lane']][2] // 2)
                pygame.draw.rect(screen, active_color, draw_rect)

            elif note['type'] == 'long' and not note['is_holding'] and not note['is_released']:
                # まだ押されていない（落下中）のロングノーツ
                pygame.draw.rect(screen, lane_colors[note['lane']], draw_rect)
            
            elif note['type'] == 'single':
                # 単発ノーツ
                pygame.draw.rect(screen, lane_colors[note['lane']], draw_rect)

def draw_info_panel() -> None:
    """スコア、コンボ、最高コンボ、HPバー、判定強化の残り時間を描画します。"""
    if game_state == GAME_STATE_PLAYING:
        # スコア、コンボ、最高コンボの表示
        score_text = font.render(f"Score: {score}", True, WHITE)
        # フィーバー中はコンボ文字を黄色にする
        combo_color = YELLOW if fever_active else WHITE
        combo_text = font.render(f"Combo: {combo}", True, combo_color)
        max_combo_text = small_font.render(f"Max Combo: {max_combo}", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(combo_text, (10, 50))
        # マックスコンボのY座標を調整してHPバーと重ならないようにする
        screen.blit(max_combo_text, (SCREEN_WIDTH - max_combo_text.get_width() - 10, 40))

        # HPバーの描画
        hp_bar_x = (SCREEN_WIDTH - HP_BAR_WIDTH) // 2
        hp_bar_y = 10
        hp_bar_fill_width = int(HP_BAR_WIDTH * (current_hp / MAX_HP))
        
        pygame.draw.rect(screen, GRAY, (hp_bar_x, hp_bar_y, HP_BAR_WIDTH, HP_BAR_HEIGHT), 2) # HPバーの枠
        # HPに応じて色を変える (今回は紫を追加)
        if current_hp > MAX_HP / 3:
            hp_fill_color = PURPLE # HPが1/3より上なら紫
        else:
            hp_fill_color = RED # HPが1/3以下なら赤
        pygame.draw.rect(screen, hp_fill_color, (hp_bar_x, hp_bar_y, hp_bar_fill_width, HP_BAR_HEIGHT)) # HPの量
        
        hp_text = small_font.render(f"HP: {current_hp}/{MAX_HP}", True, WHITE)
        screen.blit(hp_text, (hp_bar_x + HP_BAR_WIDTH + 10, hp_bar_y)) # HPの数値

        # 判定強化の残り時間を表示
        if judgement_boost_active:
            boost_text = small_font.render(f"Boost: {judgement_boost_timer // FPS + 1}s", True, CYAN) # シアン色で表示
            screen.blit(boost_text, (SCREEN_WIDTH - boost_text.get_width() - 10, 70)) # この位置も調整したよ

def draw_judgement_message() -> None:
    """判定メッセージ（PERFECT!, GOOD!, MISS!, TOO LATE!）を表示します。"""
    if game_state == GAME_STATE_PLAYING and judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)
    
def draw_game_over_screen() -> None:
    """ゲームオーバー時の画面（メッセージ、最終スコア、リスタート指示）を描画します。"""
    if game_state == GAME_STATE_GAME_OVER:
        # メッセージが"FINISH!"であればそのまま、そうでなければ"GAME OVER!"を表示
        display_message = judgement_message if judgement_message == "FINISH!" else "GAME OVER!"
        game_over_text = large_font.render(display_message, True, WHITE if display_message == "FINISH!" else RED)
        
        final_score_text = font.render(f"Final Score: {score}", True, WHITE)
        max_combo_final_text = font.render(f"Max Combo: {max_combo}", True, WHITE)
        
        go_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80))
        fs_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        mc_rect = max_combo_final_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))

        screen.blit(game_over_text, go_rect)
        screen.blit(final_score_text, fs_rect)
        screen.blit(max_combo_final_text, mc_rect)
        
        restart_text = small_font.render("Rキーでメニューに戻る", True, WHITE) # 日本語
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(restart_text, restart_rect)

def draw_menu_screen() -> None:
    """ゲーム開始前のメニュー画面を描画します。"""
    screen.fill(BLACK) # メニュー画面は黒背景
    
    # ★「君もシャイニングマスターの道へ」キャッチフレーズの表示調整
    line1_text = "音と光が織りなす究極の律動――"
    line2_text = "さぁ、君もシャイニングマスターの道へ！"

    rendered_line1 = font.render(line1_text, True, WHITE)
    rendered_line2 = small_font.render(line2_text, True, WHITE) 

    y_pos_line1 = SCREEN_HEIGHT // 2 - 180
    y_pos_line2 = SCREEN_HEIGHT // 2 - 130 # 1行目と2行目の間隔を調整

    rect1 = rendered_line1.get_rect(center=(SCREEN_WIDTH // 2, y_pos_line1))
    rect2 = rendered_line2.get_rect(center=(SCREEN_WIDTH // 2, y_pos_line2))

    screen.blit(rendered_line1, rect1)
    screen.blit(rendered_line2, rect2)

    # ゲームスタートオプション
    option1_text = font.render("1: ゲームスタート (判定強化なし)", True, WHITE)
    option1_rect = option1_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(option1_text, option1_rect)

    option2_text = font.render("2: ゲームスタート (判定強化あり)", True, CYAN) # Boostはシアン
    option2_rect = option2_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
    screen.blit(option2_text, option2_rect)

    # 操作説明
    info_text = small_font.render("対応する数字キーを押して選択してください", True, GRAY)
    info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
    screen.blit(info_text, info_rect)


# --- メインのゲームループ --- 
clock = pygame.time.Clock() # mainループの外で一度だけ初期化

running = True
while running:

    # ゲームの状態更新
    if game_state == GAME_STATE_PLAYING: 
        check_game_start() # 音楽再生とゲーム開始のチェック
        generate_notes() # 譜面からノーツを生成
        update_notes_position() # ノーツの移動と判定外れチェック
        update_timers() # 各種タイマーの更新
        check_game_over() # HPが0になったらゲームオーバーにする最終チェック
        check_game_finish() # ゲーム終了判定（音楽終了＆ノーツ枯渇）

    # 描画
    screen.fill(BLACK) # 毎フレーム画面をクリア

    if game_state == GAME_STATE_MENU: 
        draw_menu_screen()
    elif game_state == GAME_STATE_PLAYING: 
        draw_background() # 背景とレーン枠、判定ライン、キーの描画
        draw_notes() # ノーツの描画
        draw_info_panel() # スコア、コンボ、HPバーなどの描画
        draw_judgement_message() # 判定メッセージの描画
    elif game_state == GAME_STATE_GAME_OVER: 
        draw_game_over_screen() # ゲームオーバー画面の描画

    for event in pygame.event.get():
        running = handle_quit_event(event) # QUITイベントを処理
        if not running:
            break 

        if game_state == GAME_STATE_MENU:
            handle_menu_input(event) 
        elif game_state == GAME_STATE_PLAYING: 
            if event.type == pygame.KEYDOWN: 
                # 押されたキーをheld_keysに追加
                if event.key in lane_keys: 
                    held_keys.add(event.key) 
                # キープレス時のノーツ判定（単発ノーツヒット or ロングノーツ押し始め）
                process_key_press(event) 
            
            if event.type==pygame.KEYUP:
                # 離されたキーをheld_keysから削除
                if event.key in held_keys: 
                    released_lane_idx = key_to_lane_idx[event.key]
                    held_keys.remove(event.key) 

                    current_game_time_ms = (time.time() - game_start_time) * 1000

                    # 離されたキーに対応するレーンで、現在「押下中」のロングノーツを探す
                    found_long_note_index = -1
                    for i, note in enumerate(notes):
                        if note['type'] == 'long' and note['lane'] == released_lane_idx and note['is_holding'] and not note['is_released']:
                            found_long_note_index = i
                            break
                    
                    if found_long_note_index != -1:
                        released_long_note = notes[found_long_note_index]
                        
                        # 離すタイミングの判定
                        release_time_diff = abs(current_game_time_ms - released_long_note['end_time_ms'])

                        if judgement_boost_active and release_time_diff <= JUDGEMENT_WINDOW_GOOD:
                            judgement_message = "PERFECT! (Boosted Release)"
                            judgement_color = GREEN
                            score += 100 # 離した点数
                        elif release_time_diff <= JUDGEMENT_WINDOW_PERFECT:
                            judgement_message = "PERFECT! (Release)"
                            judgement_color = GREEN
                            score += 100
                        elif release_time_diff <= JUDGEMENT_WINDOW_GOOD:
                            judgement_message = "GOOD! (Release)"
                            judgement_color = YELLOW
                            score += 50
                        else:
                            judgement_message = "BAD RELEASE! (Long Note)"
                            judgement_color = RED
                            current_hp -= HP_LOSS_PER_MISS # ミス時のHP減少

                        # 離す判定が行われたので、ノーツをリストから削除し、状態を更新
                        notes.pop(found_long_note_index) # リストから削除
                        released_long_note['is_released'] = True # 処理済みとしてマーク

                        # その他の判定結果更新
                        if judgement_color == RED: # リリース判定がMISSならコンボリセット
                            combo = 0
                            fever_active = False
                        else: # 成功ならコンボ継続
                            combo += 1
                            max_combo = max(max_combo, combo)
                            if combo >= FEVER_COMBO_THRESHOLD and not fever_active:
                                fever_active = True
                                fever_flash_color_timer = FEVER_FLASH_INTERVAL

                        lane_effects[released_lane_idx] = judgement_color
                        judgement_effect_timer = 30
                        # break # そのレーンのロングノーツは一つしかありえないので抜ける (popでリストのインデックスが変わるためbreakは必要)

        elif game_state == GAME_STATE_GAME_OVER:
            handle_game_over_input(event)
    
    # 長押し中のノーツ表示 (キーが押されている間、下部の四角を描画する機能)
    for key in held_keys:
        if key in pressing_notes:
            pressing_notes[key].update(screen)

    # 画面の更新とフレームレート固定
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
