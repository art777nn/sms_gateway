from fastapi import FastAPI
from repository import SmsRepositry, BalanceRepository, EnvRepository, CallRepository
from modem_command import ModemCommand
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get-sms")
async def get_sms(sender: str = '', dttm: str = '', limit: int = 10):
    return SmsRepositry().get_by_sender_and_dttm(sender=sender, dttm=dttm, limit=limit)


@app.get("/get-calls")
async def get_calls(dttm: str = '', limit: int = 10):
    return CallRepository().get_by_dttm(dttm=dttm, limit=limit)


@app.get("/get-balance")
async def get_balance():
    return EnvRepository().get_by_key('balance')


@app.get("/get-operator")
async def get_operator():
    return EnvRepository().get_by_key('operator')


@app.get("/get-signal")
async def get_signal():
    return EnvRepository().get_by_key('signal')


@app.get("/get-signal-type")
async def get_signal_type():
    return EnvRepository().get_by_key('signal_type')


@app.get("/custom-at")
async def custom_at(command):
    modem = ModemCommand()
    modem.publish(command)
