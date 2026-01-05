import os
import sys

def create_files():
    print("--- 批量创建章节文件工具 ---")

    # 1. 获取脚本文件本身所在的绝对路径
    # 不管你在哪里运行这个脚本，文件都会生成在脚本旁边的文件夹里
    script_path = os.path.abspath(__file__)
    folder_path = os.path.dirname(script_path)
    
    print(f"当前脚本位置: {folder_path}")
    print(f"文件将创建在此文件夹内。\n")

    # 2. 获取输入
    while True:
        try:
            start_input = input("请输入起始章节号 (x): ")
            if not start_input.strip(): continue # 防止空输入
            start_num = int(start_input)

            end_input = input("请输入结束章节号 (y): ")
            if not end_input.strip(): continue
            end_num = int(end_input)
            
            if start_num > end_num:
                print("错误：起始号不能大于结束号。")
                continue
            break
        except ValueError:
            print("错误：请输入纯数字。")

    count = 0
    skipped = 0

    print("-" * 30)

    # 3. 循环创建
    for i in range(start_num, end_num + 1):
        file_name = f"第{i}章.txt"
        # 拼接完整路径
        full_file_path = os.path.join(folder_path, file_name)
        
        # 4. 防覆盖检查 (如果文件已存在，则跳过)
        if os.path.exists(full_file_path):
            print(f"[跳过] {file_name} 已存在，未覆盖。")
            skipped += 1
            continue

        try:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"[成功] {file_name}")
            count += 1
        except Exception as e:
            print(f"[失败] 无法创建 {file_name}，原因: {e}")

    print("-" * 30)
    print(f"处理完成。")
    print(f"新建: {count} 个")
    print(f"跳过: {skipped} 个 (防止覆盖)")
    
    # 防止双击运行后窗口瞬间消失
    input("\n按回车键退出...")

if __name__ == "__main__":
    create_files()
