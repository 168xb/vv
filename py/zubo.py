from threading import Thread
import os
import time
import datetime
import glob
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def read_config(config_file):
    print(f"读取设置文件：{config_file}")
    ip_configs = []
    try:
        with open(config_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if "," in line and not line.startswith("#"):
                    parts = line.strip().split(',')
                    ip_part, port = parts[0].strip().split(':')
                    a, b, c, d = ip_part.split('.')
                    if int(parts[1]) == 0:
                        ip, option, url_end = f"{a}.{b}.{c}.1", 0, "/stat"
                    elif int(parts[1]) == 1:
                        ip, option, url_end = f"{a}.{b}.1.1", 1, "/stat"
                    elif int(parts[1]) == 2:
                        ip, option, url_end = f"{a}.{b}.{c}.1", 0, "/status"
                    elif int(parts[1]) == 3:
                        ip, option, url_end = f"{a}.{b}.1.1", 1, "/status"
                    ip_configs.append((ip, port, option, url_end))
                    print(f"第{line_num}行：http://{ip}:{port}{url_end}添加到扫描列表")
        return ip_configs
    except Exception as e:
        print(f"读取文件错误: {e}")
        return None

def check_ip_port(ip_port, url_end):    
    try:
        url = f"http://{ip_port}{url_end}"
        resp = requests.get(url, timeout=2)
        resp.raise_for_status()
        if "Multi stream daemon" in resp.text or "udpxy status" in resp.text:
            print(f"{url} 访问成功")
            return ip_port
    except:
        return None

def scan_ip_port(ip, port, option, url_end):
    def show_progress():
        while checked[0] < len(ip_ports) and option == 1:
            print(f"已扫描：{checked[0]}/{len(ip_ports)}, 有效ip_port：{len(valid_ip_ports)}个")
            time.sleep(30)
    
    valid_ip_ports = []
    a, b, c, d = map(int, ip.split('.'))
    ip_ports = [f"{a}.{b}.{x}.{y}:{port}" for x in range(256) for y in range(1,256)] if option == 1 \
               else [f"{a}.{b}.{c}.{x}:{port}" for x in range(1,256)]
    checked = [0]
    Thread(target=show_progress, daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=300 if option == 1 else 50) as executor:
        futures = {executor.submit(check_ip_port, ip_port, url_end): ip_port for ip_port in ip_ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_ip_ports.append(result)
            checked[0] += 1
    return valid_ip_ports

def multicast_province(config_file):
    filename = os.path.basename(config_file)
    province = filename.split('_')[0]
    print(f"{'='*25}\n   获取: {province}ip_port\n{'='*25}")
    
    # 确保ip目录存在
    os.makedirs('ip', exist_ok=True)
    # 确保vv目录存在
    os.makedirs('vv', exist_ok=True)
    
    configs = sorted(set(read_config(config_file)))
    print(f"读取完成，共需扫描 {len(configs)}组")
    all_ip_ports = []
    
    for ip, port, option, url_end in configs:
        print(f"\n开始扫描  http://{ip}:{port}{url_end}")
        all_ip_ports.extend(scan_ip_port(ip, port, option, url_end))
    
    if len(all_ip_ports) != 0:
        all_ip_ports = sorted(set(all_ip_ports))
        print(f"\n{province} 扫描完成，获取有效ip_port共：{len(all_ip_ports)}个\n{all_ip_ports}\n")
        
        # 写入当前扫描结果到ip目录
        with open(f"ip/{province}_ip.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_ip_ports))
        
        # 处理存档文件
        archive_file = f"ip/存档_{province}_ip.txt"
        lines = []
        
        # 如果存档文件存在，读取原有内容
        if os.path.exists(archive_file):
            with open(archive_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 添加新的IP
        for ip_port in all_ip_ports:
            ip, port = ip_port.split(":")
            a, b, c, d = ip.split(".")
            lines.append(f"{a}.{b}.{c}.1:{port}\n")
        
        # 去重并排序
        lines = sorted(set(lines))
        
        # 写回存档文件
        with open(archive_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # 处理模板文件
        template_file = os.path.join('template', f"template_{province}.txt")
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                tem_channels = f.read()
            
            output = [] 
            with open(f"ip/{province}_ip.txt", 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    ip = line.strip()
                    output.append(f"{province}-组播{line_num},#genre#\n")
                    output.extend(tem_channels.replace("ipipip", f"{ip}"))
            
            # 将组播文件写入vv目录
            with open(f"vv/zubo_{province}.txt", 'w', encoding='utf-8') as f:
                f.writelines(output)
        else:
            print(f"缺少模板文件: {template_file}")
    else:
        print(f"\n{province} 扫描完成，未扫描到有效ip_port")

def main():
    # 确保ip和vv目录存在
    os.makedirs('ip', exist_ok=True)
    os.makedirs('vv', exist_ok=True)
    
    for config_file in glob.glob(os.path.join('ip', '*_config.txt')):
        multicast_province(config_file)
    
    file_contents = []
    for file_path in glob.glob('vv/zubo_*.txt'):
        with open(file_path, 'r', encoding="utf-8") as f:
            content = f.read()
            file_contents.append(content)
    
    now = datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)
    current_time = now.strftime("%Y/%m/%d %H:%M")
    
    # 将汇总文件写入vv目录
    with open("vv/zubo_all.txt", "w", encoding="utf-8") as f:
        f.write(f"{current_time}更新,#genre#\n")
        f.write(f"浙江卫视,http://ali-m-l.cztv.com/channels/lantian/channel001/1080p.m3u8\n")
        f.write('\n'.join(file_contents))
    
    print(f"组播地址获取完成，结果已保存到vv目录")

if __name__ == "__main__":
    main()