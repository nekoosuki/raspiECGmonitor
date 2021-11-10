import keras
import numpy as np
from keras.layers import *
import glob
import heartpy as hp

NUM_SENSORS = 1


def normalize(v: np.ndarray) -> np.ndarray:
    return (v-v.min())/(v.max()-v.min())


def norm_filt(v: np.ndarray) -> np.ndarray:
    v_rmbs = hp.filter_signal(v, 0.01, 360, filtertype='notch')
    v_norm = normalize(v_rmbs)
    v_filt = hp.filter_signal(v_norm, [0.18, 40], 360, filtertype='bandpass')
    return v_filt


TIME_PERIODS = 5000


def build_model(input_shape=(TIME_PERIODS, NUM_SENSORS), num_classes=7):
    model = keras.models.Sequential()
    model.add(Conv1D(8, 16, strides=2, activation='relu', padding='same',
                     input_shape=input_shape))
    model.add(Conv1D(8, 16, strides=2, activation='relu', padding='same'))
    model.add(MaxPooling1D(2))
    model.add(Conv1D(32, 8, strides=2, activation='relu', padding='same'))
    model.add(Conv1D(32, 8, strides=2, activation='relu', padding='same'))
    model.add(MaxPooling1D(2))
    model.add(Conv1D(64, 4, strides=2, activation='relu', padding='same'))
    model.add(Conv1D(64, 4, strides=2, activation='relu', padding='same'))
    model.add(MaxPooling1D(2))
    model.add(Conv1D(128, 2, strides=1, activation='relu', padding='same'))
    model.add(Conv1D(128, 2, strides=1, activation='relu', padding='same'))
    model.add(GlobalAveragePooling1D())
    model.add(Dropout(0.3))
    model.add(Dense(num_classes, activation='softmax',
                    kernel_regularizer=keras.regularizers.l2()))
    return model


def get_feature(img):
    data = np.loadtxt(img)
    feature = norm_filt(data)
    return feature.reshape((5000, 1))


def train():
    img_list = glob.glob('abnormaldata/' + '/*.txt')
    normal_img_list = glob.glob('normaldata/'+'/*.txt')
    noise_list = glob.glob('noise/' + '/*.txt')
    img_list.extend(normal_img_list)
    img_list.extend(noise_list)
    label_list = glob.glob('label/' + '/*.txt')
    x = np.array([get_feature(img)for img in img_list])
    y = keras.utils.to_categorical(
        np.hstack([np.array([np.loadtxt(label)for label in label_list]), np.array([0]*1000), np.array([6]*1000)]))
    model = build_model()
    print(model.summary())
    ckpt = keras.callbacks.ModelCheckpoint(
        filepath='best_model.{epoch:02d}-{val_accuracy:.4f}-1sensor-acc-filted-notch-MITBIH-7types-sinnoise.h5',
        monitor='val_accuracy', verbose=1, save_best_only=True)
    model.compile(loss='categorical_crossentropy',
                  optimizer='Nadam', metrics=['accuracy'])
    model.fit(x, y, batch_size=20, epochs=40,
              callbacks=[ckpt], validation_split=0.15)
    keras.utils.plot_model(model, to_file='model.png', show_shapes=True)


train()
