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
import os

# 初期化
pygame.init()
pygame.mixer.init()

# --- 定数と初期設定 ---
# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# ★タイトル名を「君もシャイニングマスターの道へ」に設定
pygame.display.set_caption("君もシャイニングマスターの道へ")

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255) # 判定強化表示用
YELLOW = (255, 255, 0) # フィーバー時のコンボ色 (コンボ表示用なのでそのまま)
BLUE = (0, 0, 255) # メニュー選択肢用

# フォントの設定
# 日本語フォントのパスを自動で探す試み。環境に合わせて調整してください。
font_path = None
try:
    if sys.platform.startswith('win'): # Windows
        potential_font_paths = [
            "C:/Windows/Fonts/YuGothM.ttc", # 游ゴシック Medium
            "C:/Windows/Fonts/meiryo.ttc",   # メイリオ
            "C:/Windows/Fonts/msgothic.ttc"  # MS ゴシック
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

# 実際のフォント初期化
font = pygame.font.Font(font_path, 48)
large_font = pygame.font.Font(font_path, 72) # メニュータイトル用
small_font = pygame.font.Font(font_path, 36)

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
JUDGEMENT_WINDOW = 30 # 通常のPERFECT/GOOD判定の許容範囲

# ノーツが画面上端から判定ラインまで落ちるのにかかる時間 (ミリ秒)
# 60FPSを想定して計算
FALL_TIME_MS = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED * (1000 / 60)

# 各レーンに対応するキーとレーンインデックス (キー入力判定用)
lane_keys_input_map = {
    pygame.K_d: {"lane_idx": 0}, # Dキーは0番目のレーン
    pygame.K_f: {"lane_idx": 1}, # Fキーは1番目のレーン
    pygame.K_j: {"lane_idx": 2}, # Jキーは2番目のレーン
    pygame.K_k: {"lane_idx": 3}  # Kキーは3番目のレーン
}
# # キー定義
# lane_keys = {
#     pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
#     pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
#     pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
#     pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
# }
# key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys_input_map.items()}

# 各レーンに対応する色をリストで定義 (描画用)。レーンインデックスと色が確実に一致する！
lane_colors = [
    (255, 100, 100), # レーン0 (Dキー) の色
    (100, 255, 100), # レーン1 (Fキー) の色
    (100, 100, 255), # レーン2 (Jキー) の色
    (255, 255, 100)  # レーン3 (Kキー) の色
]

lane_idx_to_key_char = {0: 'D', 1: 'F', 2: 'J', 3: 'K'} # 表示文字も変更

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

# --- ゲームの状態を管理するEnum (または定数) ---
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

# --- グローバル変数 (ゲームの状態を保持) ---
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
FEVER_COMBO_THRESHOLD = 10 # フィーバーが発動するコンボ数
fever_active = False # フィーバーが現在有効か (コンボ数で継続)
fever_flash_color_timer = 0 # 色を点滅させるためのタイマー (今回は背景には使わないが、他の用途のために残しておく)
FEVER_FLASH_INTERVAL = 120 # (今回は背景には使わないが、他の用途のために残しておく)

# フィーバー時の背景色 (めちゃ薄い黄色)
FEVER_BACKGROUND_COLOR = (40, 40, 0) # 黒に近い、ごく薄い黄土色 (R, G, B)

judgement_effect_timer = 0
judgement_message = ""
judgement_color = WHITE

beatmap_index = 0
notes = [] # 現在画面に表示されているノーツのリスト

# ゲーム状態の初期値はメニュー
game_state = GAME_STATE_MENU
game_start_time = 0

# --- ファイル読み込み処理 (関数化) ---
def load_beatmap(path: str) -> list[list[int]]:
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
BEATMAP = load_beatmap(BEATMAP_FULL_PATH)
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

    score = 0
    combo = 0
    max_combo = 0
    current_hp = MAX_HP
    notes.clear()
    beatmap_index = 0
    game_state = GAME_STATE_PLAYING # ゲーム開始状態に設定
    game_start_time = 0
    judgement_effect_timer = 0
    judgement_message = ""
    judgement_color = WHITE
    judgement_boost_active = activate_boost_initially # ここで初期設定を適用
    judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES if activate_boost_initially else 0
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

def handle_menu_input(event: pygame.event.Event) -> None:
    """メニュー画面でのキー入力を処理します。"""
    global game_state, judgement_boost_active

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_1: # Start without Judgment Boost
            judgement_boost_active = False
            reset_game_state(activate_boost_initially=False)
        elif event.key == pygame.K_2: # Start with Judgment Boost
            judgement_boost_active = True
            reset_game_state(activate_boost_initially=True)

def handle_game_over_input(event: pygame.event.Event) -> None:
    """
    ゲームオーバー時にRキーが押された際のリスタート処理を行います。
    """
    global game_state
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
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
    global notes

    # Process key input only if the game is in PLAYING state
    if game_state == GAME_STATE_PLAYING and event.key in lane_keys_input_map:
        pressed_lane_idx = key_to_lane_idx[event.key]
        hit_found = False
        # Judge from the closest note first
        for note in reversed(notes):
            if note['lane'] == pressed_lane_idx and not note['hit']:
                # Check if the note is within the judgment window (GOOD or better)
                if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                    score += 100
                    combo += 1
                    max_combo = max(max_combo, combo)
                    notes.remove(note) # Remove the judged note
                    
                    # If judgment boost is active, or within regular PERFECT range, make it PERFECT
                    # Regular PERFECT range is JUDGEMENT_WINDOW / 2
                    if judgement_boost_active or abs(note['rect'].centery - JUDGEMENT_LINE_Y) < (JUDGEMENT_WINDOW / 2):
                        judgement_message = "PERFECT!"
                    else:
                        judgement_message = "GOOD!"
                    
                    judgement_color = GREEN
                    judgement_effect_timer = 30
                    hit_found = True
                    
                    # Recover HP if combo is a multiple of 3
                    if combo > 0 and combo % 3 == 0:
                        hp_recovered = min(10, MAX_HP - current_hp)
                        current_hp += hp_recovered
                        if hp_recovered > 0:
                            judgement_message += f" (+{hp_recovered} HP!)"
                    
                    # Check for Judgment Boost activation
                    if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                        judgement_boost_active = True
                        judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                        judgement_message += " (BOOST!)" # Add BOOST activation message
                    
                    # Check for Fever activation (activate when combo reaches threshold)
                    if combo >= FEVER_COMBO_THRESHOLD:
                        if not fever_active: # Only reset timer the first time entering fever
                            fever_flash_color_timer = FEVER_FLASH_INTERVAL
                        fever_active = True
                    
                    break # Exit loop once a hit is found for this lane
                
        if not hit_found: # If a key was pressed but no valid note was hit (MISS)
            combo = 0 # Reset combo
            judgement_message = "MISS!"
            judgement_color = RED
            judgement_effect_timer = 30
            current_hp -= HP_LOSS_PER_MISS # Decrease HP
            check_game_over() # Call HP check and game over judgment
            
            # Deactivate Fever if combo is reset
            fever_active = False
            fever_flash_color_timer = 0


# --- ゲーム状態更新の関数群 ---
def check_game_start() -> None:
    """ゲーム開始条件をチェックし、ゲームを開始します。音楽の再生も行います。"""
    global game_start_time
    # 音楽がロードされており、まだゲームが開始されていない場合、かつゲームオーバーでない
    if game_state == GAME_STATE_PLAYING and pygame.mixer.get_init() and BEATMAP:
        if not pygame.mixer.music.get_busy(): # 音楽が再生中でない場合のみ開始
            pygame.mixer.music.play()
            game_start_time = time.time()

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
            
            notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
            
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
                    judgement_message += " (BOOST!)" # Add BOOST activation message
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

    # フィーバー演出の点滅タイマーを更新 (背景色には影響しないが、他の要素で使う可能性を考慮して残す)
    if fever_active:
        fever_flash_color_timer -= 1
        if fever_flash_color_timer <= 0:
            fever_flash_color_timer = FEVER_FLASH_INTERVAL

    # 判定メッセージ表示タイマーの更新
    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

def check_game_over() -> None:
    """HPが0以下になった場合にゲームオーバー状態を設定し、音楽を停止します。"""
    global current_hp, game_state
    if current_hp <= 0:
        current_hp = 0
        game_state = GAME_STATE_GAME_OVER
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

# --- 描画処理の関数群 ---
def draw_background() -> None:
    """ゲームの背景（レーン枠、判定ライン、対応キー）を描画します。フィーバー中は背景色を特別な色にします。"""
    if fever_active and game_state == GAME_STATE_PLAYING: # プレイ中のみフィーバー背景
        screen.fill(FEVER_BACKGROUND_COLOR) # フィーバー中はごく薄い黄色の背景
    else:
        screen.fill(BLACK) # 通常の背景は黒

    if game_state == GAME_STATE_PLAYING: # プレイ中のみレーン等を描画
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
    if game_state == GAME_STATE_PLAYING and judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)
    
def draw_game_over_screen() -> None:
    """ゲームオーバー時の画面（メッセージ、最終スコア、リスタート指示）を描画します。"""
    if game_state == GAME_STATE_GAME_OVER:
        game_over_text = large_font.render("GAME OVER!", True, RED)
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

    # ここでフォントサイズを調整！両方の行に 'font' (48pt) を使用
    rendered_line1 = font.render(line1_text, True, WHITE)
    rendered_line2 = small_font.render(line2_text, True, WHITE) 

    # 画面中央より少し上に配置
    # y_pos の値を調整して、文字の垂直位置と行間をコントロールします
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
running = True
clock = pygame.time.Clock()

while running:
    # イベント処理
    for event in pygame.event.get():
        running = handle_quit_event(event) # QUITイベントを処理

        if game_state == GAME_STATE_MENU:
            handle_menu_input(event)
        elif game_state == GAME_STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                process_key_press(event) # キー入力処理
        elif game_state == GAME_STATE_GAME_OVER:
            handle_game_over_input(event)

    # ゲームの状態更新
    if game_state == GAME_STATE_PLAYING:
        check_game_start() # 音楽再生とゲーム開始のチェック
        generate_notes() # 譜面からノーツを生成
        update_notes_position() # ノーツの移動と判定外れチェック
        update_timers() # 各種タイマーの更新
        check_game_over() # HPが0になったらゲームオーバーにする最終チェック

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
        draw_game_over_screen() # ゲームオーバー画面の描画 (背景はdraw_backgroundでBLACKになる)

    # 画面の更新とフレームレート固定
    pygame.display.flip()
    clock.tick(60)

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

"""----------------------------------------------------------------------------------------------------"""
# # 譜面読み込み
# BEATMAP_FILE = 'beatmap.csv'
# try:
#     with open(BEATMAP_FILE, 'r') as f:
#         reader = csv.reader(f)
#         BEATMAP = [[int(row[0]), int(row[1])] for row in reader]
# except FileNotFoundError:
#     print("Error: beatmap.csv not found.")
#     pygame.quit()
#     sys.exit()

# # -------- Scene 基底クラス --------
# class Scene:
#     """
#     各画面での基底クラス定義
#     操作に応じて実行
#     状態の更新
#     画面の更新
#     """
#     def handle_events(self, events): pass
#     def update(self): pass
#     def draw(self): pass

# # -------- タイトル画面 --------
# class TitleScene(Scene):
#     """
#     タイトル画面を表示
#     spaceキーでPlayScene(プレイ中の画面)に移動
#     """

#     def __init__(self, game):
#         self.game = game

#     def handle_events(self, events):

#         for event in events:
#             if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
#                 self.game.change_scene(PlayScene(self.game))

#     def draw(self):
#         screen.fill(BLACK)
#         text = font.render("Press SPACE to Start", True, WHITE)
#         screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

# # -------- リザルト画面 --------
# class ResultScene(Scene):
#     """
#     リザルトの表示
#     Ｒキーでタイトル画面に移動
#     """
#     def __init__(self, game):
#         self.game = game

#     def handle_events(self, events):
#         for event in events:
#             if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
#                 self.game.change_scene(TitleScene(self.game))

#     def draw(self):
#         if self.game.notes_count == 0:
#             self.game.notes_count = 1  # ゼロ割り防止（0%表示）
#         else:
#             self.notes_count = self.game.notes_count
#         screen.fill(BLACK)
#         screen.blit(font.render("RESULT", True, WHITE), (300, 100))
#         screen.blit(font.render(f"Score: {self.game.score}", True, WHITE), (300, 200))
#         screen.blit(font.render(f"Max Combo: {self.game.max_combo}", True, WHITE), (300, 250))
#         screen.blit(font.render(f"Perfect: {self.game.perfect} , {self.game.perfect*100//self.game.notes_count}%", True, WHITE), (300, 300))
#         screen.blit(font.render(f"Good FAST : {self.game.good_fast} , {self.game.good_fast*100//self.game.notes_count}%", True, WHITE), (300, 350))
#         screen.blit(font.render(f"Good LATE : {self.game.good_late} , {self.game.good_late*100//self.game.notes_count}%", True, WHITE), (300, 400))
#         screen.blit(font.render(f"Miss : {self.game.miss} , {self.game.miss*100//self.game.notes_count}%", True, WHITE), (300, 450))
#         screen.blit(small_font.render("Press R to Restart", True, WHITE), (250, 500))

# # -------- プレイ画面 --------
# class PlayScene(Scene):
#     """
#     キーが押されたとき、ジャッジラインから±15px 以内でperfect、15px ～ 30px の範囲でgood、それ以上ズレるか、判定タイミングを過ぎるとmiss
#     ノーツがすべて生成され、画面からノーツがなくなったら曲を止めリザルト画面へ移動
#     """
#     def __init__(self, game):
#         self.game = game
#         self.game.reset_score()  # ゲーム開始時にスコア関連を初期化
#         self.notes = []
#         self.beatmap_index = 0
#         self.start_time = time.time()
#         self.judgement_message = ""
#         self.judgement_color = WHITE
#         self.judgement_effect_timer = 0
#         pygame.mixer.music.load('maou_short_14_shining_star.mp3')
#         pygame.mixer.music.play()

#     def handle_events(self, events):
#         for event in events:
#             if event.type == pygame.KEYDOWN and event.key in key_to_lane_idx:
#                 lane = key_to_lane_idx[event.key]
#                 for note in self.notes[:]:
#                     if note['lane'] == lane and abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
#                         self.notes.remove(note)
#                         self.game.score += 100
#                         self.game.combo += 1
#                         if  self.game.combo > self.game.max_combo:
#                             self.game.max_combo = self.game.combo
#                         if abs(note['rect'].centery - JUDGEMENT_LINE_Y) <= JUDGEMENT_WINDOW / 2:
#                             self.judgement_message = "PERFECT!"
#                             self.game.perfect += 1
#                             self.game.notes_count += 1
#                         elif abs(note['rect'].centery - JUDGEMENT_LINE_Y) > JUDGEMENT_WINDOW / 2:
#                             if note['rect'].centery < JUDGEMENT_LINE_Y:
#                                 self.judgement_message = "GOOD FAST"
#                                 self.game.good_fast += 1
#                                 self.game.notes_count += 1
#                             else :
#                                 self.judgement_message = "GOOD LATE"
#                                 self.game.good_late += 1
#                                 self.game.notes_count += 1
#                         self.judgement_color = GREEN
#                         self.judgement_effect_timer = 30
#                         self.hit_found = True
#                         break

#     def update(self):
#         current_time = (time.time() - self.start_time) * 1000
#         while self.beatmap_index < len(BEATMAP) and current_time >= BEATMAP[self.beatmap_index][0]:
#             lane = BEATMAP[self.beatmap_index][1]
#             x = LANE_SPACING + lane * (LANE_WIDTH + LANE_SPACING)
#             y = -NOTE_HEIGHT - (JUDGEMENT_LINE_Y + NOTE_HEIGHT)
#             rect = pygame.Rect(x, y, LANE_WIDTH, NOTE_HEIGHT)
#             self.notes.append({'rect': rect, 'lane': lane})
#             self.beatmap_index += 1

#         for note in self.notes[:]:
#             note['rect'].y += NOTE_SPEED
#             if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW:
#                 self.notes.remove(note)
#                 self.game.combo = 0
#                 self.game.miss += 1  # Miss数を加算
#                 self.game.notes_count += 1  # 総ノーツ数にもカウント
#                 self.judgement_message = "MISS"
#                 self.judgement_color = RED
#                 self.judgement_effect_timer = 30

#         if self.beatmap_index >= len(BEATMAP) and not self.notes:
#             pygame.mixer.music.stop()
#             self.game.change_scene(ResultScene(self.game))
        
        
#     def draw(self):
#         screen.fill(BLACK)
#         for i in range(LANE_COUNT):
#             x = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
#             pygame.draw.rect(screen, GRAY, (x, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)
#             key_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
#             screen.blit(key_text, (x + (LANE_WIDTH - key_text.get_width()) // 2, JUDGEMENT_LINE_Y + 40))
#         pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

#         for note in self.notes:
#             color = lane_keys[list(lane_keys.keys())[note['lane']]]['color']
#             pygame.draw.rect(screen, color, note['rect'])

#         # 画面左上にスコアとコンボ数を表示
#         screen.blit(font.render(f"Score: {self.game.score}", True, WHITE), (10, 10))
#         screen.blit(font.render(f"Combo: {self.game.combo}", True, WHITE), (10, 60))

#         # 判定エフェクトタイマーがあるときエフェクトを表示
#         if self.judgement_effect_timer > 0:
#             self.judgement_display = font.render(self.judgement_message, True, self.judgement_color)
#             self.judgement_rect = self.judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
#             screen.blit(self.judgement_display, self.judgement_rect)
#             self.judgement_effect_timer -= 1

# # -------- ゲーム本体 --------
# class Game:
#     def __init__(self):
#         self.clock = pygame.time.Clock()
#         self.score = 0
#         self.combo = 0
#         self.max_combo = 0
#         self.perfect = 0
#         self.good_fast = 0
#         self.good_late = 0
#         self.miss = 0
#         self.notes_count = self.perfect+self.good_fast+self.good_late+self.miss
#         self.current_scene = TitleScene(self)
    
#     def reset_score(self):
#         self.score = 0
#         self.combo = 0
#         self.max_combo = 0
#         self.perfect = 0
#         self.good_fast = 0
#         self.good_late = 0
#         self.miss = 0
#         self.notes_count = 0

#     def change_scene(self, new_scene):
#         self.current_scene = new_scene

#     def run(self):
#         running = True
#         while running:
#             events = pygame.event.get()
#             for event in events:
#                 if event.type == pygame.QUIT:
#                     running = False

#             self.current_scene.handle_events(events)
#             self.current_scene.update()
#             self.current_scene.draw()
#             pygame.display.flip()
#             self.clock.tick(60)

#         pygame.quit()

# # -------- 起動 --------
# if __name__ == "__main__":
#     Game().run()
