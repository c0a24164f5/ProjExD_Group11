import threading
import winsound

def play_beep(freq=600, dur=100):
    threading.Thread(target=winsound.Beep, args=(freq, dur), daemon=True).start()

import pygame
import csv
import time
import sys

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Rhythm Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)

font = pygame.font.Font(None, 48)
small_font = pygame.font.Font(None, 36)

LANE_COUNT = 4
LANE_WIDTH = 100
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)
NOTE_SPEED = 5
NOTE_HEIGHT = 20
JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30

lane_keys = {
    pygame.K_a: {"lane_idx": 0, "color": (255, 100, 100)},
    pygame.K_s: {"lane_idx": 1, "color": (100, 255, 100)},
    pygame.K_d: {"lane_idx": 2, "color": (100, 100, 255)},
    pygame.K_f: {"lane_idx": 3, "color": (255, 255, 100)}
}
key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys.items()}
lane_idx_to_key_char = {0: 'A', 1: 'S', 2: 'D', 3: 'F'}

# 効果音の再生
def play_sound(path):
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
    except pygame.error:
        print(f"効果音ファイル '{path}' を読み込めませんでした。")

# レーンごとの円形エフェクトを描画
def draw_lane_effect(screen, x_center, color, alpha=100, radius=50):
    s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(s, color + (alpha,), (x_center, JUDGEMENT_LINE_Y), radius)
    screen.blit(s, (0, 0))

BEATMAP_FILE = 'beatmap.csv'
BEATMAP = []
try:
    with open(BEATMAP_FILE, 'r') as f:
        reader = csv.reader(f)
        BEATMAP = [[int(row[0]), int(row[1])] for row in reader]
except FileNotFoundError:
    print(f"エラー: '{BEATMAP_FILE}' が見つかりません。")
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

# レーンごとのエフェクト情報
lane_effects = [None] * LANE_COUNT
lane_effect_timers = [0] * LANE_COUNT

try:
    pygame.mixer.music.load('ex5/maou_short_14_shining_star.mp3')
except pygame.error:
    print("音楽ファイルをロードできませんでした。")

running = True
clock = pygame.time.Clock()
game_started = False
game_start_time = 0

while running:
    if not game_started and BEATMAP:
        pygame.mixer.music.play()
        game_start_time = time.time()
        game_started = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key in lane_keys:
                play_sound("ex5/T.mp3")

                pressed_lane_idx = key_to_lane_idx[event.key]
                hit_found = False
                for note in notes[:]:
                    if note['lane'] == pressed_lane_idx and not note['hit']:
                        if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW:
                            score += 100
                            combo += 1
                            max_combo = max(max_combo, combo)
                            notes.remove(note)
                            if abs(note['rect'].centery - JUDGEMENT_LINE_Y) < JUDGEMENT_WINDOW / 2:
                                judgement_message = "PERFECT!"
                                lane_effects[pressed_lane_idx] = (255, 255, 0)  # 黄色
                            else:
                                judgement_message = "GOOD!"
                                lane_effects[pressed_lane_idx] = (0, 128, 255)  # 青
                            judgement_color = GREEN
                            lane_effect_timers[pressed_lane_idx] = 30
                            judgement_effect_timer = 30
                            hit_found = True
                            break
                if not hit_found:
                    combo = 0
                    judgement_message = "MISS!"
                    lane_effects[pressed_lane_idx] = (255, 0, 0)  # 赤
                    lane_effect_timers[pressed_lane_idx] = 30
                    judgement_color = RED
                    judgement_effect_timer

    if game_started:
        current_game_time_ms = (time.time() - game_start_time) * 1000
        while beatmap_index < len(BEATMAP) and current_game_time_ms >= BEATMAP[beatmap_index][0]:
            note_data = BEATMAP[beatmap_index]
            target_time_ms = note_data[0]
            target_lane = note_data[1]
            lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)
            new_note_rect = pygame.Rect(lane_x_start, -NOTE_HEIGHT, LANE_WIDTH, NOTE_HEIGHT)
            frames_to_travel = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED
            new_note_rect.y -= frames_to_travel * NOTE_SPEED
            notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
            beatmap_index += 1

    for note in notes[:]:
        note['rect'].y += NOTE_SPEED
        if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW and not note['hit']:
            notes.remove(note)
            combo = 0
            judgement_message = "TOO LATE!"
            lane = note['lane']
            lane_effects[lane] = (128, 0, 128)  # 紫
            lane_effect_timers[lane] = 30
            judgement_color = RED
            judgement_effect_timer = 30

    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

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

    # 各レーンのエフェクトを描画
    for i in range(LANE_COUNT):
        if lane_effect_timers[i] > 0 and lane_effects[i]:
            x_center = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING) + LANE_WIDTH // 2
            draw_lane_effect(screen, x_center, lane_effects[i])
            lane_effect_timers[i] -= 1

    pygame.display.flip()
    clock.tick(60)

pygame.quit()