import cv2
import numpy as np

# 讀取圖片
# image = cv2.imread('radar_data_png/Gesture.png')

img = cv2.imread('radar_data_png/Gesture.png')
image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


# 檢查是否成功讀取圖片
if image is not None:
    # 定義ROI的範圍
    roi1 = image[80:530, 105:555]  # ROI 1
    roi2 = image[80:530, 705:1155]  # ROI 2
    roi3 = image[80:530, 1300:1750]  # ROI 3

    # 調整ROI解析度為32x32
    roi1_resized = cv2.resize(roi1, (64, 64))
    roi2_resized = cv2.resize(roi2, (64, 64))
    roi3_resized = cv2.resize(roi3, (64, 64))

    # 顯示ROI
    cv2.imshow('Gesture', image)
    cv2.imshow('ROI 1', roi1)
    cv2.imshow('ROI 2', roi2)
    cv2.imshow('ROI 3', roi3)
 
    # 儲存調整後的ROI圖像
    cv2.imwrite('Resized_ROI1.png', roi1_resized)
    cv2.imwrite('Resized_ROI2.png', roi2_resized)
    cv2.imwrite('Resized_ROI3.png', roi3_resized)

    # array_2d = np.array(roi3_resized)
    # np.set_printoptions(threshold=np.inf)
    # print("array:\n", array_2d.shape)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print('無法讀取圖片')