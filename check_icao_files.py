import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 基础URL
BASE_URL = "https://icao.oldsai.cn/"
# 线程数（请求过快会被封，建议 5~10）
MAX_THREADS = 20
# 超时时间（秒）
TIMEOUT = 30

# 直接读取本地 files.json 文件
with open("files.json", "r", encoding="utf-8") as f:
    data = json.load(f)
files = data["files"]

# 存储无法访问的文件
failed_files = []

# 请求头（模拟浏览器，避免被拦截）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

def check_file(file_path):
    """检查单个文件是否可访问"""
    try:
        url = BASE_URL + file_path
        # 使用 GET + stream 不下载完整文件，只检测是否能访问
        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT,
            stream=True,
            allow_redirects=True
        )
        response.close()

        if response.status_code != 200:
            return (file_path, f"状态码: {response.status_code}")
        return (file_path, "成功")

    except requests.exceptions.RequestException as e:
        return (file_path, f"请求失败: {str(e)}")

def main():
    start_time = time.time()
    print(f"开始检查 {len(files)} 个文件，线程数: {MAX_THREADS}")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_file = {executor.submit(check_file, file): file for file in files}

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                file_path, result = future.result()
                if "成功" not in result:
                    failed_files.append((file_path, result))
                    print(f"❌ {file_path} - {result}")
            except Exception as e:
                failed_files.append((file_path, f"处理异常: {str(e)}"))

    # 输出结果
    print("\n" + "="*50)
    print(f"检查完成！耗时: {time.time() - start_time:.2f} 秒")
    print(f"成功访问: {len(files) - len(failed_files)} 个")
    print(f"无法访问: {len(failed_files)} 个")

    if failed_files:
        print("\n无法访问的文件列表：")
        for idx, (file, reason) in enumerate(failed_files, 1):
            print(f"{idx}. {file} - {reason}")

        # 保存失败列表
        with open("failed_files.txt", "w", encoding="utf-8") as f:
            f.write("无法访问的文件列表：\n")
            for file, reason in failed_files:
                f.write(f"{file} - {reason}\n")
        print("\n✅ 失败列表已保存到 failed_files.txt")

if __name__ == "__main__":
    main()