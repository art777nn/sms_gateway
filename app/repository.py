from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import psycopg2
import os
import json


@dataclass
class Message:
    id: int = None
    message_id: str = None
    message_receive_dttm: datetime = None
    sender: str = None
    text: str = None

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "message_id": self.message_id,
            "message_receive_dttm": self.message_receive_dttm.isoformat(),
            "sender": self.sender,
            "text": self.text
        })


@dataclass
class Env:
    key: str = None
    data: any = None
    updated_at: str = None

    def to_json(self) -> str:
        return json.dumps({
            "key": self.key,
            "data": self.any,
            "updated_at": self.updated_at,
        })

@dataclass
class Call:
    caller: str = None
    created_at: datetime = None

    def to_json(self) -> str:
        return json.dumps({
            "caller": self.caller,
            "created_at": self.created_at.isoformat(),
        })


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
        psycopg2.connect(os.getenv("POSTGRES_DSN"))

        self.con.autocommit = True
        self.cur = self.con.cursor()


class Entity:
    def init_entity(self):
        pass

    def __init__(self) -> None:
        self.init_entity()


class SmsRepository(DefaultConnection, Entity):

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

    def get_by_sender_and_dttm(self, sender: str, dttm: str, limit=10) -> List[Message]:
        statement = f'''
            SELECT id, message_id, message_receive_dttm, sender, text FROM SMS where 1 = 1
        '''

        if sender and len(sender) > 0:
            statement = statement + f" and  sender like '%{sender}%'"

        if dttm and len(dttm) > 0:
            statement = statement + f" and created_at > '{dttm}'"

        statement = statement + " order by message_receive_dttm desc"

        statement = statement + f" limit {limit}"
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

    def create(self, messages) -> List[Message]:

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

    def create(self, caller) -> Optional[Call]:
        statement = f'''
        INSERT INTO Calls(caller) VALUES ('{caller}') RETURNING caller, created_at;
        '''
        self.cur.execute(statement)
        res = self.cur.fetchone()

        if res:
            return Call(caller=res[0], created_at=res[1])

        return None

    def get_by_caller_dttm(self,caller:str, dttm: str, limit=10) -> List[Call]:
        statement = f'''
            SELECT caller, created_at FROM Calls where 1 = 1
        '''
        if caller and len(caller) > 0:
            statement = statement + f" and caller like '%{caller}%'"

        if dttm and len(dttm) > 0:
            statement = statement + f" and created_at > '{dttm}'"

        statement = statement + " order by created_at desc"

        statement = statement + f" limit {limit}"
        self.cur.execute(statement)

        result = []
        for row in self.cur.fetchall():
            result.append(Call(caller=row[0], created_at=row[1]))

        return result

    def __init__(self) -> None:
        super().__init__()

        self.init_entity()
