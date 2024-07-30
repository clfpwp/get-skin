import base64
import json
import re
import requests
import os
import random
import string
import time
import tkinter as tk
from tkinter import simpledialog, messagebox
from threading import Thread, Event
from requests.exceptions import ProxyError, ConnectionError, Timeout, HTTPError

def decode_base64(encoded_str):
    try:
        padding = '=' * (4 - len(encoded_str) % 4)
        encoded_str += padding
        decoded_bytes = base64.b64decode(encoded_str)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        print(f"Base64 解码失败，错误信息：{e}")
        return None

def fetch_profile(uuid):
    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
    try:
        response = requests.get(url, proxies={"http": None, "https": None}, timeout=10)
        response.raise_for_status()
        return response.text
    except (ProxyError, ConnectionError, Timeout, HTTPError) as e:
        print(f"请求失败，错误信息：{e}")
        return None

def save_skin_image(url, username, output_dir="images"):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f'{username}.jpg')
        with open(file_path, 'wb') as img_file:
            img_file.write(response.content)
        return file_path
    else:
        return None

def get_uuid_from_username(username):
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    try:
        response = requests.get(url, proxies={"http": None, "https": None}, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('id', None)
    except requests.exceptions.RequestException as e:
        return None

def generate_random_username(min_length=2, max_length=8):
    length = random.randint(min_length, max_length)
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def fetch_skins(total_skins_needed, stop_event, progress_text):
    skins_collected = 0

    while skins_collected < total_skins_needed and not stop_event.is_set():
        username = generate_random_username()
        progress_text.insert(tk.END, f"生成的随机玩家名称: {username}\n")
        progress_text.see(tk.END)

        uuid = get_uuid_from_username(username)
        if uuid:
            progress_text.insert(tk.END, f"玩家 '{username}' 的 UUID 是：{uuid}\n")
            progress_text.see(tk.END)

            profile_data = fetch_profile(uuid)

            if profile_data:
                value_match = re.search(r'"value"\s*:\s*"([^"]+)"', profile_data)
                if value_match:
                    base64_encoded_value = value_match.group(1)
                    progress_text.insert(tk.END, f"Base64 编码的值：{base64_encoded_value}\n")
                    progress_text.see(tk.END)

                    decoded_profile = decode_base64(base64_encoded_value)
                    if decoded_profile:
                        try:
                            decoded_json = json.loads(decoded_profile)
                            skin_url_match = re.search(r'"SKIN"\s*:\s*\{\s*"url"\s*:\s*"([^"]+)"', json.dumps(decoded_json))
                            if skin_url_match:
                                skin_url = skin_url_match.group(1)
                                progress_text.insert(tk.END, f"皮肤 URL：{skin_url}\n")
                                progress_text.see(tk.END)

                                file_path = save_skin_image(skin_url, username)
                                if file_path:
                                    skins_collected += 1
                                    progress_text.insert(tk.END, f"成功获取第 {skins_collected} 个皮肤，已保存到 {file_path}\n")
                                    progress_text.see(tk.END)
                                    if skins_collected >= total_skins_needed:
                                        progress_text.insert(tk.END, f"已成功获取 {total_skins_needed} 个皮肤，程序结束。\n")
                                        progress_text.see(tk.END)
                                        return
                            else:
                                progress_text.insert(tk.END, "未找到皮肤 URL\n")
                                progress_text.see(tk.END)
                        except json.JSONDecodeError as e:
                            progress_text.insert(tk.END, f"解码 JSON 失败，错误信息：{e}\n")
                            progress_text.see(tk.END)
                    else:
                        progress_text.insert(tk.END, "Base64 解码失败\n")
                        progress_text.see(tk.END)
                else:
                    progress_text.insert(tk.END, "未找到 'value' 字段\n")
                    progress_text.see(tk.END)
            else:
                progress_text.insert(tk.END, "无法获取玩家配置文件\n")
                progress_text.see(tk.END)
        else:
            progress_text.insert(tk.END, f"无法获取玩家 '{username}' 的 UUID\n")
            progress_text.see(tk.END)

        time.sleep(5)

def start_fetching():
    total_skins_needed = simpledialog.askinteger("输入", "请输入你想要获取的皮肤数量：", minvalue=1, maxvalue=100)
    if total_skins_needed is None:
        messagebox.showinfo("信息", "没有输入皮肤数量。程序结束。")
        return

    stop_event.clear()
    fetch_thread = Thread(target=fetch_skins, args=(total_skins_needed, stop_event, progress_text))
    fetch_thread.start()

def stop_program():
    stop_event.set()
    messagebox.showinfo("完成", "程序已停止。")

def show_gui():
    global stop_event, progress_text
    stop_event = Event()

    root = tk.Tk()
    root.title("皮肤获取程序")

    progress_text = tk.Text(root, wrap='word', height=20, width=80)
    progress_text.pack(padx=10, pady=10)

    tk.Button(root, text="开始获取皮肤", command=start_fetching).pack(pady=5)
    tk.Button(root, text="停止程序", command=stop_program).pack(pady=5)
    tk.Button(root, text="退出", command=root.quit).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    show_gui()
