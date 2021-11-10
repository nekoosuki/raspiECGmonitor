# AI心电智能监护系统 树莓派设备端

###### 归档
* 项目时间2021.3-2021.6

## 主要功能
* 实时心电监护
* 异常报警（5种异常+噪声）
* 异常短信提醒
* 紧急联系电话按钮
* 摄像监控
* 温湿度检测
* 烟雾检测
* 语音播报

## 运行环境
windows 10 : 训练模型与调试运行

python 3.7.9
pip 20.2.4

serial 0.0.97
pyserial 3.5
numpy 1.19.4
heartpy 1.2.7
tensorflow 1.15.0
keras 2.3.1
matplotlib 3.3.2
wfdb 3.3.0

树莓派4B : 仅运行

python 3.7.3
pip 20.2.4

serial 0.0.97
pyserial 3.5
numpy 1.20.0
heartpy 1.2.7
tensorflow 2.3.0
keras 2.4.3
matplotlib 3.0.2

## 调用API
百度文字转语音模块
阿里云物联网