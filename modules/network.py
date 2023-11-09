import csv
import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM, Masking, Concatenate, Dropout
from keras.optimizers import Adam
from keras.utils import normalize


class Network:

    def __init__(self):
        self.max_frame = 32
        self.model = None
        self.data_init()

    def data_init(self):
        x, xyz, vr, y = self.load_data("./np_label.csv")

        idx = np.random.permutation(len(x))

        x_shuffled = x[idx]
        xyz_shuffled = xyz[idx]
        vr_shuffled = vr[idx]

        x_normalize = normalize(x_shuffled, axis=0)
        xyz_normalize = normalize(xyz_shuffled, axis=0)
        vr_normalize = normalize(vr_shuffled, axis=0)
        y_shuffled = y[idx]

        print(len(x_normalize))

        print(x_shuffled[100], y_shuffled[100])


    def load_data(self, filename):
        x = []
        x1 = []
        x2 = []
        x3 = []
        x4 = []
        x5 = []
        xyz = []
        vr = []
        y = []
        
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                npy_file = row[0]
                label = row[1]
                data = np.load(npy_file)
                if data.shape[0] < self.max_frame:
                    padding_len = self.max_frame - data.shape[0]
                    padding = np.zeros((padding_len, 7))
                    data = np.concatenate([data, padding], axis=0)
                x.append(data[:,:5]) # 只保留前三個欄位
                xyz.append(data[:,:3]) # 取出xyz座標
                vr.append(data[:,3:5]) # 取出vr
                y.append(label)
        
        return np.array(x), np.array(xyz), np.array(vr), np.array(y)
    
    
    def model_init(self):
        inputs_xyz = keras.Input(shape=(32, 3), name="input_xyz")
        mask_xyz = Masking(0.0)(inputs_xyz)
        lstm_xyz = LSTM(units=128, activation='relu', recurrent_dropout=0.3, return_sequences=True)(mask_xyz)
        lstm_xyz = LSTM(units=128, activation='relu', recurrent_dropout=0.3)(lstm_xyz)
        lstm_xyz = Dropout(0.3)(lstm_xyz)

        inputs_vr = keras.Input(shape=(32, 2), name="input_vr")
        mask_vr = Masking(0.0)(inputs_vr)
        lstm_vr = LSTM(units=128, activation='relu', recurrent_dropout=0.3, return_sequences=True)(mask_vr)
        lstm_vr = LSTM(units=128, activation='relu', recurrent_dropout=0.3)(lstm_vr)
        lstm_vr = Dropout(0.3)(lstm_vr)

        merged = Concatenate()([lstm_xyz, lstm_vr])
        dense1 = Dense(units=128, activation="relu")(merged)
        dense1 = Dropout(0.5)(dense1)
        outputs = Dense(units=8, activation="softmax")(dense1)
        self.model = keras.Model(inputs=[inputs_xyz, inputs_vr], outputs=outputs)

        optimizer = Adam(learning_rate=0.001)
        self.model.compile(loss="categorical_crossentropy", optimizer=optimizer, metrics=["accuracy"])

        self.model.summary()
        keras.utils.plot_model(self.model, "123.png", show_shapes=True)

    def weight_loading(self, filename):
        self.model.load_weights(filename)

    def predict(self):
        # # 載入模型
        # model = load_model('my_model.h5')

        # # 載入新資料，假設新資料的特徵維度為 (220, 26, 3)
        # new_data = np.random.rand(220, 26, 3)

        # 將label轉換為one-hot編碼
        label_dict = {'left wave': 0, 'right wave': 1, 'up wave': 2, 'down wave': 3, "push wave": 4, "pull wave": 5, "clockwise wave": 6, "underclockwise wave": 7}
        label = np.array([label_dict[label] for label in y_shuffled])
        label = np.eye(8)[label]

        test_data = x_normalize[1000:]
        test_data_xyz = xyz_normalize[1000:]
        test_data_vr = vr_normalize[1000:]
        test_label = label[1000:]

        # 進行預測
        predictions = self.model.predict([test_data_xyz, test_data_vr])

        # 模型三專用
        # predictions = model.predict(test_data_xyz)

        # 將預測結果轉換為類別
        predicted_labels = np.argmax(predictions, axis=1)
        real_labels = np.argmax(test_label, axis=1)

        for i in predictions:
            print(i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7])

        # 顯示預測結果
        print(predicted_labels)
        print(real_labels)