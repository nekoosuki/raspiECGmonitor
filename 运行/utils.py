# -*- coding: utf-8 -*-

from keras.models import load_model
from keras import backend as K
import serial
import numpy as np
from process_function import *
try:
    import RPi.GPIO as GPIO
    import dht11
except:
    pass
import time
import threading
from aip import AipSpeech
import os
import pymysql

num2result = {0: 'N', 1: '/', 2: 'V', 3: 'L', 4: 'R', 5: 'A', 6: 'noise'}
state2num = {'N': '0', '/': '1', 'V': '2', 'L': '3', 'R': '4',
             'A': '5', 'noise': '6', 'disconnected': '7', 'receving': '8'}
state2voice = {'N': '正常', 'noise': '噪声',
               'disconnected': '导联脱落', 'receving': '预测中'}
DHT11_PIN = 29
MQ2_PIN = 32

# 'N':正常,'/':起搏器心率,'L':左束支传导阻滞,'V':室性期前收缩,'R':右束支传导阻滞,'A':心房早期收缩


class ConnSql:
    def __init__(self) -> None:
        self.conn = pymysql.connect(
            host='81.68.215.252', port=3306, user='root', passwd='87283325', db='wx')
        self.cur = self.conn.cursor()

    def gettele(self) -> str:
        self.cur.execute('select telephone from device where device_id = 1')
        res = self.cur.fetchone()
        return (res[0])

    def __del__(self) -> None:
        self.cur.close()
        self.conn.commit()
        self.conn.close()


class VoicePlayer:
    def __init__(self) -> None:
        APP_ID = '24096316'
        API_KEY = 'zw9t69PYOXkcM6bNzTQCfw3T'
        SECRET_KEY = '2VnRSeFFGallXwzMiOgGDFWwWISdZGUs'
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    def generate_play(self, bpm: int, state: str) -> None:
        v = state2voice.get(state, '异常')
        result = self.client.synthesis(f'您的心率是{bpm}, 心电检测{v}', 'zh', 1, {
            'per': 4,
            'spd': 3,
            'vol': 7,
            'per': 0
        })
        if not isinstance(result, dict):
            with open('test.mp3', 'wb') as f:
                f.write(result)
        os.system('omxplayer -o alsa test.mp3')


class Emergency:
    def __init__(self, COM: str, tele: str) -> None:
        self.ser = serial.Serial(COM, 38400, timeout=1)
        self.ser.flushInput()
        self.lock = threading.Lock()
        self.send_start = -1
        self.dial_start = -1
        self.send_tele = ''
        self.dial_tele = tele
        for i in range(11):
            self.send_tele = self.send_tele + '003' + tele[i]
        self.lock.acquire()
        self.ser.write(b'AT+CMGF=1\r\n')
        time.sleep(1)
        self.ser.read_until(b'OK\r\n')
        self.ser.write(b'AT+CSCS=\"UCS2\"\r\n')
        time.sleep(1)
        self.ser.read_until(b'OK\r\n')
        self.ser.write(b'AT+CSMP=17,167,0,8\r\n')
        time.sleep(1)
        self.ser.read_until(b'OK\r\n')
        self.lock.release()

    def send(self) -> None:
        end = time.perf_counter()
        if self.send_start == -1 or end-self.send_start >= 60:
            self.send_start = time.perf_counter()
            try:
                self.lock.acquire()
                print('sending')
                self.ser.write(f'AT+CMGS=\"{self.send_tele}\"\r\n'.encode())
                time.sleep(1)
                self.ser.read_until(b'>\r\n')
                # self.ser.write(b'warn\r\n')
                self.ser.write(
                    b'5FC375358BBE59078FDE7EED76D16D4B52305F025E38\r\n')
                time.sleep(1)
                self.ser.read_until(b'>\r\n')
                self.ser.write(bytes.fromhex('1A')+b'\r\n')
                time.sleep(5)
                self.ser.read_until(b'OK\r\n')
            finally:
                self.lock.release()
                print('send done')

    def dial(self) -> None:
        end = time.perf_counter()
        if self.dial_start == -1 or end-self.dial_start >= 30:
            self.dial_start = time.perf_counter()
            try:
                self.lock.acquire()
                print('dialing')
                self.ser.write(f'ATD{self.dial_tele};\r\n'.encode())
                time.sleep(5)
                self.ser.read_until(b'OK\r\n')
            finally:
                self.lock.release()
                print('dial done')

    def test(self) -> bool:
        self.lock.acquire()
        self.ser.write(b'AT\r\n')
        self.ser.read_until(b'OK')
        self.ser.write(b'AT\r\n')
        self.ser.read_until(b'OK')
        self.lock.release()
        return True


class DataWriter:
    def __init__(self) -> None:
        self.databuff = ''
        self.state = 'receving'
        self.bpm = 0
        self.seq = 0
        self.temp = 0
        self.humi = 0
        self.gas = 0

    def write(self) -> None:
        with open('data.txt', 'wt') as f:
            f.writelines(
                state2num[self.state]+'\n'+str(self.bpm)+'\n'+self.databuff+'\n'+str(self.seq)+'\n'+str(self.temp)+'\n'+str(self.humi)+'\n'+str(self.gas))

    def update_databuff(self, data: list) -> None:
        self.databuff = ','.join(list(map(str, data[:512])))
        if self.seq == 2**31-1:
            self.seq = 0
        else:
            self.seq += 1
        self.write_disconnected = False

    def update_sensor(self, data: tuple) -> None:
        self.temp, self.humi, self.gas = data

    def update_state(self, state: str) -> None:
        assert state in state2num
        self.state = state

    def update_bpm(self, bpm: int) -> None:
        self.bpm = bpm


class SerialData:
    def __init__(self, COM: str) -> None:
        self.data = []
        self.newdata = []
        self.ser = SerialReader(COM)

    def update_data(self, emer: Emergency) -> bool:
        tmp = self.ser.read(emer)
        if tmp:
            self.data.extend(tmp)
            self.newdata = tmp
            return True
        return False

    def clear_data(self) -> None:
        self.data.clear()

    def get_data(self) -> list:
        return self.data

    def get_newdata(self) -> list:
        return self.newdata

    def get_len(self) -> int:
        return len(self.data)

    def set_data(self, data: list) -> None:
        self.data = data


class SerialReader:
    def __init__(self, COM: str) -> None:
        self.ser = serial.Serial(
            COM, 38400, timeout=1, parity=serial.PARITY_NONE)
        self.ser.flushInput()

    def read(self, emer: Emergency) -> list:
        tmp = self.ser.read_all()
        if tmp == b'OK+LOST\r\n':
            return []
        try:
            tmp = tmp.decode()
        except:
            return []
        if '?' in tmp:
            threading.Thread(target=emer.dial).start()
        if '!' in tmp or not tmp:
            return []
        return self.pre_process(tmp)

    def pre_process(self, x: str) -> list:
        try:
            tmp = x.split(sep='\r\n')
        except:
            return []
        for item in tmp:
            try:
                if int(item) > 660 or int(item) < 50:
                    tmp.remove(item)
            except:
                tmp.remove(item)
        try:
            tmp = list(map(int, tmp))
        except:
            return []
        return tmp


class Processor:
    def __init__(self, TARGET_LEN: int, fs: int) -> None:
        self.TARGET_LEN = TARGET_LEN
        self.fs = fs

    def process(self, data: list) -> np.ndarray:
        npdata = np.array(data)
        npdata = norm_filt(npdata, self.fs)
        return npdata[-self.TARGET_LEN:]


class Predictor:
    def __init__(self, model: str) -> None:
        self.model = load_model(model)

    def predict(self, data: np.ndarray) -> str:
        return num2result[np.argmax(self.model.predict(data.reshape((1, 5000, 1))), axis=-1)[0]]

    def clear_s(self) -> None:
        K.clear_session()


class Sensor:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup([DHT11_PIN, MQ2_PIN], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.temp = 0
        self.humi = 0
        self.gas = 0

    def update(self) -> None:
        instance = dht11.DHT11(DHT11_PIN)
        th_result = instance.read()
        if th_result.is_valid():
            self.temp = th_result.temperature
            self.humi = th_result.humidity
        if GPIO.input(MQ2_PIN):
            self.gas = 0
        else:
            self.gas = 1

    def get_data(self) -> tuple:
        return self.temp, self.humi, self.gas
