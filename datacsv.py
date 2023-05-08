"""用於解析每一幀的 uart data"""
import csv

with open('datacsv.csv', 'r') as f:
    reader = csv.reader(f)
    data = list(reader)

# 將逗號刪除並每個數字換行
output = []
for row in data:
    output.extend(row)

# 將結果寫入另一個 CSV 檔
with open('datacsv2.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for number in output:
        writer.writerow([number])
