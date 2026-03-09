# Prosocial Effort Task (PET)

Tarea experimental para estudiar el comportamiento prosocial mediante decisiones de esfuerzo. Los participantes eligen entre trabajar (presionar la barra espaciadora repetidamente) o descansar para ganar créditos para sí mismos o para otros participantes (in-group/out-group).

## Descripción

En cada trial, el participante debe decidir entre:
- **Trabajar**: Rellenar una barra de esfuerzo presionando la barra espaciadora para ganar más créditos (2-5 créditos)
- **Descansar**: No hacer nada y ganar 1 crédito

Los créditos pueden ser asignados a:
- **TI**: El propio participante
- **In-group**: Una persona que "vota igual" al participante
- **Out-group**: Una persona que "vota distinto" al participante

### Estructura del experimento

1. **Calibración**: 3 fases para determinar la capacidad máxima de presiones del participante
2. **Práctica de esfuerzo**: 2 rondas de práctica con los 4 niveles de esfuerzo
3. **Práctica de decisión**: 6 trials de práctica (2 por condición)
4. **Tarea experimental**: 3 bloques × 48 trials = 144 trials totales

### Parámetros temporales

- Tiempo de decisión: 4 segundos
- Tiempo de trabajo/descanso: 5 segundos
- Tiempo de feedback: 1 segundo
- **Duración total estimada**: 30-40 minutos

## Requisitos

### Python
```
Python 3.10 o superior
```

### Librerías
```bash
pip install pygame pylsl opencv-python
```

| Librería | Versión | Descripción |
|----------|---------|-------------|
| pygame | ≥2.0 | Interfaz gráfica y manejo de eventos |
| pylsl | ≥1.16 | Comunicación con EEG via Lab Streaming Layer |
| opencv-python | ≥4.0 | Procesamiento de imágenes (cv2) |

### Instalación de dependencias

```bash
pip install pygame pylsl opencv-python
```

## Estructura de carpetas

```
proyecto/
├── Prosocial_Effort_Task.py    # Script principal
├── README.md
├── media/
│   ├── images/
│   │   ├── TI_schema.jpg       # Esquema para instrucciones
│   │   └── testing_schema.jpg  # Esquema de calibración
│   ├── Arial_Rounded_MT_Bold.ttf
│   ├── Rest.png                # Imagen de descanso
│   ├── 50_self.png             # Círculos de esfuerzo por condición
│   ├── 50_other.png
│   ├── 50_group.png
│   ├── 65_self.png
│   ├── 65_other.png
│   ├── 65_group.png
│   ├── 80_self.png
│   ├── 80_other.png
│   ├── 80_group.png
│   ├── 95_self.png
│   ├── 95_other.png
│   └── 95_group.png
└── data/                       # Carpeta donde se guardan los resultados (se crea automáticamente)
```

## Ejecución

### Ejecución directa con Python
```bash
python prosocial_effort_task.py
```

### Compilar a ejecutable (.exe)
```bash
pyinstaller --onefile --windowed --add-data "media;media" --add-data "data;data" --hidden-import=pylsl --hidden-import=pygame --collect-all pylsl --name "Prosocial_Effort_Task" prosocial_effort_task.py
```

**Nota para Mac**: Cambiar `;` por `:` en `--add-data`:
```bash
pyinstaller --onefile --windowed --add-data "media:media" --add-data "data:data" --hidden-import=pylsl --hidden-import=pygame --collect-all pylsl --name "Prosocial_Effort_Task" prosocial_effort_task.py
```

El ejecutable se generará en la carpeta `dist/`.

## Conexión con EEG (Lab Streaming Layer)

La tarea envía marcadores al sistema EEG mediante el protocolo LSL (Lab Streaming Layer).

### Configuración del stream LSL

- **Nombre del stream**: `ProsocialTaskMarkers`
- **Tipo**: `Markers`
- **Canales**: 1
- **Formato**: `int32`
- **Source ID**: `ProsocialTask`

### Marcadores LSL

| Código | Evento | Descripción |
|--------|--------|-------------|
| **Decisión** |||
| 100 | DECISION_START_SELF | Inicio decisión para TI |
| 101 | DECISION_START_OTHER | Inicio decisión para IN-GROUP |
| 102 | DECISION_START_GROUP | Inicio decisión para OUT-GROUP |
| 110 | RESPONSE_WORK | Respuesta: trabajar |
| 111 | RESPONSE_REST | Respuesta: descansar |
| 112 | RESPONSE_OMISSION | Sin respuesta (timeout) |
| **Esfuerzo** |||
| 120 | EFFORT_BAR_START | Inicio de la barra de esfuerzo |
| 121 | EFFORT_BAR_SUCCESS | Completó la barra exitosamente |
| 122 | EFFORT_BAR_FAIL | No completó la barra |
| **Feedback** |||
| 130 | FEEDBACK_SELF_START | Inicio feedback TI |
| 131 | FEEDBACK_OTHER_START | Inicio feedback IN-GROUP |
| 132 | FEEDBACK_GROUP_START | Inicio feedback OUT-GROUP |
| 140+ | FEEDBACK_CREDITS | Créditos ganados (140 + n créditos) |
| **Bloques** |||
| 200 | BLOCK_START | Inicio de bloque |
| 201 | BLOCK_END | Fin de bloque |
| 250 | EXPERIMENT_START | Inicio del experimento |
| 251 | EXPERIMENT_END | Fin del experimento |
| 252 | CALIBRATION_START | Inicio calibración |
| 253 | CALIBRATION_END | Fin calibración |
| 254 | PRACTICE_START | Inicio práctica |
| 255 | PRACTICE_END | Fin práctica |

### Recibir marcadores en el software de EEG

1. Inicia la tarea y espera a que aparezca el mensaje de conexión LSL
2. En tu software de EEG (ej: BrainVision Recorder, OpenBCI, LabRecorder), busca el stream `ProsocialTaskMarkers`
3. Conecta al stream
4. Presiona ENTER en la tarea para continuar

**Ejemplo con LabRecorder**:
```
1. Abrir LabRecorder
2. Click en "Update" para buscar streams
3. Seleccionar "ProsocialTaskMarkers"
4. Click en "Start" para comenzar la grabación
5. Presionar ENTER en la tarea
```

## Configuración personalizada

### Modificar nombres de condiciones

En el archivo principal, modifica estas variables:

```python
# Nombres que se muestran en pantalla al participante
DISPLAY_NAME_SELF = "TI"
DISPLAY_NAME_INGROUP = "Votará igual a ti"
DISPLAY_NAME_OUTGROUP = "Votará distinto a ti"
```

### Modificar parámetros del experimento

```python
# Niveles de esfuerzo (% de la capacidad máxima calibrada)
effort_levels = [50, 65, 80, 95]

# Niveles de créditos
credits_levels = [2, 3, 4, 5]

# Número de bloques
blocks_number = 3

# Tiempos (en segundos)
max_decision_time = 4    # Tiempo para decidir
max_answer_time = 5      # Tiempo para trabajar
max_resting_time = 5     # Tiempo de descanso
```

### Modo ventana (para debugging)

```python
FullScreenShow = False  # Cambiar a False para modo ventana
```

## Datos de salida

Los datos se guardan en `data/PET_[fecha]_[hora].csv` con las siguientes columnas:

| Columna | Descripción |
|---------|-------------|
| effort_level | Nivel de esfuerzo (50, 65, 80, 95) |
| credits | Créditos ofrecidos |
| condition | Self, Other, o Group |
| selection | task, resting, o no decision |
| presses | Número de presiones realizadas |
| target_reached | Si completó el objetivo |
| earned_credits | Créditos ganados |
| decision_rt | Tiempo de reacción (ms) |
| first_press_time | Tiempo de la primera presión |
| last_press_time | Tiempo de la última presión |

## Controles

| Tecla | Función |
|-------|---------|
| → (Flecha derecha) | Avanzar en instrucciones |
| N | Seleccionar opción izquierda |
| M | Seleccionar opción derecha |
| Espacio | Presionar durante fase de esfuerzo |
| ESC | Salir de la tarea |

## Solución de problemas

### La flecha derecha no funciona en las instrucciones

En algunos equipos Windows, la ventana de pygame puede no capturar correctamente el foco del teclado al inicio. Soluciones:
1. Presiona `Alt + Tab` para cambiar de ventana y vuelve a la tarea
2. Haz clic en la ventana de la tarea antes de presionar teclas


## Contacto

Correo electrónico: diegogarridocerpa@gmail.com
Correo institucional: digarrido@alumnos.uai.cl
