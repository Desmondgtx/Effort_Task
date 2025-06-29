#!/usr/bin/env python3.10.9
# coding=utf-8

"""
Prosocial Effort Task (PET) - A neuroscience experiment to study prosocial behavior.
This experiment measures how much effort participants are willing to exert for themselves versus others.
Participants choose between a low-effort option (rest) for 1 credit or a higher-effort option 
(clicking on buttons) for more credits, both for themselves or for another participant.

tested in Python 3.10.9
"""
import pygame, sys, os, cv2
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_c
from os.path import join
from time import gmtime, strftime
from pylsl import StreamInfo, StreamOutlet  # Lab Streaming Layer for sending triggers to recording devices
from math import ceil, sqrt
import itertools
from random import shuffle

# Set to True for testing, disables LSL trigger sending
debug_mode = True

class TextRectException(Exception):
    """Custom exception for text rendering issues"""
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message

# Global configuration parameters:
FullScreenShow = True  # Run experiment in fullscreen mode
keys = [pygame.K_SPACE]  # Response keys (space bar)
test_name = "PET"        # Name of the experiment (Prosocial Effort Task)
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())  # Timestamp for data files

# Effort levels as percentages - will be converted to actual number of buttons
effort_levels = [20, 30, 40, 60, 70, 80]  
# Reward levels - credits earned for completing the task
credits_levels = [2, 3, 4, 5, 6, 7]  

# LSL trigger codes for synchronizing with physiological recordings:
start_trigger = 500  # Experiment start
stop_trigger = 550   # Experiment end
slide_trigger = 100  # New slide/instructions display
decision_start_trigger = 200  # Start of decision period
decision_made_trigger = 210   # Decision was made
not_decision_made_trigger = 250  # No decision made within time limit
start_task_trigger = 300       # Start of button-clicking task
last_button_pressed_trigger = 260  # All buttons clicked
correct_task_trigger = 350   # Task completed successfully
failed_task_trigger = 360    # Task failed
resting_trigger = 400        # Participant chose to rest

# How to divide trials into blocks
block_type = "division"  # Could be "division" or "total"

# Minimum number of buttons a participant must click in calibration
min_buttons = 10

# Practice settings
practice_iterations = 1      # Number of practice rounds
decision_practice_trials = 4  # Number of decision practice trials

# Number of experimental blocks
blocks_number = 3
max_answer_time = 10  # Maximum time (seconds) to complete button task
max_decision_time = 6  # Maximum time (seconds) to make a decision

# List of perfect squares and other "aesthetically pleasing" numbers for button layouts
optimal_square = [1, 2, 3, 4, 6, 8, 9, 12, 15, 16, 18, 20, 21, 24, 25, 27, 28, 30, 32, 35, 36, 40, 42, 45, 48, 49, 50]

# Button appearance configuration
base_button_color = (255, 255, 255)  # White
pressed_button_color = (0, 255, 0)   # Green

# Define text content for instruction slides
def select_slide(slide_name):
    """
    Returns the text content for a specific instruction slide.
    
    Args:
        slide_name (str): The name identifier of the slide to display
        
    Returns:
        list: List of text strings to display on the slide
    """
    if slide_name.startswith("intro_block"):
        slide_to_use = "intro_block"
    else:
        slide_to_use = slide_name

    basic_slides = {
        'welcome': [
            u"Bienvenido/a, a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer."
        ],
        'intro_block': [
            u"Ahora comenzará el " + ("primer" if len(slide_name.split("_")) == 3 and slide_name.split("_")[2] == "1" else "segundo" if len(slide_name.split("_")) == 3 and slide_name.split(
                "_")[2] == "2" else "tercer") + " bloque del experimento",
            " ",
            u"Puedes descansar unos segundos, cuando te sientas",
            u"listo para comenzar presiona Espacio para continuar."
        ],
        'Instructions_Casillas': [
            u"Tarea de las Casillas:",
            " ",
            u"Abajo puedes encontrar un esquema de la tarea",
            u"Tu meta es hacer click en el mayor número de casillas en 10 segundos. Esta tarea será mostrada 2 veces"
        ],
        'Interlude_Casillas': [
            u"¡Muy bien! Ahora INTENTA Y SUPERA TU RENDIMIENTO!"
        ],
        'Exit_Casillas': [
            u"Gracias por completar la tarea.",
            " ",
            u"Procede ahora a la siguiente pagina para las instrucciones de la próxima tarea."
        ],
        'Instructions_Decision_1': [
            u"Tarea de decisiones:",
            " ",
            u"En esta tarea, tú podrás hacer click en cierto número de casillas para ganar créditos que serán convertidos en dinero.",
            u"Estos créditos pueden ser otorgados a ti, o a otro/a participante de esta investigación",
            u"quien estará completando otro tipo de pruebas.",
            " ",
            u"Se te ha asignado el rol de Jugador 1, mientras que a otro/a participante se le ha asignado el rol de Jugador 2.",
            u"Esto significa que tomarás decisiones que afectarán al Jugador 2, pero él no tomará decisiones que te afecten a ti.",
            " ",
            u"En cada ronda de esta tarea, tendrás que elegir entre dos opciones:",
            " ",
            u'"Descansar": No tendrás que hacer click en ninguna casilla y podrás descansar a cambio de 1 crédito.',
            u'"Trabajar": Tendrás que hacer click en las casillas para ganar una mayor cantidad de créditos',
            " ",
            u"En algunas rondas (rondas TI), decidirás si quieres ganar créditos para ti mismo.",
            u"En otras rondas (rondas OTRO), decidirás si quieres ganar créditos para otro/a jugador/a anónimo/a.",
            u"Los créditos que ganes serán convertidos en dinero.",
            u"En rondas TI, tú recibirás este dinero. En las rondas OTRO, el dinero será recibido por otro jugador.",
            " ",
            u"Tus decisiones serán completamente anónimas y confidenciales."
        ],
        'Instructions_Decision_2': [
            u"A continuación puedes ver 2 casos de ejemplo,", 
            u"el primero es para un caso de decisión para TI y el segundo para OTRO"
        ],
        'Instructions_Decision_3': [
            u"Cada ronda mostrará 1 crédito por Descansar, y {} o {} créditos".format((', '.join(str(x) for x in credits_levels[:-1])), credits_levels[-1]),
            u"por hacer click a un determinado número de casillas.",
            " ",
            u"Tienes un máximo de {} segundos para responder.".format(max_decision_time), 
            u"Si tardas más de {} segundos, se darán 0 créditos a ti o a la otra persona dependiendo de la ronda.".format(max_decision_time),
            " ",
            u"Si eliges hacer click en las casillas para ganar más créditos,", 
            u"debes hacer click en todas las casillas en la pantalla en 10 segundos.",
            u"De lo contrario, no se otorgarán créditos para esa ronda.",
            " ",
            u"Siempre que elijas Descansar, podrás hacerlo durante 10 segundos y no tendrás que hacer click en ninguna casilla."
        ],
        'Instructions_Decision_final': [
            u"Recuerda, en cada ronda:",
            " ",
            u"• Verás si los créditos serán para TI beneficio o para al de un/a OTRO/A desconocido/a.",
            " ",
            u"• Debes escoger entre dos opciones: Una opción te da 1 crédito por descansar, la otra", 
            u"te da más créditos pero debes hacer click en un número de casillas.",
            " ",
            u"• Tendrás {} segundos para tomar una decisión, de lo contrario se darán 0 créditos para esa ronda.".format(max_decision_time),
            " ",
            u"Continúa con la página siguiente para una ronda de práctica. Aquí verás cómo se hace click en las casillas.", 
            u"Tu objetivo es hacer click en el número de casillas que se muestran en la pantalla.", 
            u"Ya que es sólo práctica, no se obtendrás créditos en estas rondas."
        ],
        'Effort_ending': [
            u"¡Genial! ya has practicado cómo hacer click en las casillas", 
            u"para así ganar créditos para TI o para a él/la OTRO/A participante.",
            " ",
            u"Ahora tendrás una ronda de práctica que es similar a la tarea que tendrás que realizar en este estudio.",
            u"Como fue dicho anteriormente, aquí podrás elegir entre Descansar y ganar 1 crédito,",
            u"o hacer click en las casillas para ganar una mayor cantidad de créditos. "
        ],
        'Practice_ending': [
            u"¡Excelente! Has completado la ronda de práctica.",
            " ",
            u"Ahora comenzarás con la tarea principal.",
            " ",
            u"Recuerda que en cada ronda tendrás que tomar una decisión entre Descansar y Trabajar.",
            u"Si eliges Trabajar, tendrás que hacer click en todas las casillas en la pantalla en 10 segundos.",
            u"Si eliges Descansar, podrás hacerlo durante 10 segundos y no tendrás que hacer click en ninguna casilla."
        ],
        'TestingDecision': [
            u"Recordar que si no se toma ninguna decisión",
            u"No ganarás créditos"
        ],
        'Break': [
            u"Puedes tomar un descanso.",
            " ",
            u"Cuando te sientas listo para continuar presiona Espacio."
        ],
        'wait': [
            "+"
        ],
        'farewell': [
            u"El experimento ha terminado.",
            "",
            u"Muchas gracias por su colaboración!!"
        ]
    }

    selected_slide = basic_slides[slide_to_use]
    return (selected_slide)

#%% LSL Functions for sending event markers
# Function to initialize the LSL stream
def init_lsl():
    """
    Initializes the Lab Streaming Layer (LSL) stream for sending trigger markers.
    These triggers are used to synchronize experiment events with physiological recordings.
    If debug_mode is True, LSL initialization is skipped.
    """
    if debug_mode:
        return
    
    # Create a global outlet variable for sending triggers
    global outlet
    info = StreamInfo(name="TriggerStream", type="Markers", channel_count=1,
                      channel_format="double64", source_id="Stream")
    outlet = StreamOutlet(info)
    print('LSL stream created')

# Function to send triggers using LSL
def send_trigger(trigger):
    """
    Sends a numerical trigger code via the LSL stream.
    This allows marking specific events in the physiological data stream.
    
    Args:
        trigger (int): The numerical code to send as a trigger
    """
    if debug_mode:
        return
    
    try:
        outlet.push_sample([trigger])
        print('Trigger ' + str(trigger) + ' sent')
    except:
        print('Failed to send trigger ' + str(trigger))


# Text and screen Functions
def setfonts():
    """
    Sets up fonts for text display in the experiment.
    Creates three font sizes: big, regular, and small.
    """
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(font, 96)    # Large font
    char = pygame.font.Font(font, 32)       # Medium font
    charnext = pygame.font.Font(font, 24)   # Small font


def render_textrect(string, font, rect, text_color, background_color, justification=1):
    """
    Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Args:
        string: The text to render. \n begins a new line.
        font: A Font object
        rect: A rectstyle giving the size of the surface requested.
        text_color: RGB tuple for text color (e.g., (0, 0, 0) for black)
        background_color: RGB tuple for background color
        justification: 0 for left-justified, 1 for centered, 2 for right-justified

    Returns:
        tuple: (final_lines, surface) containing the text lines and rendered surface
        
    Raises:
        TextRectException: If the text won't fit onto the surface
    """
    import pygame

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided rectangle
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # Check if any words are too long to fit
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException(
                        "The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Create the surface and render the text
    surface = pygame.Surface(rect.size)
    surface.fill(background_color)

    accumulated_height = 0
    for line in final_lines:
        if accumulated_height + font.size(line)[1] >= rect.height:
            raise TextRectException(
                "Once word-wrapped, the text string was too tall to fit in the rect.")
        if line != "":
            tempsurface = font.render(line, 1, text_color)
            if justification == 0:
                surface.blit(tempsurface, (0, accumulated_height))
            elif justification == 1:
                surface.blit(
                    tempsurface, ((rect.width - tempsurface.get_width()) / 2, accumulated_height))
            elif justification == 2:
                surface.blit(tempsurface, (rect.width -
                             tempsurface.get_width(), accumulated_height))
            else:
                raise TextRectException(
                    "Invalid justification argument: " + str(justification))
        accumulated_height += font.size(line)[1]

    return final_lines, surface


def paragraph(text, key=None, no_foot=False, color=None):
    """
    Displays a paragraph of text on the screen.
    
    Args:
        text (list): List of strings, each representing a line of text
        key (int, optional): Pygame key code for continuing (e.g., K_SPACE)
        no_foot (bool): If True, doesn't display footer text
        color (tuple): RGB color tuple for text. Uses default color if None
    """
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    # Display each line of text
    for line in text:
        phrase = char.render(line, True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40
        
    # Handle footer text
    if key != None:
        if key == K_SPACE:
            foot = u"Para continuar presione la tecla ESPACIO..."
        elif key == K_RETURN:
            foot = u"Para continuar presione la tecla ENTER..."
    else:
        foot = u"Responda con la fila superior de teclas de numéricas"
    if no_foot:
        foot = ""

    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()


def slide(text, info, key, limit_time=0):
    """
    Displays a slide with text and waits for key press or timeout.
    
    Args:
        text (list): List of strings to display
        info (bool): Whether to display the footer info
        key (int): Pygame key code to wait for (e.g., K_SPACE)
        limit_time (int): Time limit in milliseconds, 0 for no limit
        
    Returns:
        int: Time waited in milliseconds
    """
    paragraph(text, key, info)
    wait_time = wait(key, limit_time)
    return wait_time


def calibration_slide(text, key, image=None):
    """
    Displays a calibration slide with text and optionally an image.
    
    Args:
        text (list): List of strings to display
        key (int): Pygame key code to wait for (e.g., K_SPACE)
        image (str, optional): Filename of image to display
        
    Returns:
        int: Time waited in milliseconds
    """
    screen.fill(background)
    row = screen.get_rect().height // 8

    # Display each line of text
    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    # Display image if provided
    if image != None:
        picture = pygame.image.load("media\\images\\" + image)
        picture = pygame.transform.scale(picture, (screen.get_rect().height/2*picture.get_width()/picture.get_height(), screen.get_rect().height/2))        
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/2 - picture.get_width()/2,row + 40))
        screen.blit(picture, rect)
    
    # Add footer text
    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
    return wait_time


def cases_slide(text, key, images=[]):
    """
    Displays a slide with text and multiple images.
    Used for showing example cases for the task.
    
    Args:
        text (list): List of strings to display
        key (int): Pygame key code to wait for (e.g., K_SPACE)
        images (list): List of image filenames to display
        
    Returns:
        int: Time waited in milliseconds
    """
    screen.fill(background)
    row = screen.get_rect().height // 8
    first_image = 0

    # Display each line of text
    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    # Display images side by side
    for image in images:
        picture = pygame.image.load("media\\images\\" + image)
        picture = pygame.transform.scale(picture, (screen.get_rect().width/2, screen.get_rect().width/2*picture.get_height()/picture.get_width()))        
        rect = picture.get_rect()
        rect = rect.move(( (1+(2*first_image)) * screen.get_rect().width/4 - picture.get_width()/2, row + 40))
        screen.blit(picture, rect)
        first_image += 1

    # Add footer text
    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
    return wait_time


def blackscreen(blacktime=0):
    """
    Shows a blank screen for a specified time.
    
    Args:
        blacktime (int): Time to display black screen in milliseconds
    """
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)


def wait(key, limit_time):
    """
    Waits for a key press or until time limit is reached.
    
    Args:
        key (int): Pygame key code to wait for (e.g., K_SPACE)
        limit_time (int): Time limit in milliseconds, 0 for no limit
        
    Returns:
        int: Time waited in milliseconds
    """
    TIME_OUT_WAIT = USEREVENT + 1
    if limit_time != 0:
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time, loops=1)

    tw = pygame.time.get_ticks()

    switch = True
    while switch:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            elif event.type == KEYUP:
                if event.key == key:
                    switch = False
            elif event.type == TIME_OUT_WAIT and limit_time != 0:
                switch = False

    pygame.time.set_timer(TIME_OUT_WAIT, 0)
    pygame.event.clear()  # Clear events queue to prevent buildup

    return (pygame.time.get_ticks() - tw)


def ends():
    """
    Shows the ending screen and waits for escape key to exit.
    This is the final screen of the experiment.
    """
    blackscreen()
    dot = char.render('.', True, char_color)
    dotbox = dot.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(dot, dotbox)
    pygame.display.flip()
    while True:
        for evento in pygame.event.get():
            if evento.type == KEYUP and evento.key == K_ESCAPE:
                pygame_exit()


def windows(text, key=None, limit_time=0):
    """
    Displays a window with centered text, used for feedback screens.
    Special handling for "TI" (self) and "OTRO" (other) text with colors.
    
    Args:
        text (list): List of strings to display
        key (int, optional): Pygame key code to wait for
        limit_time (int): Time limit in milliseconds, 0 for no limit
    """
    screen.fill(background)
    row = center[1] - 120

    font = pygame.font.Font(None, 90)

    # Special handling for TI (self) and OTRO (other) text with colors
    if "TI" in text[1] or "OTRO" in text[1]:
        phrase = font.render(text[0], True, (0, 0, 0))
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 120

        font = pygame.font.Font(None, 140)

        # Red for self, blue for other
        color = (255, 0, 0) if text[1] == "TI" else (0, 0, 255)

        phrase = font.render(text[1], True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
    
    else:
        # Standard text display (green)
        for line in text:
            phrase = font.render(line, True, (0, 128, 0))
            phrasebox = phrase.get_rect(centerx=center[0], top=row)
            screen.blit(phrase, phrasebox)
            row += 120

    pygame.display.flip()
    wait(key, limit_time)


# Program Functions
def init():
    """
    Initializes the pygame display and sets up global variables.
    This creates the main screen and defines visual elements used throughout the experiment.
    """
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox, fix_think, fixbox_think, izq, der, quest, questbox
    pygame.init()  # Initialize pygame
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)  # Hide cursor initially
    
    # Set up display resolution
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)
        screen = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]  # Use fourth display mode
        except:
            resolution = (1280, 720)  # Fallback resolution
        screen = pygame.display.set_mode(resolution)
        
    # Define screen coordinates
    center = (int(resolution[0] / 2), int(resolution[1] / 2))  # Center of screen
    izq = (int(resolution[0] / 8), (int(resolution[1] / 8)*7))  # Left position
    der = ((int(resolution[0] / 8)*7), (int(resolution[1] / 8)*7))  # Right position
    
    # Define colors and text elements
    background = Color('lightgray')
    char_color = Color('black')
    charnext_color = Color('black')
    
    # Create fixation cross and question mark
    fix = char.render('+', True, char_color)
    fixbox = fix.get_rect(centerx=center[0], centery=center[1])
    fix_think = bigchar.render('+', True, Color('red'))
    fixbox_think = fix.get_rect(centerx=center[0], centery=center[1])
    quest = bigchar.render('?', True, char_color)
    questbox = quest.get_rect(centerx=center[0], centery=center[1])
    
    # Initial screen setup
    screen.fill(background)
    pygame.display.flip()


def pygame_exit():
    """
    Properly closes pygame and exits the program.
    """
    pygame.quit()
    sys.exit()


def optimal_division(n):
    """
    Calculates the optimal number of rows for displaying n buttons.
    Tries to make the grid as square-like as possible.
    
    Args:
        n (int): Total number of buttons
        
    Returns:
        int: Optimal number of rows for the layout
    """
    # If n is not in the optimal_square list, round up to the next value
    if n not in optimal_square:
        n = next(x[0] for x in enumerate(optimal_square) if x[1] > n)
        n = optimal_square[n]

    # Find the pair of factors with the smallest difference
    factors = [(i, n // i) for i in range(1, int(sqrt(n)) + 1) if n % i == 0]
    a, b = min(factors, key=lambda x: abs(x[0] - x[1]))
    return min(a, b)  # Return the smaller of the two factors (number of rows)


def draw_buttons(buttons_count, rows, hborder, vborder):
    """
    Draws clickable buttons on the screen in a grid layout.
    
    Args:
        buttons_count (int): Number of buttons to draw
        rows (int): Number of rows in the button grid
        hborder (int): Horizontal border size in pixels
        vborder (int): Vertical border size in pixels
        
    Returns:
        list: List of pygame.Rect objects representing the buttons
    """
    # Calculate number of columns needed
    columns = ceil(buttons_count / rows)

    button_list = []

    # Create and draw each button
    for i in range(1, buttons_count + 1):
        # Calculate button position and size
        button = pygame.Rect(
            (((resolution[0]/columns) * ((i-1)//rows) + hborder), 
             (((resolution[1])/(rows + 1)) * ((i-1)%rows + 1) + vborder)), 
            (resolution[0]/columns - (hborder*2), 
             resolution[1]/(rows + 1) - (vborder*2))
        )
        
        # Draw the button with rounded corners (radius 45)
        pygame.draw.rect(screen, base_button_color, button, 0, 45)
        
        # Add button number text
        font = pygame.font.Font(None, 36)
        text = font.render(str(i), True, (0, 0, 0))
        text_rect = text.get_rect(center=button.center)
        screen.blit(text, text_rect)
        
        button_list.append(button)

    pygame.display.flip()
    return button_list


def show_buttons(buttons_count, rows = 5, hborder = 10, vborder = 20, max_time = 10, title_text = ""):
    """
    Main function for the button-clicking task. Shows a grid of buttons the participant must click.
    
    Args:
        buttons_count (int): Number of buttons to display
        rows (int): Number of rows in the button grid
        hborder (int): Horizontal border size in pixels
        vborder (int): Vertical border size in pixels
        max_time (int): Maximum time in seconds to complete the task
        title_text (str): Text to display as the title
        
    Returns:
        tuple: (buttons_pressed, success, first_button_time, last_button_time)
            - buttons_pressed (int): Number of buttons clicked
            - success (bool): True if all buttons were clicked
            - first_button_time (int): Time of first button press in ms
            - last_button_time (int): Time of last button press in ms
    """
    # Setup timers for task end and countdown
    stage_change = USEREVENT + 2
    pygame.time.set_timer(stage_change, max_time * 1000)

    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    # Clear the screen
    screen.fill(background)
    pygame.display.flip()

    buttons_pressed = []  # Track which buttons were pressed
    done = False
    
    # Draw title text with special handling for TI and OTRO conditions
    font = pygame.font.Font(None, 36)
    
    if "TI" in title_text:  # Self condition (red)
        text = font.render(title_text, True, (255, 0, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

        text2 = font.render(title_text[:-2], True, (0, 128, 0))
        
        text_width, text_height = text2.get_size()
        top_left = text_rect.topleft
        pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))

        text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))
    
    
    elif "OTRO" in title_text:  # Other condition (blue)
        text = font.render(title_text, True, (0, 0, 255))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))
        
        text2 = font.render(title_text[:-4], True, (0, 128, 0))

        text_width, text_height = text2.get_size()
        top_left = text_rect.topleft
        pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))

        text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

    else:  # Regular title (green)
        text = font.render(title_text, True, (0, 128, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/((rows+1)*2)))

    screen.blit(text, text_rect)
    if "OTRO" in title_text or "TI" in title_text:
        screen.blit(text2, text_rect2)

    # Draw the buttons
    buttons = draw_buttons(buttons_count, rows, hborder, vborder)

    # Draw the countdown timer
    timer_text = pygame.font.Font(None, 36)
    text = timer_text.render(str(max_time) + " s", True, (0, 0, 0))
    seconds_text_rect = text.get_rect(center=(resolution[0] * 0.9, resolution[1]/((rows+1)*2)))
    screen.blit(text, seconds_text_rect)
    pygame.display.flip()

    # Show mouse cursor for button clicking
    pygame.mouse.set_visible(True)

    # Timing variables
    first_button_pressed_time = None
    last_button_pressed_time = None

    tw = pygame.time.get_ticks()  # Start time
    rt = 0  # Reaction time

    # Send task start trigger
    send_trigger(start_task_trigger)
    
    # Main task loop
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_c:
                done=True  # Debugging shortcut to end task

            # Update countdown timer
            elif event.type == seconds:
                # Erase previous timer
                pygame.draw.rect(screen, background, seconds_text_rect, 0)

                # Draw new timer
                rt = pygame.time.get_ticks() - tw
                text = timer_text.render(str(max_time - int(rt/1000)) + " s", True, (0, 0, 0))
                screen.blit(text, seconds_text_rect)
                pygame.display.flip()

            # Handle button clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(buttons):
                    if button.collidepoint(event.pos):
                        # Change button color when clicked
                        pygame.draw.rect(screen, pressed_button_color, button, 0, 45)
                        font = pygame.font.Font(None, 36)
                        text = font.render(str(i+1), True, (0, 0, 0))
                        button_text_rect = text.get_rect(center=button.center)
                        screen.blit(text, button_text_rect)
                        pygame.display.flip()

                        # Record button press if not already pressed
                        if i+1 not in buttons_pressed:
                            if first_button_pressed_time == None:
                                first_button_pressed_time = pygame.time.get_ticks() - tw
                            buttons_pressed.append(i+1)
                            
                            # If all buttons pressed, send trigger and record time
                            if len(buttons_pressed) == buttons_count:
                                send_trigger(last_button_pressed_trigger)
                                last_button_pressed_time = pygame.time.get_ticks() - tw

            # End task when time runs out
            elif event.type == stage_change:
                done = True

    # Clean up timers and mouse
    pygame.time.set_timer(stage_change, 0)
    pygame.mouse.set_visible(False)
    pygame.event.clear()  # Clear event queue

    # Return results
    return len(buttons_pressed), len(buttons_pressed) == buttons_count, first_button_pressed_time, last_button_pressed_time


def take_decision(buttons_number, credits_number, title_text, max_time = 6, test = False):
    """
    Presents the decision screen where participants choose between working and resting.
    
    Args:
        buttons_number (int): Number of buttons in the work option
        credits_number (int): Number of credits for the work option
        title_text (str): Title text (indicates self or other condition)
        max_time (int): Maximum time in seconds to make a decision
        test (bool): Whether this is a practice trial
        
    Returns:
        tuple: (selection, scroll_type, reaction_time)
            - selection (int): 1 for work option, 2 for rest option, 0 for no decision
            - scroll_type (str): Direction of mouse scroll ("up" or "down")
            - reaction_time (int): Time taken to make decision in ms
    """
    screen.fill(background)

    # Setup title text with special handling for TI (self) and OTRO (other)
    font = pygame.font.Font(None, 72)

    if "TI" in title_text:  # Self condition
        offset = 2
        offset_color = (255, 0, 0)  # Red
    elif "OTRO" in title_text:  # Other condition
        offset = 4
        offset_color = (0, 0, 255)  # Blue

    # Draw the title text
    text = font.render(title_text[:-offset], True, (0, 128, 0))  # "Credits for" in green
    text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
    text2 = font.render(title_text[-offset:], True, offset_color)  # "TI" or "OTRO" in color
    text_rect2 = text2.get_rect(center=(resolution[0]/2, (resolution[1]/6) + 100))

    screen.blit(text, text_rect)
    screen.blit(text2, text_rect2)

    # Define button positions randomly (to counterbalance left/right bias)
    button_positions = [4, 8]  # Vertical positions
    shuffle(button_positions)
    
    # Create the two choice buttons
    button1 = pygame.Rect((resolution[0]/8*3, resolution[1]/12*button_positions[0]), (resolution[0]/4, resolution[1]/4))
    button2 = pygame.Rect((resolution[0]/8*3, resolution[1]/12*button_positions[1]), (resolution[0]/4, resolution[1]/4))

    # Draw the buttons
    pygame.draw.rect(screen, base_button_color, button1, 0, 45)
    pygame.draw.rect(screen, base_button_color, button2, 0, 45)

    # Add text to the "work" button
    font = pygame.font.Font(None, 36)
    text = font.render(f"{credits_number} créditos", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render(f"por {buttons_number} cajas", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] + 20)
    screen.blit(text, text_rect)

    # Add text to the "rest" button
    text = font.render("1 crédito", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render("por descansar", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] + 20)
    screen.blit(text, text_rect)

    # Draw button borders
    pygame.draw.rect(screen, (0, 0, 0), button1, 1, 45)
    pygame.draw.rect(screen, (0, 0, 0), button2, 1, 45)

    # For practice trials, show mouse wheel instructions
    if test:
        picture = pygame.image.load("media\\images\\" + "mouse_scroll_wheel.png").convert_alpha()
        picture = pygame.transform.scale(picture, (screen.get_rect().height/8*picture.get_width()/picture.get_height(), screen.get_rect().height/8))

        row = center[1] - screen.get_rect().height/16 + picture.get_height()
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/10*8 - picture.get_width()/2, row))
        screen.blit(picture, rect)

        # Instruction text
        font = pygame.font.Font(None, 36)
        text = font.render("Gira la rueda del ratón hacia arriba", True, (0, 0, 0))
        text_rect = text.get_rect(center=(screen.get_rect().width/10*8, row - 40))
        screen.blit(text, text_rect)

        text = font.render("Gira la rueda del ratón hacia abajo", True, (0, 0, 0))
        text_rect = text.get_rect(center=(screen.get_rect().width/10*8, row + 40 + picture.get_height()))
        screen.blit(text, text_rect)

    pygame.display.flip()

    done = False
    selected_button = 0  # 0 = no selection, 1 = work, 2 = rest
    scroll_type = None   # Direction of mouse scroll

    # Setup timer for countdown
    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    tw = pygame.time.get_ticks()  # Start time
    rt = 0  # Reaction time
    reaction_time = None  # Time when decision was made

    # Send decision start trigger
    send_trigger(decision_start_trigger)
    
    # Decision loop
    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            
            # Mouse wheel is used to make selections
            elif event.type == pygame.MOUSEWHEEL:
                if event.y > 0:  # Scroll up
                    reaction_time = pygame.time.get_ticks() - tw
                    scroll_type = "up"
                    # Select based on which button is in the upper position
                    if button_positions[0] == 4:
                        selected_button = 1
                    else:
                        selected_button = 2
                elif event.y < 0:  # Scroll down
                    reaction_time = pygame.time.get_ticks() - tw
                    scroll_type = "down"
                    # Select based on which button is in the lower position
                    if button_positions[0] == 4:
                        selected_button = 2
                    else:
                        selected_button = 1
                done = True  # End decision phase after selection

            # Check if time limit exceeded
            elif event.type == seconds:
                rt = pygame.time.get_ticks() - tw
                if rt >= max_time * 1000:
                    pygame.time.set_timer(seconds, 0)
                    done = True  # End if time runs out

    # Return selection result
    return (selected_button, scroll_type, reaction_time)


def show_resting(title_text, max_time = 10):
    """
    Shows the rest screen when participant chooses to rest.
    
    Args:
        title_text (str): Title text (indicates self or other condition)
        max_time (int): Duration of rest in seconds
    """
    screen.fill(background)
    font = pygame.font.Font(None, 42)

    # Special handling for TI (self) and OTRO (other) in title
    if "TI" in title_text:  # Self condition
        text = font.render(title_text, True, (255, 0, 0))  # Red
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
        text2 = font.render(title_text[:-2], True, (0, 128, 0))  # Green

    elif "OTRO" in title_text:  # Other condition
        text = font.render(title_text, True, (0, 0, 255))  # Blue
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
        text2 = font.render(title_text[:-4], True, (0, 128, 0))  # Green

    # Position and display title text
    text_width, text_height = text2.get_size()
    top_left = text_rect.topleft
    pygame.draw.rect(screen, (background), (top_left[0], top_left[1], text_width, text_height))
    text_rect2 = text.get_rect(center=(resolution[0]/2, resolution[1]/10))

    screen.blit(text, text_rect)
    screen.blit(text2, text_rect2)

    # Draw countdown timer
    timer_text = pygame.font.Font(None, 42)
    text = timer_text.render(str(max_time) + " s", True, (0, 0, 0))
    seconds_text_rect = text.get_rect(center=(resolution[0] * 0.9, resolution[1]/10))
    screen.blit(text, seconds_text_rect)

    # Draw "RESTING" text
    resting_text = pygame.font.Font(None, 90)
    text = resting_text.render("DESCANSO", True, (0, 0, 0))
    resting_text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/2))
    screen.blit(text, resting_text_rect)

    pygame.display.flip()

    # Setup countdown timer
    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    tw = pygame.time.get_ticks()  # Start time
    rt = 0  # Current time

    # Rest period loop
    while True:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
                
            # Update countdown timer
            elif event.type == seconds:
                # Erase previous timer
                pygame.draw.rect(screen, background, seconds_text_rect, 0)

                # Draw new timer
                rt = pygame.time.get_ticks() - tw
                text = timer_text.render(str(max_time - int(rt/1000)) + " s", True, (0, 0, 0))
                screen.blit(text, seconds_text_rect)
                pygame.display.flip()

                # End rest period when time runs out
                if rt >= max_time * 1000:
                    pygame.time.set_timer(seconds, 0)
                    return


def task(self_combinations, other_combinations, blocks_number, block_type, max_answer_time, 
         test = False, decision_practice_trials = 1, file = None, effort_table = None):
    """
    Main task function that runs a full experimental block.
    
    Args:
        self_combinations (list): List of combinations for self trials (effort, credits, "TI")
        other_combinations (list): List of combinations for other trials (effort, credits, "OTRO")
        blocks_number (int): Number of blocks to run
        block_type (str): How to organize blocks ("division" or "total")
        max_answer_time (int): Maximum time in seconds for button task
        test (bool): Whether this is a practice block
        decision_practice_trials (int): Number of practice trials to run if test=True
        file (file): File object for data saving
        effort_table (dict): Mapping between button counts and effort levels
    """
    # For "division" block_type, divide trials evenly among blocks
    last_list_cut = 0
    actual_list_cut = len(self_combinations)//blocks_number

    # Run each block
    for _ in range(blocks_number):
        # Create list of combinations for this block based on block_type
        if block_type == "division":
            # Each block gets a portion of trials
            actual_combinations_list = self_combinations[last_list_cut:actual_list_cut] + other_combinations[last_list_cut:actual_list_cut]
        elif block_type == "total":
            # Each block gets all trials
            actual_combinations_list = self_combinations + other_combinations
        else:
            print("Tipo de bloque no reconocido")
            break

        # Randomize trial order
        shuffle(actual_combinations_list)

        practice_count = 0

        # Run each trial in the block
        for combination in actual_combinations_list:
            # Initialize timing variables
            first_button_pressed_time, last_button_pressed_time = None, None

            # Show recipient (self or other)
            windows([f"Créditos para", combination[2]], K_SPACE, 2000)

            # Present decision screen
            selection, scroll_type, decision_reaction_time = take_decision(
                combination[0],  # Number of buttons (effort)
                combination[1],  # Number of credits (reward)
                f"Créditos para {combination[2]}",  # Title text
                max_time = max_decision_time, 
                test = test
            )

            # Handle no decision (timeout) case
            if selection not in [1, 2]:
                if test:  # In practice, force a decision
                    while selection not in [1, 2]:
                        slide(select_slide('TestingDecision'), False, K_SPACE)
                        selection, scroll_type, decision_reaction_time = take_decision(
                            combination[0], combination[1], f"Créditos para {combination[2]}", 
                            max_time = max_decision_time, test = test
                        )
                else:  # In real trials, show rest screen if no decision
                    show_resting(f"Créditos para {combination[2]}", max_time = 10)

            button_clear = False

            # Run the selected option (work or rest)
            if selection == 1:  # Work option
                # Show button task
                buttons_pressed, button_clear, first_button_pressed_time, last_button_pressed_time = show_buttons(
                    buttons_count = combination[0],  # Number of buttons
                    rows = optimal_division(combination[0]),  # Optimal layout
                    hborder = 10, 
                    vborder = 20, 
                    max_time = max_answer_time, 
                    title_text = f"Créditos para {combination[2]}"
                )
                
                # Determine credits earned
                earned_credits = combination[1]  # Full credits if successful
                if not button_clear:  # If failed to press all buttons
                    earned_credits = 0
                    show_resting(f"Créditos para {combination[2]}", max_time = 10)
                    send_trigger(failed_task_trigger)
                else:
                    send_trigger(correct_task_trigger)

            elif selection == 2:  # Rest option
                show_resting(f"Créditos para {combination[2]}", max_time = 10)
                earned_credits = 1  # 1 credit for resting
                send_trigger(resting_trigger)

            else:  # No decision
                print("No se ha seleccionado decisiones")
                earned_credits = 0
                send_trigger(not_decision_made_trigger)
            
            # Save data and show feedback (except in practice)
            if not test:
                # Write data to CSV file
                if file != None:
                    file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                        effort_table[combination[0]],  # Effort level
                        combination[1],  # Credits level
                        "Self" if combination[2] == "TI" else "Other",  # Condition
                        "task" if selection == 1 else ("resting" if selection == 2 else "no decision"),  # Decision
                        buttons_pressed,  # Number of buttons clicked
                        "True" if selection == 2 else button_clear,  # Success
                        earned_credits,  # Credits earned
                        decision_reaction_time,  # Decision time
                        first_button_pressed_time,  # First button time
                        last_button_pressed_time  # Last button time
                    ))
                    file.flush()
                    
                # Show feedback about credits earned
                if combination[2] == "TI":
                    windows(["Has ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
                else:
                    windows(["Otra persona ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)

            # In practice mode, limit number of trials
            if test:
                practice_count += 1
                if practice_count >= decision_practice_trials:
                    break

        # After each block (except in practice)
        if not test:
            slide(select_slide('Break'), False, K_SPACE)
            last_list_cut = actual_list_cut
            actual_list_cut += len(self_combinations)//blocks_number
        else:
            slide(select_slide('Practice_ending'), False, K_SPACE)
            return

# Main Function
def main():
    """
    Main function that runs the experiment from start to finish.
    Handles initialization, participant ID, data file creation, 
    and calls the appropriate task functions in sequence.
    """
    # Initialize LSL for trigger sending
    init_lsl()

    # Create data directory if it doesn't exist
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Get participant ID
    subj_name = input(
        "Ingrese el ID del participante y presione ENTER para iniciar: ")

    # Validate participant ID
    while (len(subj_name) < 1):
        os.system('cls')
        print("ID ingresado no cumple con las condiciones, contacte con el encargado...")
        subj_name = input(
            "Ingrese el ID del participante y presione ENTER para iniciar: ")

    pygame.init()

    # Create data file
    csv_name = join('data', date_name + "_" + subj_name + ".csv")
    dfile = open(csv_name, 'w')
    # Write CSV header
    dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
        "NivelEsfuerzo", "NivelReward", "Condición", "Decisión", 
        "CuadrosClickeados", "ÉxitoTarea", "CréditosGanados", 
        "TiempoReacciónDecisión", "TiempoReacciónPrimerCuadro", "TiempoReacciónÚltimoCuadro"
    ))
    dfile.flush()

    # Initialize display
    init()

    # Send experiment start trigger
    send_trigger(start_trigger)

    # Welcome screen
    slide(select_slide('welcome'), False, K_SPACE)

    # ------------------- Calibration block ------------------------
    # Show instructions
    send_trigger(slide_trigger + 10)
    calibration_slide(select_slide('Instructions_Casillas'), K_SPACE, "testing_schema.jpg")

    # First calibration task - establish baseline clicking speed
    max_button_count, _, _, _ = show_buttons(
        buttons_count = 50, 
        rows = optimal_division(50), 
        hborder = 10, 
        vborder = 20, 
        max_time = max_answer_time, 
        title_text = "Comienza!"
    )

    # Second calibration task - try to improve performance
    send_trigger(slide_trigger + 20)
    slide(select_slide('Interlude_Casillas'), False, K_SPACE)

    actual_button_count, _, _, _ = show_buttons(
        buttons_count = 50, 
        rows = 5, 
        hborder = 10, 
        vborder = 20, 
        max_time = max_answer_time, 
        title_text = "Comienza!"
    )

    # Use the higher of the two performances
    if actual_button_count > max_button_count:
        max_button_count = actual_button_count

    # Ensure minimum number of buttons
    if max_button_count < min_buttons:
        max_button_count = min_buttons
    
    # ------------------- Decision instructions block ------------------------
    send_trigger(slide_trigger + 30)
    slide(select_slide('Instructions_Decision_1'), False, K_SPACE)
    send_trigger(slide_trigger + 40)
    cases_slide(select_slide('Instructions_Decision_2'), K_SPACE, ["TI_schema.jpg", "OTRO_schema.jpg"])
    send_trigger(slide_trigger + 50)
    slide(select_slide('Instructions_Decision_3'), False, K_SPACE)
    send_trigger(slide_trigger + 60)
    slide(select_slide('Instructions_Decision_final'), False, K_SPACE)

    # ------------------------ Training Section -----------------------------
    # Calculate actual button counts based on calibrated max and effort levels
    effort_levels_recalculated = [ceil(max_button_count*(effort/100)) for effort in effort_levels]
    # Create mapping between actual button counts and effort level percentages
    effort_table = dict(zip(effort_levels_recalculated, effort_levels))

    # Create all possible trial combinations
    self_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, ["TI"]*len(effort_levels_recalculated)))
    other_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, ["OTRO"]*len(effort_levels_recalculated)))

    # Randomize trial order
    shuffle(self_combinations)
    shuffle(other_combinations)

    # Practice trials for each effort level
    for _ in range(practice_iterations):
        for effort_level in effort_levels_recalculated:
            show_buttons(
                buttons_count = effort_level, 
                rows = optimal_division(effort_level), 
                hborder = 10, 
                vborder = 20, 
                max_time = max_answer_time, 
                title_text = f"Créditos para TI"
            )

    # Practice decision trials
    send_trigger(slide_trigger + 70)        
    slide(select_slide('Effort_ending'), False, K_SPACE)

    task(
        self_combinations, 
        other_combinations, 
        blocks_number, 
        block_type, 
        max_answer_time, 
        test = True, 
        decision_practice_trials = decision_practice_trials
    )

    # ------------------------ Experiment Section -----------------------------
    # Run the full experiment
    task(
        self_combinations, 
        other_combinations, 
        blocks_number, 
        block_type, 
        max_answer_time, 
        file = dfile, 
        effort_table = effort_table
    )

    # Close data file
    dfile.flush()

    # Show farewell slide and end experiment
    send_trigger(slide_trigger + 80)
    slide(select_slide('farewell'), True, K_SPACE)
    send_trigger(stop_trigger)
    dfile.close()
    ends()


# Experiment starts here...
if __name__ == "__main__":
    main()

