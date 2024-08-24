from paho.mqtt.client import Client
import os
import json

from typing_extensions import override


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
        self.client = Client()
        self._connect()

    def _connect(self):
        self.client.connect(
            host=os.getenv('MQTT_HOST', 'localhost'),
            port=os.getenv('MQTT_PORT', 1883),
        )

    def publish(self, topic: str, data: str):
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
            "uniq_id" : DEVICE_CLASS_ENUM.MESSAGE_SENDER,
            "name": DEVICE_CLASS_ENUM.MESSAGE_SENDER,
            "command_topic": COMMAND_SMS_TOPIC,
        }

        self.publish(f'homeassistant/sensor/{DEVICE_ID}_{DEVICE_CLASS_ENUM.MESSAGE}/config',
                  json.dumps(config_messages))

        self.publish(f'homeassistant/sensor/{DEVICE_ID}_{DEVICE_CLASS_ENUM.CALL}/config',
                  json.dumps(config_calls))

        self.publish(f'homeassistant/notify/{DEVICE_ID}_{DEVICE_CLASS_ENUM.MESSAGE_SENDER}/config',
                  json.dumps(notify_configuration))



    # print(config_messages)
    # print(config_calls)
    #
    # time.sleep(2)
    #
    # c.publish(config_calls.get('stat_t'),CallRepository().get_by_caller_dttm(caller='', dttm='2024-08-20', limit=1)[0].to_json())
    # c.publish(config_messages.get('stat_t'),SmsRepository().get_by_sender_and_dttm(sender='', dttm='2024-08-20', limit=1)[0].to_json())
def send_sms(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

if __name__ == '__main__':
    service = HaMQTT()
    service.publish_discovery_messages()
    service.client.subscribe(COMMAND_SMS_TOPIC)
    service.client.on_message = send_sms