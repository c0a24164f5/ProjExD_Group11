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
NOTE_HEIGHT: int = 20

# 判定設定
JUDGEMENT_LINE_Y: int = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW_PERFECT: int = 15 # PERFECT判定の許容範囲 (JUDGEMENT_LINE_Yからの距離)
JUDGEMENT_WINDOW_GOOD: int = 30 # GOOD判定の許容範囲 (JUDGEMENT_LINE_Yからの距離)
JUDGEMENT_WINDOW: int = JUDGEMENT_WINDOW_GOOD # process_key_press関数で使われている汎用判定ウィンドウ

# ノーツが画面上端から判定ラインまで落ちるのにかかる時間 (ミリ秒)
FALL_TIME_MS: float = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED * (1000 / FPS)

# 各レーンに対応するキーとレーンインデックス (キー入力判定用)
# `create_beatmap.py`と合わせたキー設定 (A, S, D, F) を使用
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

# 長押しに使うdict
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
notes: List[Dict] = [] # 現在画面に表示されているノーツのリスト (辞書形式: {'rect', 'lane', 'hit'})  この時点では空

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

#***ロングノーツのクラスの追加
class Long_note:
    """
    x座標,y座標,高さ,横幅から四角を作成
    引数1:x座標
    引数2:y座標
    引数3:高さ
    引数4:横幅
    """
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)  # x座標,y座標,高さ,横幅から四角を作成
        self.color = color
          # print("Long_noteクラス")  # 確認用
    def update(self, screen: pygame.Surface):
        """
        引数:画面screen
        画面screenに四角を描画
        """
        pygame.draw.rect(screen, self.color, self.rect)
          # print("update called")  # ← 呼ばれているか確認　デバッグ
        #time.sleep(0.000000001)

miss_invalid_time=0 #  *** ヒット時間用
# *** 位置はロングノーツclassの下でないと動かない「今、どのキーが押され続けているか」を記録するための変数の設定と押されている間描画するためのコード　draw_lane_effect(screen: pygame.Surface, x_center: int, color: Tuple[int, int, int], alpha: int = 100, radius: int = 50)でそれか自身のクラスを作って透明にするか
pressed_lane_idx=0  #  追加　自身でいじくってたら必要になった
held_keys = set()  # 「今、どのキーが押され続けているか」を記録するための変数
pressing_notes = {}  # 辞書
for key, data in lane_keys.items():  # dcit.items()で中身が取り出せる  key = pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f
    lane_idx = key_to_lane_idx[key]  # a,s,d,fに対応したレーン番号 数字で来るのでkey_to_lane_idxに変更  
    #color = data["color"]  # a,s,d,fに対応した色
    color = (100, 100, 100)  # 灰色
    lane_x = LANE_SPACING + lane_idx * (LANE_WIDTH + LANE_SPACING)  # a,s,d,fに対応したレーンに表示するx座標
    pressing_notes[key] = Long_note(lane_x, JUDGEMENT_LINE_Y -5, LANE_WIDTH, 10, color)  # a,s,d,fのキーを押したときのLong_note()の辞書ができる
# def make(key:int):
    # 関数にしてprocess_key_press関数内で更新しないと動かないかも 
    # for key, data in lane_keys.items():  # dcit.items()で中身が取り出せる  key = pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f
    #     lane_idx = key_to_lane_idx[key]  # a,s,d,fに対応したレーン番号 数字で来るのでkey_to_lane_idxに変更  
    #     #color = data["color"]  # a,s,d,fに対応した色
    #     color = (100, 100, 100)  # 灰色
    #     lane_x = LANE_SPACING + lane_idx * (LANE_WIDTH + LANE_SPACING)  # a,s,d,fに対応したレーンに表示するx座標
    #     pressing_notes[key] = Long_note(lane_x, JUDGEMENT_LINE_Y -5, LANE_WIDTH, 10, color)  # a,s,d,fのキーを押したときのLong_note()の辞書ができる



# --- ファイル読み込み処理 (関数化) ---
def load_beatmap(path: str) -> List[List[int]]:
    """
    譜面ファイルを読み込み、ノーツデータ（時間、レーン）のリストを返します。
    ファイルが見つからない場合はエラーメッセージを表示し、ゲームを終了します。
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' not found.")

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

    if event.type == pygame.KEYDOWN:  # メニュー画面から1,2キーで選択
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
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:  # rキーが押されたらリスタート
        game_state = GAME_STATE_MENU # Return to menu

def process_key_press(event: pygame.event.Event) -> None:
    """
    キーが押された際のノーツ判定処理を行います。
    score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgment_boost_active, judgment_boost_timer,
    fever_active, fever_flash_color_timer, notes グローバル変数を更新します。
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes, lane_effects, lane_effect_timers
    global miss_invalid_time,pressing_notes #  globalにして　関数外から持ってこないと動かない
    # Process key input only if the game is in PLAYING state
    if game_state == GAME_STATE_PLAYING and event.key in key_to_lane_idx:
        pressed_lane_idx = key_to_lane_idx[event.key]  # 押されたキーに対応した数字0,1,2,3が得られる=pressed_lane_idx
        hit_found = False
        
        # 効果音を鳴らす (T.mp3の準備が必要)
        # play_sound(t_sound) # t_soundが定義されていないためコメントアウト。必要なら定義してください。

        judgement_effect_timer = 30 # 判定メッセージ表示時間
        lane_effect_timers[pressed_lane_idx] = 10 # エフェクト表示時間 (例: 10フレーム)
        
        if hit_found:
            # HP回復 (コンボが3の倍数で回復)
            if combo > 0 and combo % 3 == 0:
                hp_recovered = min(10, MAX_HP - current_hp)
                current_hp += hp_recovered
                if hp_recovered > 0:
                    judgement_message += f" (+{hp_recovered} HP!)"
            
            # 判定強化の発動 (コンボが設定閾値の倍数で発動)
            if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                judgement_boost_active = True
                judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                judgement_message += " (BOOST!)" # Add BOOST activation message
            
            # フィーバーの発動 (コンボが設定閾値以上で発動)
            if combo >= FEVER_COMBO_THRESHOLD:
                if not fever_active: # 初めてフィーバーに入った時のみタイマーリセット
                    fever_flash_color_timer = FEVER_FLASH_INTERVAL
                fever_active = True
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
    # 音楽がロードされており、まだゲームが開始されていない場合、かつゲームオーバーでない
    # 注意: handle_menu_inputでgame_start_timeが設定されるため、この関数は基本的には最初の1回のみ実行されるか、
    # 音楽再生と時刻設定のロジックが重複する可能性があります。
    if game_state == GAME_STATE_PLAYING and pygame.mixer.get_init() and BEATMAP:
        if not pygame.mixer.music.get_busy() and game_start_time == 0: # game_start_timeが0の場合のみ音楽を再生
            pygame.mixer.music.play()
            game_start_time = time.time() # ゲーム開始時刻をここで設定

def generate_notes() -> None:
    """譜面データに基づいてノーツを生成し、notesリストに追加します。"""
    global beatmap_index, notes
    if game_state == GAME_STATE_PLAYING:
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
            
            notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})  # ノーツの作成 notes=リスト[辞書形式: {'rect', 'lane', 'hit'}]
            
            beatmap_index += 1 # 次のノーツへ

def update_notes_position() -> None:
    """
    画面上のノーツの位置を更新し、判定ラインを完全に過ぎてしまったノーツを処理します。
    (TOO LATE! / Missed Note の判定と処理を含みます)
    score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgment_boost_active, judgment_boost_timer,
    fever_active, fever_flash_color_timer グローバル変数を更新します。
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes, lane_effects, lane_effect_timers

    for note in notes[:]: # リストをコピーして要素削除時にエラーを防ぐ
        note['rect'].y += NOTE_SPEED
        # ノーツが判定ラインを完全に通り過ぎてしまった場合 (TOO LATE! / Missed Note)
        if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW_GOOD and not note['hit']:
            notes.remove(note)
            note['hit'] = True # 既に処理済みとしてマーク

            # レーンエフェクトの表示をここでリセットし、TOO LATEの処理に応じて色を設定
            lane_effect_timers[note['lane']] = 10 # エフェクト表示時間 (例: 10フレーム)

            if judgement_boost_active:
                # 判定強化中はTOO LATEもPERFECTに昇格
                score += 100 # スコア加算
                combo += 1 # コンボ継続
                max_combo = max(max_combo, combo)
                judgement_message = "PERFECT! (Boosted)" # BOOSTによるPERFECTであることを示す
                judgement_color = GREEN
                lane_effects[note['lane']] = GREEN # エフェクト色をPERFECTに設定
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
                    judgement_message += " (BOOST!)" # Add BOOST activation message
                
                # フィーバーの発動 (BOOSTによりコンボが増加し、閾値を超えた場合)
                if combo >= FEVER_COMBO_THRESHOLD:
                    if not fever_active:
                        fever_flash_color_timer = FEVER_FLASH_INTERVAL
                    fever_active = True

            else:
                # 判定強化中でない場合は通常のTOO LATE (コンボリセット & HP減少)
                combo = 0 # コンボをリセット
                judgement_message = "TOO LATE!" # 遅すぎた場合もMISS扱い
                judgement_color = RED
                lane_effects[note['lane']] = RED # エフェクト色をTOO LATE (MISS) に設定
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
        for note in notes:
            # レーンの色でノーツを描画
            pygame.draw.rect(screen, lane_colors[note['lane']], note['rect'])

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

    # pygame.display.flip() # 描画はメインループの最後で行うため削除

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


# --- メインのゲームループ ---  # 最終的に動かすのはここ
clock = pygame.time.Clock() # mainループの外で一度だけ初期化

running = True
while running:

    # ゲームの状態更新
    if game_state == GAME_STATE_PLAYING:  # プレイ画面ならば
        check_game_start() # 音楽再生とゲーム開始のチェック (game_start_timeが0の場合のみ)
        generate_notes() # 譜面からノーツを生成
        update_notes_position() # ノーツの移動と判定外れチェック
        update_timers() # 各種タイマーの更新
        check_game_over() # HPが0になったらゲームオーバーにする最終チェック
        check_game_finish() # ゲーム終了判定（音楽終了＆ノーツ枯渇）

    # 描画
    screen.fill(BLACK) # 毎フレーム画面をクリア

    if game_state == GAME_STATE_MENU:  # メニュー画面ならば
        draw_menu_screen()
    elif game_state == GAME_STATE_PLAYING:  # プレイ画面ならば
        draw_background() # 背景とレーン枠、判定ライン、キーの描画
        draw_notes() # ノーツの描画
        draw_info_panel() # スコア、コンボ、HPバーなどの描画
        draw_judgement_message() # 判定メッセージの描画
    elif game_state == GAME_STATE_GAME_OVER:  # ゲームオーバー画面ならば
        draw_game_over_screen() # ゲームオーバー画面の描画 (背景はdraw_backgroundでBLACKになる)

    for event in pygame.event.get():
        running = handle_quit_event(event) # QUITイベントを処理  # pygameが動いているかどうか動いていなかったら→False
        if not running:
            break  # Falseの時終了

        if game_state == GAME_STATE_MENU:
            handle_menu_input(event)  # ゲーム開始時の選択画面関連の関数
        elif game_state == GAME_STATE_PLAYING:  # プレイ画面ならば
            if event.type == pygame.KEYDOWN:  
                if event.key in lane_keys:  # 押したキーがa,s,d,f
                    held_keys.add(event.key)  # 押したキーを集合に追加
                process_key_press(event) # キー入力処理
            # *** KEYUP追加
            if event.type==pygame.KEYUP:
                if event.key in held_keys:  #  離したキーがa,s,d,f
                    held_keys.remove(event.key)  # 押したキーを集合から消す

        elif game_state == GAME_STATE_GAME_OVER:
            handle_game_over_input(event)
    
      # ノーツの判定　長押し対応
    for key in held_keys:
        for note in notes:  # 譜面をひとつづつ取り出す
            # print(note) 確認用
            if note['lane'] == pressed_lane_idx and not note['hit']:  #note['lane']にレーンの数字
                # ノーツが判定ラインの中心からどれだけ離れているか
                distance = abs(note['rect'].centery - JUDGEMENT_LINE_Y) # ** 自身のcente_diffと同じ
                press_rect = pressing_notes[key].rect  
                note_rect = note['rect']  
                  # print(note_rect)  # 確認用　常に回っている
                # ***衝突colliderect
                if press_rect.colliderect(note_rect):  

                    # 判定強化中のPERFECT判定 (GOOD判定の範囲内であればPERFECTに昇格)
                    if judgement_boost_active and distance <= JUDGEMENT_WINDOW_GOOD:
                        judgement_message = "PERFECT! (Boosted)"
                        judgement_color = GREEN
                        lane_effects[pressed_lane_idx] = GREEN # エフェクト色をPERFECTに設定
                        score += 100
                        combo += 1
                        max_combo = max(max_combo, combo)
                        notes.remove(note)
                        note['hit'] = True # 処理済みとしてマーク
                        hit_found = True
                        miss_invalid_time=time.time()  # ロングノーツ判定用で現在の時間を取る
                        #break
                    # 通常のPERFECT判定
                    elif distance <= JUDGEMENT_WINDOW_PERFECT:  # ノーツとの差が15
                        judgement_message = "PERFECT!"
                        judgement_color = GREEN
                        lane_effects[pressed_lane_idx] = GREEN # エフェクト色をPERFECTに設定
                        score += 100
                        combo += 1
                        max_combo = max(max_combo, combo)
                        notes.remove(note)
                        note['hit'] = True
                        hit_found = True
                        miss_invalid_time=time.time()  # # ロングノーツ判定用で現在の時間を取る
                        #break
                    # GOOD判定
                    elif distance <= JUDGEMENT_WINDOW_GOOD:  # ノーツとの差が30
                        judgement_message = "GOOD!"
                        judgement_color = YELLOW
                        lane_effects[pressed_lane_idx] = YELLOW # エフェクト色をGOODに設定
                        score += 50 # GOODで入るスコア
                        combo += 1
                        max_combo = max(max_combo, combo)
                        notes.remove(note)
                        note['hit'] = True
                        hit_found = True
                        miss_invalid_time=time.time()  #  # ロングノーツ判定用で現在の時間を取る
                        #break

                else:
                # MISS（接触していない場合）
                    # print(f"{note_rect.centery} - {press_rect.centery}={distance}")
                    if time.time()-miss_invalid_time >0.2:  # 他の判定がされてからmissが表示されないための時間
                        #print(time.time()-miss_invalid_time) #確認用 動いてはいる
                        judgement_message = "MISS!"
                        judgement_color = (255, 0, 0)
                        combo = 0
                        judgement_effect_timer = 30

    # 長押し中のノーツ表示
    for key in held_keys:
        if key in pressing_notes:
            # print(f"キー: {key}, Rect: {pressing_notes[key].rect}")  # ← デバッグ出力
            pressing_notes[key].update(screen)

    # 画面の更新とフレームレート固定
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit() 