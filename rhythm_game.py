import pygame
import csv
import time
import sys
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# --- Constants and Initial Settings ---
# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("My Rhythm Game (Final Version)")

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
CYAN = (0, 255, 255) # For Judgment Boost display
YELLOW = (255, 255, 0) # For Combo during Fever (kept as is for combo display)
BLUE = (0, 0, 255) # For Menu options

# Font settings
# --- IMPORTANT: Font path for Japanese characters ---
# This block attempts to find a Japanese font file based on common OS locations.
# You might need to adjust the paths below based on your specific system.
font_path = None
try:
    if sys.platform.startswith('win'): # Windows
        potential_font_paths = [
            "C:/Windows/Fonts/YuGothM.ttc", # Yu Gothic Medium
            "C:/Windows/Fonts/meiryo.ttc",   # Meiryo UI
            "C:/Windows/Fonts/msgothic.ttc"  # MS Gothic
        ]
    elif sys.platform == 'darwin': # macOS
        potential_font_paths = [
            "/System/Library/Fonts/AquaKana.ttc",
            "/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc", # Hiragino Maru Gothic
            "/System/Library/Fonts/SFCompactText.ttf" # A system font, might support some Japanese
        ]
    else: # Linux (common paths for Noto Sans CJK JP)
        potential_font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansJP-Regular.ttf",
            "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf", # IPA P Gothic
            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
        ]

    for path in potential_font_paths:
        if os.path.exists(path):
            font_path = path
            print(f"Using font: {font_path}")
            break
    
    if font_path is None:
        print("Warning: No suitable Japanese font found at common locations. Text might appear as squares (□).")

except Exception as e:
    print(f"An error occurred while trying to find fonts: {e}")
    font_path = None # Fallback to default if there's an issue

# Actual font initialization
font = pygame.font.Font(font_path, 48)
large_font = pygame.font.Font(font_path, 72) # For menu title
small_font = pygame.font.Font(font_path, 36)

# Game settings
LANE_COUNT = 4
LANE_WIDTH = 100
LANE_SPACING = (SCREEN_WIDTH - LANE_COUNT * LANE_WIDTH) // (LANE_COUNT + 1)

NOTE_SPEED = 5
NOTE_HEIGHT = 20

JUDGEMENT_LINE_Y = SCREEN_HEIGHT - 100
JUDGEMENT_WINDOW = 30 # Allowance for PERFECT/GOOD judgment

# Time it takes for a note to fall from top of screen to judgment line (in ms)
# Calculated assuming 60 FPS
FALL_TIME_MS = (JUDGEMENT_LINE_Y + NOTE_HEIGHT) / NOTE_SPEED * (1000 / 60)

# Map keys to lane indices (for input handling)
lane_keys_input_map = {
    pygame.K_d: {"lane_idx": 0}, # D key for lane 0
    pygame.K_f: {"lane_idx": 1}, # F key for lane 1
    pygame.K_j: {"lane_idx": 2}, # J key for lane 2
    pygame.K_k: {"lane_idx": 3}  # K key for lane 3
}
key_to_lane_idx = {key: data["lane_idx"] for key, data in lane_keys_input_map.items()}

# Colors corresponding to each lane (for drawing)
lane_colors = [
    (255, 100, 100), # Color for Lane 0 (D key)
    (100, 255, 100), # Color for Lane 1 (F key)
    (100, 100, 255), # Color for Lane 2 (J key)
    (255, 255, 100)  # Color for Lane 3 (K key)
]

lane_idx_to_key_char = {0: 'D', 1: 'F', 2: 'J', 3: 'K'} # Key characters for display

# Beatmap and Music file path settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = BASE_DIR # Assuming assets are in the same directory as the script

BEATMAP_FILE_NAME = 'beatmap.csv' # Change if needed, e.g., 'ex5_beatmap.csv'
MUSIC_FILE_NAME = 'maou_short_14_shining_star.mp3' # Change if needed, e.g., 'ex5.mp3'

BEATMAP_FULL_PATH = os.path.join(ASSET_DIR, BEATMAP_FILE_NAME)
MUSIC_FULL_PATH = os.path.join(ASSET_DIR, MUSIC_FILE_NAME)

# --- HP Bar Size Definition ---
HP_BAR_WIDTH = 200
HP_BAR_HEIGHT = 20

# --- Game State Enums (or Constants) ---
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

# --- Global Variables (holding game state) ---
score = 0
combo = 0
max_combo = 0

MAX_HP = 500
current_hp = MAX_HP
HP_LOSS_PER_MISS = 10 # HP lost per normal miss

# Judgment Boost settings
JUDGEMENT_BOOST_COMBO_THRESHOLD = 10 # Combo multiple to activate boost
JUDGEMENT_BOOST_DURATION_FRAMES = 60 * 5 # Boost duration (5 seconds = 60FPS * 5 seconds)
judgement_boost_active = False # Is judgment boost currently active?
judgement_boost_timer = 0 # Remaining time for judgment boost (in frames)

# Fever Mode settings
FEVER_COMBO_THRESHOLD = 10 # Combo count to activate fever
fever_active = False # Is fever currently active? (持續 based on combo)
fever_flash_color_timer = 0 # Timer for color flashing (not used for background, but kept for other uses)
FEVER_FLASH_INTERVAL = 120 # (not used for background, but kept for other uses)

# Fever background color (very light yellow)
FEVER_BACKGROUND_COLOR = (40, 40, 0) # A very faint yellowish-brown, close to black (R, G, B)

judgement_effect_timer = 0
judgement_message = ""
judgement_color = WHITE

beatmap_index = 0
notes = [] # List of notes currently on screen

# Initial game state is Menu
game_state = GAME_STATE_MENU
game_start_time = 0

# --- File Loading Functions ---
def load_beatmap(path: str) -> list[list[int]]:
    """
    Loads the beatmap file and returns a list of note data (time, lane).
    Displays an error message and exits the game if the file is not found.
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' not found.")

        with open(path, 'r') as f:
            reader = csv.reader(f)
            # Convert each row to integers and add to list
            beatmap_data = [[int(row[0]), int(row[1])] for row in reader]
        return beatmap_data
    except FileNotFoundError as e:
        print(f"Error: Beatmap file not found. {e}")
        print("Please ensure 'beatmap.csv' is in the same directory as the game script.")
        print("Or run 'create_beatmap.py' to generate a beatmap file.")
        print(f"Expected beatmap path: {path}")
        pygame.quit()
        sys.exit()

def load_music(path: str) -> None:
    """
    Loads the music file. Displays a warning if the file is not found or fails to load.
    """
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"'{path}' not found.")
        pygame.mixer.music.load(path)
    except pygame.error as e:
        print(f"Warning: Could not load music file. {e}")
        print(f"Expected music path: {path}")
    except FileNotFoundError as e:
        print(f"Warning: Music file not found. {e}")
        print(f"Expected music path: {path}")

# Execute beatmap and music loading
BEATMAP = load_beatmap(BEATMAP_FULL_PATH)
load_music(MUSIC_FULL_PATH)

# --- Function to Reset Game State (for restart) ---
def reset_game_state(activate_boost_initially: bool = False) -> None:
    """Resets all game states to their initial values.
    activate_boost_initially: Whether to activate judgment boost at the start of the game.
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
    game_state = GAME_STATE_PLAYING # Set game to playing state
    game_start_time = 0
    judgement_effect_timer = 0
    judgement_message = ""
    judgement_color = WHITE
    judgement_boost_active = activate_boost_initially # Apply initial setting here
    judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES if activate_boost_initially else 0
    fever_active = False
    fever_flash_color_timer = 0

    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.load(MUSIC_FULL_PATH)
        except (pygame.error, FileNotFoundError) as e:
            print(f"Warning: Could not reload music file. {e}")

# --- Event Handling Functions ---
def handle_quit_event(event: pygame.event.Event) -> bool:
    """Handles the QUIT event. Returns whether the game loop should continue."""
    if event.type == pygame.QUIT:
        return False # Set running to False
    return True # Keep running as True

def handle_menu_input(event: pygame.event.Event) -> None:
    """Handles key input on the menu screen."""
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
    Handles restart process when 'R' key is pressed during game over.
    """
    global game_state
    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
        game_state = GAME_STATE_MENU # Return to menu

def process_key_press(event: pygame.event.Event) -> None:
    """
    Handles note judgment when a key is pressed.
    Updates global variables: score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgement_boost_active, judgement_boost_timer,
    fever_active, fever_flash_color_timer, and notes.
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


# --- Game State Update Functions ---
def check_game_start() -> None:
    """Checks game start conditions and starts the game. Also plays music."""
    global game_start_time
    # If music is loaded, game has not started, and not game over
    if game_state == GAME_STATE_PLAYING and pygame.mixer.get_init() and BEATMAP:
        if not pygame.mixer.music.get_busy(): # Only start if music is not already playing
            pygame.mixer.music.play()
            game_start_time = time.time()

def generate_notes() -> None:
    """Generates notes based on beatmap data and adds them to the notes list."""
    global beatmap_index, notes
    if game_state == GAME_STATE_PLAYING:
        current_game_time_ms = (time.time() - game_start_time) * 1000

        # BEATMAP[beatmap_index][0] is the time the note should reach the judgment line
        # FALL_TIME_MS is the time it takes for a note to fall from the top to the judgment line
        # This condition determines when a note should be generated.
        while beatmap_index < len(BEATMAP) and current_game_time_ms >= BEATMAP[beatmap_index][0] - FALL_TIME_MS:
            note_data = BEATMAP[beatmap_index]
            target_lane = note_data[1]

            # Create a new note (starts hidden at the top of the screen)
            lane_x_start = LANE_SPACING + target_lane * (LANE_WIDTH + LANE_SPACING)
            new_note_rect = pygame.Rect(lane_x_start, -NOTE_HEIGHT, LANE_WIDTH, NOTE_HEIGHT)
            
            notes.append({'rect': new_note_rect, 'lane': target_lane, 'hit': False})
            
            beatmap_index += 1 # Move to the next note

def update_notes_position() -> None:
    """
    Updates the position of notes on the screen and processes notes that have passed the judgment line.
    (Includes "TOO LATE!" / Missed Note judgment and processing)
    Updates global variables: score, combo, max_combo, current_hp, judgement_message, judgement_color,
    judgement_effect_timer, judgement_boost_active, judgement_boost_timer,
    fever_active, fever_flash_color_timer.
    """
    global score, combo, max_combo, current_hp, judgement_message, judgement_color, judgement_effect_timer
    global judgement_boost_active, judgement_boost_timer, fever_active, fever_flash_color_timer
    global notes

    for note in notes[:]: # Iterate over a copy of the list to safely remove elements
        note['rect'].y += NOTE_SPEED
        # If the note has completely passed the judgment line (TOO LATE! / Missed Note)
        if note['rect'].top > JUDGEMENT_LINE_Y + JUDGEMENT_WINDOW and not note['hit']:
            notes.remove(note)
            note['hit'] = True # Mark as processed

            if judgement_boost_active:
                # If judgment boost is active, "TOO LATE!" is upgraded to "PERFECT!"
                score += 100 # Add score
                combo += 1 # Continue combo
                max_combo = max(max_combo, combo)
                judgement_message = "PERFECT! (Boosted)" # Indicate it's a BOOSTED PERFECT
                judgement_color = GREEN
                judgement_effect_timer = 30
                
                # Also check for HP recovery here (if TOO LATE became PERFECT)
                if combo > 0 and combo % 3 == 0:
                    hp_recovered = min(10, MAX_HP - current_hp)
                    current_hp += hp_recovered
                    if hp_recovered > 0:
                        judgement_message += f" (+{hp_recovered} HP!)"

                # Check for Judgment Boost activation (even if already boosted, to reset timer)
                if combo > 0 and combo % JUDGEMENT_BOOST_COMBO_THRESHOLD == 0:
                    judgement_boost_active = True
                    judgement_boost_timer = JUDGEMENT_BOOST_DURATION_FRAMES
                    judgement_message += " (BOOST!)" # Add BOOST activation message
            else:
                # If judgment boost is not active, it's a regular "TOO LATE!" (combo reset & HP loss)
                combo = 0 # Reset combo
                judgement_message = "TOO LATE!" # Treat as a MISS
                judgement_color = RED
                judgement_effect_timer = 30
                current_hp -= HP_LOSS_PER_MISS # Decrease HP
                check_game_over() # Call HP check and game over judgment
                
                # Deactivate Fever if combo is reset
                fever_active = False
                fever_flash_color_timer = 0
    
    # If combo drops below Fever threshold (e.g., due to a missed note), deactivate Fever
    if combo < FEVER_COMBO_THRESHOLD and fever_active:
        fever_active = False
        fever_flash_color_timer = 0

def update_timers() -> None:
    """Updates various timers (judgment effect, judgment boost, fever flash)."""
    global judgement_effect_timer, judgement_boost_timer, judgement_boost_active
    global fever_flash_color_timer, fever_active

    # Update judgment boost timer
    if judgement_boost_active:
        judgement_boost_timer -= 1
        if judgement_boost_timer <= 0:
            judgement_boost_active = False
            judgement_boost_timer = 0

    # Update fever effect flash timer (not directly impacting background, but kept for other potential uses)
    if fever_active:
        fever_flash_color_timer -= 1
        if fever_flash_color_timer <= 0:
            fever_flash_color_timer = FEVER_FLASH_INTERVAL

    # Update judgment message display timer
    if judgement_effect_timer > 0:
        judgement_effect_timer -= 1

def check_game_over() -> None:
    """Sets game over state if HP drops to 0 or below, and stops music."""
    global current_hp, game_state
    if current_hp <= 0:
        current_hp = 0
        game_state = GAME_STATE_GAME_OVER
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

# --- Drawing Functions ---
def draw_background() -> None:
    """Draws the game background (lane outlines, judgment line, corresponding keys).
    Changes background color during Fever mode.
    """
    if fever_active and game_state == GAME_STATE_PLAYING: # Fever background only when playing
        screen.fill(FEVER_BACKGROUND_COLOR) # Very faint yellow background during Fever
    else:
        screen.fill(BLACK) # Normal background is black

    if game_state == GAME_STATE_PLAYING: # Only draw lanes etc. when playing
        for i in range(LANE_COUNT):
            lane_x_start = LANE_SPACING + i * (LANE_WIDTH + LANE_SPACING)
            pygame.draw.rect(screen, GRAY, (lane_x_start, 0, LANE_WIDTH, SCREEN_HEIGHT), 2) # Lane outline
            # Display corresponding key below the lane
            key_char_text = small_font.render(lane_idx_to_key_char[i], True, WHITE)
            screen.blit(key_char_text, (lane_x_start + (LANE_WIDTH - key_char_text.get_width()) // 2, JUDGEMENT_LINE_Y + 50))
        
        # Draw judgment line background and the line itself
        pygame.draw.rect(screen, GRAY, (0, JUDGEMENT_LINE_Y, SCREEN_WIDTH, NOTE_HEIGHT), 0)
        pygame.draw.line(screen, WHITE, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 3)

def draw_notes() -> None:
    """Draws notes currently on the screen."""
    if game_state == GAME_STATE_PLAYING:
        for note in notes:
            # Draw note with the lane's color
            pygame.draw.rect(screen, lane_colors[note['lane']], note['rect'])

def draw_info_panel() -> None:
    """Draws score, combo, max combo, HP bar, and remaining judgment boost time."""
    if game_state == GAME_STATE_PLAYING:
        # Display score, combo, max combo
        score_text = font.render(f"Score: {score}", True, WHITE)
        # Combo text turns yellow during Fever
        combo_color = YELLOW if fever_active else WHITE
        combo_text = font.render(f"Combo: {combo}", True, combo_color)
        max_combo_text = small_font.render(f"Max Combo: {max_combo}", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(combo_text, (10, 50))
        # Adjust Y position of max combo to avoid overlapping with HP bar
        screen.blit(max_combo_text, (SCREEN_WIDTH - max_combo_text.get_width() - 10, 40))

        # Draw HP bar
        hp_bar_x = (SCREEN_WIDTH - HP_BAR_WIDTH) // 2
        hp_bar_y = 10
        hp_bar_fill_width = int(HP_BAR_WIDTH * (current_hp / MAX_HP))
        
        pygame.draw.rect(screen, GRAY, (hp_bar_x, hp_bar_y, HP_BAR_WIDTH, HP_BAR_HEIGHT), 2) # HP bar outline
        hp_fill_color = GREEN if current_hp > MAX_HP / 3 else RED # Change color based on HP
        pygame.draw.rect(screen, hp_fill_color, (hp_bar_x, hp_bar_y, hp_bar_fill_width, HP_BAR_HEIGHT)) # HP fill
        
        hp_text = small_font.render(f"HP: {current_hp}/{MAX_HP}", True, WHITE)
        screen.blit(hp_text, (hp_bar_x + HP_BAR_WIDTH + 10, hp_bar_y)) # HP value

        # Display remaining judgment boost time
        if judgement_boost_active:
            boost_text = small_font.render(f"Boost: {judgement_boost_timer // 60 + 1}s", True, CYAN) # Display in Cyan
            screen.blit(boost_text, (SCREEN_WIDTH - boost_text.get_width() - 10, 70)) # Adjusted Y position

def draw_judgement_message() -> None:
    """Displays judgment messages (PERFECT!, GOOD!, MISS!, TOO LATE!)."""
    if game_state == GAME_STATE_PLAYING and judgement_effect_timer > 0:
        judgement_display = font.render(judgement_message, True, judgement_color)
        judgement_rect = judgement_display.get_rect(center=(SCREEN_WIDTH // 2, JUDGEMENT_LINE_Y - 50))
        screen.blit(judgement_display, judgement_rect)
    
def draw_game_over_screen() -> None:
    """Draws the game over screen (message, final score, restart instruction)."""
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
        
        restart_text = small_font.render("Rキーでメニューに戻る", True, WHITE) # Japanese text
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        screen.blit(restart_text, restart_rect)

def draw_menu_screen() -> None:
    """Draws the pre-game menu screen."""
    screen.fill(BLACK) # Menu screen has a black background
    
    title_text = large_font.render("My Rhythm Game", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
    screen.blit(title_text, title_rect)

    # Option for starting without Judgment Boost (Japanese text)
    option1_text = font.render("1: ゲームスタート (判定強化なし)", True, WHITE)
    option1_rect = option1_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(option1_text, option1_rect)

    # Option for starting with Judgment Boost (Japanese text)
    option2_text = font.render("2: ゲームスタート (判定強化あり)", True, CYAN) # Boost is Cyan
    option2_rect = option2_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
    screen.blit(option2_text, option2_rect)

    # Instruction for choosing (Japanese text)
    info_text = small_font.render("対応する数字キーを押して選択してください", True, GRAY)
    info_rect = info_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
    screen.blit(info_text, info_rect)


# --- Main Game Loop ---
running = True
clock = pygame.time.Clock()

while running:
    # Event processing
    for event in pygame.event.get():
        running = handle_quit_event(event) # Handle QUIT event

        if game_state == GAME_STATE_MENU:
            handle_menu_input(event)
        elif game_state == GAME_STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                process_key_press(event) # Handle key input
        elif game_state == GAME_STATE_GAME_OVER:
            handle_game_over_input(event)

    # Game state updates
    if game_state == GAME_STATE_PLAYING:
        check_game_start() # Check music playback and game start
        generate_notes() # Generate notes from beatmap
        update_notes_position() # Move notes and check for misses
        update_timers() # Update various timers
        check_game_over() # Final check for game over if HP drops to 0

    # Drawing
    screen.fill(BLACK) # Clear the screen every frame

    if game_state == GAME_STATE_MENU:
        draw_menu_screen()
    elif game_state == GAME_STATE_PLAYING:
        draw_background() # Draw background, lane outlines, judgment line, keys
        draw_notes() # Draw notes
        draw_info_panel() # Draw score, combo, HP bar, etc.
        draw_judgement_message() # Draw judgment message
    elif game_state == GAME_STATE_GAME_OVER:
        draw_game_over_screen() # Draw game over screen (background will be black from screen.fill)

    # Update display and fix frame rate
    pygame.display.flip()
    clock.tick(60)

pygame.quit()