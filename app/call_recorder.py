
import serial
import time
import wave

# Конфигурация параметров
VOICE_PORT = '/dev/ttyUSB2'
VOICE_BAUDRATE = 115200
RECORD_SECONDS = 10

def setup_serial(port, baudrate, rtscts=False, dsrdtr=False):
    """Устанавливает соединение с последовательным портом."""
    ser = serial.Serial(port, baudrate, rtscts=rtscts, dsrdtr=dsrdtr)
    return ser

def record_audio(voice_serial, duration):
    """Записывает аудио с последовательного порта в течение заданной продолжительности."""
    frames = []
    start_time = time.time()

    while (time.time() - start_time) < duration:
        if voice_serial.in_waiting > 0:
            data = voice_serial.read(voice_serial.in_waiting)
            frames.append(data)

    return b''.join(frames)

def save_to_wav(data, filename):
    """Сохранить данные в формате PCM WAV."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # Моно
        wf.setsampwidth(1)  # Биты на выборку (16-бит PCM)
        wf.setframerate(8000)  # Частота дискретизации для μ-law
        wf.writeframes(data)

def record(id: str):
    # Устанавливаем соединение с голосовым портом и активируем RTS/CTS и DSR/DTR
    voice_serial = setup_serial(VOICE_PORT, VOICE_BAUDRATE, rtscts=True, dsrdtr=True)

    recorded_data = record_audio(voice_serial, RECORD_SECONDS)

    # Сохранение данных в WAV файл
    save_to_wav(recorded_data, f'/var/app/app/records/{id}.wav')

    print(f"Audio converted to {id}.")

    # Закрываем трубку
    voice_serial.close()