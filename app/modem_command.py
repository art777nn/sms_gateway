import pika
import json
import logging
import os
from repository import Message, SmsRepositry
import re
from datetime import datetime
import traceback
from mf180_worker import mf180_commands

logger = logging.getLogger(__name__)


class ModemCommand:

    queue = 'commands'
    rmq_host = os.getenv('RMQ_HOST', 'locahost')

    def __init__(self) -> None:
        logger.info(f"Connect to RMQ: {self.rmq_host}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rmq_host)
        )
        self.channel = connection.channel()
        # Убедитесь, что очередь существует
        self.channel.queue_declare(queue=self.queue)

    def publish(self, command):
        body = json.dumps({"command": command})
        logger.info(f"Publish command: {body}")
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=body)

    def drop_message(self, id):
        self.publish(command=mf180_commands.drop_sms_by_id(id))

    def make_ussd(self, number):
        self.publish(command=mf180_commands.ussd(number))

    def get_sms(self):
        self.publish(command=mf180_commands.get_all_sms())

    def get_operator(self):
        self.publish(command=mf180_commands.get_operator())

    def get_signal_level(self):
        self.publish(command=mf180_commands.get_signal_level())

    def get_signal_type(self):
        self.publish(command=mf180_commands.get_signal_type())
