import pika

class RabbitMQConnection:
    _instance = None

    def __new__(cls, dsn):
        if cls._instance is None:
            cls._instance = super(RabbitMQConnection, cls).__new__(cls)
            cls._instance.connection = pika.BlockingConnection(pika.URLParameters(dsn))
            cls._instance.channel = cls._instance.connection.channel()
        return cls._instance

    def get_channel(self):
        return self.channel

    def close(self):
        if self.connection:
            self.connection.close()
            print("[x] Connection closed")