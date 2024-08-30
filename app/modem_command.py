import json
import logging
import os
from typing import List

import pika

from at_commands import commands

logger = logging.getLogger(__name__)


class ModemCommand:

    queue = 'commands'
    rmq_host = os.getenv('RMQ_HOST', 'localhost')

    def __init__(self) -> None:
        logger.info(f"Connect to RMQ: {self.rmq_host}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rmq_host)
        )
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.queue)

    def publish(self, command, priority: int=5):
        body = json.dumps({"command": command})
        logger.info(f"Publish command: {body}")
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=body, properties=pika.BasicProperties(priority=priority))

    def publish_many(self, cmds: List[str], priority: int=5):
        stmt = []
        for cmd in cmds:
            stmt.append({"command": cmd})

        logger.info(f"Publish command: {stmt}")
        self.channel.basic_publish(exchange='', routing_key=self.queue, body=json.dumps(stmt), properties=pika.BasicProperties(priority=priority))

    def drop_message(self, id):
        self.publish(command=commands.drop_sms_by_id(id), priority=10)

    def make_ussd(self, number):
        self.publish(command=commands.ussd(number))

    def get_sms(self):
        self.publish(command=commands.get_all_sms())

    def get_operator(self):
        self.publish(command=commands.get_operator())

    def get_signal_level(self):
        self.publish(command=commands.get_signal_level())

    def get_signal_type(self):
        self.publish(command=commands.get_signal_type())

    def send_sms(self, phone, text):
        self.publish_many([
            commands.send_sms(phone),
            f"{text}\x1A"
        ])
