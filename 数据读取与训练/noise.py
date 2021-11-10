import numpy as np
import glob
import random
import os

data_list = glob.glob('data/' + '/*.txt')
np.random.shuffle(data_list)
success = 0


def generateSin(a, f, ph, L, Fs):
    d = 1/Fs
    T = L*d
    t = np.arange(0, T, d)
    y = 0
    for i in range(len(a)):
        x = a[i]*np.sin(2*np.pi*t*f[i]+ph[i])
        y = y + x
    return y


for file in data_list:
    data = np.loadtxt(file)
    randpos = np.random.randint(1000, 5000)
    randlist = []
    sinnoise = generateSin([np.max(data)-np.min(data)]*3, [np.random.rand()*3, np.random.rand()*3, np.random.rand()*3], [
                           2*np.pi*np.random.rand(), 2*np.pi*np.random.rand(), 2*np.pi*np.random.rand()], randpos, 1000)
    for i in range(randpos):
        randlist.append(random.uniform(np.min(data)*(i/randpos) *
                                       np.random.rand(), np.max(data)*(i/randpos)*np.random.rand()))
    try:
        randlist = np.hstack([np.zeros(4000), randlist+sinnoise])[-5000:]
    except:
        continue
    randdata = data+randlist
    np.savetxt('noise\\'+os.path.basename(file),
               randdata, fmt='%.3f', newline=' ')
    success += 1
    if success == 1000:
        break
