# Alunos: Caio Bertoldo, Diogo Gomes, Rodolfo Simões

import time
import random
import paho.mqtt.client as mqtt
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

console = Console()

# Mock do DHT22
class MockDHT:
    def read(self):
        temperature = round(random.uniform(20, 35), 2)
        humidity = round(random.uniform(40, 70), 2)
        return temperature, humidity

# Mock do LCD
# class MockLCD:
#     def clear(self):
#         print("[LCD] LIMPO")
    
#     def setCursor(self, x, y):
#         print(f'[LCD] Cursor em {x}, {y}')
    
#     def print(self, message):
#         print(f'[LCD] {message}')

# Mock do Servo
class MockServo:
    def write(self, angle):
        global servoAngle
        servoAngle = angle

# Mock dos sensores e atuadores
def readPhotoresistor():
    return random.randint(0, 1023)

def readMotionSensor():
    return random.choice([0, 1])

def setLed(state):
    global ledState
    ledState = state

# Estado inicial 
servoAngle = 0
ledState = False
photo = 0
motion = 0
temp = 0
humidity = 0
lastMessage = ""

# Inicializando mocks
dhtSensor = MockDHT()
# lcd = MockLCD()
servo = MockServo()

# MQTT Setup
broker = 'test.mosquitto.org'
client = mqtt.Client(client_id="PythonMockClient", protocol=mqtt.MQTTv311)

# Tópicos
topicPup = "test/bertoldo/sensors"
topicPhoto = "test/bertoldo/photo"
topicTemp = "test/bertoldo/temp"
topicMotion = "test/bertoldo/motion"
topicLight = "test/bertoldo/light"
topicAir = "test/bertoldo/air"

# Callback do MQTT
def onConnect(client, userdata, flags, rc):
    # print(f'[MQTT] Conectado com código: {rc}')
    client.subscribe(topicLight)
    client.subscribe(topicAir)

def onMessage(client, userdata, msg):
    # print(f'[MQTT] Mensagem recebida em {msg.topic}: {msg.payload.decode()}')
    global lastMessage
    command = msg.payload.decode()
    lastMessage = f'{msg.topic}: {command}'

    if command == 'ligar luz':
        setLed(True)
    elif command == 'desligar luz':
        setLed(False)
    elif command == 'ligar ar':
        servo.write(90)
    elif command == 'desligar ar':
        servo.write(0)

client.on_connect = onConnect
client.on_message = onMessage

# print('[MQTT] Conectando...')
client.connect(broker, 1883, 60)
client.loop_start()

# Interface Rich
def renderInterface():
    table = Table(title="🚀 Painel de Simulação dos Crias", style="bold blue")

    table.add_column("Sensor", justify="center")
    table.add_column("Valor", justify="center")

    tempColor = "red" if temp > 27 else "green"
    photoColor = "yellow" if photo < 300 else "green"
    motionText = "[bold red]Detectado!" if motion else "Ausente"

    table.add_row("Temperatura", f"[{tempColor}]{temp:.1f}ºC[/{tempColor}]")
    table.add_row("Luminosidade", f"[{photoColor}]{photo}[/{photoColor}]")
    table.add_row("Movimento", motionText)
    table.add_row("LED", "🟢 Ligado" if ledState else "⚫ Desligado")
    table.add_row("Ar-condicionado", f"{servoAngle}º")
    table.add_row("MQTT Último", lastMessage or "Esperando mensagem...")

    return Panel(table, title="Sistema de Sala Inteligente Simulado", border_style="bold magenta", expand=False)


# Loop principal (simulação)
try:
    with Live(renderInterface(), refresh_per_second=2) as live:
        while True:
            # Atualiza os sensores
            photo = readPhotoresistor()
            motion = readMotionSensor()
            temp, humidity = dhtSensor.read()

            # Publica os tópicos
            msg = f"Valores: Photo = {photo}, Motion = {motion}, Temp = {temp:.1f}ºC"
            client.publish(topicPup, msg)
            client.publish(topicPhoto, str(photo))
            client.publish(topicTemp, str(temp))
            client.publish(topicMotion, str(motion))

            # Lógica do sistema
            if motion or photo < 300:
                setLed(True)
            else:
                setLed(False)
            
            if temp > 27:
                servo.write(90)
            else: 
                servo.write(0)
            
            # Atualiza o painel
            live.update(renderInterface())
            time.sleep(2)

except KeyboardInterrupt:
    console.print("\n[bold red]Encerrando simulação...[/bold red]")
    client.loop_stop()
    client.disconnect()
