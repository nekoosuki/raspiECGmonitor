# -*- coding: utf-8 -*-

from typing import NoReturn
from utils import SerialData, Predictor, Processor, DataWriter, Sensor, Emergency, VoicePlayer, ConnSql
from debug import debug_SerialData, debug_Emergency, debug_ReadData

import time
import threading
import heartpy as hp
import matplotlib.pyplot as plt
import math


TARGET_LEN = 5000
REV_LEN = TARGET_LEN+50
XLIM = REV_LEN + 300
SIM_FS = 360
COM_DATA = '/dev/ttyUSB1'
COM_SIM = '/dev/ttyAMA0'

state = 'receving'
bpm = 0

sql = ConnSql()
tele = sql.gettele()
del sql

DEBUG = True
if DEBUG:
    data = debug_ReadData()
    emer = debug_Emergency(tele)
else:
    data = SerialData(COM_DATA)
    emer = Emergency(COM_SIM, tele)

predictor = Predictor(
    'best_model.29-0.9961-1sensor-acc-filted-notch-MITBIH-7types-sinnoise.h5')
processor = Processor(TARGET_LEN, SIM_FS)
datawriter = DataWriter()
sensor = Sensor()
player = VoicePlayer()


def get_from_serial() -> NoReturn:
    global state
    global bpm
    while True:
        time.sleep(1)
        if not data.update_data(emer):
            state = 'disconnected'
            datawriter.update_state(state)
            datawriter.seq += 1
            continue
        if state == 'disconnected':
            state = 'receving'
            datawriter.update_state(state)
        datawriter.update_databuff(data.get_newdata())
        try:
            tmp_bpm = hp.process(
                processor.process(data.get_data()), SIM_FS)[1]['bpm']
            if not math.isnan(bpm):
                bpm = tmp_bpm
                datawriter.update_bpm(round(bpm))
        except:
            pass
        if data.get_len() >= REV_LEN:
            threading.Thread(target=process_predict, args=(
                data.get_data()[:REV_LEN],), name='predict').start()
            data.clear_data()


def process_predict(data: list) -> None:
    global state
    final_data = processor.process(data)
    state = predictor.predict(final_data)
    predictor.clear_s()
    datawriter.update_state(state)
    if state in ['/', 'V', 'L', 'R', 'A']:
        threading.Thread(target=emer.send, name='emer').start()


def draw() -> NoReturn:
    while True:
        plt.clf()
        plt.xlim(0, XLIM)
        plt.xlabel('simple point')
        plt.title(state+f'   bpm:{bpm}')
        plt.plot(data.get_data(), '-r')
        plt.pause(1)


def get_sensor() -> NoReturn:
    while True:
        sensor.update()
        datawriter.update_sensor(sensor.get_data())
        time.sleep(5)


def voice() -> NoReturn:
    while True:
        if not math.isnan(bpm):
            time.sleep(15)
            if not math.isnan(bpm):
                player.generate_play(round(bpm), state)
            time.sleep(15)


def main():
    # 交互模式用于更新绘图
    plt.ion()
    # 启动用于接受更新预测数据的线程
    threading.Thread(target=get_from_serial, name='get_data').start()
    # 获取传感器数据
    threading.Thread(target=get_sensor, name='get_sensor').start()
    threading.Thread(target=voice, name='voice').start()
    # 启动绘图线程 演示用
    # matplotlib在子线程中不安全
    threading.Thread(target=draw, name='draw').start()
    while True:
        # 这里上传数据
        datawriter.write()
        time.sleep(1)


main()
