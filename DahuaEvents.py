import appdaemon.plugins.hass.hassapi as hass
import requests
from requests.auth import HTTPDigestAuth
from datetime import datetime
import threading
import time

class DahuaEvents(hass.Hass):
    def initialize(self):
        # Crea un evento para controlar la terminación de hilos
        self.stop_event = threading.Event()
        
        # Inicia un hilo para cada cámara en la configuración
        for camera in self.args["cameras"]:
            threading.Thread(target=self.listen_to_camera_events, args=(camera,), daemon=True).start()

    def listen_to_camera_events(self, camera):
        events = ",".join(camera['events'])
        url = f'http://{camera["host"]}:{camera["port"]}/cgi-bin/eventManager.cgi?action=attach&codes=[{events}]'
        self.log(f"Conectando a {camera['name']} en URL: {url}")

        while not self.stop_event.is_set():
            try:
                with requests.get(url, auth=HTTPDigestAuth(camera['user'], camera['pass']), stream=True, timeout=86400) as response:
                    if response.status_code == 200:
                        self.log(f"Conectado. Escuchando eventos IVS en {camera['host']}:{camera['port']} ({camera['name']})")

                        for line in response.iter_lines(chunk_size=512):
                            if line:
                                decoded_line = line.decode('utf-8')
                                self.log(f"Recibido: {decoded_line}")

                                rule_name = self.extract_rule_name(decoded_line)
                                self.process_event(decoded_line, camera, rule_name)

                    else:
                        self.log(f"Error en el canal {camera['host']}:{camera['port']} ({camera['name']}): Codigo de estado HTTP {response.status_code}")
                        self.log(f"Respuesta: {response.text}")
                        time.sleep(10)  # Espera antes de intentar reconectar

            except requests.exceptions.Timeout:
                self.log(f"Timeout al conectar con {camera['host']}:{camera['port']} ({camera['name']}). Reintentando...")
                time.sleep(5)  # Espera antes de reintentar
            except requests.exceptions.RequestException as e:
                self.log(f"Error de conexion en el canal {camera['host']}:{camera['port']} ({camera['name']}): {e}")
                time.sleep(10)  # Espera antes de reintentar

    def process_event(self, decoded_line, camera, rule_name):
        """
        Procesa el evento recibido, activando el sensor correspondiente.
        """
        if "Code=CrossLineDetection" in decoded_line:
            self.handle_detection_event("CrossLineDetection", camera, rule_name)

        elif "Code=CrossRegionDetection" in decoded_line:
            self.handle_detection_event("CrossRegionDetection", camera, rule_name)

def handle_detection_event(self, event_code, camera, rule_name):
    """
    Maneja la lógica de activación y desactivación de los sensores para un evento dado.
    """
    current_time = datetime.now().strftime("%H:%M:%S")
    self.log(f"Evento IVS detectado - {event_code} - Hora: {current_time} - Cámara: {camera['name']} - Regla: {rule_name}")

    # Mapear event_code a los nombres de sensores en Home Assistant
    if event_code == "CrossLineDetection":
        event_type = "linea"
    elif event_code == "CrossRegionDetection":
        event_type = "region"
    else:
        self.log(f"Evento no reconocido: {event_code}")
        return

    # Crear el nombre del sensor basado en el nombre de la cámara y el tipo de evento
    sensor_name = f"binary_sensor.cruce_{event_type}_termal{camera['name'].lower()}"

    # Activa el sensor
    self.set_state(sensor_name, state="on")
    self.log(f"El sensor activado es: {sensor_name}")

    # Reinicia el temporizador para apagar el sensor después de 10 segundos
    self.run_in(self.turn_off_sensor, 10, sensor=sensor_name)


    def turn_off_sensor(self, kwargs):
        """
        Función para apagar un sensor después de 10 segundos.
        """
        sensor = kwargs["sensor"]
        if self.get_state(sensor) == "on":
            self.set_state(sensor, state="off")
            self.log(f"{sensor} apagado automaticamente despues de 10 segundos.")

    def extract_rule_name(self, decoded_line):
        """
        Extrae el nombre de la regla de la línea decodificada.
        """
        rule_marker = "Name"
        start = decoded_line.find(rule_marker)
        if start != -1:
            end = decoded_line.find(";", start)
            if end == -1:
                end = len(decoded_line)
            rule_name = decoded_line[start+len(rule_marker):end]
            return rule_name.strip()
        return "Desconocida"

    def terminate(self):
        """
        Detiene todos los hilos de escucha.
        """
        self.stop_event.set()
