import wfdb
import numpy as np


def insert_pos(nums, target):
    if target < nums[0]:
        return 0
    for i in range(len(nums)):
        if nums[i] == target or nums[i] > target and nums[i-1] < target:
            return i
    return len(nums)


#{'N': 4384, '/': 477, 'f': 13, 'Q': 1, 'V': 75, 'L': 481, 'R': 434, 'J': 3, 'a': 2, '!': 12, 'E': 8, 'A': 143, 'j': 5, '"': 25}
# '/' 起搏器心率 'L' 左束支传导阻滞 'V' 室性期前收缩 'R' 右束支传导阻滞 'A' 房性期前收缩
dict1 = {}
N_list = []
for file in ['100', '101', '102', '103', '104', '105', '106', '107', '108', '109', '111', '112', '113', '114', '115', '116', '117', '118', '119', '121', '122', '123', '124', '200', '201', '202', '203', '205', '207', '209', '210', '212', '213', '214', '215', '217', '219', '220', '221', '222', '223', '228', '230', '231', '232', '233', '234']:
    signals, field = wfdb.rdsamp(
        'mit-bih-arrhythmia-database-1.0.0\\'+file, channels=[0, ])
    signal_anno = wfdb.rdann(
        'mit-bih-arrhythmia-database-1.0.0\\'+file, 'atr', sampfrom=0)
    assert field['fs'] == 360 and field['sig_len'] == 650000
    pre_index = 0
    s_list = []
    for i in range(5000, 650000, 5000):
        signal = signals.flatten()[i:i+5000]
        index = insert_pos(list(signal_anno.sample), i)
        label = list(signal_anno.symbol)[pre_index:index]
        m = max(label, key=label.count)
        if m not in ['N', '/', 'V', 'L', 'R', 'A']:
            continue
        if m == 'N':
            N_list.append(signal)
            continue
        label_dic = {'N': 0, '/': 1, 'V': 2, 'L': 3, 'R': 4, 'A': 5}
        if m not in dict1:
            dict1[m] = 1
        else:
            dict1[m] = 1 + dict1[m]
        pre_index = index
        np.savetxt('abnormaldata\\'+file+'{}.txt'.format(100+(i // 5000)),
                   signal, fmt='%.3f', newline=' ')
        np.savetxt('label\\'+file +
                   '{}.txt'.format(100+(i // 5000)), [label_dic[m]], fmt='%d')
np.random.shuffle(N_list)
for i in range(1000, 2000):
    signal = N_list[i-1000]
    np.savetxt(f'normaldata\{i}.txt', signal, fmt='%.3f', newline=' ')
print(dict1)
