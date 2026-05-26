import json
import os
import ssl
import time
import logging
import threading
import requests
import paho.mqtt.client as mqtt

PRINTER_IP      = os.environ["PRINTER_IP"]
SERIAL_NUMBER   = os.environ["SERIAL_NUMBER"]
ACCESS_CODE     = os.environ["ACCESS_CODE"]
PHONE_IP        = os.environ["PHONE_IP"]
MACRODROID_PORT = int(os.getenv("MACRODROID_PORT", "8080"))
MACRODROID_PATH = os.getenv("MACRODROID_PATH", "/timelapse")
LAYER_DELAY_SEC = float(os.getenv("LAYER_DELAY_SEC", "1.5"))

MQTT_PORT   = 8883
MQTT_USER   = "bblp"
TOPIC       = f"device/{SERIAL_NUMBER}/report"
TRIGGER_URL = f"http://{PHONE_IP}:{MACRODROID_PORT}{MACRODROID_PATH}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

current_layer = -1


def shoot(layer: int, total):
    time.sleep(LAYER_DELAY_SEC)
    try:
        r = requests.post(TRIGGER_URL, timeout=5)
        log.info(f"Foto disparada — capa {layer}/{total}  (HTTP {r.status_code})")
    except requests.RequestException as e:
        log.warning(f"No se pudo disparar foto — capa {layer}/{total}: {e}")


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        log.info("Conectado al MQTT de la Bambu Lab")
        client.subscribe(TOPIC)
    else:
        log.error(f"Error de conexión MQTT — código {rc}")


def on_message(client, userdata, msg):
    global current_layer
    try:
        payload = json.loads(msg.payload)
        print_data = payload.get("print", {})
        layer = print_data.get("layer_num")

        if layer is None or layer == current_layer:
            return

        current_layer = layer
        total = print_data.get("total_layer_num", "?")
        log.info(f"Nueva capa: {layer}/{total}")
        threading.Thread(target=shoot, args=(layer, total), daemon=True).start()

    except (json.JSONDecodeError, KeyError):
        pass


def main():
    log.info(f"Printer: {PRINTER_IP} | Serial: {SERIAL_NUMBER}")
    log.info(f"Trigger URL: {TRIGGER_URL}")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, ACCESS_CODE)

    tls_ctx = ssl.create_default_context()
    tls_ctx.check_hostname = False
    tls_ctx.verify_mode = ssl.CERT_NONE
    client.tls_set_context(tls_ctx)

    client.on_connect = on_connect
    client.on_message = on_message

    log.info(f"Conectando a {PRINTER_IP}:{MQTT_PORT} ...")
    client.connect(PRINTER_IP, MQTT_PORT, keepalive=60)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        log.info("Detenido.")
        client.disconnect()


if __name__ == "__main__":
    main()
