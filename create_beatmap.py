import pygame  # import pygame as pg にするとpgでも動くようになる
import sys
import time
import csv

#  譜面作成
# --- 設定 ---
# あなたのゲームで使うキー設定に合わせます
KEYS = {  # 辞書
    pygame.K_a: 0, # レーン0
    pygame.K_s: 1, # レーン1
    pygame.K_d: 2, # レーン2
    pygame.K_f: 3  # レーン3
}
SONG_FILE = './ProjExD/maou_short_14_shining_star.mp3'
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
recorded_notes = []  # ノーツを記録するリスト
print("音楽の再生を開始します。")
pygame.mixer.music.play()
start_time = time.time()
running = True  # 動いている間

while running:

    key_list=pygame.key.get_pressed()  # pg.key.get_pressed()で押されている間

    for event in pygame.event.get():  
        if key_list[pygame.K_a]:  # 長押しで連続に作成
              # print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") 確認用
            current_time_ms = int((time.time() - start_time)*1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
            lane_index = KEYS[pygame.K_a]  # 押されたキーから対応したレーンの番号を取り出す:
            recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン
        if key_list[pygame.K_s]:
              # print("ssssssssssssssssssssssssssssssss") 確認用
            current_time_ms = int((time.time() - start_time) * 1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
            lane_index = KEYS[pygame.K_s]  # 押されたキーから対応したレーンの番号を取り出す
            recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン
        if key_list[pygame.K_d]:
              # print("dddddddddddddddddddddddddddddddd") 確認用
            current_time_ms = int((time.time() - start_time) * 1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
            lane_index = KEYS[pygame.K_d]  # 押されたキーから対応したレーンの番号を取り出す
            recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン
        if key_list[pygame.K_f]:
              # print("ffffffffffffffffffffffffffffffff") 確認用
            current_time_ms = int((time.time() - start_time) * 1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
            lane_index = KEYS[pygame.K_f]  # 押されたキーから対応したレーンの番号を取り出す
            recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン

        if event.type == pygame.QUIT:
            running = False  # 押されていない間while文が実行されない
        # if event.type == pygame.KEYDOWN:  # キーが押されたとき pg.key.get_pressed()で押されている間
        #     #for i,key in enumerate(KEYS):  # for i,n in enumerate(): i=数,n=リスト内のもの  4つに変更
        #     if event.key in KEYS:  # KEYSに対応したキーが押されたならば KEYS[[対応したキーが押されてというイベント][レーン番号]]
        #         current_time_ms = int((time.time() - start_time) * 1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
        #         lane_index = KEYS[event.key]  # 押されたキーから対応したレーンの番号を取り出す
        #         recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン
        #         print(f"ノーツ記録: {current_time_ms}ms, レーン: {lane_index}")  # ターミナルに出力
        #         #if event.key == key:  # KEYSに対応したキーが押されたならば KEYS[[対応したキーが押されてというイベント][レーン番号]]
        #         print("すごい途中")
        #         #for key in (KEYS):  # for i,n in enumerate(): i=数,n=リスト内のもの
        #             #current_time_ms = int((time.time() - start_time) * 1000)  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
        #             #dafsdlane_index = KEYS[event.key]  # 押されたキーから対応したレーンの番号を取り出す
        #             # if key_list[key]:  # 対応しているキーが押されている時間を記録したい
        #             #     current_time_ms +=1000  # キーが押された瞬間の時間をミリ秒で記録 current_time_ms =(現在の時刻-ゲーム開始の時刻)*1000
        #             #     # lane_index = KEYS[event.key]  # 押されたキーから対応したレーンの番号を取り出す
        #             #     recorded_notes.append([current_time_ms, lane_index])  # ノーツを記録するリストに追加　押された時間(タイミング),レーン
        #             #     print(f"ノーツ記録: {current_time_ms}ms, レーン: {lane_index}")  # ターミナルに出力

    # 画面の描画
    screen.fill((0, 0, 0))
    time_text = font.render(f"Time: {int((time.time() - start_time) * 1000)} ms", True, (255, 255, 255))
    notes_text = font.render(f"Notes: {len(recorded_notes)}", True, (255, 255, 255))  # 追加したノーツの数を画面に表示
    screen.blit(time_text, (10, 10))
    screen.blit(notes_text, (10, 60))
    pygame.display.flip()

# --- 譜面の保存 ---
pygame.quit()  # 辞めたとき
if recorded_notes:
    # 時間順に並べ替えてから保存
    recorded_notes.sort(key=lambda x: x[0])  # lambda:無名関数 xを受け取りx[0]を返す 2番目の要素でソートする
    with open(OUTPUT_CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(recorded_notes)
    print(f"譜面を'{OUTPUT_CSV_FILE}'に保存しました。")
else:
    print("ノーツが記録されなかったので、ファイルは作成されませんでした。")
sys.exit()