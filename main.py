import pygame
import unicodedata

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1300, 720))
pygame.display.set_caption('UDDERWORLD')

# Load the background image once outside the loop
background_image = pygame.image.load('background.png').convert()
controls1_image = pygame.image.load('controls1-1.png').convert()
controls2_image = pygame.image.load('controls2-1.png').convert()

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
create_account_submit_button = Button('SUBMIT', 1100, 430, yellow, button_font)
back_button = Button('BACK', 200, 600, red, button_font)
backTOP_button = Button('BACK', 140, 40, red, button_font)

switch_button = Button('SWITCH?', 1110, 40, red, button_font)

create_account_subtitle = Text('CREATE AN ACCOUNT', 650, 275, orange, subtitle_font)
validation1_subtitle = Text('Username cannot be empty!', 200, 400, orange, subtitle_font)
validation2_subtitle = Text('Password cannot be empty!', 200, 400, orange, subtitle_font)
validation3_subtitle = Text('Password must be at least 8 characters long!', 200, 400, orange, subtitle_font)
validation4_subtitle = Text('Passwords do not match!', 200, 400, orange, subtitle_font)
success_subtitle = Text('Success!', 200, 400, orange, subtitle_font)


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
        create_account_submit_button.draw()
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
<<<<<<< Updated upstream
          
=======
>>>>>>> Stashed changes

            # Submit Button Logic
            if create_account_submit_button.check_if_clicked(event):
                username = username_box.input.strip()
                password = password_box.password.strip()

                if not username:
                    print("Username cannot be empty!")
                    validation1_subtitle.draw()
                elif not password:
                    print("Password cannot be empty!")
                    validation2_subtitle.draw()
                elif len(password) < 8:
                    print("Password must be at least 8 characters long!")
                    validation3_subtitle.draw()
                else:
                    success_subtitle.draw()
                    print(f"Inputs submitted: USERNAME: {username}, PASSWORD: {password}")

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
        create_account_submit_button.draw()
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
            if create_account_submit_button.check_if_clicked(event):
                username = username_box.input.strip()
                password = password_box.password.strip()
                confirm_password = passwordcheck_box.password.strip()

                if not username:
                    validation1_subtitle.draw()
                    print("Username cannot be empty!")
                elif not password:
                    validation2_subtitle.draw()
                    print("Password cannot be empty!")
                elif len(password) < 8:
                    validation3_subtitle.draw()
                    print("Password must be at least 8 characters long!")
                elif password != confirm_password:
                    validation4_subtitle.draw()
                    print("Passwords do not match!")
                else:
                    success_subtitle.draw()
                    print(f"Account created successfully: USERNAME: {username}, PASSWORD: {password}")
                    current_screen = "login"
                    username_box.clear_input()
                    password_box.clear_input()
                    passwordcheck_box.clear_input()

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
                current_screen == "altcontrols"
                

        pygame.display.update()

    elif current_screen == "altcontrols":
        screen.blit(controls2_image, (0, 0))  # Draw background image
        ''' the button pics aren't right and text should be in yellow not green, go back on ppt and change this image, also the screen image will not switch for some reason '''
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
                current_screen == "controls"

        pygame.display.update()


    clock.tick(60)
