import json
import logging
import os
import threading
import time
from dataclasses import dataclass, asdict

from paho.mqtt.client import Client, MQTTMessage

from modem_command import ModemCommand

logger = logging.getLogger(__name__)

@dataclass
class DiscoveryMessage:
    device: dict
    uniq_id: str
    name: str
    stat_t: str
    unit_of_meas: str = None
    device_class: str = None
    state_class: str = None
    value_template: str = "{{ value }}"

    def __init__(self, base_device, device_class, additional: dict = None):
        self.device = base_device
        self.uniq_id = device_class
        self.name = device_class
        self.stat_t = f"smsgateway/{device_class}"

        if additional:
            for key, value in additional.items():
                self.__dict__[key] = value


    def to_json(self):
        return json.dumps(asdict(self))


DEVICE_ID = "4c078a33-c9d7-492a-aa71-3834a0da33c5"

BASE_DEVICE = {
    "identifiers": DEVICE_ID,
    "name": "SmsGateway",
    "manufacturer": "DIY",
    "model": "MODEM"
}

MESSAGE_SENSOR = "message"
CALL_SENSOR = "call"
MESSAGE_SENDER_DEVICE = "message_sender"

DISCOVERY_MESSAGE_TOPIC = f'homeassistant/sensor/{DEVICE_ID}_{MESSAGE_SENSOR}/config'
DISCOVERY_CALL_TOPIC = f'homeassistant/sensor/{DEVICE_ID}_{CALL_SENSOR}/config'
DISCOVERY_MESSAGE_SENDER_TOPIC = f'homeassistant/notify/{DEVICE_ID}_{MESSAGE_SENDER_DEVICE}/config'

COMMAND_SMS_TOPIC = f"smsgateway/{MESSAGE_SENDER_DEVICE}/send"
AVAILABLE_SMS_TOPIC = f"smsgateway/{MESSAGE_SENDER_DEVICE}/available"

devices = {
    DISCOVERY_MESSAGE_TOPIC: DiscoveryMessage(BASE_DEVICE, MESSAGE_SENSOR).to_json(),
    DISCOVERY_CALL_TOPIC: DiscoveryMessage(BASE_DEVICE, CALL_SENSOR).to_json(),
    DISCOVERY_MESSAGE_SENDER_TOPIC: DiscoveryMessage(BASE_DEVICE, MESSAGE_SENDER_DEVICE, {
        "command_topic": COMMAND_SMS_TOPIC,
        "availability":
            {
                "topic": AVAILABLE_SMS_TOPIC,
                "payload_available": "online",
                "payload_not_available": "offline",
            },
    }).to_json()
}


class HaMQTT:
    client: Client = None

    def __init__(self):
        self.client = Client(client_id=DEVICE_ID)
        self._connect()

    def _connect(self):
        self.client.connect(
            host=os.getenv('MQTT_HOST'),
            port=int(os.getenv('MQTT_PORT'))
        )

    def publish(self, topic: str, data: str):
        logger.info(f'Publish to {topic}: {data}')
        if not self.client.is_connected():
            self._connect()

        self.client.publish(topic=topic, payload=data, qos=0)

    def publish_discovery_messages(self):

        for topic, data in devices.items():
            self.publish(topic, data)

    def publish_available_sender(self, frequency=15):
        while True:
            self.publish(AVAILABLE_SMS_TOPIC, "online")
            time.sleep(frequency)


def beat():
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")


def main():
    modem = ModemCommand()

    def send_sms(client, userdata, msg: MQTTMessage):
        logger.info(f'Got msg from ha: {msg.payload}')
        message = json.loads(msg.payload)
        modem.send_sms(message.get('phone'), message.get('text'))

    service = HaMQTT()
    service.publish_discovery_messages()
    service.client.subscribe(COMMAND_SMS_TOPIC)
    service.client.on_message = send_sms
    service.client.loop_start()
    threading.Thread(target=HaMQTT.publish_available_sender, daemon=True, args=[service]).start()
    beat()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,  # Уровень логгирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат логов
        datefmt='%Y-%m-%d %H:%M:%S',  # Формат даты и времени
        handlers=[
            # logging.FileHandler("app.log"),  # Запись логов в файл
            logging.StreamHandler()  # Вывод логов в консоль
        ],
    )

    main()
