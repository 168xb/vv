import os
import requests
from urllib.parse import urlparse

# 要下载的文件列表
file_urls = [
    "https://zb.wxwb.dpdns.org/ip/江苏_config.txt",
    "https://zb.wxwb.dpdns.org/ip/广东_config.txt",
    "https://zb.wxwb.dpdns.org/ip/浙江_config.txt"
]

# 本地存储目录
output_dir = "ip"

def download_file(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        print(f"Successfully downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")
        return False

def main():
    print("Starting IP files download...")
    
    success_count = 0
    for url in file_urls:
        if download_file(url):
            success_count += 1
    
    print(f"Download completed. {success_count}/{len(file_urls)} files downloaded successfully.")

if __name__ == "__main__":
    main()