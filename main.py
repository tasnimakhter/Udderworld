import pygame
import sqlite3
import hashlib

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1300, 720))
pygame.display.set_caption('UDDERWORLD')

# load the background image once outside the loop
background_image = pygame.image.load('background.png').convert()
controls1_image = pygame.image.load('controls1.png').convert()
controls2_image = pygame.image.load('controls2.png').convert()
room1_image = pygame.image.load('room1.png').convert()
rescaled_image = pygame.transform.scale(room1_image, (1300, 720))
room1_image = rescaled_image
room1_subtitle_timer = None
room1_subtitle_duration = 3000

# font colours
orange = (255, 69, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)
pink = (255, 16, 240)

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
conn.close()

def username_exists(username):
    conn = sqlite3.connect("UDD_database.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM TBL_Player WHERE username = ?", (username,))
    result = cur.fetchone()
    conn.close()
    return result if result is not None else False

def verify_user(username, password):
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

def switch_room(room_name):
    global current_room
    current_room = rooms[room_name]  # Change to the new room
    
    # puts player at entrance
    if room_name == "room2":
        player.x = 80  # starting pos in new room
        player.y = 250  # adjust to match entrance alignment
    elif room_name == "room1":
        player.x = 10  # puts player at the exit of room2
        player.y = 500

# PLAYER CLASS
class Player: 
    def __init__(self, x, y, sprite_sheet, scale_factor = 2):
        self.x = x
        self.y = y
        self.speed = 3
        self.scale_factor = scale_factor
        self.control_mode = "arrows" # default controls

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
            switch_room("room2")

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


# ROOM CLASS
class Room:
        def __init__(self, background_image, unwalkablle_areas, boundaries):
            self.background = pygame.image.load(background_image).convert()
            self.unwalkable_areas = unwalkablle_areas # list of pygame.Rect obj
            self.boundaries = boundaries # left right top bottom

        def draw(self): # draws bg and collision areas
            screen.blit(pygame.transform.scale(self.background, (1300, 720)), (0,0))

            #for area in self.unwalkable_areas:
            #    pygame.draw.rect(screen, (0, 0, 255), area, 2) 


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
back_button = Button('BACK', 200, 600, red, button_font)
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


# INITIALISING PLAYER
sprite_sheet = pygame.image.load("cows_spritesheet_white_pinkspots.png").convert_alpha()
# CREATING PLAYER INSTANCE
player = Player(600, 400, sprite_sheet)

blue

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

rooms = {
    "room1" : room1,
    "room2" : room2,
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

        # drawing background
        current_room.draw()
        player.update()
        player.draw(screen)

        # ensure timer starts when entering the room
        if room1_subtitle_timer is None:
            room1_subtitle_timer = pygame.time.get_ticks()  # set the start time

        # check if less than 3 seconds have passed
        if pygame.time.get_ticks() - room1_subtitle_timer < room1_subtitle_duration:
            room1_subtitle.draw()  # only display while within the time limit

        # update and draw sprite
        player.draw(screen)



        pygame.display.flip()
        clock.tick(60)


    clock.tick(60)
 