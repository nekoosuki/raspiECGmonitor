# -*- coding: utf-8 -*-

import numpy as np
import threading
import time
import heartpy as hp


class debug_Emergency:
    def __init__(self, tele: str) -> None:
        self.lock = threading.Lock()
        self.send_start = time.perf_counter()
        self.dial_start = -1
        self.tele = tele

    def send(self) -> None:
        end = time.perf_counter()
        if self.send_start == -1 or end-self.send_start >= 30:
            self.lock.acquire()
            print('\n\n\nsending to {}'.format(self.tele))
            self.send_start = time.perf_counter()
            time.sleep(10)
            self.lock.release()
            print('\n\n\nsend done')

    def dial(self) -> None:
        end = time.perf_counter()
        if self.dial_start == -1 or end-self.dial_start >= 30:
            self.lock.acquire()
            print('\n\n\ndialing to {}'.format(self.tele))
            self.dial_start = time.perf_counter()
            time.sleep(10)
            self.lock.release()
            print('\n\n\ndial done')


class debug_SerialData:
    def __init__(self) -> None:
        self.data = []
        self.newdata = []
        self.ser = debug_SerialReader()

    def update_data(self, emer: debug_Emergency) -> bool:
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


class debug_SerialReader:
    def __init__(self) -> None:
        pass

    def read(self, emer: debug_Emergency) -> list:
        tmp = np.random.randint(0, 600, np.random.randint(0, 500)).tolist()
        if np.random.rand() < 0.1:
            tmp.append('?')
            print('\n\n\nemer')
        # print(tmp)
        if '!' in tmp or not tmp:
            return []
        if '?' in tmp:
            threading.Thread(target=emer.dial).start()
        return self.pre_process(tmp)

    def pre_process(self, x: str) -> list:
        tmp = x
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


class debug_ReadData:
    def __init__(self) -> None:
        self.data = []
        self.newdata = []
        self.i = 0

    def update_data(self, emer: debug_Emergency) -> bool:
        dic = {'1': '/home/pi/heartpro/abnormaldata/102101.txt', '2': '', '3': '/home/pi/heartpro/abnormaldata/109101.txt',
               '4': '/home/pi/heartpro/abnormaldata/118101.txt', '5': '/home/pi/heartpro/abnormaldata/232101.txt'}
        d = np.loadtxt(dic['3'])[self.i:self.i+500]
        self.data.extend(d)
        self.newdata = list(map(int, hp.scale_data(d, 0, 600)))
        self.i += 500
        if self.i >= 5000:
            self.i = 0
        return True

    def clear_data(self) -> None:
        self.data.clear()

    def get_data(self) -> list:
        return self.data

    def get_newdata(self) -> list:
        return self.newdata

    def get_len(self) -> int:
        return len(self.data)
