import os
import shutil
import tempfile
from dotenv import load_dotenv

# 加載 .env 文件中的環境變量
load_dotenv()

# 讀取環境變量
data_storage_file_path = os.getenv("DATA_STORAGE_FILE_PATH")
data_storage_file_name = os.getenv("DATA_STORAGE_FILE_NAME")

def rename_npy_files(directory, base_file_name, start_number):
    """
    重新編號指定目錄下的 .npy 文件。
    
    :param directory: 存儲文件的目錄。
    :param base_file_name: 基礎文件名。
    :param start_number: 開始編號。
    """
    # 創建臨時目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        # 獲取指定目錄下的所有 .npy 文件
        npy_files = sorted([f for f in os.listdir(directory) if f.endswith('.npy')])

        # 先移動到臨時目錄
        for file in npy_files:
            shutil.move(os.path.join(directory, file), temp_dir)

        # 從臨時目錄移動回原目錄，並重命名
        for idx, file in enumerate(npy_files, start=start_number):
            # 構建新文件名，使用環境變量中的基礎文件名
            new_file_name = f"{base_file_name}_{idx}.npy"
            shutil.move(os.path.join(temp_dir, file), os.path.join(directory, new_file_name))

        print("重新命名完成。")

if __name__ == '__main__':
    # 讓用戶輸入起始編號
    start_number = int(input("請輸入起始編號: "))
    # 調用函數，傳入從環境變量獲取的路徑、文件名及開始編號
    rename_npy_files(data_storage_file_path, data_storage_file_name, start_number)
