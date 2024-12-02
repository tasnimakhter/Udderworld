import pygame
import unicodedata

pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((1300, 720))
pygame.display.set_caption('UDDERWORLD')

# Load the background image once outside the loop
background_image = pygame.image.load('background.png').convert()

# Font colors
orange = (255, 69, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
green = (0, 255, 0)

# TEXT FONT AND TEXT DEFINITIONS
subtitle_font = pygame.font.Font('pixelFont.ttf', 80)
box_subtitle_font = pygame.font.Font('pixelFont.ttf', 30)
button_font = pygame.font.Font('pixelFont.ttf', 75)
username_font = pygame.font.Font('pixelFont.ttf', 40)

# LOOPS
mainMenu_loop = True
login_loop = False
controls_loop = False

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
        # Timer for backspace key handling
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
        # Ensure self.input is a string before rendering
        input_text = self.input if isinstance(self.input, str) else ""
        input_surf = self.font.render(input_text, True, self.color)
        screen.blit(input_surf, (self.x + 5, self.y + 5))  # Render text with padding

    def input_text(self, event):
        if event.type == pygame.KEYDOWN:
            # Remove the last character if backspace is pressed
            if event.key == pygame.K_BACKSPACE:
                current_time = pygame.time.get_ticks()
                if current_time - self.backspace_timer > self.backspace_delay:
                    self.input = self.input[:-1]  # Remove last character
                    self.backspace_timer = current_time  # Reset the timer

            # Add character unless tab, enter, or invalid key
            elif event.key != pygame.K_TAB and event.key != pygame.K_RETURN:
                if event.unicode:  # Ensure valid input
                    char = str(event.unicode)  # Convert to string
                    if char.isalnum() or char in "._@":  # Allow letters, numbers, and . _ @
                        self.input += char
                        self.truncate_input()

        elif event.type == pygame.KEYUP:
            # Reset timer when the key is released
            if event.key == pygame.K_BACKSPACE:
                self.backspace_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activate box if clicked
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.selected = True
                self.color = green
            else:
                self.selected = False
                self.color = red

        if self.selected and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]  # Remove the last character
            elif event.unicode and (event.unicode.isalnum() or event.unicode in "._@"):
                self.input += event.unicode
                self.truncate_input()

# password box - asterisk for privacy, inherited from the input box
# OOP Password Box Class
class Password_Box(Input_Box):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.password = "" # stores actual password

    def display(self):
        # Display masked password with asterisks
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
                self.color = green
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
        self.clicked = False

    def check_if_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.clicked = True
        return self.clicked

username_box = Input_Box(600, 400, 250, 50)
username_box.set_font_size(40)
username_subtitle = Text('USERNAME', 500, 400, orange, box_subtitle_font)
passwordcheck_box = Password_Box(300, 400, 200, 30)
password_box = Input_Box(600, 480, 250, 50)
password_box.set_font_size(40)
password_subtitle = Text('PASSWORD', 500, 480, orange, box_subtitle_font)
login_boxes = [username_box, password_box]
create_account_boxes = [username_box, password_box, passwordcheck_box]

# BUTTON OBJECTS & SUBTITLE
login_button = Button('LOGIN', 650, 300, orange, button_font)
controls_button = Button('CONTROLS', 650, 400, orange, button_font)
exit_button = Button('EXIT', 650, 500, orange, button_font)
login_subtitle = Text('LOGIN', 650, 275, orange, subtitle_font)
create_account_button = Button('create an account', 650, 550, orange, button_font)

# Game loop
while mainMenu_loop:
    screen.blit(background_image, (0, 0))
    login_button.draw()
    controls_button.draw()
    exit_button.draw()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            mainMenu_loop = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:  # Check if the ESC key is pressed
            mainMenu_loop = False
        if exit_button.check_if_clicked(event):
            mainMenu_loop = False
        if login_button.check_if_clicked(event):
            mainMenu_loop = False
            login_loop = True

    pygame.display.update()

while login_loop:
    for event in pygame.event.get():
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:  # Check if the ESC key is pressed
            login_loop = False
        if event.type == pygame.QUIT:
            login_loop = False
            mainMenu_loop = False
        if create_account_button.check_if_clicked(event):
            login_loop = False

        username_box.handle_event(event)
        password_box.handle_event(event)

    screen.blit(background_image, (0, 0))
    login_subtitle.draw()
    create_account_button.draw()
    username_box.display()
    username_subtitle.draw()
    password_box.display()
    password_subtitle.draw()



    pygame.display.update()
    clock.tick(60)

pygame.quit()

