from celery import Celery
import os
from modem_command import ModemCommand

broker = os.getenv('CELERY_BROKER_URL', 'redis://localhost/0')

app = Celery('tasks', broker=broker)


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(3600.0, get_balance.s(), name='get balance')
    sender.add_periodic_task(10, get_sms.s(), name='get sms')
    sender.add_periodic_task(60, get_operator.s(), name='get operator')
    sender.add_periodic_task(60, get_signal_level.s(), name='get signal level')
    sender.add_periodic_task(60, get_signal_type.s(), name='get signal type')


@app.task
def get_balance():
    modem_command = ModemCommand()
    modem_command.make_ussd('*105#')


@app.task
def get_sms():
    modem_command = ModemCommand()
    modem_command.get_sms()


@app.task
def get_operator():
    modem_command = ModemCommand()
    modem_command.get_operator()


@app.task
def get_signal_level():
    modem_command = ModemCommand()
    modem_command.get_signal_level()


@app.task
def get_signal_type():
    modem_command = ModemCommand()
    modem_command.get_signal_type()
