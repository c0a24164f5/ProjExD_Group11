import pygame
import sys
import time
import csv

# --- 設定 ---
# あなたのゲームで使うキー設定に合わせます
KEYS = {
    pygame.K_a: 0, # レーン0
    pygame.K_s: 1, # レーン1
    pygame.K_d: 2, # レーン2
    pygame.K_f: 3  # レーン3
}
SONG_FILE = "ex5\maou_short_14_shining_star.mp3"
OUTPUT_CSV_FILE = 'beatmap.csv'

# --- Pygameの初期化 ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("譜面作成ツール: A, S, D, F を押して記録 (ウィンドウを閉じると保存)")
font = pygame.font.Font(None, 48)

# --- 音楽の読み込み ---
try:
    pygame.mixer.music.load(SONG_FILE)
except pygame.error as e:
    print(f"エラー: '{SONG_FILE}'が見つかりません。プログラムと同じフォルダにありますか？")
    sys.exit()

# --- メイン処理 ---
recorded_notes = []
print("音楽の再生を開始します。")
pygame.mixer.music.play()
start_time = time.time()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in KEYS:
                # キーが押された瞬間の時間をミリ秒で記録
                current_time_ms = int((time.time() - start_time) * 1000)
                lane_index = KEYS[event.key]
                recorded_notes.append([current_time_ms, lane_index])
                print(f"ノーツ記録: {current_time_ms}ms, レーン: {lane_index}")

    # 画面の描画
    screen.fill((0, 0, 0))
    time_text = font.render(f"Time: {int((time.time() - start_time) * 1000)} ms", True, (255, 255, 255))
    notes_text = font.render(f"Notes: {len(recorded_notes)}", True, (255, 255, 255))
    screen.blit(time_text, (10, 10))
    screen.blit(notes_text, (10, 60))
    pygame.display.flip()

# --- 譜面の保存 ---
pygame.quit()
if recorded_notes:
    # 時間順に並べ替えてから保存
    recorded_notes.sort(key=lambda x: x[0])
    with open(OUTPUT_CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(recorded_notes)
    print(f"譜面を'{OUTPUT_CSV_FILE}'に保存しました。")
else:
    print("ノーツが記録されなかったので、ファイルは作成されませんでした。")
sys.exit()