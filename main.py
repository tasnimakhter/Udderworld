import pygame
import unicodedata
import sqlite3

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1300, 720))
pygame.display.set_caption('UDDERWORLD')

# Load the background image once outside the loop
background_image = pygame.image.load('background.png').convert()
controls1_image = pygame.image.load('controls1.png').convert()
controls2_image = pygame.image.load('controls2.png').convert()


# Font colors
orange = (255, 69, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)
yellow = (255, 255, 0)

# TEXT FONT AND TEXT DEFINITIONS
subtitle_font = pygame.font.Font('pixelFont.ttf', 80)
box_subtitle_font = pygame.font.Font('pixelFont.ttf', 30)
button_font = pygame.font.Font('pixelFont.ttf', 75)
username_font = pygame.font.Font('pixelFont.ttf', 40)

# login messages handling
error_message = ""
error_display_end_time = 0  # Time in milliseconds when error should disappear
error_duration = 3000  # Duration in ms (e.g., 3000ms = 3 seconds)


# database design
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
    # If no row is found, username doesn't exist; otherwise, compare passwords.
    return row is not None and row[0] == password




# OOP INPUT CLASS
class Input_Box:
    def __init__(self, x, y, width, height, input=''):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.input = str(input)  # Ensure input is always a string
        self.color = orange
        self.selected = False
        self.font = username_font  # Default font
        self.backspace_timer = 0
        self.backspace_delay = 200  # Delay in milliseconds
        self.rect = pygame.Rect(x, y, width, height)
        self.max_width = self.width - 10

    def set_font_size(self, size):
        # Updates the font size for the input box
        self.font = pygame.font.Font('pixelFont.ttf', size)

    def truncate_input(self):
        # Ensures the input text fits within the input box by truncating if necessary
        while self.font.render(self.input, True, self.color).get_width() > self.max_width:
            self.input = self.input[:-1]

    def display(self):
        # Render the input text inside the box
        pygame.draw.rect(screen, (0, 0, 0), self.rect)  # Draw background
        pygame.draw.rect(screen, self.color, self.rect, 2)  # Draw border
        input_text = self.input if isinstance(self.input, str) else ""
        input_surf = self.font.render(input_text, True, self.color)
        screen.blit(input_surf, (self.x + 5, self.y + 5))  # Render text with padding

    def handle_event(self, event):
        # Handle mouse click and key press events for input boxes
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activate box if clicked
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
        # Clear the input text
        self.input = ""

# password box - asterisk for privacy, inherited from the input box
class Password_Box(Input_Box):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.password = ""  # stores actual password

    def display(self):
        # Display original password as asterisks
        pygame.draw.rect(screen, (0, 0, 0), self.rect)  # Box background
        pygame.draw.rect(screen, self.color, self.rect, 2)  # Box border
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
        # Ensure the password stays within the box
        while self.font.render("*" * len(self.password), True, self.color).get_width() > self.max_width:
            self.password = self.password[:-1]

    def clear_input(self):
        # Clear the password text
        self.password = ""

# OOP TEXT CLASS

class Text:
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.text_surf = self.font.render(self.text, True, self.color)
        self.rect = self.text_surf.get_rect(midtop=(self.x, self.y))

    # DISPLAY TEXT METHOD
    def draw(self):
        screen.blit(self.text_surf, self.rect)

# OOP BUTTON CLASS - SUBCLASS OF TEXT CLASS (inherits)
class Button(Text):
    def __init__(self, text, x, y, color, font):
        super().__init__(text, x, y, color, font)

    def check_if_clicked(self, event):
        # Return True only if the button is clicked and the mouse button is released
        if event.type == pygame.MOUSEBUTTONUP and self.rect.collidepoint(pygame.mouse.get_pos()):
            return True
        return False

# Input Boxes & Subtitles
username_box = Input_Box(600, 400, 250, 50)
username_box.set_font_size(40)
username_subtitle = Text('USERNAME', 500, 400, orange, box_subtitle_font)

password_box = Password_Box(600, 480, 250, 50)
password_box.set_font_size(40)
password_subtitle = Text('PASSWORD', 500, 480, orange, box_subtitle_font)

passwordcheck_box = Password_Box(600, 560, 250, 50)
confirm_password_subtitle = Text('CONFIRM PASSWORD', 430, 567, orange, box_subtitle_font)

# Buttons and Titles
login_button = Button('LOGIN', 650, 300, orange, button_font)
controls_button = Button('CONTROLS', 650, 400, orange, button_font)
exit_button = Button('EXIT', 650, 500, orange, button_font)
login_subtitle = Text('LOGIN', 650, 275, orange, subtitle_font)

create_account_button = Button('CREATE ACCOUNT', 650, 550, orange, button_font)
submit_button = Button('SUBMIT', 1100, 430, yellow, button_font)
back_button = Button('BACK', 200, 600, red, button_font)
backTOP_button = Button('BACK', 140, 40, red, button_font)

switch_button = Button('SWITCH?', 1110, 40, red, button_font)

create_account_subtitle = Text('CREATE AN ACCOUNT', 650, 275, orange, subtitle_font)
validation1_subtitle = Text('Username cannot be empty!', 200, 400, orange, subtitle_font)
validation2_subtitle = Text('Password cannot be empty!', 200, 400, orange, subtitle_font)
validation3_subtitle = Text('Password must be at least 8 characters long!', 200, 400, orange, subtitle_font)
validation4_subtitle = Text('Passwords do not match!', 200, 400, orange, subtitle_font)
success_subtitle = Text('Success!', 200, 400, orange, subtitle_font)

username_exists_subtitle = Text('Username already exists!', 200, 400, orange, subtitle_font)



create_account_boxes = [username_box, password_box, passwordcheck_box]

# Screen Control
current_screen = "main_menu"



while True:
    if current_screen == "main_menu":
        screen.blit(background_image, (0, 0))
        login_button.draw()
        controls_button.draw()
        exit_button.draw()

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
                password_box.clear_input()
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
        back_button.draw()

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
            password_box.handle_event(event)

            # Back Button Logic
            if back_button.check_if_clicked(event):
                current_screen = "main_menu"

            # Submit Button Logic
            if submit_button.check_if_clicked(event):
                username = username_box.input.strip()
                password = password_box.password.strip()

                if not username:
                    error_message = "Username cannot be empty!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Username cannot be empty!")
                elif not password:
                    error_message = "Password cannot be empty!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Password cannot be empty!")
                elif not username_exists(username):
                    error_message = "Username does not exist!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Username does not exist!")
                elif not verify_user(username, password):
                    error_message = "Incorrect password!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Incorrect password!")
                else:
                    error_message = "Login Successful!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print(f"Login successful: USERNAME: {username}")
                    # If desired, change current_screen or proceed further after a successful login

        # Display the feedback message (error or success) if it's still active
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
        back_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Back Button Logic
            if back_button.check_if_clicked(event):
                current_screen = "login"
                username_box.clear_input()
                password_box.clear_input()
                passwordcheck_box.clear_input()

            username_box.handle_event(event)
            password_box.handle_event(event)
            passwordcheck_box.handle_event(event)

            # Submit Button Logic
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
                elif password != confirm_password:
                    error_message = "Passwords do not match!"
                    error_display_end_time = pygame.time.get_ticks() + error_duration
                    print("Passwords do not match!")
                else:
                    try:
                        # Inserting data into the database
                        conn = sqlite3.connect("UDD_database.db")
                        cur = conn.cursor()
                        cur.execute(
                            '''
                            INSERT INTO TBL_Player (username, password, room_num)
                            VALUES (?, ?, ?)
                            ''',
                            (username, password, 0)  # Placeholder for room number
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

        # Display the error message if it is still active.
        current_time = pygame.time.get_ticks()
        if error_message and current_time < error_display_end_time:
            error_surf = subtitle_font.render(error_message, True, blue)
            error_rect = error_surf.get_rect(center=(650, 100))  # Adjust position as needed
            screen.blit(error_surf, error_rect)
        elif current_time >= error_display_end_time:
            error_message = ""

        pygame.display.update()

    elif current_screen == "controls":
        screen.blit(controls1_image, (0, 0))  # Draw background image
        backTOP_button.draw()  # Back button to return to main menu
        switch_button.draw() # Switch to alternative controls

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # Back Button Logic
            if backTOP_button.check_if_clicked(event):
                current_screen = "main_menu"

            if switch_button.check_if_clicked(event):
                current_screen = "altcontrols"
                print("switching to altcontrols") # debugging
                print(f"Current screen: {current_screen}")
                

        pygame.display.update()

    elif current_screen == "altcontrols":
        screen.blit(controls2_image, (0, 0))  # Draw background image
        backTOP_button.draw()  # Back button to return to main menu
        switch_button.draw() # Switch to alternative controls

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()


            # Back Button Logic
            if backTOP_button.check_if_clicked(event):
                current_screen = "main_menu"

            if switch_button.check_if_clicked(event):
                current_screen = "controls"
                print("switching to controls")
                print(f"Current screen: {current_screen}")


        pygame.display.update()


    clock.tick(60)
