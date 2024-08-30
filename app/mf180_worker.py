from typing import List

import serial
import time
import pika
import json
import os
import logging
from at_commands import commands


logger = logging.getLogger(__name__)


PERIODICAL_TASKS = {
    commands.ussd("*105#"): 3600,
    commands.get_all_sms(): 20,
    commands.get_operator(): 60,
    commands.get_signal_level(): 60,
    commands.get_signal_type(): 60
}

class mf180:
    port = os.getenv('MODEM_PORT', '/dev/ttyUSB3')  # Замените на ваш порт
    baud_rate = 115200  # Скорость передачи данных
    data_bits = 8  # Количество бит данных
    parity = serial.PARITY_NONE  # Бит четности (N - No parity)
    stop_bits = serial.STOPBITS_ONE  # Количество стоп-битов
    ser = None
    channel = None
    rmq_host = os.getenv('RMQ_HOST', 'locahost')
    command_queue = 'commands'
    response_queue = 'response'


    def rmq_connection(self):
        logger.info(f"Connect to RMQ: {self.rmq_host}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rmq_host)
        )
        self.channel = connection.channel()
        self.channel.queue_declare(queue=self.command_queue)
        self.channel.queue_declare(queue=self.response_queue)

    def get_message(self) -> dict | List | None:
        method_frame, header_frame, body = self.channel.basic_get(
            queue=self.command_queue, auto_ack=True
        )
        if method_frame:
            logger.info(f'Got external command: {body}')
            return json.loads(body)
        else:
            return None

    def open_serial(self):

        logger.info(f"Open serial port: {self.port}")

        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baud_rate,
            bytesize=self.data_bits,
            parity=self.parity,
            stopbits=self.stop_bits,
            xonxoff=True,
            timeout=10,
        )

        time.sleep(1)

    def publish_result(self, handler, result):
        body = json.dumps(
            {
                "handler": handler,
                "data": result,
            }
        )
        logger.info(f"Publish message: {body}")
        self.channel.basic_publish(
            exchange='', routing_key=self.response_queue, body=body
        )

    def close_serial(self):
        if 'ser' in locals() and self.ser.is_open:
            self.ser.close()

    def ussd_handler(self, row):
        self.publish_result(self.ussd_handler.__name__, row)

    def sms_handler(self, row):
        result = [row]

        while True:
            row = self.ser.read_until().decode('utf-8').strip()
            if row == "OK" or row == "ERROR":
                break
            result.append(row)

        self.publish_result(self.sms_handler.__name__, result)

    def operator_handler(self, row):
        self.publish_result(self.operator_handler.__name__, row)

    def signal_handler(self, row):
        self.publish_result(self.signal_handler.__name__, row)

    def call_handler(self, row):
        self.publish_result(self.call_handler.__name__, row)

    def input_sms_handler(self, row):
        self.publish_result(self.input_sms_handler.__name__, row)

    def signal_type_handler(self, row):
        self.publish_result(self.signal_type_handler.__name__, row)

    allow_handle = {
        "+CUSD": ussd_handler,
        "+CMGL": sms_handler,
        "+CMGR": sms_handler,
        "+COPS": operator_handler,
        "+CSQ": signal_handler,
        "+CLIP": call_handler,
        "+CMTI": input_sms_handler,
        "+ZPAS": signal_type_handler,
    }

    def write(self, command):
        logger.info(f'Send to port command: {command}')
        self.ser.write((command + '\r').encode())
        time.sleep(1)

    def loop(self):
        timers = {}
        while True:
            try:
                # Input command from RMQ
                message = self.get_message()
                if message:
                    if isinstance(message, dict):
                        self.write(message['command'])
                    if isinstance(message, list):
                        for cmd in message:
                            self.write(cmd['command'])

                # Periodical tasks
                for task in PERIODICAL_TASKS:
                    if task not in timers:
                        timers[task] = time.perf_counter()

                    if time.perf_counter() - timers[task] >= PERIODICAL_TASKS[task]:
                        self.write(task)
                        timers[task] = time.perf_counter()


                if self.ser.in_waiting > 0:
                    row = self.ser.read_until().decode('utf-8').strip()
                    logger.info(f"Response: {row}")
                    command = self.get_command(row)
                    if command in self.allow_handle:
                        logger.info(
                            f"Call handler: {self.allow_handle[command].__name__}"
                        )
                        self.allow_handle[command](self, row)

            except Exception as e:
                self.close_serial()
                exit(127)

    def get_command(self, row):
        splitted = row.split(":")

        if not splitted:
            return ''
        return splitted[0]


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

    modem = mf180()
    modem.open_serial()
    modem.rmq_connection()
    modem.write(commands.gsm_mode())
    modem.write(commands.txt_mode())
    modem.loop()
