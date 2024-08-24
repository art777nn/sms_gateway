from optparse import Option
from typing import Optional, Any

import pika
import json
import logging
import os

from app.ha_mqtt import HaMQTT, get_device_configuration, DEVICE_CLASS_ENUM
from repository import Message, SmsRepository, EnvRepository, Env, CallRepository, Call
import re
from datetime import datetime, timedelta
import traceback
from modem_command import ModemCommand


logger = logging.getLogger(__name__)


class Handler:

    result: Any = None

    def process(self, data) -> Optional[Any]:
        logger.info(data)

        return None

    def exec_integrations(self) -> None:
        logger.info(f'Integration for {self.__class__.__name__} not set')

    def decode_ucs2_string(self, encoded_string):
        """
        Декодирует строку, содержащую шестнадцатеричные символы, в текст UCS2.

        :param encoded_string: Закодированная строка в формате UCS2 в виде шестнадцатеричных символов.
        :return: Декодированная строка.
        """
        bytes_data = bytes.fromhex(encoded_string)

        # Декодируем по 16-битам (UCS2) в строку
        decoded_message = bytes_data.decode('utf-16-be')
        return decoded_message

    def decode_gsm7bit(self, encoded_message):
        """Декодирует 7-битное сообщение в формате GSM."""
        decoded_message = ""
        n = len(encoded_message)

        for i in range(n):
            byte = encoded_message[i]
            for bit in range(7):
                if byte & (1 << bit):
                    decoded_message += chr((383 + bit) if i * 7 + bit < n * 8 else 0)

        return decoded_message

    def drop_quotas(self, text):
        return text.replace('"', '')


class call_handler(Handler):

    call_repo: CallRepository = CallRepository()
    mqtt_service = HaMQTT()

    def process(self, data) -> Optional[Call]:
        logger.info(f"Got incoming call: {data}")

        caller = self.extract_phone_number(data)

        if not caller:
            logger.info(f"Undefined caller: {data}")
            caller = data

        # Если в течении 30 секунд продолжает звонить телефон, то не делаем записи
        dttm =  (datetime.now() - timedelta(seconds=30)).isoformat()

        if self.call_repo.get_by_caller_dttm(caller=caller,
                                             dttm=dttm,
                                             limit=1):
            logger.info(f"Already created: {data}")
            return

        self.result = self.call_repo.create(caller=self.extract_phone_number(data))

    def exec_integrations(self) -> None:

        configuration = get_device_configuration(DEVICE_CLASS_ENUM.CALL)
        self.mqtt_service.publish(
            topic=configuration.get('stat_t'),
            data=self.result.to_json()
        )

    def extract_phone_number(self, input_string):
        # Искать номер телефона в формате +79999999999
        match = re.search(r'\+(\d{1,3})(\d{10})', input_string)
        if match:
            # Формируем номер телефона с кодом
            country_code = match.group(1)  # Код страны
            phone_number = match.group(2)  # Номер
            return f"+{country_code}{phone_number}"
        return None


class ussd_handler(Handler):

    evn_repo: EnvRepository = EnvRepository()

    def process(self, data):
        logger.info(f'Got ussd response: {data}')

        parts = data.split(',')

        text: str = self.decode_ucs2_string(self.drop_quotas(parts[1]))

        if 'Баланс' in text:
            self.evn_repo.update('balance', data={"message": text})

    def get_balance_from_text(self, text):
        # text = 'Баланс: 104.48 pуб. 7 дней VIP-статуса для сервиса "Мамба" за 149 руб.: *702#'
        # Используем регулярное выражение для поиска числа
        match = re.search(r'\d+\.\d+', text)

        if match:
            # Выводим найденное число
            return match.group(0)
        else:
            raise Exception('Не могу вытащить баланс из строки')


class operator_handler(Handler):

    repo = EnvRepository()

    def process(self, data):

        logger.info(f'Got operator values: {self.drop_quotas(data)}')
        operator = data.split(',')

        self.repo.update('operator', {"value": self.drop_quotas(operator[2])})


class signal_handler(Handler):
    repo = EnvRepository()

    def process(self, data):
        # "+CSQ: 28,99"
        logger.info(f'Got signal values: {self.drop_quotas(data)}')

        signal_level, _ = self.extract_numbers(data)

        level = signal_level / (32 / 5)

        self.repo.update('signal', {"level": level})

    def extract_numbers(self, s):
        # Используем регулярное выражение для поиска чисел
        match = re.search(r'\+CSQ:\s*(\d+),(\d+)', s)
        if match:
            # Преобразуем найденные строки в числа и возвращаем их
            return int(match.group(1)), int(match.group(2))
        else:
            # Если ничего не найдено, возвращаем None
            return None


class signal_type_handler(Handler):
    repo = EnvRepository()

    def process(self, data):
        # "+CSQ: 28,99"
        logger.info(f'Got signal type values: {self.drop_quotas(data)}')

        type = self.extract_type(self.drop_quotas(data))

        self.repo.update('signal_type', {"type": type})

    def extract_type(self, s):
        return s.split(':')[1].split(',')[0]


class sms_handler(Handler):

    original_data = None
    prepared_data = None
    modem_service: ModemCommand = ModemCommand()
    mqtt_service = HaMQTT()

    def exec_integrations(self) -> None:
        configuration = get_device_configuration(DEVICE_CLASS_ENUM.MESSAGE)
        self.mqtt_service.publish(
            topic=configuration.get('stat_t'),
            data=self.result.to_json()
        )

    def process(self, data):
        self.original_data = data
        messages_list = self.prep_list(data)
        non_quotas_list = self.drop_quotas(messages_list)
        messages = self.get_messages(non_quotas_list)

        # Сохраняем сообщения в репо
        if messages:
            res = SmsRepository().create(messages=messages)
            self.result = res[0]

        for message in messages:
            self.modem_service.drop_message(message.message_id)

    def prep_list(self, data: list):
        res = []
        for i in range(len(data)):
            if str(data[i]).startswith("+CMGL"):
                res.append(data[i] + ',' + data[i + 1])

        return res

    def drop_quotas(self, data):
        res = []
        for i in range(len(data)):
            res.append(data[i].replace('"', ""))

        return res

    def get_messages(self, data):
        res = []
        for message in data:
            parted = message.split(',')

            message_id = self.get_message_id(parted[0])
            sender = parted[2]
            receive_dt_text = parted[4]
            receive_tm_text = parted[5]

            receive_dttm = datetime.strptime(
                receive_dt_text + ' ' + receive_tm_text[:8], "%y/%m/%d %H:%M:%S"
            )

            text = parted[6].strip()

            try:
                text = self.decode_ucs2_string(text)
            except Exception:
                traceback.print_exc()
                logger.warning(f'Cant decode message: {text}')

            res.append(
                Message(
                    message_id=message_id,
                    message_receive_dttm=receive_dttm,
                    sender=sender,
                    text=text,
                )
            )

        return res

    def get_message_id(self, text):
        match = re.search(r'\d+', text)

        if match:
            return match.group(0)
        else:
            raise Exception('Не могу получить id сообщения')


class ModemHandler:

    queue = 'response'
    rmq_host = os.getenv('RMQ_HOST', 'locahost')

    def __init__(self) -> None:
        logger.info(f"Connect to RMQ: {self.rmq_host}")
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.rmq_host)
        )
        self.channel = connection.channel()
        # Убедитесь, что очередь существует
        self.channel.queue_declare(queue=self.queue)

    def consume(self):
        self.channel.basic_consume(
            queue=self.queue, on_message_callback=self.callback, auto_ack=True
        )
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        obj_body = json.loads(body)
        handler = obj_body.get('handler', None)

        if not handler:
            logger.error(f"Body not contains handler: {body}")

        cls = globals().get(handler)

        if cls:
            instance = cls()
            instance.process(obj_body.get('data'))  # Создаем и возвращаем экземпляр

            if instance.result:
                instance.exec_integrations()
        else:
            logger.warning(f"Handler for '{handler}' not found")
            Handler().process(data=obj_body.get('data'))


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

    ModemHandler().consume()
