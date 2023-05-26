"""讀取 radar_data_png/Gesture.png 並畫出 ROI 範圍"""
import cv2

# 讀取圖片
img = cv2.imread('radar_data_png/Gesture.png')
image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 檢查是否成功讀取圖片
if image is not None:
    # 定義ROI的範圍
    roi_ranges = [
        ((130, 110), (730, 710)),    # ROI 1
        ((920, 110), (1520, 710)),   # ROI 2
        ((130, 900), (730, 1500)),   # ROI 3
        ((920, 900), (1520, 1500))   # ROI 4
    ]

    # 在圖像上為每個ROI範圍繪製矩形
    for roi_range in roi_ranges:
        roi_start = roi_range[0]
        roi_end = roi_range[1]
        cv2.rectangle(img, roi_start, roi_end, (0, 0, 255), 2)

    # 顯示帶有繪製矩形的圖像
    cv2.imshow('手勢圖像與ROI', img)

    # 調整ROI解析度為32x32
    roi_resized = []
    for roi_range in roi_ranges:
        roi_start = roi_range[0]
        roi_end = roi_range[1]
        roi = image[roi_start[1]:roi_end[1], roi_start[0]:roi_end[0]]
        cv2.imshow(f'ROI_{roi_range}', roi)
        roi_resized.append(cv2.resize(roi, (100, 100)))

    # 儲存調整後的ROI圖像
    cv2.imwrite('Resized_ROI1.png', roi_resized[0])
    cv2.imwrite('Resized_ROI2.png', roi_resized[1])
    cv2.imwrite('Resized_ROI3.png', roi_resized[2])

    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print('無法讀取圖片')
