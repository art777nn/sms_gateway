from dataclasses import dataclass
from datetime import datetime
import psycopg2
import os
import json


@dataclass
class Message:
    id: int
    message_id: str
    message_receive_dttm: datetime
    sender: str
    text: str

    def __init__(self, *args, **kwargs) -> None:
        self.id = kwargs.get('id', None)
        self.message_id = kwargs.get('message_id', None)
        self.message_receive_dttm = kwargs.get('message_receive_dttm', None)
        self.sender = kwargs.get('sender', None)
        self.text = kwargs.get('text', None)


@dataclass
class Env:
    key: str
    data: any
    updated_at: str

    def __init__(self, *args, **kwargs) -> None:
        self.key = kwargs.get('key', None)
        self.data = kwargs.get('data', None)
        self.updated_at = kwargs.get('updated_at', None)


@dataclass
class Call:
    caller: str
    created_at: datetime

    def __init__(self, *args, **kwargs) -> None:
        self.caller = kwargs.get('caller', None)
        self.created_at = kwargs.get('created_at', None)


class DefaultConnection:

    con = None

    cur = None

    def __init__(self) -> None:
        self.con = psycopg2.connect(
            database=os.getenv("DB_NAME", "db"),
            user=os.getenv("DB_USER", "user"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
        )

        self.con.autocommit = True
        self.cur = self.con.cursor()


class Entity:
    def init_entity(self):
        pass

    def __init__(self) -> None:
        self.init_entity()


class SmsRepositry(DefaultConnection, Entity):

    def init_entity(self):
        statement = '''
        CREATE TABLE IF NOT EXISTS SMS(
            id SERIAL,
            message_id int NOT NULL,
            message_receive_dttm timestamp NOT NULL,
            sender varchar(20),
            text varchar(400),
            is_dropped boolean default false,
            created_at timestamp NOT NULL default now()
        )
        '''

        self.cur.execute(statement)

    def get_by_sender_and_dttm(self, sender: str, dttm: str, limit=10):
        statement = f'''
            SELECT id, message_id, message_receive_dttm, sender, text FROM SMS where 1 = 1
        '''

        if sender and len(sender) > 0:
            statement = statement + f" and  sender like '%{sender}%'"

        if dttm and len(dttm) > 0:
            statement = statement + f" and created_at > '{dttm}'"

        statement = statement + " order by message_receive_dttm desc"

        statement = statement + f" limit {limit}"
        print(statement)
        self.cur.execute(statement)

        result = []
        for row in self.cur.fetchall():
            result.append(
                Message(
                    id=row[0],
                    message_id=row[1],
                    message_receive_dttm=row[2],
                    sender=row[3],
                    text=row[4],
                )
            )

        return result

    def create(self, messages):

        statement = '''
            INSERT INTO SMS(message_id, message_receive_dttm, sender, text) VALUES {values} RETURNING id, message_id, message_receive_dttm, sender, text
        '''
        values = []
        for message in messages:
            values.append(
                f"('{message.message_id}','{message.message_receive_dttm}','{message.sender}','{message.text}')"
            )

        prepared_values = ','.join(values)

        prepared_statement = statement.format(values=prepared_values)

        self.cur.execute(prepared_statement)

        result = []

        for row in self.cur.fetchall():
            result.append(
                Message(
                    id=row[0],
                    message_id=row[1],
                    message_receive_dttm=row[2],
                    sender=row[3],
                    text=row[4],
                )
            )

        return result

    def get_ids_not_dropped(self):

        statement = '''
        SELECT id from SMS where is_dropped = false
        '''

    def set_is_dropped(self, id):

        statement = '''
        UPDATE SMS SET is_dropped=trye where id = {id}
        '''


    def __init__(self) -> None:
        super().__init__()

        self.init_entity()

class BalanceRepository(DefaultConnection, Entity):

    def init_entity(self):
        statement = '''
        CREATE TABLE IF NOT EXISTS Balance(
            created_at timestamp NOT NULL default now(),
            balance numeric(16,4)
        )
        '''

        self.cur.execute(statement)

    def create(self, balance):
        self.cur.execute(f'INSERT INTO Balance(balance) VALUES ({balance})')

    def get_last_balance(self):
        self.cur.execute(
            'SELECT created_at, balance FROM Balance order by created_at desc limit 1'
        )

        res = self.cur.fetchone()

        return res[0], res[1]

    def __init__(self) -> None:
        super().__init__()

        self.init_entity()


class EnvRepository(DefaultConnection, Entity):
    def init_entity(self):
        statement = '''
        CREATE TABLE IF NOT EXISTS Env(
            key varchar(64) UNIQUE,
            value JSONB,
            updated_at timestamp
        )
        '''

        self.cur.execute(statement)

    def update(self, key, data):
        statement = f'''
        INSERT INTO Env(key, value, updated_at) VALUES ('{key}', '{json.dumps(data)}', now()) 
        ON CONFLICT (key) 
        DO UPDATE set value='{json.dumps(data)}', updated_at=now()
        '''

        self.cur.execute(statement)

    def get_by_key(self, key):
        statement = f'''
        SELECT key, value, updated_at from Env WHERE key='{key}';
        '''
        self.cur.execute(statement)

        res = self.cur.fetchone()

        if res:
            return Env(
                key=res[0],
                data=res[1],
                updated_at=res[2],
            )
        else:
            return None

    def __init__(self) -> None:
        super().__init__()

        self.init_entity()


class CallRepository(DefaultConnection, Entity):
    def init_entity(self):
        statement = '''
        CREATE TABLE IF NOT EXISTS Calls(
            caller varchar(64),
            created_at timestamp default now()
        )
        '''

        self.cur.execute(statement)

    def create(self, caller):
        statement = f'''
        INSERT INTO Calls(caller) VALUES ('{caller}')
        '''

        self.cur.execute(statement)

    def get_by_dttm(self, dttm: str, limit=10):
        statement = f'''
            SELECT caller, created_at FROM Calls where 1 = 1
        '''

        if dttm and len(dttm) > 0:
            statement = statement + f" and created_at > '{dttm}'"

        statement = statement + " order by created_at desc"

        statement = statement + f" limit {limit}"
        print(statement)
        self.cur.execute(statement)

        result = []
        for row in self.cur.fetchall():
            result.append(Call(caller=row[0], created_at=row[1]))

        return result

    def __init__(self) -> None:
        super().__init__()

        self.init_entity()
