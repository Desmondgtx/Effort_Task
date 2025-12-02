#!/usr/bin/env python3.10.9
# coding=utf-8

# Important parameters
# Size of the circle = standard_circle_size 
# Size of the square = box_padding
# Total Blocks = blocks_number

"""
tested in Python 3.10.18
"""
import pygame, sys, os, cv2, math
from pygame.locals import FULLSCREEN, USEREVENT, KEYUP, K_SPACE, K_RETURN, K_ESCAPE, QUIT, Color, K_c, K_n, K_m
from os.path import join
from time import gmtime, strftime
from math import ceil, sqrt
import itertools
from random import shuffle
from pylsl import StreamInfo, StreamOutlet

debug_mode = True

# MARCADORES LSL PARA EEG
MARKERS = {
    # Eventos de decisión
    'DECISION_START_SELF': 100,      # Inicio decisión para TI
    'DECISION_START_OTHER': 101,     # Inicio decisión para OTRO
    'DECISION_START_GROUP': 102,     # Inicio decisión para GRUPO
    'RESPONSE_WORK': 110,             # Respuesta: trabajar
    'RESPONSE_REST': 111,             # Respuesta: descansar
    'RESPONSE_OMISSION': 112,         # Sin respuesta (timeout)
    
    # Eventos de trabajo (barra de esfuerzo)
    'EFFORT_BAR_START': 120,          # Inicio de la barra de esfuerzo
    'EFFORT_BAR_SUCCESS': 121,        # Completó la barra exitosamente
    'EFFORT_BAR_FAIL': 122,           # No completó la barra
    
    # Eventos de feedback
    'FEEDBACK_SELF_START': 130,       # Inicio feedback TI
    'FEEDBACK_OTHER_START': 131,      # Inicio feedback OTRO
    'FEEDBACK_GROUP_START': 132,      # Inicio feedback GRUPO
    'FEEDBACK_CREDITS': 140,          # Créditos ganados (seguido por el número)
    
    # Eventos de bloque y experimento
    'BLOCK_START': 200,               # Inicio de bloque
    'BLOCK_END': 201,                 # Fin de bloque
    'EXPERIMENT_START': 250,          # Inicio del experimento
    'EXPERIMENT_END': 251,            # Fin del experimento
    'CALIBRATION_START': 252,         # Inicio calibración
    'CALIBRATION_END': 253,           # Fin calibración
    'PRACTICE_START': 254,            # Inicio práctica
    'PRACTICE_END': 255,              # Fin práctica
}

# Variable global para LSL outlet
lsl_outlet = None

def initialize_lsl():
    """Inicializa la conexión LSL para enviar marcadores al EEG"""
    global lsl_outlet
    print("\n" + "="*50)
    print("INICIALIZANDO CONEXIÓN LSL PARA EEG")
    print("="*50)
    
    # Crear stream LSL
    info = StreamInfo(name='ProsocialTaskMarkers',
                      type='Markers',
                      channel_count=1,
                      channel_format='int32',
                      source_id='ProsocialTask')
    
    lsl_outlet = StreamOutlet(info)
    print("✓ Stream LSL creado exitosamente")
    print("  Por favor, conecte la aplicación de EEG ahora...")
    input("  Presione ENTER cuando el EEG esté conectado...")
    print("="*50 + "\n")
    
    return lsl_outlet

def send_marker(marker_code, description=""):
    """Envía un marcador al sistema EEG via LSL"""
    global lsl_outlet
    if lsl_outlet:
        try:
            lsl_outlet.push_sample([marker_code])
            if debug_mode:
                print(f"[EEG Marker] {marker_code} - {description}")
        except Exception as e:
            print(f"Error enviando marcador: {e}")

class TextRectException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message

# Configurations:
FullScreenShow = True  # Pantalla completa automáticamente al iniciar el experimento
keys = [pygame.K_SPACE]  # Teclas elegidas para mano derecha o izquierda
test_name = "Task"
date_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
effort_levels = [50, 65, 80, 95]
credits_levels = [2, 3, 4, 5]

# Configuración de nombres de condiciones (beneficiarios)
# Nombres internos en el código (para lógica y archivos de datos)
CONDITION_SELF = "TI"
CONDITION_INGROUP = "in-group"
CONDITION_OUTGROUP = "out-group"

# Nombres que se muestran en pantalla al participante
DISPLAY_NAME_SELF = "TI"
DISPLAY_NAME_INGROUP = "JUAN"
DISPLAY_NAME_OUTGROUP = "PEDRO"

# Color de relleno de la barra de esfuerzo (RGB)
bar_fill_color = (255, 255, 0)  # Amarillo

def get_display_name(condition):
    """Convierte el nombre interno de la condición al nombre que se muestra en pantalla"""
    if condition == CONDITION_SELF:
        return DISPLAY_NAME_SELF
    elif condition == CONDITION_INGROUP:
        return DISPLAY_NAME_INGROUP
    elif condition == CONDITION_OUTGROUP:
        return DISPLAY_NAME_OUTGROUP
    else:
        return condition

# Parámetros
block_type = "division" #block_type = division, total

min_buttons = 10

practice_iterations = 2  # repetir la práctica de esfuerzos
decision_practice_trials = 2  # trials de práctica

blocks_number = 3 # Cambiar a 3 bloques para tener 96 trials
max_answer_time = 5  # Tiempo para trabajar 
max_decision_time = 4  # Tiempo de decisión 
max_resting_time = 5  # Tiempo para descansar

optimal_square = [1, 2, 3, 4, 6, 8, 9, 12, 15, 16, 18, 20, 21, 24, 25, 27, 28, 30, 32, 35, 36, 40, 42, 45, 48, 49, 50]

# buttons configuration
base_button_color = (255, 255, 255)
pressed_button_color = (0, 255, 0)

# Onscreen instructions
def select_slide(slide_name):

    if slide_name.startswith("intro_block"):
        slide_to_use = "intro_block"
    else:
        slide_to_use = slide_name

    basic_slides = {
        'welcome': [
            u"¡Bienvenido/a, a este experimento!",
            " ",
            u"Se te indicará paso a paso qué hacer."
        ],
        'intro_block': [
            u"Ahora comenzará un bloque del experimento",
            " ",
            u"Puedes descansar unos segundos,",
            u"cuando te sientas listo presiona Espacio para continuar."
        ],
        'Instructions_Casillas': [
            u"Tarea de presionar la barra espaciadora:",
            " ",
            u"Abajo puedes encontrar un esquema de la tarea",
            u"Tu meta es presionar la barra espaciadora el mayor número de veces en 5 segundos.",
        ],
        'Interlude_Casillas': [
            u"¡Muy bien! AHORA INTENTA SUPERAR TU RENDIMIENTO"
        ],
        'Interlude_Practice': [
            u"¡Muy bien!",
            " ",
            u"Ahora vamos a practicar los niveles de esfuerzo nuevamente"
        ],
        'Exit_Casillas': [
            u"Gracias por completar la tarea.",
            " ",
            u"Presiona Espacio para continuar con la próxima tarea."
        ],
        'Pre_Instructions': [
            u"Se te ha asignado el rol de Jugador 1,",
            u"mientras que a otro participante se le ha asignado el rol de Jugador 2.",
            u"Esto significa que tomarás decisiones que afectarán al Jugador 2,",
            u"pero él no podrá tomar decisiones que te afecten a ti."
        ],
        'Cargando':[
            u"Ahora haz click para conectarte con otro jugador",
            u"",


        ],
        'Instructions_Decision_1': [
            u"Tarea de decisiones:",
            " ",
            u"En esta tarea, tú tendrás que rellenar la barra para ganar créditos.",
            u"Estos créditos pueden ser otorgados a TI, o a OTRO participante de esta investigación",
            " ",
            u"En cada ronda de esta tarea, tendrás que elegir entre dos opciones:",
            u'"Descansar": No tendrás que hacer nada y podrás descansar a cambio de 1 crédito.',
            u'"Trabajar": Tendrás que rellenar la barra para ganar una mayor cantidad de créditos',
            " ",
            u"En algunas rondas (para TI), decidirás si quieres ganar créditos para ti mismo.",
            u"En otras rondas (para OTRO), decidirás si quieres ganar créditos para otro jugador anónimo.",
            u"Los créditos que ganes serán convertidos en dinero.",
            u"En rondas TI, tú recibirás este dinero. En las rondas OTRO, el dinero será recibido por otro jugador.",
            " ",
            u"Tus decisiones serán completamente anónimas y confidenciales."
        ],
        'Instructions_Decision_2': [
            u"A continuación puedes ver 1 caso de ejemplo,", 
            u"este caso se aplicará para que TÚ o JUAN o PEDRO gane dinero"
        ],
        'Instructions_Decision_3': [
            u"Cada ronda mostrará 1 crédito por Descansar, y {} o {} créditos".format((', '.join(str(x) for x in credits_levels[:-1])), credits_levels[-1]),
            u"por completar exitosamente la tarea al rellenar la barra.",
            " ",
            u"Tienes un máximo de {} segundos para responder.".format(max_decision_time), 
            u"Si tardas más de {} segundos, se darán 0 créditos a ti o a la otra persona.".format(max_decision_time),
            " ",
            u"Si eliges trabajar para ganar más créditos,", 
            u"debes rellenar la barra, presionando Espacio repetidamente durante 5 segundos.",
            u"De lo contrario, no se otorgarán créditos para esa ronda.",
            " ",
            u"Siempre que elijas la opción Descansar, podrás reposar durante 5 segundos."
        ],
        'Instructions_Decision_final': [
            u"Recuerda, en cada ronda:",
            " ",
            u"• Verás si los créditos serán para TI o para el beneficio de un OTRO desconocido.",
            " ",
            u"• Debes escoger entre dos opciones: Una opción te da 1 crédito por descansar,", 
            u"la otra te da más créditos pero debes rellenar la barra.",
            " ",
            u"• Tendrás {} segundos para tomar una decisión, de lo contrario se darán 0 créditos para esa ronda.".format(max_decision_time),
            " ",
            u"Continúa con la página siguiente para una ronda de práctica.", 
            u"Tu objetivo es rellenar la barra presionando repetidamente la tecla Espacio.", 
            u"Ya que es sólo práctica, no se obtendrás créditos en estas rondas."
        ],
        'Effort_ending': [
            u"¡Genial! ya has practicado cómo rellenar la barra", 
            u"para así ganar créditos para TI o para a el OTRO participante.",
            " ",
            u"Ahora tendrás unas rondas de práctica similares a la tarea que tendrás posteriormente.",
            u"Como fue dicho anteriormente, aquí podrás elegir entre Descansar y ganar 1 crédito,",
            u"o trabajar para ganar una mayor cantidad de créditos. "
        ],
        'Practice_ending': [
            u"¡Excelente! Has completado las rondas de práctica.",
            " ",
            u"Ahora comenzarás con la tarea principal.",
            " ",
            u"Recuerda que en cada ronda tendrás que tomar una decisión entre Descansar y Trabajar.",
            u"Si eliges Trabajar, tendrás que rellenar la barra que se muestra en pantalla en 5 segundos.",
            u"Si eliges Descansar, podrás hacerlo durante 5 segundos."
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
            u"¡Muchas gracias por su colaboración!"
        ]
    }

    selected_slide = basic_slides[slide_to_use]

    return (selected_slide)

# Text and screen Functions
def setfonts():
    """Sets font parameters"""
    global bigchar, char, charnext
    pygame.font.init()
    font = join('media', 'Arial_Rounded_MT_Bold.ttf')
    bigchar = pygame.font.Font(font, 96)
    char = pygame.font.Font(font, 32)
    charnext = pygame.font.Font(font, 24)


def render_textrect(string, font, rect, text_color, background_color, justification=1):
    """Returns a surface containing the passed text string, reformatted
    to fit within the given rect, word-wrapping as necessary. The text
    will be anti-aliased.

    Takes the following arguments:

    string - the text you wish to render. \n begins a new line.
    font - a Font object
    rect - a rectstyle giving the size of the surface requested.
    text_color - a three-byte tuple of the rgb value of the
                 text color. ex (0, 0, 0) = BLACK
    background_color - a three-byte tuple of the rgb value of the surface.
    justification - 0 left-justified
                    1 (default) horizontally centered
                    2 right-justified

    Returns the following values:

    Success - a surface object with the text rendered onto it.
    Failure - raises a TextRectException if the text won't fit onto the surface.
    """

    import pygame

    final_lines = []

    requested_lines = string.splitlines()

    # Create a series of lines that will fit on the provided
    # rectangle.
    for requested_line in requested_lines:
        if font.size(requested_line)[0] > rect.width:
            words = requested_line.split(' ')
            # if any of our words are too long to fit, return.
            for word in words:
                if font.size(word)[0] >= rect.width:
                    raise TextRectException(
                        "The word " + word + " is too long to fit in the rect passed.")
            # Start a new line
            accumulated_line = ""
            for word in words:
                test_line = accumulated_line + word + " "
                # Build the line while the words fit.
                if font.size(test_line)[0] < rect.width:
                    accumulated_line = test_line
                else:
                    final_lines.append(accumulated_line)
                    accumulated_line = word + " "
            final_lines.append(accumulated_line)
        else:
            final_lines.append(requested_line)

    # Let's try to write the text out on the surface.
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
    """Organizes a text into a paragraph"""
    screen.fill(background)
    row = center[1] - 20 * len(text)

    if color == None:
        color = char_color

    for line in text:
    # Verificar si la línea contiene palabras que deben ser coloreadas
        if "TÚ" in line and "JUAN" in line and "PEDRO" in line:
            # Renderizar texto multicolor
            # Dividir la línea en partes
            before_tu = line.split("TÚ")[0]
            after_tu = line.split("TÚ")[1]
            between_tu_juan = after_tu.split("JUAN")[0]
            after_juan = after_tu.split("JUAN")[1]
            between_juan_pedro = after_juan.split("PEDRO")[0]
            after_pedro = after_juan.split("PEDRO")[1]
            
            # Calcular posición inicial para centrar todo
            total_width = (char.size(before_tu)[0] + char.size("TÚ")[0] + char.size(between_tu_juan)[0] + 
                        char.size("JUAN")[0] + char.size(between_juan_pedro)[0] + char.size("PEDRO")[0] + 
                        char.size(after_pedro)[0])
            x_pos = center[0] - total_width // 2
            
            # Renderizar cada parte con su color
            # Parte antes de TÚ (negro)
            phrase = char.render(before_tu, True, char_color)
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size(before_tu)[0]
            
            # TÚ (rojo)
            phrase = char.render("TÚ", True, (255, 0, 0))
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size("TÚ")[0]
            
            # Parte entre TÚ y JUAN (negro)
            phrase = char.render(between_tu_juan, True, char_color)
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size(between_tu_juan)[0]
            
            # JUAN (azul)
            phrase = char.render("JUAN", True, (0, 0, 255))
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size("JUAN")[0]
            
            # Parte entre JUAN y PEDRO (negro)
            phrase = char.render(between_juan_pedro, True, char_color)
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size(between_juan_pedro)[0]
            
            # PEDRO (verde)
            phrase = char.render("PEDRO", True, (0, 128, 0))
            screen.blit(phrase, (x_pos, row))
            x_pos += char.size("PEDRO")[0]
            
            # Parte después de PEDRO (negro)
            phrase = char.render(after_pedro, True, char_color)
            screen.blit(phrase, (x_pos, row))
        else:
            # Renderizar línea normal
            phrase = char.render(line, True, char_color)
            phrasebox = phrase.get_rect(centerx=center[0], top=row)
            screen.blit(phrase, phrasebox)
        row += 40

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
    """Organizes a paragraph into a slide"""
    paragraph(text, key, info)
    wait_time = wait(key, limit_time)
    return wait_time

def show_gif_loading(gif_path=None, duration_ms=10000):
    """Muestra una animación de carga durante un tiempo específico"""
    global screen, background
    
    # Obtener dimensiones de la pantalla
    width = screen.get_width()
    height = screen.get_height()
    
    # Variables para el control del tiempo
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    
    # Configuración del spinner
    spinner_radius = 50
    spinner_thickness = 8
    center_x = width // 2
    center_y = height // 2
    
    angle = 0
    
    # Bucle principal para mostrar la animación
    while pygame.time.get_ticks() - start_time < duration_ms:
        # Manejar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ends()
            elif event.type == KEYUP and event.key == K_ESCAPE:
                ends()
        
        # Limpiar pantalla
        screen.fill(background)
        
        # Dibujar texto "Cargando..."
        font = pygame.font.SysFont("Arial", 40, bold=False)
        text = font.render("Cargando...", True, pygame.Color('white'))
        text_rect = text.get_rect(center=(center_x, center_y - 100))
        screen.blit(text, text_rect)
        
        # Dibujar spinner animado
        for i in range(12):
            a = angle + i * 30
            x = center_x + spinner_radius * math.cos(math.radians(a))
            y = center_y + spinner_radius * math.sin(math.radians(a))
            
            # Variar la opacidad para crear efecto de movimiento
            opacity = int(255 * (1 - i / 12.0))
            color = (opacity, opacity, opacity)
            
            pygame.draw.circle(screen, color, (int(x), int(y)), spinner_thickness)
        
        angle = (angle + 5) % 360
        
        # Texto de progreso (opcional)
        elapsed = (pygame.time.get_ticks() - start_time) / 1000
        progress = min(elapsed / (duration_ms / 1000) * 100, 100)
        progress_text = font.render(f"{int(progress)}%", True, pygame.Color('white'))
        progress_rect = progress_text.get_rect(center=(center_x, center_y + 100))
        screen.blit(progress_text, progress_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    # Limpiar la pantalla al final
    screen.fill(background)
    pygame.display.flip()

def calibration_slide(text, key, image=None):    
    screen.fill(background)
    row = screen.get_rect().height // 8

    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    if image != None:
        # Cambiado para usar PNG
        picture = pygame.image.load(join("media", "images", image))
        picture = pygame.transform.scale(picture, (screen.get_rect().height/2*picture.get_width()/picture.get_height(), screen.get_rect().height/2))        
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/2 - picture.get_width()/2,row + 40))
        screen.blit(picture, rect)
    


    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
    return wait_time


def cases_slide(text, key, images=[]):    
    screen.fill(background)
    row = screen.get_rect().height // 8
    first_image = 0

    for line in text:
        phrase = char.render(line, True, char_color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 40

    # Primera fila: primeras 2 imágenes lado a lado
    first_row_images = images[:2]
    row_after_first = row
    
    for image in first_row_images:
        # Cambiado para usar PNG si es necesario
        picture = pygame.image.load(join("media", "images", image))
        picture = pygame.transform.scale(picture, (screen.get_rect().width/2, screen.get_rect().width/2*picture.get_height()/picture.get_width()))        
        rect = picture.get_rect()
        rect = rect.move(( (1+(2*first_image)) * screen.get_rect().width/4 - picture.get_width()/2, row + 40))
        screen.blit(picture, rect)
        row_after_first = max(row_after_first, row + 40 + picture.get_height())
        first_image += 1

    # Segunda fila: tercera imagen centrada (si existe)
    if len(images) > 2:
        third_image = images[2]
        picture = pygame.image.load(join("media", "images", third_image))
        picture = pygame.transform.scale(picture, (screen.get_rect().width/2, screen.get_rect().width/2*picture.get_height()/picture.get_width()))        
        rect = picture.get_rect()
        rect = rect.move((screen.get_rect().width/2 - picture.get_width()/2, row_after_first + 20))
        screen.blit(picture, rect)

    nextpage = charnext.render(u"Para continuar presione la tecla ESPACIO...", True, charnext_color)
    nextbox = nextpage.get_rect(left=15, bottom=resolution[1] - 15)
    screen.blit(nextpage, nextbox)
    pygame.display.flip()
    wait_time = wait(key, 0)
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
    pygame.event.clear()                    # CLEAR EVENTS

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

    if DISPLAY_NAME_SELF in text[1] or DISPLAY_NAME_INGROUP in text[1] or DISPLAY_NAME_OUTGROUP in text[1]:
        phrase = font.render(text[0], True, (0, 0, 0))
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
        row += 120

        font = pygame.font.Font(None, 140)

        if text[1] == DISPLAY_NAME_SELF:
            color = (255, 0, 0)  # Red for self
        elif text[1] == DISPLAY_NAME_INGROUP:
            color = (0, 0, 255)  # Blue for in-group
        else:
            color = (0, 128, 0)  # Green for out-group

        phrase = font.render(text[1], True, color)
        phrasebox = phrase.get_rect(centerx=center[0], top=row)
        screen.blit(phrase, phrasebox)
    
    else:
        for line in text:
            phrase = font.render(line, True, (255, 255, 0))
            phrasebox = phrase.get_rect(centerx=center[0], top=row)
            screen.blit(phrase, phrasebox)
            row += 120

    pygame.display.flip()
    wait(key, limit_time)


# Program Functions
def init():
    """Init display and others"""
    setfonts()
    global screen, resolution, center, background, char_color, charnext_color, fix, fixbox, fix_think, fixbox_think, izq, der, quest, questbox
    pygame.init()  # soluciona el error de inicializacion de pygame.time
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
    izq = (int(resolution[0] / 8), (int(resolution[1] / 8)*7))
    der = ((int(resolution[0] / 8)*7), (int(resolution[1] / 8)*7))
    background = Color('lightgray')
    char_color = Color('black')
    charnext_color = Color('black')
    fix = char.render('+', True, char_color)
    fixbox = fix.get_rect(centerx=center[0], centery=center[1])
    fix_think = bigchar.render('+', True, Color('red'))
    fixbox_think = fix.get_rect(centerx=center[0], centery=center[1])
    quest = bigchar.render('?', True, char_color)
    questbox = quest.get_rect(centerx=center[0], centery=center[1])
    screen.fill(background)
    pygame.display.flip()


def pygame_exit():
    # Enviar marcador de fin del experimento antes de salir
    send_marker(MARKERS['EXPERIMENT_END'], "Experiment ended")
    pygame.quit()
    sys.exit()


def block_spacebar(duration_ms):
    """Block spacebar input for specified duration in milliseconds"""
    start_time = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_time < duration_ms:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame_exit()
            # Consume all other events during blocking period
        pygame.time.delay(10)  # Small delay to prevent CPU overuse
    pygame.event.clear()  # Clear any accumulated events


def draw_progress_bar(current_presses, total_presses, bar_width=100, bar_height=400):
    """Draw a vertical progress bar"""
    # Calculate bar position (centered on screen)
    bar_x = center[0] - bar_width // 2
    bar_y = center[1] - bar_height // 2
    
    # Draw background (empty bar)
    pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
    
    # Calculate fill height
    fill_height = int((current_presses / total_presses) * bar_height)
    fill_height = min(fill_height, bar_height)  # Cap at max height
    
    # Draw filled portion (from bottom up)
    if fill_height > 0:
        fill_y = bar_y + bar_height - fill_height
        pygame.draw.rect(screen, bar_fill_color, (bar_x, fill_y, bar_width, fill_height))
    
    # Draw border
    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height), 3)
    
    pygame.display.flip()


def show_effort_preview(effort_level, effort_percentage):
    """Show effort circle preview before practice"""
    screen.fill(background)
    
    # CORRECCIÓN: Mostrar solo "Nivel de esfuerzo" sin el porcentaje
    font = pygame.font.Font(None, 48)
    text = font.render("Nivel de esfuerzo", True, (0, 0, 0))
    text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/3))
    screen.blit(text, text_rect)
    
    # Load and display effort image - use PNG with self version (red)
    try:
        effort_image = pygame.image.load(join('media', f'{effort_percentage}_self.png'))
        
        # USAR EL MISMO TAMAÑO QUE EN take_decision() para consistencia
        # Aquí también se puede personalizar el tamaño
        preview_size = 550
        
        # Mantener proporción original
        original_width = effort_image.get_width()
        original_height = effort_image.get_height()
        
        # Calcular el factor de escala manteniendo la proporción
        scale_factor = preview_size / max(original_width, original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Escalar la imagen manteniendo su proporción
        effort_image = pygame.transform.scale(effort_image, (new_width, new_height))
        img_rect = effort_image.get_rect(center=(resolution[0]/2, resolution[1]/2))
        screen.blit(effort_image, img_rect)
    except:
        # Fallback: draw a simple circle if image not found
        circle_radius = 175  # Mitad del tamaño estándar
        circle_center = (resolution[0]//2, resolution[1]//2)
        pygame.draw.circle(screen, (255, 255, 255), circle_center, circle_radius)
        pygame.draw.circle(screen, (255, 0, 0), circle_center, circle_radius, 2)  # Red border for self
        fallback_font = pygame.font.Font(None, 24)
        text = fallback_font.render(f"{effort_percentage}%", True, (255, 0, 0))
        text_rect = text.get_rect(center=circle_center)
        screen.blit(text, text_rect)
    
    # Instructions
    instruction_font = pygame.font.Font(None, 32)
    text = instruction_font.render("Presiona Espacio para continuar", True, (0, 0, 0))
    text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]*2/3))
    screen.blit(text, text_rect)
    
    pygame.display.flip()
    wait(K_SPACE, 0)


def show_effort_bar(target_presses, max_time=5, title_text="", is_calibration=False):
    """Show vertical bar that fills with spacebar presses"""
    # CORRECCIÓN BUG: Limpiar el buffer de eventos antes de empezar
    pygame.event.clear()
    
    # Enviar marcador de inicio de barra de esfuerzo
    send_marker(MARKERS['EFFORT_BAR_START'], f"Effort bar start - Target: {target_presses}")
    
    stage_change = USEREVENT + 2
    pygame.time.set_timer(stage_change, max_time * 1000)

    screen.fill(background)
    
    # Determine color based on condition
    if DISPLAY_NAME_SELF in title_text:
        text_color = (255, 0, 0)  # Red for self
    elif DISPLAY_NAME_INGROUP in title_text:
        text_color = (0, 0, 255)  # Blue for in-group
    elif DISPLAY_NAME_OUTGROUP in title_text:
        text_color = (0, 128, 0)  # Green for out-group
    else:
        text_color = (0, 0, 0)  # Black for calibration/neutral
    
    # Draw title text at the top of the screen
    font = pygame.font.Font(None, 36)
    text = font.render(title_text, True, text_color)
    text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/8))
    screen.blit(text, text_rect)
    
    # Draw initial empty bar
    draw_progress_bar(0, target_presses)
    
    # Instructions for calibration
    if is_calibration:
        instruction_font = pygame.font.Font(None, 24)
        instruction_text = "Presiona la barra espaciadora repetidamente para llenar la barra"
        text = instruction_font.render(instruction_text, True, (0, 0, 0))
        text_rect = text.get_rect(centerx=center[0], bottom=resolution[1] - 50)
        screen.blit(text, text_rect)
        pygame.display.flip()

    presses_count = 0
    done = False
    first_press_time = None
    last_press_time = None

    # CORRECCIÓN BUG: Añadir un pequeño delay y limpiar eventos otra vez
    pygame.time.delay(100)
    pygame.event.clear()
    
    tw = pygame.time.get_ticks()

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()

            elif event.type == KEYUP and event.key == K_c:
                done = True

            # Detect spacebar press
            elif event.type == KEYUP and event.key == K_SPACE:
                presses_count += 1
                if first_press_time is None:
                    first_press_time = pygame.time.get_ticks() - tw
                last_press_time = pygame.time.get_ticks() - tw
                
                # Update progress bar
                screen.fill(background)
                
                # Redraw title with proper color
                font = pygame.font.Font(None, 36)
                text = font.render(title_text, True, text_color)
                text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/8))
                screen.blit(text, text_rect)
                
                # Redraw instructions for calibration
                if is_calibration:
                    instruction_font = pygame.font.Font(None, 24)
                    instruction_text = "Presiona la barra espaciadora repetidamente para llenar la barra"
                    text = instruction_font.render(instruction_text, True, (0, 0, 0))
                    text_rect = text.get_rect(centerx=center[0], bottom=resolution[1] - 50)
                    screen.blit(text, text_rect)
                
                draw_progress_bar(presses_count, target_presses)
                
                # Check if target reached
                if presses_count >= target_presses:
                    last_press_time = pygame.time.get_ticks() - tw
                    done = True

            elif event.type == stage_change:
                done = True

    pygame.time.set_timer(stage_change, 0)
    pygame.event.clear()  # CLEAR EVENTS

    # Enviar marcador de fin de barra de esfuerzo
    if presses_count >= target_presses:
        send_marker(MARKERS['EFFORT_BAR_SUCCESS'], f"Effort bar completed - Presses: {presses_count}")
    else:
        send_marker(MARKERS['EFFORT_BAR_FAIL'], f"Effort bar failed - Presses: {presses_count}/{target_presses}")

    # Block spacebar for 3 seconds
    block_spacebar(3000)

    # Return the presses count and whether target was reached
    return presses_count, presses_count >= target_presses, first_press_time, last_press_time


def take_decision(buttons_number, credits_number, title_text, max_time = 5, test = False, effort_level = None, condition = None):
    """Show decision screen with condition-specific colors and images"""
    # CORRECCIÓN BUG: Limpiar el buffer de eventos antes de empezar
    pygame.event.clear()
    
    # Enviar marcador de inicio de decisión según condición
    if condition == CONDITION_SELF or DISPLAY_NAME_SELF in title_text:
        send_marker(MARKERS['DECISION_START_SELF'], f"Decision start - Self - Credits: {credits_number}")
    elif condition == CONDITION_OUTGROUP or DISPLAY_NAME_OUTGROUP in title_text:
        send_marker(MARKERS['DECISION_START_GROUP'], f"Decision start - out-group - Credits: {credits_number}")
    else:
        send_marker(MARKERS['DECISION_START_OTHER'], f"Decision start - in-group - Credits: {credits_number}")
    
    screen.fill(background)

    font = pygame.font.Font(None, 72)
    
    # Determine condition and colors
    if condition == CONDITION_SELF or DISPLAY_NAME_SELF in title_text:
        condition = CONDITION_SELF
        text_color = (255, 0, 0)  # Red for self
        offset = len(DISPLAY_NAME_SELF)
    elif condition == CONDITION_INGROUP or DISPLAY_NAME_INGROUP in title_text:
        condition = CONDITION_INGROUP
        text_color = (0, 0, 255)  # Blue for in-group
        offset = len(DISPLAY_NAME_INGROUP)
    elif condition == CONDITION_OUTGROUP or DISPLAY_NAME_OUTGROUP in title_text:
        condition = CONDITION_OUTGROUP
        text_color = (0, 128, 0)  # Green for out-group
        offset = len(DISPLAY_NAME_OUTGROUP)
    else:
        text_color = (0, 128, 0)  # Green for neutral
        offset = 0

    if offset > 0:
        text = font.render(title_text[:-offset], True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
        text2 = font.render(title_text[-offset:], True, text_color)
        text_rect2 = text2.get_rect(center=(resolution[0]/2, (resolution[1]/6) + 100))
        
        screen.blit(text, text_rect)
        screen.blit(text2, text_rect2)
    else:
        text = font.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
        screen.blit(text, text_rect)

    # Changed from vertical to horizontal layout
    button_positions = ["left", "right"]  # Left and right positions

    shuffle(button_positions)
    
    # Define positions for text and images (no button rectangles)
    left_x = resolution[0]/4  # Left side of screen
    right_x = 3*resolution[0]/4  # Right side of screen
    content_y = resolution[1]/2  # Vertically centered
    
    font = pygame.font.Font(None, 48)
    
    # Position 1 (Work option) - determine if left or right
    if button_positions[0] == "left":
        work_x = left_x
        rest_x = right_x
        work_key = "N"
        rest_key = "M"
    else:
        work_x = right_x
        rest_x = left_x
        work_key = "M"
        rest_key = "N"
    
    # Aquí se declara el tamaño de las imágenes - PERSONALIZABLE
    standard_circle_size = 550
    
    # Work option - credits text
    text = font.render(f"{credits_number} créditos", True, text_color)
    text_rect = text.get_rect(centerx=work_x, centery=content_y - 130)
    screen.blit(text, text_rect)
    
    # Store positions and sizes for drawing selection box
    work_img_rect = None
    rest_img_rect = None
    work_text_rect = text_rect  # Guardar la posición del texto
    
    # Load and display effort image with condition-specific colors
    if effort_level is not None:
        try:
            # Use condition-specific image (self or other)
            if condition == CONDITION_SELF:
                effort_image = pygame.image.load(join('media', f'{effort_level}_self.png'))
            elif condition == CONDITION_INGROUP:
                effort_image = pygame.image.load(join('media', f'{effort_level}_other.png'))
            elif condition == CONDITION_OUTGROUP:
                effort_image = pygame.image.load(join('media', f'{effort_level}_group.png'))
            else:
                # Fallback to self version if condition not specified
                effort_image = pygame.image.load(join('media', f'{effort_level}_self.png'))
            
            # CORRECCIÓN: Escalar manteniendo la proporción original
            original_width = effort_image.get_width()
            original_height = effort_image.get_height()
            
            # Calcular el factor de escala manteniendo la proporción
            scale_factor = standard_circle_size / max(original_width, original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Escalar la imagen manteniendo su proporción
            effort_image = pygame.transform.scale(effort_image, (new_width, new_height))
            work_img_rect = effort_image.get_rect(centerx=work_x, centery=content_y + 20)
            screen.blit(effort_image, work_img_rect)
        except:
            # Fallback: draw a simple circle with text if image not found
            circle_radius = standard_circle_size // 2
            circle_center = (int(work_x), int(content_y + 20))
            work_img_rect = pygame.Rect(circle_center[0] - circle_radius, circle_center[1] - circle_radius, 
                                        standard_circle_size, standard_circle_size)
            pygame.draw.circle(screen, (255, 255, 255), circle_center, circle_radius)
            pygame.draw.circle(screen, text_color, circle_center, circle_radius, 2)
            fallback_font = pygame.font.Font(None, 24)
            text = fallback_font.render(f"{effort_level}%", True, text_color)
            text_rect = text.get_rect(center=circle_center)
            screen.blit(text, text_rect)

    # Rest option - text
    text = font.render("1 crédito", True, text_color)
    text_rect = text.get_rect(centerx=rest_x, centery=content_y - 130)
    screen.blit(text, text_rect)
    rest_text_rect = text_rect  # Guardar la posición del texto
    
    # Load and display rest image with same size as effort image
    try:
        rest_image = pygame.image.load(join('media', 'Rest.png'))
        # CORRECCIÓN: Escalar manteniendo la proporción original
        original_width = rest_image.get_width()
        original_height = rest_image.get_height()
        
        # Calcular el factor de escala manteniendo la proporción
        scale_factor = standard_circle_size / max(original_width, original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Escalar la imagen manteniendo su proporción
        rest_image = pygame.transform.scale(rest_image, (new_width, new_height))
        rest_img_rect = rest_image.get_rect(centerx=rest_x, centery=content_y + 20)
        screen.blit(rest_image, rest_img_rect)
    except:
        # Fallback: draw a simple circle with text if image not found
        circle_radius = standard_circle_size // 2
        circle_center = (int(rest_x), int(content_y + 20))
        rest_img_rect = pygame.Rect(circle_center[0] - circle_radius, circle_center[1] - circle_radius, 
                                    standard_circle_size, standard_circle_size)
        pygame.draw.circle(screen, (255, 255, 255), circle_center, circle_radius)
        pygame.draw.circle(screen, text_color, circle_center, circle_radius, 2)
        fallback_font = pygame.font.Font(None, 24)
        text = fallback_font.render("Descanso", True, text_color)
        text_rect = text.get_rect(center=circle_center)
        screen.blit(text, text_rect)

    # MODIFICACIÓN: NO mostrar el cuadro inicial
    # El cuadro solo aparecerá después de que se tome una decisión
    
    # Add key indicators below images ONLY in test mode
    if test:
        key_font = pygame.font.Font(None, 60)
        text_work = key_font.render(work_key, True, text_color)
        text_work_rect = text_work.get_rect(centerx=work_x, top=content_y + 210)
        screen.blit(text_work, text_work_rect)
        
        text_rest = key_font.render(rest_key, True, text_color)
        text_rest_rect = text_rest.get_rect(centerx=rest_x, top=content_y + 210)
        screen.blit(text_rest, text_rest_rect)

        # Instructions at the bottom ONLY in test mode
        instruction_font = pygame.font.Font(None, 36)
        text = instruction_font.render("Presiona N para la opción izquierda o M para la opción derecha", True, (0, 0, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1] * 0.89))
        screen.blit(text, text_rect)

    pygame.display.flip()

    done = False
    selected_button = 0
    key_pressed = None
    tw = pygame.time.get_ticks()
    reaction_time = None

    # MODIFICACIÓN: Padding aumentado a 50px
    box_padding = 25

    while not done:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                    pygame_exit()
            
            elif event.type == KEYUP and event.key == K_n:
                reaction_time = pygame.time.get_ticks() - tw
                key_pressed = "left"
                if button_positions[0] == "left":  # First button is on the left
                    selected_button = 1
                    selected_option = "work"
                    selected_img_rect = work_img_rect
                    selected_text_rect = work_text_rect
                    send_marker(MARKERS['RESPONSE_WORK'], f"Response: Work - RT: {reaction_time}ms")
                else:  # Second button is on the left
                    selected_button = 2
                    selected_option = "rest"
                    selected_img_rect = rest_img_rect
                    selected_text_rect = rest_text_rect
                    send_marker(MARKERS['RESPONSE_REST'], f"Response: Rest - RT: {reaction_time}ms")
                
                # MODIFICACIÓN: Calcular tiempo de display del cuadro
                time_to_show_box = (max_time * 1000) - reaction_time
                
                # Redibujar pantalla con el cuadro de selección (código completo para N y M)
                _redraw_decision_screen_with_box(title_text, text_color, offset, credits_number, 
                                                effort_level, condition, work_x, rest_x, content_y,
                                                selected_img_rect, selected_text_rect, box_padding,
                                                standard_circle_size, test, work_key, rest_key)
                
                pygame.display.flip()
                pygame.time.delay(int(time_to_show_box))
                pygame.event.clear()
                done = True
                
            elif event.type == KEYUP and event.key == K_m:
                reaction_time = pygame.time.get_ticks() - tw
                key_pressed = "right"
                if button_positions[0] == "left":  # Second button is on the right
                    selected_button = 2
                    selected_option = "rest"
                    selected_img_rect = rest_img_rect
                    selected_text_rect = rest_text_rect
                    send_marker(MARKERS['RESPONSE_REST'], f"Response: Rest - RT: {reaction_time}ms")
                else:  # First button is on the right
                    selected_button = 1
                    selected_option = "work"
                    selected_img_rect = work_img_rect
                    selected_text_rect = work_text_rect
                    send_marker(MARKERS['RESPONSE_WORK'], f"Response: Work - RT: {reaction_time}ms")
                
                # MODIFICACIÓN: Calcular tiempo de display del cuadro
                time_to_show_box = (max_time * 1000) - reaction_time
                
                # Redibujar pantalla con el cuadro de selección
                _redraw_decision_screen_with_box(title_text, text_color, offset, credits_number, 
                                                effort_level, condition, work_x, rest_x, content_y,
                                                selected_img_rect, selected_text_rect, box_padding,
                                                standard_circle_size, test, work_key, rest_key)
                
                pygame.display.flip()
                pygame.time.delay(int(time_to_show_box))
                pygame.event.clear()
                done = True
        
        # Check for timeout without visual timer
        rt = pygame.time.get_ticks() - tw
        if rt >= max_time * 1000:
            send_marker(MARKERS['RESPONSE_OMISSION'], f"Response: Timeout after {rt}ms")
            done = True

    return (selected_button, key_pressed, reaction_time)


def _redraw_decision_screen_with_box(title_text, text_color, offset, credits_number, 
                                    effort_level, condition, work_x, rest_x, content_y,
                                    selected_img_rect, selected_text_rect, box_padding,
                                    standard_circle_size, test, work_key, rest_key):
    """Helper function to redraw decision screen with selection box"""
    screen.fill(background)
    
    # Redibujar título
    font_title = pygame.font.Font(None, 72)
    if offset > 0:
        text = font_title.render(title_text[:-offset], True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
        text2 = font_title.render(title_text[-offset:], True, text_color)
        text_rect2 = text2.get_rect(center=(resolution[0]/2, (resolution[1]/6) + 100))
        screen.blit(text, text_rect)
        screen.blit(text2, text_rect2)
    else:
        text = font_title.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, (resolution[1]/6)))
        screen.blit(text, text_rect)
    
    # Redibujar todos los elementos
    font = pygame.font.Font(None, 48)
    
    # Work option
    text = font.render(f"{credits_number} créditos", True, text_color)
    text_rect = text.get_rect(centerx=work_x, centery=content_y - 130)
    screen.blit(text, text_rect)
    
    if effort_level is not None:
        try:
            if condition == CONDITION_SELF:
                effort_image = pygame.image.load(join('media', f'{effort_level}_self.png'))
            elif condition == CONDITION_INGROUP:
                effort_image = pygame.image.load(join('media', f'{effort_level}_other.png'))
            elif condition == CONDITION_OUTGROUP:
                effort_image = pygame.image.load(join('media', f'{effort_level}_group.png'))
            
            original_width = effort_image.get_width()
            original_height = effort_image.get_height()
            scale_factor = standard_circle_size / max(original_width, original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            effort_image = pygame.transform.scale(effort_image, (new_width, new_height))
            work_img_rect = effort_image.get_rect(centerx=work_x, centery=content_y + 20)
            screen.blit(effort_image, work_img_rect)
        except:
            pass
    
    # Rest option
    text = font.render("1 crédito", True, text_color)
    text_rect = text.get_rect(centerx=rest_x, centery=content_y - 130)
    screen.blit(text, text_rect)
    
    try:
        rest_image = pygame.image.load(join('media', 'Rest.png'))
        original_width = rest_image.get_width()
        original_height = rest_image.get_height()
        scale_factor = standard_circle_size / max(original_width, original_height)
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        rest_image = pygame.transform.scale(rest_image, (new_width, new_height))
        rest_img_rect = rest_image.get_rect(centerx=rest_x, centery=content_y + 20)
        screen.blit(rest_image, rest_img_rect)
    except:
        pass
    
    # Add key indicators if in test mode
    if test:
        key_font = pygame.font.Font(None, 60)
        text_work = key_font.render(work_key, True, text_color)
        text_work_rect = text_work.get_rect(centerx=work_x, top=content_y + 210)
        screen.blit(text_work, text_work_rect)
        
        text_rest = key_font.render(rest_key, True, text_color)
        text_rest_rect = text_rest.get_rect(centerx=rest_x, top=content_y + 210)
        screen.blit(text_rest, text_rest_rect)
        
        instruction_font = pygame.font.Font(None, 36)
        text = instruction_font.render("Presiona N para la opción izquierda o M para la opción derecha", True, (0, 0, 0))
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1] * 0.89))
        screen.blit(text, text_rect)
    
    # Dibujar cuadro de selección
    if selected_img_rect and selected_text_rect:
        min_top = min(selected_text_rect.top, selected_img_rect.top)
        max_bottom = max(selected_text_rect.bottom, selected_img_rect.bottom)
        combined_height = max_bottom - min_top
        
        box_rect = pygame.Rect(
            selected_img_rect.centerx - selected_img_rect.width//2 - box_padding,
            min_top - box_padding,
            selected_img_rect.width + box_padding * 2,
            combined_height + box_padding * 2
        )
        pygame.draw.rect(screen, (0, 0, 0), box_rect, 5)


def show_resting(title_text, max_time = 5):
    """Show resting screen with condition-specific colors"""
    screen.fill(background)
    font = pygame.font.Font(None, 42)

    # Determine condition and use appropriate color
    if DISPLAY_NAME_SELF in title_text:
        text_color = (255, 0, 0)  # Red for self
        text = font.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
    elif DISPLAY_NAME_INGROUP in title_text:
        text_color = (0, 0, 255)  # Blue for in-group
        text = font.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
    elif DISPLAY_NAME_OUTGROUP in title_text:
        text_color = (0, 128, 0)  # Green for out-group
        text = font.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))
    else:
        text_color = (0, 128, 0)  # Green for neutral
        text = font.render(title_text, True, text_color)
        text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/10))

    screen.blit(text, text_rect)

    resting_text = pygame.font.Font(None, 90)
    text = resting_text.render("DESCANSO", True, (0, 0, 0))
    resting_text_rect = text.get_rect(center=(resolution[0]/2, resolution[1]/2))
    screen.blit(text, resting_text_rect)

    pygame.display.flip()

    tw = pygame.time.get_ticks()

    while True:
        for event in pygame.event.get():
            if event.type == KEYUP and event.key == K_ESCAPE:
                pygame_exit()
        # Check for timeout without visual timer
        rt = pygame.time.get_ticks() - tw
        if rt >= max_time * 1000:
            return


def task(self_combinations, other_combinations, group_combinations, blocks_number, block_type, max_answer_time, 
         test = False, decision_practice_trials = 1, file = None, effort_table = None):
    # Para práctica
    if test:
        send_marker(MARKERS['PRACTICE_START'], "Practice trials start")
        import random
        practice_self = random.sample(self_combinations, min(2, len(self_combinations)))
        practice_other = random.sample(other_combinations, min(2, len(other_combinations)))
        practice_group = random.sample(group_combinations, min(2, len(group_combinations)))
        actual_combinations_list = practice_self + practice_other + practice_group
        shuffle(actual_combinations_list)
        
        for combination in actual_combinations_list:
            first_button_pressed_time, last_button_pressed_time = None, None

            display_name = get_display_name(combination[2])
            windows([f"Créditos para", display_name], K_SPACE, 1000)

            effort_level = effort_table[combination[0]] if effort_table else None

            selection, key_pressed, decision_reaction_time = take_decision(
                combination[0], combination[1], f"Créditos para {display_name}", 
                max_time = max_decision_time, test = test, effort_level = effort_level, 
                condition = combination[2]
            )

            if selection not in [1, 2]:
                while selection not in [1, 2]:
                    slide(select_slide('TestingDecision'), False, K_SPACE)
                    selection, key_pressed, decision_reaction_time = take_decision(
                        combination[0], combination[1], f"Créditos para {display_name}", 
                        max_time = max_decision_time, test = test, effort_level = effort_level,
                        condition = combination[2]
                    )

            if selection == 1:
                presses_done, target_reached, first_press_time, last_press_time = show_effort_bar(
                    target_presses=combination[0], max_time=max_answer_time, 
                    title_text=f"Créditos para {display_name}"
                )
                earned_credits = combination[1] if target_reached else 0
            elif selection == 2:
                show_resting(f"Créditos para {display_name}", max_time = max_resting_time)
                earned_credits = 1
                presses_done = 0
                target_reached = True
                first_press_time = None
                last_press_time = None

            # Enviar marcador de feedback
            if combination[2] == CONDITION_SELF:
                send_marker(MARKERS['FEEDBACK_SELF_START'], f"Feedback self - Credits: {earned_credits}")
                windows(["Has ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
            elif combination[2] == CONDITION_OUTGROUP:
                send_marker(MARKERS['FEEDBACK_GROUP_START'], f"Feedback out-group - Credits: {earned_credits}")
                windows([f"{DISPLAY_NAME_OUTGROUP} ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
            else:
                send_marker(MARKERS['FEEDBACK_OTHER_START'], f"Feedback in-group - Credits: {earned_credits}")
                windows([f"{DISPLAY_NAME_INGROUP} ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
        
        send_marker(MARKERS['PRACTICE_END'], "Practice trials end")
        return
    
    # Experimental trials (no práctica)
    repetitions_per_block = 2
    
    for block_num in range(blocks_number):
        send_marker(MARKERS['BLOCK_START'], f"Block {block_num + 1} start")
        
        if block_type == "division":
            block_self_combinations = self_combinations * repetitions_per_block
            block_other_combinations = other_combinations * repetitions_per_block
            block_group_combinations = group_combinations * repetitions_per_block
            actual_combinations_list = block_self_combinations + block_other_combinations + block_group_combinations
        elif block_type == "total":
            actual_combinations_list = (self_combinations + other_combinations + group_combinations) * repetitions_per_block
        else:
            print("Tipo de bloque no reconocido")
            break

        shuffle(actual_combinations_list)

        for combination in actual_combinations_list:
            first_button_pressed_time, last_button_pressed_time = None, None

            display_name = get_display_name(combination[2])
            windows([f"Créditos para", display_name], K_SPACE, 1000)

            effort_level = effort_table[combination[0]] if effort_table else None

            selection, key_pressed, decision_reaction_time = take_decision(
                combination[0], combination[1], f"Créditos para {display_name}", 
                max_time = max_decision_time, test = test, effort_level = effort_level,
                condition = combination[2]
            )

            if selection not in [1, 2]:
                show_resting(f"Créditos para {display_name}", max_time = max_resting_time)
                presses_done = 0
                target_reached = False
                first_press_time = None
                last_press_time = None
                earned_credits = 0

            elif selection == 1:
                presses_done, target_reached, first_press_time, last_press_time = show_effort_bar(
                    target_presses=combination[0], max_time=max_answer_time, 
                    title_text=f"Créditos para {display_name}"
                )
                earned_credits = combination[1] if target_reached else 0

            elif selection == 2:
                show_resting(f"Créditos para {display_name}", max_time = max_resting_time)
                earned_credits = 1
                presses_done = 0
                target_reached = True
                first_press_time = None
                last_press_time = None
            
            # Log data
            if file != None:
                file.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
                    effort_table[combination[0]], combination[1], 
                    "Self" if combination[2] == CONDITION_SELF else ("out-group" if combination[2] == CONDITION_OUTGROUP else "in-group"), 
                    "task" if selection == 1 else ("resting" if selection == 2 else "no decision"), 
                    presses_done if selection == 1 else 0, 
                    "True" if selection == 2 else target_reached, 
                    earned_credits, decision_reaction_time, 
                    first_press_time, last_press_time
                ))
                file.flush()
            
            # Enviar marcador de feedback y mostrar créditos ganados
            if combination[2] == CONDITION_SELF:
                send_marker(MARKERS['FEEDBACK_SELF_START'], f"Feedback self - Credits: {earned_credits}")
                send_marker(MARKERS['FEEDBACK_CREDITS'] + earned_credits, f"Credits earned: {earned_credits}")
                windows(["Has ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
            elif combination[2] == CONDITION_OUTGROUP:
                send_marker(MARKERS['FEEDBACK_GROUP_START'], f"Feedback out-group - Credits: {earned_credits}")
                send_marker(MARKERS['FEEDBACK_CREDITS'] + earned_credits, f"Credits earned: {earned_credits}")
                windows([f"{DISPLAY_NAME_OUTGROUP} ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)
            else:
                send_marker(MARKERS['FEEDBACK_OTHER_START'], f"Feedback in-group - Credits: {earned_credits}")
                send_marker(MARKERS['FEEDBACK_CREDITS'] + earned_credits, f"Credits earned: {earned_credits}")
                windows([f"{DISPLAY_NAME_INGROUP} ha ganado", f"{earned_credits} créditos"], K_SPACE, 1000)

        send_marker(MARKERS['BLOCK_END'], f"Block {block_num + 1} end")
        
        if block_num < blocks_number - 1:  # No mostrar break después del último bloque
            slide(select_slide('Break'), False, K_SPACE)


# Main Function
def main():
    """Game's main loop"""
    
    # Inicializar conexión LSL
    initialize_lsl()

    # Si no existe la carpeta data se crea
    if not os.path.exists('data/'):
        os.makedirs('data/')

    # Username = id_condition_geometry_hand
    subj_name = input(
        "Ingrese el ID del participante y presione ENTER para iniciar: ")

    while (len(subj_name) < 1):
        os.system('cls')
        print("ID ingresado no cumple con las condiciones, contacte con el encargado...")
        subj_name = input(
            "Ingrese el ID del participante y presione ENTER para iniciar: ")

    pygame.init()

    csv_name = join('data', date_name + "_" + subj_name + ".csv")
    dfile = open(csv_name, 'w')
    # condition = self/other
    dfile.write("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" % ("NivelEsfuerzo", "NivelReward", "Condición", "Decisión", "PresionesHechas", "ÉxitoTarea", "CréditosGanados", "TiempoReacciónDecisión", "TiempoReacciónPrimerPresión", "TiempoReacciónÚltimaPresión"))
    dfile.flush()

    init()

    # Enviar marcador de inicio del experimento
    send_marker(MARKERS['EXPERIMENT_START'], "Experiment started")

    slide(select_slide('welcome'), False, K_SPACE)

    # ------------------- calibration block ------------------------
    send_marker(MARKERS['CALIBRATION_START'], "Calibration start")
    
    calibration_slide(select_slide('Instructions_Casillas'), K_SPACE, "testing_schema.jpg")

    # Calibraciones
    presses_count_1, _, _, _ = show_effort_bar(target_presses=50, max_time=max_answer_time, title_text="Comienza!", is_calibration=True)
    slide(select_slide('Interlude_Casillas'), False, K_SPACE)

    # Segunda calibración: 110% de la primera
    target_calibration_2 = ceil(presses_count_1 * 1.1)
    presses_count_2, _, _, _ = show_effort_bar(target_presses=target_calibration_2, max_time=max_answer_time, title_text="Comienza!", is_calibration=True)
    slide(select_slide('Interlude_Casillas'), False, K_SPACE)

    # Tercera calibración: 110% del máximo previo
    max_previous = max(presses_count_1, presses_count_2)
    target_calibration_3 = ceil(max_previous * 1.1)
    presses_count_3, _, _, _ = show_effort_bar(target_presses=target_calibration_3, max_time=max_answer_time, title_text="Comienza!", is_calibration=True)

    # Usar el máximo de las tres calibraciones
    max_presses_count = max(presses_count_1, presses_count_2, presses_count_3)
    if max_presses_count < min_buttons:
        max_presses_count = min_buttons
    send_marker(MARKERS['CALIBRATION_END'], f"Calibration end - Max presses: {max_presses_count}")

    # Mostrar GIF de carga por 10 segundos
    slide(select_slide('Cargando'), False, K_SPACE)
    show_gif_loading(duration_ms=30000)

    # ------------------- Decision instructions block ------------------------
    slide(select_slide('Pre_Instructions'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_1'), False, K_SPACE)
    cases_slide(select_slide('Instructions_Decision_2'), K_SPACE, ["TI_schema.jpg"])
    slide(select_slide('Instructions_Decision_3'), False, K_SPACE)
    slide(select_slide('Instructions_Decision_final'), False, K_SPACE)

    # ------------------------ Training Section -----------------------------
    effort_levels_recalculated = [ceil(max_presses_count*(effort/100)) for effort in effort_levels]
    # effort table effort_levels_recalculated: effort_levels
    effort_table = dict(zip(effort_levels_recalculated, effort_levels))

    self_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, [CONDITION_SELF]*len(effort_levels_recalculated)))
    other_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, [CONDITION_INGROUP]*len(effort_levels_recalculated)))
    group_combinations = list(itertools.product(effort_levels_recalculated, credits_levels, [CONDITION_OUTGROUP]*len(effort_levels_recalculated)))

    shuffle(self_combinations)
    shuffle(other_combinations)
    shuffle(group_combinations)

    # Testing Trials for all effort levels
    for iteration in range(practice_iterations):
        # Agregar mensaje entre las dos rondas de práctica
        if iteration == 1:  # Antes de la segunda ronda
            slide(select_slide('Interlude_Practice'), False, K_SPACE)
        
        for i, effort_level in enumerate(effort_levels_recalculated):
            # Show effort circle preview before each practice level
            show_effort_preview(effort_level, effort_levels[i])
            # Then show the practice trial
            show_effort_bar(target_presses=effort_level, max_time=max_answer_time, title_text=f"Créditos para TI")

    # Testing full block      
    slide(select_slide('Effort_ending'), False, K_SPACE)

    task(self_combinations, other_combinations, group_combinations, blocks_number, block_type, max_answer_time, test = True, decision_practice_trials = decision_practice_trials, effort_table = effort_table)

    slide(select_slide('Practice_ending'), False, K_SPACE)

    # ------------------------ Experiment Section -----------------------------
    # Experiment Starting
    task(self_combinations, other_combinations, group_combinations, blocks_number, block_type, max_answer_time, file = dfile, effort_table = effort_table)

    dfile.flush()

    slide(select_slide('farewell'), True, K_SPACE)
    dfile.close()
    
    # Enviar marcador de fin del experimento
    send_marker(MARKERS['EXPERIMENT_END'], "Experiment completed")
    
    ends()


if __name__ == "__main__":
    main()