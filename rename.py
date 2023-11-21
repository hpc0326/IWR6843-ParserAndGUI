import os

def get_file_numbers(folder_path, file_extension):
    """ 獲取指定資料夾中特定文件擴展名的文件編號列表，並將其排序。 """
    file_numbers = set()
    for filename in os.listdir(folder_path):
        if filename.endswith(file_extension):
            try:
                if file_extension == '.npy':
                    number = int(filename.split('_')[2].split('.')[0])
                else:
                    number = int(filename.split('_')[2])
                file_numbers.add(number)
            except ValueError as e:
                print(f"Error parsing file number from: {filename} - {e}")
    return sorted(file_numbers)

def find_missing_numbers(numbers):
    """ 在排序的列表中找出缺失的數字。 """
    return sorted(set(range(1, max(numbers) + 1)) - set(numbers))

def prepare_renaming_operations(npy_folder, pic_folder, missing_numbers):
    """ 為 .npy 文件和相應的 .png 文件準備重命名操作。 """
    npy_numbers = get_file_numbers(npy_folder, '.npy')
    pic_numbers = get_file_numbers(pic_folder, '.png')

    renaming_operations = []
    for missing_number in missing_numbers:
        if npy_numbers:
            max_npy_number = npy_numbers.pop()
            old_npy_name = f"yuan_data_{max_npy_number}.npy"
            new_npy_name = f"yuan_data_{missing_number}.npy"
            renaming_operations.append((os.path.join(npy_folder, old_npy_name), os.path.join(npy_folder, new_npy_name)))

            for pic_suffix in ["azimuth", "doppler", "elevation", "range"]:
                if max_npy_number in pic_numbers:
                    old_pic_name = f"yuan_data_{max_npy_number}_{pic_suffix}.png"
                    new_pic_name = f"yuan_data_{missing_number}_{pic_suffix}.png"
                    renaming_operations.append((os.path.join(pic_folder, old_pic_name), os.path.join(pic_folder, new_pic_name)))

    return renaming_operations

def execute_renaming(renaming_operations):
    """ 實際執行重命名操作並提供錯誤處理。 """
    for old_name, new_name in renaming_operations:
        try:
            # print(f"Renaming '{old_name}' to '{new_name}'")
            os.rename(old_name, new_name)
        except OSError as e:
            print(f"Error renaming file {old_name} to {new_name}: {e}")

npy_folder_path = "radar_data"
pic_folder_path = "radar_data_pic"
npy_numbers = get_file_numbers(npy_folder_path, '.npy')
pic_numbers = get_file_numbers(pic_folder_path, '.png')

missing_npy_numbers = find_missing_numbers(npy_numbers)
print('missing_npy_numbers:', missing_npy_numbers)

renaming_ops = prepare_renaming_operations(npy_folder_path, pic_folder_path, missing_npy_numbers)

for op in renaming_ops:
    print(f"將 '{op[0]}' 重命名為 '{op[1]}'")

execute_renaming(renaming_ops)
