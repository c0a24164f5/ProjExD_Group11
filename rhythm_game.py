import pygame
import csv # 譜面ファイルの読み込み用
import time # ゲーム開始時間の記録用
import sys


# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # screenの設定
pygame.display.set_caption("My Rhythm Game")


# ゲーム設定
LANE_COUNT = 4
LANE_WIDTH = 100  # ノーツの横幅
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)
NOTE_SPEED = 5
NOTE_HEIGHT = 20  # ノーツの高さ
# NOTE_HEIGHT = 0  # ノーツの高さ
JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30


# class Long_note:
#     def __init__(self,x,y,width, height, color):  
#         # pygame.draw.rect(self.image, (100, 100, 100), (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)  # 判定用の四角 (左上のｘ座標、左上のｙ座標、横幅、縦の幅) 最後の数字は長方形の線の幅（ピクセル単位）
#         # self.rect = self.image.get_rect()  # 判定用のrect
#         # self.rect.centery =  500
#         self.image = pygame.Rect(x, y, width, height)
#         self.rect = self.image.get_rect()  # 判定用のrect
#         self.color = color
#         #screen.blit(self.image, self.rect)
#     def update(self, screen: pygame.Surface):
#         # screen.blit(self.image, self.rect)
#         pygame.draw.rect(screen, self.color, self.rect)
#         screen.blit(self.image,self.rect)
#         print("動いた")
#         ## 灰色の塗りつぶされた長方形で判定領域を描画
#         #pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)


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

    def update(self, screen: pygame.Surface):
        """
        引数:画面screen
        画面screenに四角を描画
        """
        pygame.draw.rect(screen, self.color, self.rect)
        #print("update called")  # ← 呼ばれているか確認　デバッグ
        #time.sleep(0.000000001)
        

def main ():
    # Pygameの初期化
    pygame.init()

    # 画面設定
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # screenの設定
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

    # # ゲーム設定
    # LANE_COUNT = 4
    # LANE_WIDTH = 100  # ノーツの横幅
    # LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)
    # NOTE_SPEED = 5
    # #NOTE_HEIGHT = 20  # ノーツの高さ
    # NOTE_HEIGHT = 0  # ノーツの高さ
    # JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
    # JUDGEMENT_WINDOW = 30

    # 各レーンに対応するキーと色、表示用の文字
    lane_keys = {
        pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
        pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
        pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
        pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
    }
    key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys.items()}  # dcit.items()で中身が取り出せる
      # print(key_to_lane_idx) # 確認用 
      # print(key_to_lane_idx[97])   # 押されたキーをkey_to_lane_idx[押されたキー]とるとlane_idxが得られる
    lane_idx_to_key_char = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

    held_keys = set()  # 「今、どのキーが押され続けているか」を記録するための変数
    pressing_notes = {}  # 辞書
    for key, data in lane_keys.items():  # dcit.items()で中身が取り出せる  key = pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f
        # print(key,data) # {key=キー押されたら(int):{レーンの番号:色}} 確認用
        lane_idx = data["lane_idx"]  # a,s,d,fに対応したレーン番号
        #color = data["color"]  # a,s,d,fに対応した色
        color = (100, 100, 100)  # 灰色
        lane_x = LANE_SPACING + lane_idx * (LANE_WIDTH + LANE_SPACING)  # a,s,d,fに対応したレーンに表示するx座標
        pressing_notes[key] = Long_note(lane_x, JUDGEMENT_LINE_Y -5, LANE_WIDTH, 10, color)  # a,s,d,fのキーを押したときのLong_note()の辞書ができる

    # --- ▼▼▼ ここからが大きな変更点 ▼▼▼ ---

    # 譜面ファイルの読み込み
    BEATMAP_FILE = 'beatmap.csv'  # create_beatmap.py
    BEATMAP = []
    try:
        with open(BEATMAP_FILE, 'r') as f:
            reader = csv.reader(f)  # beatmap.csvを読み込む 
            # [ヒットすべき時間(ms), レーン番号] のリストを作成
            BEATMAP = [[int(row[0]), int(row[1])] for row in reader]  # リスト作成[[beatmap.csvにある時刻の数字,ノーツを表示するレーン番号]]　beatmap.csvに[時刻の数字,ノーツを表示するレーン番号]がリストである
    except FileNotFoundError:
        print(f"エラー: '{BEATMAP_FILE}' が見つかりません。")
        print("先に 'create_beatmap.py' を実行して譜面ファイルを作成してください。")
        pygame.quit()
        sys.exit()

    beatmap_index = 0 # 次に生成すべきノーツのインデックス 生成するノーツの番号

    # ノーツのリスト
    notes = []

    # スコアとコンボ
    score = 0
    combo = 0
    max_combo = 0

    # 判定エフェクトの表示設定
    judgement_effect_timer = 0
    judgement_message = ""
    judgement_color = WHITE

    # 音楽のロードと再生
    try:
        pygame.mixer.music.load('./ProjExD/maou_short_14_shining_star.mp3')
    except pygame.error:
        print("警告: 音楽ファイルをロードできませんでした。")

    # ゲームループのフラグとクロック
    running = True
    clock = pygame.time.Clock()  # fps
    game_started = False
    game_start_time = 0  # ゲーム開始時の時刻を代入する用

    miss_invalid_time=0  # miss無効時間

    # -------- メインのゲームループ --------
    while running:
        if not game_started and BEATMAP:
            # 最初のノーツがあればゲームを開始
            pygame.mixer.music.play()
            game_start_time = time.time()  # time.time():現在の時刻を取得
            game_started = True

        # --- 1. イベント処理 ---
        # key_list=pygame.key.get_pressed()  # pg.key.get_pressed()で押されている間
        for event in pygame.event.get():
        
            # if key_list[pygame.K_a]:  # 長押し  四角を対応した場所に出す→かぶっていたらノーツを消してスコアアップ
            #     print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            #     # classのLong_noteインスタンス生成
            #     long_note.update(screen) 
            #     #long_note.update(screen)
            #     #pygame.draw.rect(screen)
            #     #pygame.display.update()  # ディスプレイのアップデート 
            # if key_list[pygame.K_s]:
            #     print("ssssssssssssssssssssssssssssssss")
            # if key_list[pygame.K_d]:
            #     print("dddddddddddddddddddddddddddddddd")
            # if key_list[pygame.K_f]:
            #     print("ffffffffffffffffffffffffffffffff")

            # if event.type == pygame.QUIT:
            #     running = False
            #    if event.type == pygame.KEYDOWN:  # キーを押したとき
            #     if key_list[pygame.K_a]:
            #         print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
            #     if key_list[pygame.K_s]:
            #         print("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
            #     if key_list[pygame.K_d]:
            #         print("dddddddddddddddddddddddddddddddd")
            #     if key_list[pygame.K_f]:
            #         print("ffffffffffffffffffffffffffffffff")
            if event.type == pygame.QUIT:
                running = False

            #''''''''''' KEYDOWNでセットに追加 '''''''''''
            elif event.type == pygame.KEYDOWN:
                if event.key in lane_keys:  # 押したキーがa,s,d,f
                    held_keys.add(event.key)  # 押したキーを集合に追加

            #''''''''''' KEYUPでセットから削除 '''''''''''
            elif event.type == pygame.KEYUP:
                if event.key in held_keys:  #  離したキーがa,s,d,f
                    held_keys.remove(event.key)  # 押したキーを集合から消す

                    # if event.key in lane_keys:  # a,s,d,fキーを押したとき
                    #     for event in pygame.event.get():
                    #         if event.type == pygame.QUIT:
                    #             running = False
                    #     pressed_lane_idx = key_to_lane_idx[event.key]
                    #     hit_found = False
                    #     for note in notes[:]:  # notes[:]:notesのコピー なくても動きそう notes[]内のノーツを一つずつ取り出して判定を出している
                    #         if note['lane'] == pressed_lane_idx and not note['hit']:
                    #             if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:  # abs():絶対値 162行目でnotes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
                    #                 score += 100
                    #                 combo += 1
                    #                 max_combo = max(max_combo, combo)
                    #                 #print(f"note:{note}")
                    #                 #print(f"note['rect']:{note['rect']}")
                    #                 notes.remove(note)
                    #                 if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW / 2:
                    #                     judgement_message = "PERFECT!"  # PERFECT!の時
                    #             else:
                    #                 judgement_message = "GOOD!"
                    #                 judgement_color = GREEN
                    #                 judgement_effect_timer = 30
                    #                 hit_found = True
                    #                 break
                    # if not hit_found:
                    #     combo = 0
                    #     judgement_message = "MISS!"
                    #     judgement_color = RED
                    #     judgement_effect_timer = 30

        # --- 2. ゲームの状態更新 ---

        # 【変更点】ランダム生成の代わりに譜面からノーツを生成
        if game_started:
            current_game_time_ms = (time.time() - game_start_time) * 1000 # (現在の時刻-ゲーム開始の時刻)*1000

            # 譜面の最後までチェック
            # beatmap_indexは参照するノーツの番号の変数
            while beatmap_index < len(BEATMAP) and current_game_time_ms >= BEATMAP[beatmap_index][0]:  # 生成するノーツの数がbeatmap.scvにある数より少ない and (現在の時刻-ゲーム開始の時刻)*1000がbeatmap.csvにある時刻以上
                # if beatmap_index < len(BEATMAP)-1: 
                    # if  BEATMAP[beatmap_index][1]==BEATMAP[beatmap_index+1][1]:  # 次のノーツが同じ時ロングノーツに
                    #     # print("ろんぐ") #ロング確認用
                    #     note_data_1 = BEATMAP[beatmap_index]  # [[beatmap.csvにある時刻の数字,ノーツを表示するレーン番号]] 
                    #     note_data_2 = BEATMAP[beatmap_index+1] 
                    #     target_time_ms = note_data_2[0]-note_data_1[0]   # beatmap.csvにある時刻の数字
                    #     if  target_time_ms<=40:

                    #         #print(f"{note_data_2[0]}-{note_data_1[0]}={note_data_2[0]-note_data_1[0]}")  # 確認用
                    #         target_lane = note_data_1[1]   # beatmap.csvにあるノーツを表示するレーン番号
                    #         NOTE_HEIGHT = (note_data_1[0]-note_data_2[1]) /10# ノーツの高さ(ロング) 次のノーツを削除してその長さにしたい 10で÷とちょうどよさそう
                    #         #print(f"NOTE_HEIGHT:{NOTE_HEIGHT}")
                    #     # print(key_to_lane_idx)  # なんか色々と確認用

                       
                note_data = BEATMAP[beatmap_index]  # [[beatmap.csvにある時刻の数字,ノーツを表示するレーン番号]] 
                target_time_ms = note_data[0]  # beatmap.csvにある時刻の数字  
                # print(f"target_time_ms {target_time_ms },current_game_time_ms={current_game_time_ms},current_game_time_ms-target_time_ms={current_game_time_ms-target_time_ms}")  # miss無効時間
                target_lane = note_data[1]   # beatmap.csvにあるノーツを表示するレーン番号
                #NOTE_HEIGHT = 20  # ノーツの高さ

                # 新しいノーツを作成
                lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)  
                new_note_rect = pygame.Rect(lane_x_start, -NOTE_HEIGHT, LANE_WIDTH, NOTE_HEIGHT)  # 押された時間に合わせてノーツの高さ(NOTE_HEIGHT)を変更できるように
                # Y座標を調整：判定ラインから逆算して、正しいタイミングでラインに到達するようにする
                # (移動フレーム数 = 距離 / 速度)
                frames_to_travel = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED
                # 予めそのフレーム数分だけ上に配置しておく
                new_note_rect.y -= frames_to_travel * NOTE_SPEED
                
                notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
                
                beatmap_index += 1 # 次のノーツへ

        # ノーツの移動と判定外れチェック
        for note in notes[:]:   # notes[:]:notesのコピー なくても動きそう notes[]内のノーツを一つずつ取り出して判定を出している
            note['rect'].y += NOTE_SPEED  # notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
            #print(f"note['rect'].y={note['rect'].y}")
        for key in held_keys:
            if key in pressing_notes:
                pressing_notes[key].update(screen)

                for note in notes[:]:
                    if note['lane'] == key_to_lane_idx[key] and not note['hit']:  
                        press_rect = pressing_notes[key].rect
                        note_rect = note['rect']
                        print(note_rect)
                        center_diff = abs(note_rect.centery - press_rect.centery)
                        #print(f"center_diff ={center_diff }")
                        if press_rect.colliderect(note_rect):
                            # center_diff = abs(note_rect.centery - press_rect.centery)
                            # print(f"center_diff ={center_diff }")

                            if center_diff < 40:
                                # print(f"{note_rect.centery} - {press_rect.centery}={center_diff}")
                                judgement_message = "PERFECT!"
                                judgement_color = (255, 255, 255)
                                score += 100
                                combo += 1
                                # print(f"target_time_ms {target_time_ms },current_game_time_ms={current_game_time_ms},current_game_time_ms-target_time_ms={current_game_time_ms-target_time_ms}")  # miss無効時間
                                miss_invalid_time=time.time()  # PERFECTが描画されてる時間
                            elif center_diff < 60:
                                judgement_message = "GOOD!"
                                judgement_color = (0, 255, 0)
                                score += 50
                                combo += 1
                                miss_invalid_time=time.time()  #　GOODが描画されてる時間
                            else:
                                judgement_message = "BAD!"
                                judgement_color = (100, 100, 255)
                                combo = 0
                                miss_invalid_time=time.time()  #　BADが描画されてる時間
                            note['hit'] = True
                            notes.remove(note)
                            judgement_effect_timer = 30
                            break
                        else:  # 下2桁が20の時のみロングノーツ
                            # MISS（接触していない場合）
                            # print(f"{note_rect.centery} - {press_rect.centery}={center_diff}")
                            if time.time()-miss_invalid_time >0.2:  # 他の判定がされてからmissが表示されないための時間
                                  # print(time.time()-miss_invalid_time) 確認用
                                judgement_message = "MISS!"
                                judgement_color = (255, 0, 0)
                                combo = 0
                                judgement_effect_timer = 30
                            
                                                       
                            # if center_diff>=800:
                            #     #print(f"{note_rect.centery} - {press_rect.centery}={center_diff}")
                            #     judgement_message = "MISS!"
                            #     judgement_color = (255, 0, 0)
                            #     combo = 0
                            #     judgement_effect_timer = 30
                    #     #衝突判定colliderect
                    if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW and not note['hit']:
                        notes.remove(note)
                        combo = 0
                        judgement_message = "TOO LATE!"
                        judgement_color = RED
                        judgement_effect_timer = 30
        # # --- 長押しキーとノーツとの衝突判定 ---
        # for key in held_keys: # held_keys:「今、どのキーが押され続けているか」を記録するための変数
        #     if key in pressing_notes:  # pressing_notes:a,s,d,fのキーを押したときのLong_note()の辞書
        #         pressing_rect = pressing_notes[key].rect  # 押されているキーのrect
        #         pressed_lane_idx = key_to_lane_idx[key]  # 押されているキーの番号
        #         # 長押し中に判定範囲にノーツが無い → MISS
        #         for key in held_keys:
        #             if key in pressing_notes:
        #                 pressing_notes[key].update(screen)

        #                 # 該当レーン番号
        #                 lane_idx = key_to_lane_idx[key]
        #                 hit_found = False

        #                 for note in notes:
        #                     if note['lane'] == lane_idx and not note['hit']:
        #                         if pressing_notes[key].rect.colliderect(note['rect']):
        #                             hit_found = True  # 接触してるのでセーフ
        #                             break
                        
        #                 if not hit_found:  # 一瞬でも離れたらmissになってしまう
        #                     combo = 0
        #                     judgement_message = "MISS! (Held too early)"
        #                     judgement_color = RED
        #                     judgement_effect_timer = 30

        #         for note in notes[:]:
        #             # 対応するレーンかつ未ヒット
        #             if note['lane'] == pressed_lane_idx and not note['hit']:
        #                 if pressing_rect.colliderect(note['rect']):
        #                     # 衝突していたらスコア処理など
        #                     score += 100
        #                     combo += 1
        #                     max_combo = max(max_combo, combo)
        #                     notes.remove(note)

        #                     #judgement_message = "HOLD HIT!"
        #                     judgement_message = "HIT!"
        #                     judgement_color = GREEN
        #                     judgement_effect_timer = 30
        #                     break  # 1つヒットしたらループ終了


        if judgement_effect_timer > 0:
            judgement_effect_timer -= 1

        # --- 3. 描画 ---
        screen.fill(BLACK)
        for i in range(LANE_COUNT):
            lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
            pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2)
            key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
            screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
        #pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0) # 元の文　ノーツを打つ場所の灰色
        pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, 10), 0)
        pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

        for note in notes:  # ノーツの描画
            pygame.draw.rect(screen, lane_keys[list(lane_keys.keys())[note['lane']]]['color'], note['rect'])

        score_text = font.render(f"Score: {score}", True, WHITE)
        combo_text = font.render(f"Combo: {combo}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(combo_text, (10, 50))

        if judgement_effect_timer > 0:
            judgement_display = font.render(judgement_message, True, judgement_color)
            judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
            screen.blit(judgement_display, judgement_rect)

        # 長押し中のノーツ表示
        for key in held_keys:
            if key in pressing_notes:
                #print(f"キー: {key}, Rect: {pressing_notes[key].rect}")  # ← デバッグ出力
                pressing_notes[key].update(screen)       

        #pygame.display.flip()
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    pygame.init()
    main()
    pygame.quit()
    sys.exit()