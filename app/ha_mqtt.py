import threading
import time

from paho.mqtt.client import Client, MQTTMessage
import os
import json

from pydantic.dataclasses import dataclass

from modem_command import ModemCommand
import logging

logger = logging.getLogger(__name__)

class DEVICE_CLASS_ENUM:
    MESSAGE = "message"
    CALL = "call"
    BALANCE = "balance"
    SIGNAL_LEVEL = "signal_level"
    MESSAGE_SENDER = "message_sender"

DEVICE_ID = "4c078a33-c9d7-492a-aa71-3834a0da33c5"

BASE_DEVICE = {
    "identifiers": DEVICE_ID,
    "name": "SmsGateway",
    "manufacturer": "DIY",
    "model": "MODEM"
}

COMMAND_SMS_TOPIC = f"smsgateway/{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/send"
COMMAND_SMS_TOPIC_ATTR = f"smsgateway/{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/attr"

def get_device_configuration(device_class: str, values: dict = None) -> dict:
    massage = {
            "device": BASE_DEVICE,
            "uniq_id" : device_class,
            "name": device_class,
            "stat_t": f"smsgateway/{device_class}",
            "unit_of_meas": None,
            "device_class": None,
            "state_class": None,
            "value_template" : "{{ value }}"
    }

    if values and len(values.keys()) > 0:
        massage.update(values)

    return  massage

class HaMQTT:

    client: Client = None

    def __init__(self):
        self.client = Client(client_id=DEVICE_ID)
        self._connect()

    def _connect(self):
        self.client.connect(
            host=os.getenv('MQTT_HOST', 'localhost'),
            port=int(os.getenv('MQTT_PORT', 1883))
        )

    def publish(self, topic: str, data: str):
        logger.info(f'Publish to {topic}: {data}')
        if not self.client.is_connected():
            self._connect()

        self.client.publish(topic=topic, payload=data, qos=0)

    def publish_discovery_messages(self):
        config_messages = get_device_configuration(DEVICE_CLASS_ENUM.MESSAGE, {
            "value_template" : "{{ value }}",
        })
        config_calls = get_device_configuration(DEVICE_CLASS_ENUM.CALL)

        notify_configuration = {
            "device": BASE_DEVICE,
            "platform": "mqtt",
            "schema": "json",
            "uniq_id" : DEVICE_CLASS_ENUM.MESSAGE_SENDER,
            "name": DEVICE_CLASS_ENUM.MESSAGE_SENDER,
            "command_topic": COMMAND_SMS_TOPIC,
            "availability":
                {
                    "topic": f"smsgateway/{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/available",
                    "payload_available": "online",
                    "payload_not_available": "offline",
                },
        }

        self.publish(f'homeassistant/sensor/{DEVICE_ID}_{DEVICE_CLASS_ENUM.MESSAGE}/config',
                  json.dumps(config_messages))

        self.publish(f'homeassistant/sensor/{DEVICE_ID}_{DEVICE_CLASS_ENUM.CALL}/config',
                  json.dumps(config_calls))

        self.publish(f'homeassistant/notify/{DEVICE_ID}_{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/config',
                  json.dumps(notify_configuration))

    def publish_available_sender(self):
        while True:
            self.publish(f"smsgateway/{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/available", "online")
            time.sleep(15)

def beat():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

def main():
    logging.basicConfig(
        level=logging.INFO,  # Уровень логгирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат логов
        datefmt='%Y-%m-%d %H:%M:%S',  # Формат даты и времени
        handlers=[
            # logging.FileHandler("app.log"),  # Запись логов в файл
            logging.StreamHandler()  # Вывод логов в консоль
        ],
    )
    modem = ModemCommand()

    def send_sms(client, userdata, msg: MQTTMessage):
        logger.info(f'Got msg from ha: {msg.payload}')
        message = json.loads(msg.payload)
        modem.send_sms(message.get('phone'), message.get('text'))

    service = HaMQTT()
    service.publish_discovery_messages()
    service.client.subscribe([(COMMAND_SMS_TOPIC, 0), (COMMAND_SMS_TOPIC_ATTR, 0)])
    service.client.on_message = send_sms
    service.client.loop_start()
    threading.Thread(target=HaMQTT.publish_available_sender, daemon=True, args=[service]).start()
    beat()

if __name__ == '__main__':
    main()
