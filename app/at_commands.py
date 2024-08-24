class commands:

    @staticmethod
    def txt_mode():
        return str("AT+CMGF=1")

    @staticmethod
    def code_ucs2():
        return str("AT+CSCS=\"UCS2\"")

    @staticmethod
    def gsm_mode():
        return str("AT+CSCS=\"GSM\"")

    @staticmethod
    def ussd(number: str):
        return str(f"AT+CUSD=1,{number}")

    @staticmethod
    def get_operator():
        return str("AT+COPS?")

    @staticmethod
    def get_signal_level():
        return str("AT+CSQ")

    @staticmethod
    def get_all_sms():
        return str("AT+CMGL=\"ALL\"")

    @staticmethod
    def get_sms_by_id(id):
        return str(f"AT+CMGR={id}")

    @staticmethod
    def drop_sms_by_id(id):
        return str(f"AT+CMGD={id}")

    @staticmethod
    def deny_incoming_call():
        return str("AT+GSMBUSY=0")

    @staticmethod
    def get_signal_type():
        return str("AT+ZPAS?")

    @staticmethod
    def send_sms(phone):
        return str(f"AT+CMGS=\"{phone}\"")