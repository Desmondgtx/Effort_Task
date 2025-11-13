#!/usr/bin/env python3.10.9
# coding=utf-8

"""
Electric Shock Decision Task
tested in Python 3.10.9
"""
import pygame, sys, os
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_n, K_m
from os.path import join
from time import gmtime, strftime
import itertools
from random import shuffle

# Configurations:
FullScreenShow = True  # Pantalla completa automáticamente al iniciar el experimento
test_name = "Shock_Decision_Task"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
shock_levels = [4, 6, 8, 10]  # Number of shocks
reward_levels = [3, 6, 9, 12]  # Money rewards
max_decision_time = 5  # Tiempo máximo para decidir en segundos
fixation_duration = 2  # Duration of fixation cross in seconds (EASY TO CHANGE)
trials_per_condition = 35  # 35 trials for self, 35 for other

# Fixed low option (always 2 shocks for 1 peso)
low_shock_option = 2
low_reward_option = 1

# buttons configuration
base_button_color = (255, 255, 255)

# Onscreen instructions
def select_slide(slide_name):
    basic_slides = {
        'welcome': [
            u"Bienvenido/a a este experimento!!!",
            " ",
            u"Se te indicará paso a paso que hacer."
        ],
        'Instructions_Decision_1': [
            u"Tarea de decisiones sobre descargas eléctricas:",
            " ",
            u"En esta tarea, deberás tomar decisiones sobre recibir descargas eléctricas",
            u"hipotéticas a cambio de dinero.",
            " ",
            u"Es importante que imagines estas descargas como si fueran reales.",
            u"Piensa en ellas como pequeños pinchazos dolorosos, similares a una inyección",
            u"o a cuando tocas algo que te da corriente. Cada descarga adicional",
            u"aumenta el dolor y la incomodidad.",
            " ",
            u"En cada ronda, tendrás que elegir entre dos opciones:",
            u"- Una opción con pocas descargas pero poco dinero",
            u"- Una opción con más descargas pero más dinero",
            " ",
            u"Debes imaginar vívidamente el dolor de las descargas al tomar tu decisión."
        ],
        'Instructions_Decision_2': [
            u"Habrá dos tipos de rondas:",
            " ",
            u"Rondas TI: Decidirás cuántas descargas recibirías TÚ por dinero.",
            u"El dinero sería para ti, pero también las descargas.",
            " ",
            u"Rondas OTRO: Decidirás cuántas descargas recibiría OTRA persona por dinero.",
            u"El dinero sería para esa persona, y también las descargas.",
            " ",
            u"Esta otra persona es un/a participante real que está en otro lugar",
            u"completando otras tareas. Tus decisiones afectarán directamente",
            u"su experiencia en el experimento.",
            " ",
            u"Tus decisiones serán completamente anónimas y confidenciales."
        ],
        'Instructions_Decision_3': [
            u"En cada decisión verás dos opciones:",
            " ",
            u"Por ejemplo:",
            u"Opción 1: 2 descargas por $1",
            u"Opción 2: 8 descargas por $9",
            " ",
            u"Tendrás {} segundos para decidir presionando:".format(max_decision_time),
            u"- N para la opción de la izquierda",
            u"- M para la opción de la derecha",
            " ",
            u"Si no tomas una decisión a tiempo, no se otorgarán",
            u"ni dinero ni descargas para esa ronda."
        ],
        'Instructions_Decision_final': [
            u"Recuerda:",
            " ",
            u"• Imagina las descargas como pinchazos dolorosos reales",
            u"• En rondas TI, decides por ti mismo/a",
            u"• En rondas OTRO, decides por otra persona real",
            u"• Usa N para izquierda, M para derecha",
            u"• Tienes {} segundos para decidir".format(max_decision_time),
            " ",
            u"¿Estás listo/a para comenzar?"
        ],
        'no_decision': [
            u"No tomaste una decisión a tiempo",
            u"No se otorgan descargas ni dinero"
        ],
        'farewell': [
            u"El experimento ha terminado.",
            "",
            u"Muchas gracias por tu colaboración!!"
        ]
    }

    return basic_slides[slide_name]

# Text and screen Functions
def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(font, 96)
    char = pygame.font.Font(font, 32)
    charnext = pygame.font.Font(font, 24)

def paragraph(text, key=None, no_foot=False, color=None):
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    for line in text:
        phrase = char.render(line, True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40
    if key != None:
        if key == K_SPACE:
            foot = u"Para continuar presione la tecla ESPACIO..."
        elif key == K_RETURN:
            foot = u"Para continuar presione la tecla ENTER..."
    else:
        foot = u"Responda con las teclas N o M"
    if no_foot:
        foot = ""

    nextpage = charnext.render(foot, True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()

def slide(text, info, key, limit_time=0):
    """Organizes a paragraph into a slide"""
    paragraph(text, key, info)
    wait_time = wait(key, limit_time)
    return wait_time

def blackscreen(blacktime=0):
    """Erases the screen"""
    screen.fill(background)
    pygame.display.flip()
    pygame.time.delay(blacktime)

def wait(key, limit_time):
    """Hold a bit"""
    TIME_OUT_WAIT = USEREVENT + 1
    if limit_time != 0:
        pygame.time.set_timer(TIME_OUT_WAIT, limit_time * 1000, loops=1)

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
    pygame.event.clear()

    return (pygame.time.get_ticks() - tw)

def ends():
    """Closes the show"""
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
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 120

    font = pygame.font.Font(None, 90)

    if "TI" in text[1] or "OTRO" in text[1]:
        phrase = font.render(text[0], True, (0, 0, 0))
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 120

        font = pygame.font.Font(None, 140)
        color = (255, 0, 0) if text[1] == "TI" else (0, 0, 255)

        phrase = font.render(text[1], True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
    else:
        for line in text:
            phrase = font.render(line, True, (0, 128, 0))
            phrasebox = phrase.get_rect(centerx=center[0], top=row)
            screen.blit(phrase, phrasebox)
            row += 120

    pygame.display.flip()
    
    # If no key specified, just wait for the time limit
    if key is None and limit_time > 0:
        pygame.time.delay(limit_time)
    else:
        wait(key, limit_time)

def show_fixation_cross(duration):
    """Display a fixation cross for specified duration"""
    screen.fill(background)
    
    # Draw fixation cross
    cross_size = 40
    cross_width = 4
    
    # Horizontal line
    pygame.draw.line(screen, (0, 0, 0), 
                    (center[0] - cross_size//2, center[1]),
                    (center[0] + cross_size//2, center[1]),
                    cross_width)
    
    # Vertical line
    pygame.draw.line(screen, (0, 0, 0),
                    (center[0], center[1] - cross_size//2),
                    (center[0], center[1] + cross_size//2),
                    cross_width)
    
    pygame.display.flip()
    pygame.time.delay(duration * 1000)  # Convert to milliseconds

# Program Functions
def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color
    pygame.init()
    pygame.display.init()
    pygame.display.set_caption(test_name)
    pygame.mouse.set_visible(False)
    if FullScreenShow:
        resolution = (pygame.display.Info().current_w,
                      pygame.display.Info().current_h)
        screen = pygame.display.set_mode(resolution, FULLSCREEN)
    else:
        try:
            resolution = pygame.display.list_modes()[3]
        except:
            resolution = (1280, 720)
        screen = pygame.display.set_mode(resolution)
    center = (int(resolution[0] / 2), int(resolution[1] / 2))
    background = Color('lightgray')
    char_color = Color('black')
    charnext_color = Color('black')
    screen.fill(background)
    pygame.display.flip()

def pygame_exit():
    pygame.quit()
    sys.exit()

def take_decision(shock_number, reward_number, title_text, max_time=5):
    """Show decision screen with two shock/reward options"""
    screen.fill(background)

    font = pygame.font.Font(None, 72)

    # Draw title
    if "TI" in title_text:
        offset = 2
        offset_color = (255, 0, 0)
    elif "OTRO" in title_text:
        offset = 4
        offset_color = (0, 0, 255)

    text = font.render(title_text[:-offset], True, (0, 128, 0))
    text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
    text2 = font.render(title_text[-offset:], True, offset_color)
    text_rect2 = text2.get_rect(center=(resolution[0]/2, (resolution[1]/6) + 100))

    screen.blit(text, text_rect)
    screen.blit(text2, text_rect2)

    # Button positions
    button_positions = ["left", "right"]
    shuffle(button_positions)
    
    # Define button dimensions
    button_width = resolution[0]/4
    button_height = resolution[1]/4
    
    # Define horizontal positions
    left_x = resolution[0]/4 - button_width/2
    right_x = 3*resolution[0]/4 - button_width/2
    button_y = resolution[1]/2 - button_height/2
    
    # Create buttons
    if button_positions[0] == "left":
        button1 = pygame.Rect(left_x, button_y, button_width, button_height)  # High shock/reward
        button2 = pygame.Rect(right_x, button_y, button_width, button_height)  # Low shock/reward
    else:
        button1 = pygame.Rect(right_x, button_y, button_width, button_height)  # High shock/reward
        button2 = pygame.Rect(left_x, button_y, button_width, button_height)  # Low shock/reward

    # Draw buttons
    pygame.draw.rect(screen, base_button_color, button1, 0, 45)
    pygame.draw.rect(screen, base_button_color, button2, 0, 45)

    font = pygame.font.Font(None, 36)
    
    # Button 1 - High shock/reward option
    text = font.render(f"{shock_number} descargas", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render(f"por ${reward_number}", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button1.center[0], centery=button1.center[1] + 20)
    screen.blit(text, text_rect)

    # Button 2 - Low shock/reward option (fixed)
    text = font.render(f"{low_shock_option} descargas", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] - 20)
    screen.blit(text, text_rect)
    text = font.render(f"por ${low_reward_option}", True, (0, 0, 0))
    text_rect = text.get_rect(centerx=button2.center[0], centery=button2.center[1] + 20)
    screen.blit(text, text_rect)

    # Button borders
    pygame.draw.rect(screen, (0, 0, 0), button1, 1, 45)
    pygame.draw.rect(screen, (0, 0, 0), button2, 1, 45)

    # Add key indicators
    key_font = pygame.font.Font(None, 48)
    if button_positions[0] == "left":
        text_n = key_font.render("N", True, (0, 0, 0))
        text_n_rect = text_n.get_rect(centerx=button1.center[0], top=button1.bottom + 20)
        screen.blit(text_n, text_n_rect)
        
        text_m = key_font.render("M", True, (0, 0, 0))
        text_m_rect = text_m.get_rect(centerx=button2.center[0], top=button2.bottom + 20)
        screen.blit(text_m, text_m_rect)
    else:
        text_m = key_font.render("M", True, (0, 0, 0))
        text_m_rect = text_m.get_rect(centerx=button1.center[0], top=button1.bottom + 20)
        screen.blit(text_m, text_m_rect)
        
        text_n = key_font.render("N", True, (0, 0, 0))
        text_n_rect = text_n.get_rect(centerx=button2.center[0], top=button2.bottom + 20)
        screen.blit(text_n, text_n_rect)

    pygame.display.flip()

    done = False
    selected_button = 0
    key_pressed = None

    seconds = USEREVENT + 3
    pygame.time.set_timer(seconds, 1000)

    tw = pygame.time.get_ticks()
    rt = 0
    reaction_time = None

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
            
            elif event.type == KEYUP and event.key == K_n:
                reaction_time = pygame.time.get_ticks() - tw
                key_pressed = "left"
                if button_positions[0] == "left":
                    selected_button = 1  # High option
                else:
                    selected_button = 2  # Low option
                done = True
                
            elif event.type == KEYUP and event.key == K_m:
                reaction_time = pygame.time.get_ticks() - tw
                key_pressed = "right"
                if button_positions[0] == "left":
                    selected_button = 2  # Low option
                else:
                    selected_button = 1  # High option
                done = True

            elif event.type == seconds:
                rt = pygame.time.get_ticks() - tw
                if rt >= max_time * 1000:
                    pygame.time.set_timer(seconds, 0)
                    done = True

    pygame.time.set_timer(seconds, 0)
    pygame.event.clear()

    return (selected_button, key_pressed, reaction_time)

def run_trials(self_combinations, other_combinations, file=None):
    """Run all decision trials"""
    # Combine and shuffle all trials
    all_trials = []
    
    # Add self trials
    for combo in self_combinations:
        all_trials.append((combo[0], combo[1], "TI"))
    
    # Add other trials
    for combo in other_combinations:
        all_trials.append((combo[0], combo[1], "OTRO"))
    
    shuffle(all_trials)
    
    # Run each trial
    for trial_num, (shocks, reward, condition) in enumerate(all_trials):
        # Show receiver (self or other)
        windows([f"Decisión para", condition], None, 2000)
        
        # Show fixation cross
        show_fixation_cross(fixation_duration)
        
        # Get decision
        selection, key_pressed, reaction_time = take_decision(
            shocks, reward, f"Decisión para {condition}", max_time=max_decision_time
        )
        
        # Determine outcome
        if selection == 0:  # No decision made
            slide(select_slide('no_decision'), False, K_SPACE, 2)
            chosen_shocks = 0
            chosen_reward = 0
            decision = "no_decision"
        elif selection == 1:  # High shock/reward option
            chosen_shocks = shocks
            chosen_reward = reward
            decision = "high"
        else:  # Low shock/reward option
            chosen_shocks = low_shock_option
            chosen_reward = low_reward_option
            decision = "low"
        
        # Save data
        if file:
            file.write(f"{trial_num+1},{shocks},{reward},{condition},{decision},"
                      f"{chosen_shocks},{chosen_reward},{reaction_time},{key_pressed}\n")
            file.flush()
        
        # Show feedback
        if selection != 0:
            if condition == "TI":
                windows([f"Has elegido:", f"{chosen_shocks} descargas por ${chosen_reward}"], None, 2000)
            else:
                windows([f"La otra persona recibirá:", f"{chosen_shocks} descargas por ${chosen_reward}"], None, 2000)

# Main Function
def main():
    """Game's main loop"""
    
    # Create data folder if it doesn't exist
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Get participant ID
    subj_name = input("Ingrese el ID del participante y presione ENTER para iniciar: ")
    while len(subj_name) < 1:
        os.system('cls')
        print("ID ingresado no cumple con las condiciones...")
        subj_name = input("Ingrese el ID del participante y presione ENTER para iniciar: ")

    pygame.init()

    # Create data file
    csv_name = join('data', date_name + "_" + subj_name + ".csv")
    dfile = open(csv_name, 'w')
    dfile.write("Trial,Shocks_Option,Reward_Option,Condition,Decision,Chosen_Shocks,"
                "Chosen_Reward,Reaction_Time,Key_Pressed\n")
    dfile.flush()

    init()

    # Instructions
    slide(select_slide('welcome'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_1'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_2'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_3'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_final'), False, K_SPACE)

    # Create all combinations
    all_combinations = list(itertools.product(shock_levels, reward_levels))
    
    # Create trials for each condition
    self_trials = []
    other_trials = []
    
    # We need 35 trials per condition from 16 possible combinations
    # So we'll repeat some combinations
    for _ in range(2):  # 2 * 16 = 32
        self_trials.extend(all_combinations)
        other_trials.extend(all_combinations)
    
    # Add 3 more random trials to reach 35
    shuffle(all_combinations)
    self_trials.extend(all_combinations[:3])
    shuffle(all_combinations)
    other_trials.extend(all_combinations[:3])
    
    # Run the experiment
    run_trials(self_trials, other_trials, dfile)
    
    # End
    dfile.close()
    slide(select_slide('farewell'), True, K_SPACE)
    ends()

# Start the experiment
if __name__ == "__main__":
    main()