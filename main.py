import pygame
import sqlite3
import hashlib
import math 
import random
import heapq

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1300, 720))
pygame.display.set_caption('UDDERWORLD')

# font colours
orange = (255, 69, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)
pink = (255, 16, 240)
white = (255, 255, 255)

# load the background image once outside the loop
background_image = pygame.image.load('background.png').convert()
controls1_image = pygame.image.load('controls1.png').convert()
controls2_image = pygame.image.load('controls2.png').convert()
room1_image = pygame.image.load('room1.png').convert()
rescaled_image = pygame.transform.scale(room1_image, (1300, 720))
room1_image = rescaled_image
room1_subtitle_timer = None
room1_subtitle_duration = 3000
current_username = None
previous_room_name = "room1"


# A* VARIABLES
TILE_SIZE = 40
GRID_WIDTH = 1300 // TILE_SIZE
GRID_HEIGHT = 720 // TILE_SIZE

# TEXT FONT AND TEXT DEFINITIONS
subtitle_font = pygame.font.Font('pixelFont.ttf', 80)
box_subtitle_font = pygame.font.Font('pixelFont.ttf', 30)
button_font = pygame.font.Font('pixelFont.ttf', 75)
username_font = pygame.font.Font('pixelFont.ttf', 40)

# login messages handling
error_message = ""
error_display_end_time = 0  # Time in milliseconds when error should disappear
error_duration = 3000  # Duration in ms (e.g., 3000ms = 3 seconds)



# database Design
# connection and cursor objects
conn = sqlite3.connect("UDD_database.db")
cur = conn.cursor()

# creating TBL_Player with fields

cur.execute('''
            CREATE TABLE IF NOT EXISTS TBL_Player
            ([username], TEXT PRIMARY KEY, 
            [password] TEXT,
            [room_num] INTEGER)
            ''')
conn.commit()

cur.execute('''
    CREATE TABLE IF NOT EXISTS TBL_Stats (
        username TEXT PRIMARY KEY,
        level INTEGER,
        FOREIGN KEY(username) REFERENCES TBL_Player(username)
    )
''')
conn.commit()

conn.close()

def update_player_level(username, new_level):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("UPDATE TBL_Stats SET level = ? WHERE username = ?", (new_level, username))
    conn.commit()
    conn.close()

def initialise_player_stats(username):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO TBL_Stats (username, level) VALUES (?, ?)", (username, 1))
    conn.commit()
    conn.close()

def update_player_room(username, room_name):
    room_num = {"room1": 0, "room2": 1}.get(room_name, 0)  # fallback to room1
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("UPDATE TBL_Player SET room_num = ? WHERE username = ?", (room_num, username))
    conn.commit()
    conn.close()

def get_player_level(username):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("SELECT level FROM TBL_Stats WHERE username = ?", (username,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 1

def get_saved_room(username):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("SELECT room_num FROM TBL_Player WHERE username = ?", (username,))
    result = cur.fetchone()
    conn.close()
    if result:
        room_map = {0: "room1", 1: "room2"}
        return room_map.get(result[0], "room1")
    return "room1"


def username_exists(username):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM TBL_Player WHERE username = ?", (username,))
    result = cur.fetchone()
    conn.close()
    return result if result is not None else False

def verify_user(username, password):
    global current_username 
    current_username = username
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("SELECT password FROM TBL_Player WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    # if no row is found, username doesn't exist; otherwise, compare passwords.
    if row is None:
        return False # username doesnt exist
    
    stored_hashed_password = row[0] # hashed pwd from db
    hashed_input_password = hashing(password) # hash input
    return row[0] == hashed_input_password # comparing hashes
    

def hashing(password): 
    # changes password into bytes so it can be hashed
    password = password.encode('utf-8')
    # create new hash object // SHA-3-256
    sha3_256 = hashlib.sha3_256
    # hashes and converts to hex
    hashed_password = sha3_256(password).hexdigest()
    return hashed_password

# A* PATHFINDING ALGORITHM
def astar_pathfinding(grid, start, goal):
            def heuristic(a, b):
                return abs(a[0] - b[0]) + abs(a[1] - b[1])

            open_set = []
            heapq.heappush(open_set, (0, start))
            came_from = {}
            g_score = {start: 0}
            f_score = {start: heuristic(start, goal)}

            while open_set:
                _, current = heapq.heappop(open_set)
                if current == goal:
                    path = []
                    while current in came_from:
                        path.append(current)
                        current = came_from[current]
                    path.reverse()
                    return path

                x, y = current
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:  # 4-directional
                    neighbor = (x + dx, y + dy)
                    if 0 <= neighbor[0] < GRID_WIDTH and 0 <= neighbor[1] < GRID_HEIGHT:
                        if grid[neighbor[1]][neighbor[0]] == 1: continue  # skip walls
                        tentative_g = g_score[current] + 1
                        if neighbor not in g_score or tentative_g < g_score[neighbor]:
                            came_from[neighbor] = current
                            g_score[neighbor] = tentative_g
                            f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                            heapq.heappush(open_set, (f_score[neighbor], neighbor))
            return []



# OOP INPUT CLASS
class Input_Box:
    def __init__(self, x, y, width, height, input=''):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.input = str(input)  # ensure input is always a string
        self.color = orange
        self.selected = False
        self.font = username_font  # default font
        self.backspace_timer = 0
        self.backspace_delay = 200  # delay in milliseconds
        self.rect = pygame.Rect(x, y, width, height)
        self.max_width = self.width - 10

    def set_font_size(self, size):
        # updates the font size for the input box
        self.font = pygame.font.Font('pixelFont.ttf', size)

    def truncate_input(self):
        # ensures the input text fits within the input box by truncating if necessary
        while self.font.render(self.input, True, self.color).get_width() > self.max_width:
            self.input = self.input[:-1]

    def display(self):
        # render the input text inside the box
        pygame.draw.rect(screen, (0, 0, 0), self.rect)  # Draw background
        pygame.draw.rect(screen, self.color, self.rect, 2)  # Draw border
        input_text = self.input if isinstance(self.input, str) else ""
        input_surf = self.font.render(input_text, True, self.color)
        screen.blit(input_surf, (self.x + 5, self.y + 5))  # Render text with padding

    def handle_event(self, event):
        # handle mouse click and key press events for input boxes
        if event.type == pygame.MOUSEBUTTONDOWN:
            # activate box if clicked
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.selected = True
                self.color = yellow
            else:
                self.selected = False
                self.color = red

        if self.selected and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            elif event.unicode and (event.unicode.isalnum() or event.unicode in "._@"):
                self.input += event.unicode
                self.truncate_input()

    def clear_input(self):
        # clear the input text
        self.input = ""

# password box - asterisk for privacy, inherited from the input box
class Password_Box(Input_Box):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.password = ""  # stores actual password

    def display(self):
        # display original password as asterisks
        pygame.draw.rect(screen, (0, 0, 0), self.rect)  # box background
        pygame.draw.rect(screen, self.color, self.rect, 2)  # box border
        masked_input = "*" * len(self.password)
        input_surf = self.font.render(masked_input, True, self.color)
        screen.blit(input_surf, (self.rect.x + 5, self.rect.y + 5))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Select the box
            if self.rect.collidepoint(event.pos):
                self.selected = True
                self.color = yellow
            else:
                self.selected = False
                self.color = red

        if self.selected and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.password = self.password[:-1]
            elif event.unicode and (event.unicode.isalnum() or event.unicode in "._@"):
                self.password += event.unicode
                self.truncate_input()

    def truncate_input(self):
        # ensure the password stays within the box
        while self.font.render("*" * len(self.password), True, self.color).get_width() > self.max_width:
            self.password = self.password[:-1]

    def clear_input(self):
        # clear the password text
        self.password = ""

# OOP TEXT CLASS

class Text:
    def __init__(self, text, x, y, color, font, duration = None):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.text_surf = self.font.render(self.text, True, self.color)
        self.rect = self.text_surf.get_rect(midtop=(self.x, self.y))
        self.duration = duration # duration in ms 
        self.start_time = None # stores start time when displayed

    # DISPLAY TEXT METHOD
    def draw(self):
        if self.start_time is None:
            screen.blit(self.text_surf, self.rect)
        elif pygame.time.get_ticks() - self.start_time < self.duration:
            screen.blit(self.text_surf, self.rect) # only draws if within the time limit

    def start_timer(self):
        # starts timer when the subtitle is displayedZ
        self.start_time = pygame.time.get_ticks()

# OOP BUTTON CLASS - SUBCLASS OF TEXT CLASS (inherits)
class Button(Text):
    def __init__(self, text, x, y, color, font):
        super().__init__(text, x, y, color, font)

    def check_if_clicked(self, event):
        # return true only if the button is clicked and the mouse button is released
        if event.type == pygame.MOUSEBUTTONUP and self.rect.collidepoint(pygame.mouse.get_pos()):
            return True
        return False

# SWITCHING ROOMS

def switch_room(room_name, entry_direction = None):
    global current_room, previous_room_name
    previous_room_name = [name for name, room in rooms.items() if room == current_room][0]  # track previous room
    current_room = rooms[room_name]  # change to the new room
    
    # puts player at entrance
    if room_name == "room2":
        if entry_direction == "from_room1": # enters from room1
            player.x = 80
            player.y = 250 # starting pos
        
    elif room_name == "room1":
        player.x = 100
        player.y = 500

    elif room_name == "room3":
        if entry_direction == "from_room2":
            player.x = 50  # far left near doorway
            player.y = 500

# PLAYER CLASS
class Player: 
    def __init__(self, x, y, sprite_sheet, scale_factor = 2):
        self.x = x
        self.y = y
        self.speed = 5
        self.scale_factor = scale_factor
        self.control_mode = "arrows" # default controls

        self.max_hp = 100
        self.current_hp = self.max_hp
        self.player_level = 3

        # load sprite sheet 
        self.sprite_sheet = sprite_sheet
        self.width = 32
        self.height = 32
        self.new_width = int(self.width * self.scale_factor)
        self.new_height = int(self.height * self.scale_factor)

        # load animations
        self.idle_sprite = self.get_sprite(0, 0)
        self.run_right_frames = [self.get_sprite(i, 0) for i in range(1, 3)] # row 1 / right
        self.run_left_frames = [pygame.transform.flip(frame, True, False) for frame in self.run_right_frames] # row 2 / flip right to left
        self.run_down_frames = [self.get_sprite(i, 3) for i in range(4)]  # row 3 / down
        self.run_up_frames = [self.get_sprite(i, 4) for i in range(4)]  # row 4 / up

        # animation settings
        self.current_animation = [self.idle_sprite]
        self.frame_index = 0
        self.animation_speed = 220  # ms per frame
        self.last_update_time = pygame.time.get_ticks()
        self.moving = False

    # SPRITES SETUP

    # function to extract sprites from sheet and scale
    def get_sprite(self, col, row):
        # scaling and extracting
        x = col * self.width
        y = row * self.height
        sprite = self.sprite_sheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        scaled_sprite = pygame.transform.scale(sprite, (self.new_width, self.new_height))

        return scaled_sprite

        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        moving = False
        previous_animation = self.current_animation

        # choosing set of controls
        if self.control_mode == "arrows": # arrows
            left, right, up, down = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN
        else:  # WASD
            left, right, up, down = pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s

        # predicting movement
        new_x, new_y = self.x, self.y

        if keys[left]:  
            new_x -= self.speed
            self.set_animation(self.run_left_frames)
            moving = True
        elif keys[right]:  
            new_x += self.speed
            self.set_animation(self.run_right_frames)
            moving = True
        elif keys[down]:  
            new_y += self.speed
            self.set_animation(self.run_down_frames)
            moving = True
        elif keys[up]:  
            new_y -= self.speed
            self.set_animation(self.run_up_frames)
            moving = True
        else:
            self.current_animation = [self.idle_sprite]  # Idle when not moving
        
        if self.current_animation != previous_animation:
            self.frame_index = 0
        
        if current_room == room1 and new_x > 1200:
            switch_room("room2", entry_direction= "from_room1")
            return
        if current_room == room2 and new_x > 1200:
            switch_room("room3", entry_direction="from_room2")
            player.x = 30
            player.y = 350
            return



        if not current_room.check_collision(new_x, new_y, self.new_width, self.new_height):
            self.x, self.y = new_x, new_y

        current_room.check_boundaries(self)

        return moving


    def set_animation(self, new_animation):
            # sets new animation if different from current
            if self.current_animation != new_animation:
                self.current_animation = new_animation
                self.frame_index = 0
    
    def update_animation(self, moving):
            # updates animation frame only if moving
            current_time = pygame.time.get_ticks()
            if moving:
                if current_time - self.last_update_time >= self.animation_speed:
                    self.frame_index = (self.frame_index + 1) % len(self.current_animation)
                    self.last_update_time = current_time
            else:
                self.frame_index = 0 # resets to idle frame

    def update(self):
        # handles movement and animation update
        moving = self.handle_input()
        self.update_animation(moving)

    def draw(self, screen):
            # draw sprite on the screen
            if 0 <= self.frame_index < len(self.current_animation):
                screen.blit(self.current_animation[self.frame_index], (self.x, self.y))

# ENEMY CLASS
class Enemy:
    def __init__(self, x, y, sprite_sheet, scale_factor = 2, speed = 3, move_range=(400, 800)):
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = 1  # 1 for right, -1 for left
        self.scale_factor = scale_factor
        self.in_battle = False
        self.mercy_shown = False 
        self.defeated = False
        self.move_min, self.move_max = move_range

 
        # load sprite sheet
        self.sprite_sheet = sprite_sheet
        self.width = 64
        self.height = 64
        self.new_width = int(self.width * self.scale_factor)
        self.new_height = int(self.height * self.scale_factor)

        # extract animation frames
        self.idle_sprite = self.get_sprite(0, 0)
        self.run_frames = [    
            self.get_sprite(0, 0),  # 1st frame
            self.get_sprite(1, 0),  # 2nd frame
            self.get_sprite(2, 0),  # 3rd frame
            self.get_sprite(3, 0)   # 4th frame
        ]

        # animation settings
        self.current_animation = self.run_frames
        self.frame_index = 0
        self.animation_speed = 220  # ms per frame
        self.last_update_time = pygame.time.get_ticks()

    def get_sprite(self, col, row):
        # extracts and scales sprite frames from the sprite sheet
        x = col * self.width
        y = row * self.height
        sprite = self.sprite_sheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        scaled_sprite = pygame.transform.scale(sprite, (self.new_width, self.new_height))
        return scaled_sprite

    def move(self):
        # moves the enemy in a simple back-and-forth pattern
        self.x += self.speed * self.direction
        if self.x > self.move_max or self.x < self.move_min:
            self.direction *= -1


    def update_animation(self):
        # updates the animation frame
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time >= self.animation_speed:
            self.frame_index = (self.frame_index + 1) % len(self.current_animation)
            self.last_update_time = current_time

    def check_collision(self, player):
        if self.mercy_shown:
            return False 
        # to make smaller collision rectangles, pixels of padding around sprite
        padding = 10 

        # create rectangles for enemy and player for collision detection
        enemy_rect = pygame.Rect(
            self.x + padding,
            self.y + padding,
            self.new_width - (padding * 2),
            self.new_height - (padding * 2)
    )
            
        player_rect = pygame.Rect(
            player.x + padding,
            player.y + padding,
            player.new_width - (padding * 2),
            player.new_height - (padding * 2)
    )

        # checking for collision
        return enemy_rect.colliderect(player_rect)
    
        

    def draw(self, screen):
        # draws the enemy on the screen
        if self.frame_index < len(self.current_animation):
            screen.blit(self.current_animation[self.frame_index], (self.x, self.y))

    def update(self):
        # updates movement and animation if not in battle
        if not self.in_battle:
            self.move()
            self.update_animation()
        
# ROOM CLASS
class Room:
        def __init__(self, background_image, unwalkablle_areas, boundaries):
            self.background = pygame.image.load(background_image).convert()
            self.unwalkable_areas = unwalkablle_areas # list of pygame.Rect obj
            self.boundaries = boundaries # left right top bottom

        def draw(self): # draws bg and collision areas
            screen.blit(pygame.transform.scale(self.background, (1300, 720)), (0,0))

            #for area in self.unwalkable_areas:
             #   pygame.draw.rect(screen, (0, 0, 255), area, 2) 


        def check_collision(self, new_x, new_y, player_width, player_height): # checks if player collides with obstacles
            player_rect = pygame.Rect(new_x, new_y, player_width, player_height)
            for area in self.unwalkable_areas:
                if player_rect.colliderect(area):
                    return True 
            return False
        
        def check_boundaries(self, player): # making sure player stays in room boundaries
            left, right, top, bottom = current_room.boundaries
            player.x = max(left, min(player.x, right))
            player.y = max(top, min(player.y, bottom))

        def get_grid(self):
            grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    for obstacle in self.unwalkable_areas:
                        if tile_rect.colliderect(obstacle):
                            grid[y][x] = 1  # Mark as wall
                            break
            return grid




# BULLET CLASS
class Bullet:
    def __init__(self, start_pos, target_pos, grid, speed=2, speed_y=None):
        # convert positions to pixel coordinates
        if isinstance(start_pos[0], int):  # if already pixel coordinates
            self.x = start_pos[0]
            self.y = start_pos[1]
        else:  # if grid coordinates
            self.x = start_pos[0] * TILE_SIZE + TILE_SIZE // 2
            self.y = start_pos[1] * TILE_SIZE + TILE_SIZE // 2
            
        self.speed = speed
        self.speed_y = speed_y
        self.mode = "simple" if speed_y else "pathfinding"
        
        if self.mode == "pathfinding":
            # convert to grid coordinates for pathfinding
            start_grid = (start_pos[0] // TILE_SIZE if isinstance(start_pos[0], int) else start_pos[0],
                         start_pos[1] // TILE_SIZE if isinstance(start_pos[1], int) else start_pos[1])
            target_grid = (target_pos[0] // TILE_SIZE if isinstance(target_pos[0], int) else target_pos[0],
                          target_pos[1] // TILE_SIZE if isinstance(target_pos[1], int) else target_pos[1])
            
            self.path = astar_pathfinding(grid, start_grid, target_grid)
            self.current_index = 0

        self.width = 20
        self.height = 20
        self.color = white
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 3000

    def update(self):
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            return "expired"

        if self.mode == "simple":
            self.y += self.speed_y 
            return "alive"
        
        if self.mode == "pathfinding" and self.path:
            if self.current_index >= len(self.path):
                return "expired"
                
            target = self.path[self.current_index]
            target_x = target[0] * TILE_SIZE + TILE_SIZE // 2
            target_y = target[1] * TILE_SIZE + TILE_SIZE // 2
            
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < self.speed:
                self.x = target_x
                self.y = target_y
                self.current_index += 1
            else:
                self.x += (dx/distance) * self.speed
                self.y += (dy/distance) * self.speed
            
            return "alive"
        
        return "expired"

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.width, self.height))

    def check_collision(self, target_rect):
        bullet_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return bullet_rect.colliderect(target_rect)

# BATTLE CLASS
class Battle:
    def __init__(self, player, enemy, heart_width=20 , heart_height=20):
        self.player = player
        self.enemy = enemy
        self.bullets = [] # bullets as an array
        self.attack_timer = pygame.time.get_ticks()
        self.dodging_timer = None
        self.dodging_duration = 10000 # 10 seconds enemy turn
        self.item_timer = None
        self.item_duration = 2000  # item image time
        self.wave_interval = 1000 # controls time for each wave of bullets
        self.last_wave_time = 0 
        self.game_over = False # game over screen trigger logic
        self.mercy_count = 0 # track how many times mercy was clicked
        self.mercy_timer = None # timer for mercy messages
        self.mercy_message = "" # current mercy message
        self.mercy_shown = False # track if mercy was shown
        

        # battle ui elements
        self.box_width = 400
        self.box_height = 300
        self.box_x = (1300 - self.box_width) // 2
        self.box_y = (720 - self.box_height) // 2 - 50

        # player and battle movement constraints
        self.battle_player_speed = 4  # movement speed in battle

        # bullet handling
        self.bullets = []

        # battle stats
        self.damage_per_hit = 10
        self.player_current_hp = 100
        self.enemy_max_hp = 100 # total hp
        self.enemy_current_hp = 100 # current hp
        self.butterknife_image = pygame.image.load("butterknife.PNG").convert_alpha() # load butterknife image
        self.butterknife_damage = 10 # damage dealt by butterknife
        self.item_enabled = False # item option starts disabled
        self.has_fought = False # tracks if player has fought at least once

        # battle options
        self.options = [
            {'text': 'FIGHT', 'color': orange, 'selected': True}, # default selected option
            {'text': 'ITEM', 'color': orange, 'selected': False},
            {'text': 'MERCY', 'color': orange, 'selected': False}
        ]
        self.current_option = 0 # index of current selected option
        
        # battle state
        self.state = "SELECTING" # options for what the player is doing like fighting etc
        self.turn = "PLAYER" # whose turn it is
        self.message = "" # message after an action
        self.message_timer = None # timer for the message display
        self.message_duration = 3000 # duration in ms for displaying messages

        # heart dimensions
        self.heart_width = heart_width
        self.heart_height = heart_height
        self.battle_player_x = self.box_x + self.box_width // 2 - self.heart_width // 2
        self.battle_player_y = self.box_y + self.box_height // 2 - self.heart_height // 2
        self.heart_color = red

        # load battle images
        self.load_battle_images()

    def load_battle_images(self):
        # loads images for player and anemy during battle
        self.player_battle_image = pygame.image.load("cow_battle.png").convert_alpha()
        self.enemy_battle_image = pygame.image.load("carrot_battle.png").convert_alpha()
        self.heart_image = pygame.Surface((self.heart_width, self.heart_height))
        self.heart_image.fill(self.heart_color)

        try:
            self.butterknife_image = pygame.image.load("butterknife.PNG").convert_alpha()
            print("Butterknife image loaded successfully - Dimensions:", 
                  self.butterknife_image.get_width(), "x",
                  self.butterknife_image.get_height())
        except pygame.error as e:
            print(f"ERROR: Could not load butterknife image: {e}")
            self.butterknife_image = pygame.Surface((100, 100))
            self.butterknife_image.fill((255, 0, 0))
            print("Created placeholder surafce instead")

    def draw(self, screen):
        # draw battle ui including all elements
        screen.fill((0, 0, 0))

        # draw bullets
        for bullet in self.bullets:
            bullet.draw(screen)
        
        # draw player and enemy // left side
        player_image_x = 100
        player_image_y = 100
        enemy_image_x = 100
        enemy_image_y = 350
        self.player_battle_image = pygame.transform.scale(self.player_battle_image, (150, 150))
        self.enemy_battle_image = pygame.transform.scale(self.enemy_battle_image, (150, 150))
        
        # draw player stats // right side
        stats_x = 900
        stats_y = 150
        
        # draw LV and HP
        lv_text = pygame.font.Font('pixelFont.ttf', 50).render(f"LV {self.player.player_level}", True, white)
        hp_text = pygame.font.Font('pixelFont.ttf', 50).render("HP", True, white)
        
        screen.blit(lv_text, (stats_x, stats_y))
        screen.blit(hp_text, (stats_x, stats_y + 50))
        
        # draw HP bar
        hp_bar_width = 150
        hp_bar_height = 20
        hp_bar_x = stats_x + 60
        hp_bar_y = stats_y + 50

        enemy_hp_bar_width = 400
        enemy_hp_bar_height = 20
        enemy_hp_bar_x = (1300 - enemy_hp_bar_width) // 2
        enemy_hp_bar_y = 20

        # draw enemy HP bar background
        pygame.draw.rect(screen, (128, 128, 128), (enemy_hp_bar_x, enemy_hp_bar_y, enemy_hp_bar_width, enemy_hp_bar_height))

        # draw current enemy HP
        current_enemy_hp_width = (self.enemy_current_hp / self.enemy_max_hp) * enemy_hp_bar_width
        pygame.draw.rect(screen, (255, 0, 0), (enemy_hp_bar_x, enemy_hp_bar_y, current_enemy_hp_width, enemy_hp_bar_height))

        # draw enemy HP numbers
        enemy_hp_numbers = pygame.font.Font('pixelFont.ttf', 20).render(f"{self.enemy_current_hp}/{self.enemy_max_hp}", True, white)
        screen.blit(enemy_hp_numbers, (enemy_hp_bar_x + enemy_hp_bar_width + 10, enemy_hp_bar_y))
        
        # draw HP bar background
        pygame.draw.rect(screen, (255, 0, 0), (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
        
        # draw current HP
        current_hp_width = (self.player.current_hp / self.player.max_hp) * hp_bar_width
        pygame.draw.rect(screen, (255, 255, 0), (hp_bar_x, hp_bar_y, current_hp_width, hp_bar_height))

        # draw HP numbers
        hp_numbers = pygame.font.Font('pixelFont.ttf', 30).render(f"{self.player.current_hp}/{self.player.max_hp}", True, white)
        screen.blit(hp_numbers, (hp_bar_x + hp_bar_width + 20, hp_bar_y))
        
        # draw butterknife image if ITEM is selected
        if self.state == "ITEM":
            butterknife_x = 1000
            butterknife_y = 400
            screen.blit(self.butterknife_image, (butterknife_x, butterknife_y))

            pygame.draw.rect(screen, (255, 0, 0), (butterknife_x, butterknife_y, 100, 100), 2)

            try:
                # Scale the image if needed
                scaled_knife = pygame.transform.scale(self.butterknife_image, (100, 100))
                screen.blit(scaled_knife, (butterknife_x, butterknife_y))
            except:
                print("Failed to draw butterknife")  # debug

        # disable ITEM option if not available
        if not self.item_enabled:
            for option in self.options:
                if option["text"] == "ITEM":
                    # OUT ITEM OPTION
                    break
        else: 
            for option in self.options:
                if option["text"] == "ITEM":
                    option["colour"] = orange

        # draw battle box in middle
        if self.state == "DODGING":
            # expand the battle box for dodging area
            dodge_box_x = self.box_x - 50
            dodge_box_y = self.box_y - 50
            dodge_box_width = self.box_width + 100
            dodge_box_height = self.box_height + 100
            
            # draw dodging area as a larger box
            pygame.draw.rect(screen, white, (dodge_box_x, dodge_box_y, dodge_box_width, dodge_box_height), 4)

            # draw heart inside dodging area
            pygame.draw.rect(screen, self.heart_color, (self.battle_player_x, self.battle_player_y, self.heart_width, self.heart_height))

        else:
            # default small battle box
            pygame.draw.rect(screen, white, (self.box_x, self.box_y, self.box_width, self.box_height), 4)
        
        # draw battle options at bottom
        option_width = 300
        option_height = 100
        option_padding = 40
        option_y = 600 # all options are same height

        # define colors and text for options
        option_styles = {
            "FIGHT": {"color": red},   
            "ITEM": {"color": blue}, 
            "MERCY": {"color": green} 
        }
            
        
        for i, option in enumerate(self.options):
            option_x = 300 + i * (option_width + option_padding) # calculates x pos
            option_y = 600 # y pos is same for all the options

            # loop through option_styles to get the correct style for the button
            style = {"color": white}  # default style
            for s in option_styles:
                if s == option["text"]:
                    style = option_styles[s]  # assign the correct style if found
                    break

            default_color = style["color"]

            border_color = yellow if option["selected"] else default_color # highlights if chosen

            
            # draw option background and border
            pygame.draw.rect(screen, (0, 0, 0), (option_x, option_y, option_width, option_height), border_radius=20) 
            pygame.draw.rect(screen, border_color, (option_x, option_y, option_width, option_height), 5, border_radius=20)

            # draw option text
            option_text = button_font.render(option['text'], True, option['color'])
            option_text_rect = option_text.get_rect(center=(option_x + option_width // 2, option_y + option_height // 2))
            screen.blit(option_text, option_text_rect)
            
           
        # draw battle message if any
        if self.message:
            current_time = pygame.time.get_ticks()  # Get the current time

            # if the timer hasn't started yet start it 
            if self.message_timer is None:
                self.message_timer = current_time  

            # if the message is still within the display duration then render it
            if current_time - self.message_timer < self.message_duration:
                message_text = box_subtitle_font.render(self.message, True, white)  # render message text
                message_x = self.box_x + self.box_width // 2  # center x pos
                message_y = self.box_y - 40  # position message slightly above the battle box
                message_rect = message_text.get_rect(center=(message_x, message_y))  # align the text
                screen.blit(message_text, message_rect)  # draw the message on screen

            # if the time has passed then reset the message
            else:
                self.message = ""  # clear the message
                self.message_timer = None  # reset timer for future messages
        
        if self.mercy_message and self.mercy_timer:
            mercy_text = box_subtitle_font.render(self.mercy_message, True, white)
            # position mercy message in center of battle box
            mercy_rect = mercy_text.get_rect(center=(
                self.box_x + self.box_width // 2,
                self.box_y + self.box_height // 2
            ))
            screen.blit(mercy_text, mercy_rect)
        
        # draw player and enemy images
        try:
            screen.blit(self.player_battle_image, (player_image_x, player_image_y))
            screen.blit(self.enemy_battle_image, (enemy_image_x, enemy_image_y))
        except:
            # if images aren't loaded, draw placeholder rectangles
            pygame.draw.rect(screen, white, (player_image_x, player_image_y, 100, 100))
            pygame.draw.rect(screen, white, (enemy_image_x, enemy_image_y, 100, 100))



    def handle_input(self, event):
        if self.state == "SELECTING":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    # move selection left
                    self.options[self.current_option]['selected'] = False
                    self.current_option = (self.current_option - 1) % len(self.options)
                    self.options[self.current_option]['selected'] = True
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    # move selection right
                    self.options[self.current_option]['selected'] = False
                    self.current_option = (self.current_option + 1) % len(self.options)
                    self.options[self.current_option]['selected'] = True
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # select the current option
                    self.state = self.options[self.current_option]['text']
                    
                    # transition to dodging state if enemy attacks
                    if self.state == "FIGHT":  
                        self.state = "DODGING"
                        self.attack_timer = pygame.time.get_ticks()
                        self.has_fought = True # player has fought so enable item option
                        self.item_enabled = True
                        self.message = "You attacked!"
                        self.message_timer = pygame.time.get_ticks()
                        self.turn = "ENEMY"  # enemy gets a turn after the player attacks
                        self.spawn_bullet_wave() # spawns bullets immediately when fight starts
                        self.last_wave_time = pygame.time.get_ticks() # reset timer so next wave comes quickly

                    elif self.state == "ITEM":
                        if self.item_enabled:
                            print("Using butterknife!") 
                            self.state = "ITEM" # item option selected
                            self.user_item() # uses item on enemy
                            self.item_enabled = False
                            self.turn = "ENEMY"
                        else: 
                            self.message = "Fight first to use items!" # so that player cant deal damage without fighting
                            self.message_timer = pygame.time.get_ticks()
                            self.state = "SELECTING"

                    elif self.state == "MERCY":
                        # player gets two chances to show mercy
                        if self.mercy_count == 0:
                            self.mercy_message = "Mercy? MERCYYYY???"
                            self.mercy_count += 1
                            self.mercy_timer = pygame.time.get_ticks()
                            self.message_timer = pygame.time.get_ticks()
                        elif self.mercy_count == 1:
                            self.mercy_message = "what a wuss..."
                            self.mercy_count += 1
                            self.mercy_timer = pygame.time.get_ticks()
                            self.message_timer = pygame.time.get_ticks()
                            self.mercy_shown = True

                elif event.key == pygame.K_ESCAPE:
                    # return to game
                    global current_screen
                    current_screen = "start_game"
                    self.enemy.in_battle = False  

    def user_item(self):
        # use butterknife to attack the enemy
        self.enemy_current_hp -= self.butterknife_damage
        if self.enemy_current_hp < 0:
            self.enemy_current_hp = 0
        self.message = f"You used the butterknife! Enemy lost {self.butterknife_damage} HP!"
        self.message_timer = pygame.time.get_ticks()
        self.item_enabled = False
        self.has_fought = False 
        self.item_timer = pygame.time.get_ticks()

    def handle_dodging_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.battle_player_x -= self.battle_player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.battle_player_x += self.battle_player_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.battle_player_y -= self.battle_player_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.battle_player_y += self.battle_player_speed

        # clamp movement inside dodging box
        dodge_box_x = self.box_x - 50
        dodge_box_y = self.box_y - 50
        dodge_box_width = self.box_width + 100
        dodge_box_height = self.box_height + 100

        self.battle_player_x = max(dodge_box_x, min(self.battle_player_x, dodge_box_x + dodge_box_width - self.heart_width))
        self.battle_player_y = max(dodge_box_y, min(self.battle_player_y, dodge_box_y + dodge_box_height - self.heart_height))

    def update(self):
        current_time = pygame.time.get_ticks()
        global current_screen
        
        if self.state == "DODGING":
            # inititialise dodging timer if first frame
            if self.dodging_timer is None:
                self.dodging_timer = current_time
                self.last_wave_time = current_time  # initialise wave timer
                self.spawn_bullet_wave()  # first wave immediately
                
            self.handle_dodging_input()
            elapsed_time = current_time - self.dodging_timer
            
            # end dodging phase after duration
            if elapsed_time >= self.dodging_duration:
                self.state = "SELECTING"
                self.turn = "PLAYER"
                self.bullets.clear()
                self.dodging_timer = None
            # spawn new wave every 800ms (instead of 2000ms)
            elif current_time - self.last_wave_time > 800:  # faster wave frequency
                self.spawn_bullet_wave()
                self.last_wave_time = current_time
            
            # check if enemy HP is 0 (i.e. enemy defeated)
            if self.enemy_current_hp <= 0:
                self.enemy_current_hp = 0
                self.enemy.in_battle = True  # prevent future battle
                self.enemy.mercy_shown = True  # same logic as mercy
                 # LEVEL UP
                new_level = self.player.player_level + 1
                update_player_level(current_username, new_level)  # save to DB
                self.player.player_level = new_level  # update player object too

                # SAVE CHECKPOINT
                update_player_room(current_username, "room2")  # store current room

                # return to game
                current_screen = "start_game"
                current_room_name = [name for name, room in rooms.items() if room == current_room][0]
                switch_room(current_room_name)

                return
            
            # update and check all bullets
            for bullet in self.bullets[:]:  # use copy for safe removal
                status = bullet.update()
                
                # check if bullet hit player or expired
                player_rect = pygame.Rect(self.battle_player_x, self.battle_player_y, 
                                        self.heart_width, self.heart_height)
                if bullet.check_collision(player_rect):
                    self.player.current_hp -= self.damage_per_hit
                    self.bullets.remove(bullet)
                    
                    if self.player.current_hp <= 0:
                        self.player.current_hp = 0
                        self.game_over = True
                        return
                elif status == "expired":
                    self.bullets.remove(bullet)
        
        elif self.state == "ITEM" and self.item_timer:
            if current_time - self.item_timer > self.item_duration:
                self.state = "SELECTING"
                self.turn = "ENEMY"
                self.item_timer = None

        elif self.mercy_timer:
            elapsed = pygame.time.get_ticks() - self.mercy_timer
            if elapsed > 2000: # 2 seconds
                if self.mercy_count == 1:
                    self.state = "SELECTING"
                    self.mercy_timer = None
                elif self.mercy_count >= 2 and self.mercy_shown:
                    # exit battle after second mercy
                    current_screen = "start_game"
                    self.enemy.mercy_shown = True
                    # mark enemy so it won't battle again
                    self.enemy.in_battle = True
                    # reset mercy state for next potential battle
                    self.mercy_count = 0
                    self.mercy_timer = None
                    # get the current room name from the rooms dictionary
                    
                    # return to game
                    current_screen = "start_game"
                    current_room_name = [name for name, room in rooms.items() if room == current_room][0]
                    switch_room(current_room_name)
                    player.x = 600
                    player.y = 450

    
    
    def spawn_bullet_wave(self):
        attack_type = random.choice(["spread", "targeted"])
            
        if attack_type == "spread":
            wave_size = random.randint(3, 5)
            for i in range(wave_size):
                # spawn bullets at top of battle box (not screen top)
                x = random.randint(self.box_x + 20, self.box_x + self.box_width - 20)  # within box width
                y = self.box_y - 30  # top of the battle box
                self.bullets.append(Bullet(
                    (x, y),  # start position (pixels)
                    (0, 0),  # dummy target
                    current_room.get_grid(),
                    speed_y=random.uniform(4, 8)  # faster vertical speed
                ))
        
        elif attack_type == "targeted":
            # lock onto current player position in grid
            player_grid_x = int((self.battle_player_x - current_room.boundaries[0]) // TILE_SIZE)
            player_grid_y = int((self.battle_player_y - current_room.boundaries[2]) // TILE_SIZE)

            # spawn from tiles near the top of the box
            for dx in range(-2, 3):  # try several x around player
                start_x = self.battle_player_x + dx * TILE_SIZE
                start_y = self.box_y - 10
                start_grid_x = int((start_x - current_room.boundaries[0]) // TILE_SIZE)
                start_grid_y = int((start_y - current_room.boundaries[2]) // TILE_SIZE)

                if 0 <= start_grid_x < GRID_WIDTH and 0 <= start_grid_y < GRID_HEIGHT:
                    path = astar_pathfinding(current_room.get_grid(), 
                                            (start_grid_x, start_grid_y), 
                                            (player_grid_x, player_grid_y))
                    if path:
                        self.bullets.append(Bullet(
                            (start_grid_x, start_grid_y),     # spawn near top
                            (player_grid_x, player_grid_y),   # path to where player *was*
                            current_room.get_grid(),
                            speed=3
                        ))
                        break  # spawn only one per wave for now



# input boxes and subtitles
username_box = Input_Box(600, 400, 250, 50)
username_box.set_font_size(40)
username_subtitle = Text('USERNAME', 500, 400, orange, box_subtitle_font)

password_box = Password_Box(600, 480, 250, 50)
password_box.set_font_size(40)
password_subtitle = Text('PASSWORD', 500, 480, orange, box_subtitle_font)

passwordcheck_box = Password_Box(600, 560, 250, 50)
confirm_password_subtitle = Text('CONFIRM PASSWORD', 430, 567, orange, box_subtitle_font)

# buttons and titles
login_button = Button('LOGIN', 650, 300, orange, button_font)
controls_button = Button('CONTROLS', 650, 400, orange, button_font)
exit_button = Button('EXIT', 650, 500, orange, button_font)
login_subtitle = Text('LOGIN', 650, 275, orange, subtitle_font)

create_account_button = Button('CREATE ACCOUNT', 650, 550, orange, button_font)
submit_button = Button('SUBMIT', 1100, 430, yellow, button_font)
back_button = Button('BACK', 140, 40, red, button_font)
backTOP_button = Button('BACK', 140, 40, red, button_font)

switch_button = Button('SWITCH?', 1110, 40, red, button_font)
WASD_subtitle = Text('USING WASD', 650, 40, blue, subtitle_font, duration = 3000)
ARROWS_subtitle = Text('USING ARROWS', 650, 40, blue, subtitle_font, duration = 3000)

create_account_subtitle = Text('CREATE AN ACCOUNT', 650, 275, orange, subtitle_font)
validation1_subtitle = Text('Username cannot be empty!', 200, 400, orange, subtitle_font)
validation2_subtitle = Text('Password cannot be empty!', 200, 400, orange, subtitle_font)
validation3_subtitle = Text('Password must be at least 8 characters long!', 200, 400, orange, subtitle_font)
validation4_subtitle = Text('Passwords do not match!', 200, 400, orange, subtitle_font)
success_subtitle = Text('Success!', 200, 400, orange, subtitle_font)

username_exists_subtitle = Text('Username already exists!', 200, 400, orange, subtitle_font)
create_account_boxes = [username_box, password_box, passwordcheck_box]

room1_subtitle = Text('GO FORTH...', 650, 150, pink, subtitle_font)

game_over_text = Text('GAME OVER', 650, 200, red, subtitle_font)
retry_button = Button('RETRY', 650, 400, orange, button_font)

# INITIALISING PLAYER/ENEMY
sprite_sheet = pygame.image.load("cows_spritesheet_white_pinkspots.png").convert_alpha()
enemy_sprite_sheet = pygame.image.load("Carrot-sheet.png").convert_alpha()
# CREATING PLAYER/ENEMY INSTANCE
player = Player(600, 400, sprite_sheet)
enemy = Enemy(500, 300, enemy_sprite_sheet)

# load battle images
player_battle_image = pygame.image.load("cow_battle.png").convert_alpha()  
enemy_battle_image = pygame.image.load("carrot_battle.png").convert_alpha()  
soul_image = pygame.Surface((20, 20))
soul_image.fill(red)


# INSTANTIATING ROOMS
room1 = Room (
    "room1.png", # background
    [ 
    pygame.Rect(50, 300, 1300, 100),
    pygame.Rect(10, 300, 20, 400),
    pygame.Rect(1200, 400, 200, 95),
    pygame.Rect(1200, 598, 200, 95),
    pygame.Rect(400, 598, 55, 95),
    pygame.Rect(400, 390, 55, 95),
    pygame.Rect(825, 598, 55, 95),
    pygame.Rect(825, 390, 55, 95),
    pygame.Rect(50, 665, 1300, 100) # obstacles 
    ],
    (0, 1300 - player.new_width, 0, 720 - player.new_height) # boundaries
)

room2 = Room(
    "room2.png",  # background
    [   # define obstacles for room2
        pygame.Rect(50, 150, 1300, 100),
        pygame.Rect(10, 300, 45, 400),
        pygame.Rect(1200, 450, 200, 150),
        pygame.Rect(1200, 250, 200, 95),
        pygame.Rect(90, 598, 1300, 95),
        pygame.Rect(80, 370, 240, 300),
    ],
    (0, 1300 - player.new_width, 0, 720 - player.new_height)  # boundaries
)

room3 = Room(
    "room3.png", # background
    [
        pygame.Rect(0, 200, 1300, 100),   # top wall
        pygame.Rect(0, 550, 1300, 100),   # bottom wall
        pygame.Rect(1260, 470, 70, 200),  # column on right
    ],
    (0, 1300 - player.new_width, 0, 720 - player.new_height)
)

enemy1 = Enemy(300, 300, enemy_sprite_sheet, move_range=(250, 400))   # 1/4 of width
enemy2 = Enemy(650, 300, enemy_sprite_sheet, move_range=(600, 700))   # 1/2 of width
enemy3 = Enemy(1000, 300, enemy_sprite_sheet, move_range=(950, 1100)) # 3/4 of width

room3_enemies = [enemy1, enemy2, enemy3]


rooms = {
    "room1" : room1,
    "room2" : room2,
    "room3" : room3
    }

current_room = rooms["room1"]


# screen control
current_screen = "main_menu"





while True:
    if current_screen == "main_menu":
        screen.blit(background_image, (0, 0))
        login_button.draw()
        controls_button.draw()
        exit_button.draw()  # drawing display MAIN MENU

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if exit_button.check_if_clicked(event):
                pygame.quit()
                exit()
            if login_button.check_if_clicked(event):
                current_screen = "login"
                username_box.clear_input()
                password_box.clear_input()  # clears boxes so the user can login without having to delete previous entries
            if controls_button.check_if_clicked(event):
                current_screen = "controls"

        pygame.display.update()

    elif current_screen == "login":
        screen.blit(background_image, (0, 0))
        login_subtitle.draw()
        create_account_button.draw()
        username_box.display()
        username_subtitle.draw()
        password_box.display()
        password_subtitle.draw()
        submit_button.draw()
        back_button.draw() # drawing display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if create_account_button.check_if_clicked(event):
                current_screen = "create_account"
                username_box.clear_input()
                password_box.clear_input()
                passwordcheck_box.clear_input()
            username_box.handle_event(event)
            password_box.handle_event(event) # handling submissions by taking input and clearing boxes for the user so that they can then login

            # back button Logic
            if back_button.check_if_clicked(event):
                current_screen = "main_menu"

            # submit button Logic
            if submit_button.check_if_clicked(event):
                username = username_box.input.strip()
                password = password_box.password.strip()

                if not username: # input validation - presence check
                    error_message = "Username cannot be empty!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Username cannot be empty!")
                elif not password:
                    error_message = "Password cannot be empty!" # presence check
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Password cannot be empty!")
                elif not username_exists(username):
                    error_message = "Username does not exist!" # checks if existing account is in database
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Username does not exist!")
                elif not verify_user(username, password): # checks for correct password
                    error_message = "Incorrect password!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Incorrect password!")
                else:
                    error_message = "Login Successful!" # successful login
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print(f"Login successful: USERNAME: {username}")
                    current_screen = "start_game"
                    saved_room = get_saved_room(username)
                    switch_room(saved_room)
                    player.x = 600
                    player.y = 500
                    player.player_level = get_player_level(username)
                    

        # display the feedback message if still active
        current_time = pygame.time.get_ticks()
        if error_message and current_time < error_display_end_time:
            message_surf = subtitle_font.render(error_message, True, blue)
            message_rect = message_surf.get_rect(center=(650, 100))  # Adjust position as needed
            screen.blit(message_surf, message_rect)
        elif current_time >= error_display_end_time:
            error_message = ""

        pygame.display.update()

    elif current_screen == "create_account":
        screen.blit(background_image, (0, 0))
        create_account_subtitle.draw()
        username_box.display()
        username_subtitle.draw()
        password_box.display()
        password_subtitle.draw()
        passwordcheck_box.display()
        confirm_password_subtitle.draw()
        submit_button.draw()
        back_button.draw() # draws display

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # back button logic
            if back_button.check_if_clicked(event):
                current_screen = "login"
                username_box.clear_input()
                password_box.clear_input()
                passwordcheck_box.clear_input()

            username_box.handle_event(event)
            password_box.handle_event(event)
            passwordcheck_box.handle_event(event)

            # submit button logic
            if submit_button.check_if_clicked(event):
                username = username_box.input.strip()
                password = password_box.password.strip()
                confirm_password = passwordcheck_box.password.strip()

                if not username:
                    error_message = "Username cannot be empty!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Username cannot be empty!")
                elif username_exists(username):
                    error_message = "Username already exists!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Error: Username already exists!")
                elif not password:
                    error_message = "Password cannot be empty!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Password cannot be empty!")
                elif len(password) < 8:
                    error_message = "Password must be at least 8 characters long!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Password must be at least 8 characters long!")
                elif password != confirm_password: # checks if the two inputted passwords match
                    error_message = "Passwords do not match!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Passwords do not match!")
                else:
                    try:
                        # hashing password before storing
                        hashed_password = hashing(password)

                        # inserting data into the database
                        conn = sqlite3.connect("UDD_database.db")
                        cur = conn.cursor()
                        cur.execute(
                            '''
                            INSERT INTO TBL_Player (username, password, room_num)
                            VALUES (?, ?, ?)
                            ''',
                            (username, hashed_password, 0)  # placeholder for room number
                        )
                        conn.commit()
                        conn.close()

                        success_subtitle.draw()
                        print(f"Account created successfully: USERNAME: {username}, PASSWORD: {password}")
                        current_screen = "login"
                        username_box.clear_input()
                        password_box.clear_input()
                        passwordcheck_box.clear_input()
                    except sqlite3.IntegrityError:
                        error_message = "Username already exists!"
                        error_display_end_time = pygame.time.get_ticks() + error_duration
                        print("Error: Username already exists!")
            

        # display the error message if still active.
        current_time = pygame.time.get_ticks()
        if error_message and current_time < error_display_end_time:
            error_surf = subtitle_font.render(error_message, True, blue)
            error_rect = error_surf.get_rect(center=(650, 100))  # adjust position as needed
            screen.blit(error_surf, error_rect)
        elif current_time >= error_display_end_time:
            error_message = ""

        pygame.display.update()

    elif current_screen == "controls":
        screen.blit(controls1_image, (0, 0))  # draw background image
        backTOP_button.draw()  # back button to return to main menu
        switch_button.draw() # switch to alternative controls

        ARROWS_subtitle.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # back button logic
            if backTOP_button.check_if_clicked(event):
                current_screen = "main_menu"

            if switch_button.check_if_clicked(event):
                player.control_mode = "wasd"  # switch to wasd controls
                current_screen = "altcontrols"
                print("Switched to WASD controls") # debugging
                ARROWS_subtitle.start_timer()
                    

        pygame.display.update()

    elif current_screen == "altcontrols":
        screen.blit(controls2_image, (0, 0))  # draw background image
        backTOP_button.draw()  # back button to return to main menu
        switch_button.draw() # switch to alternative controls

        WASD_subtitle.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # back button logic
            if backTOP_button.check_if_clicked(event):
                current_screen = "main_menu"

            if switch_button.check_if_clicked(event):
                player.control_mode = "arrows"  # switch to arrow key controls
                current_screen = "controls"
                print("Switched to arrow key controls") # debugging
                WASD_subtitle.start_timer()
                    
        pygame.display.update()

    elif current_screen == "start_game":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        player.update()

        # drawing background and sprite
        current_room.draw()
        player.draw(screen)

        # ensure timer starts when entering the room
        if room1_subtitle_timer is None:
            room1_subtitle_timer = pygame.time.get_ticks()  # set the start time

        # check if less than 3 seconds have passed
        if current_room == "room1": 
            if pygame.time.get_ticks() - room1_subtitle_timer < room1_subtitle_duration:
                room1_subtitle.draw()  # only display while within the time limit

        if current_room == room2:
            previous_room_name = [name for name, room in rooms.items() if room == current_room][0]
            # only check collision if mercy hasn't been shown
            if not enemy.mercy_shown and enemy.check_collision(player) and not enemy.in_battle:
                enemy.in_battle = True
                current_screen = "battle"
                battle_transition_time = pygame.time.get_ticks()
            # checks for collision before updating enemy
            if not enemy.mercy_shown:
                enemy.update()
                enemy.draw(screen)

            enemy.update()
            enemy.draw(screen)

        elif current_room == room3:
            for enemy in room3_enemies:
                if not enemy.mercy_shown and enemy.check_collision(player) and not enemy.in_battle:
                    enemy.in_battle = True
                    current_screen = "battle"
                    battle_transition_time = pygame.time.get_ticks()
                    current_battle = Battle(player, enemy)  # start battle with this enemy
                if not enemy.mercy_shown:
                    enemy.update()
                    enemy.draw(screen)
                
        # display player level top right
        level_display = pygame.font.Font('pixelFont.ttf', 30).render(f"LV {player.player_level}", True, white)
        level_rect = level_display.get_rect(topright=(1280, 10))  # Adjust to fit within 1300px width
        screen.blit(level_display, level_rect)
        

        pygame.display.flip()
        clock.tick(60)

    elif current_screen == "battle":
        # initialise battle if it's the first time
        if 'current_battle' not in globals():
            current_battle = Battle(player, enemy)
        
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            
            # handle battle inputs
            current_battle.handle_input(event)
        
        # draw battle window and update logic
        current_battle.update()
        current_battle.draw(screen)

        if current_battle.game_over:
            current_screen = "game_over"
            # reset player stats for new attempt
            player.x = 600  # starting position
            player.y = 500
            player.current_hp = player.max_hp  # reset health
            enemy.in_battle = False  # reset enemy state

        pygame.display.flip()
        clock.tick(60)

    elif current_screen == "game_over":
        screen.fill((0, 0, 0,))
        game_over_text.draw()
        retry_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if retry_button.check_if_clicked(event):
                current_screen = "start_game"

                # load checkpoint room
                saved_room = get_saved_room(current_username)
                switch_room(saved_room)

                # reset player stats
                player.current_hp = player.max_hp
                player.x = 600
                player.y = 500

                # reset enemy state based on room
                if saved_room == "room2":
                    enemy.in_battle = False
                    enemy.mercy_shown = False
                    enemy.defeated = False
                    enemy.x = 500
                    enemy.y = 300

                elif saved_room == "room3":
                    for e in room3_enemies:
                        e.in_battle = False
                        e.mercy_shown = False
                        e.defeated = False
                        e.x = 600
                        e.y = 450

                enemy.in_battle = False  # reset enemy state
                enemy.x = 500
                enemy.y = 300

                # clear any existing battle
                if 'current_battle' in globals():
                    del current_battle
            
        pygame.display.flip()
        clock.tick(60)

    pygame.display.flip()
    clock.tick(60)

    
 