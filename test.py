from modules.utils import Utils

# Initialize calss
Utils = Utils()

x, y = Utils.load_radar_data("./np_label_storage.csv")

data_len = len(x)

max_frame = 0

for i in range(data_len):
    if x[i].shape[0] > max_frame:
        max_frame = x[i].shape[0]
    print(type(x))

print(max_frame)