# -*- coding: utf-8 -*-
import requests
import os
import socket
import platform
import subprocess
import psutil
import time
import re
from datetime import datetime, timedelta
from uuid import getnode
from subprocess import check_output, CalledProcessError

SERVER_URL = "http://192.168.8.155:5000/report"

def get_os_info():
    os_info = "Unknown"
    
    try:
        if platform.system() == "Windows":
            # Для Windows
	        os_info = platform.system() + " " + platform.version()
        elif platform.system() == "Darwin":
            # Для macOS
            os_info = subprocess.check_output("system_profiler SPSoftwareDataType | grep 'System Version' | awk '{print $3, $4, $5}'", shell=True).decode().strip()
        elif platform.system() == "Linux":
            # Для Linux
            os_info = subprocess.check_output("hostnamectl | grep 'Operating' | awk '{print $3, $4, $5}'", shell=True).decode().strip()
        else:
            os_info = platform.version()  # Для других систем (например, если это что-то необычное)

    except CalledProcessError as e:
        print(f"[ERROR] Ошибка при выполнении команды для получения информации о системе: {e}")
    except Exception as e:
        print(f"[ERROR] Ошибка при получении информации о системе: {e}")
    
    return os_info

    

# Функция получения даты установки ОС
def get_os_installation_date():
    installation_date = "Unknown"
    try:
        if platform.system() == "Linux":
            # Используем команду для Linux
            output = check_output("sudo stat / | grep 'Change' | awk '{print $2}'", shell=True).decode().strip()
            if output:
                # Преобразуем в формат YYYY-MM-DD
                installation_date = datetime.strptime(output, '%Y-%m-%d').strftime('%Y-%m-%d')
            else:
                installation_date = "Unknown"
        elif platform.system() == "Windows":
            # Используем команду для Windows
            installation_date = datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d')
        elif platform.system() == "Darwin":  # macOS
            # Используем команду для macOS
            output = check_output("ls -l /var/db/.AppleSetupDone | awk '{print $6, $7, $8}'", shell=True).decode().strip()
            parts = output.split()

            if len(parts) == 3 and ":" in parts[2]:  # Если вместо года время (HH:MM)
                current_year = datetime.now().year
                date_str = f"{parts[0]} {parts[1]} {current_year}"
            else:
                date_str = output

            installation_date = datetime.strptime(date_str, '%b %d %Y').strftime('%Y-%m-%d')
        else:
            installation_date = "Unknown"
    except CalledProcessError:
        print("[WARNING] Не удалось получить дату установки ОС.")
    except Exception as e:
        print(f"[ERROR] Ошибка при получении даты установки ОС: {e}")

    return installation_date


def generate_battery_report(report_path):
    subprocess.call(f"powercfg /batteryreport /output \"{report_path}\"", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

def get_battery_status():
    battery_status = "N/A"

    try:
        if platform.system() == "Windows":
            current_dir = os.getcwd()
            report_path = os.path.join(current_dir, "battery-report.html")

            if not os.path.exists(report_path):
                generate_battery_report(report_path)

            time.sleep(5)  # Даём системе время создать файл

            with open(report_path, "r", encoding="utf-8") as file:
                report_content = file.read()

            # Поиск данных в HTML-отчете
            design_capacity_match = re.search(r"DESIGN CAPACITY.*?<td>\s*([\d\s]+) mWh", report_content, re.DOTALL)
            full_charge_capacity_match = re.search(r"FULL CHARGE CAPACITY.*?<td>\s*([\d\s]+) mWh", report_content, re.DOTALL)

            design_capacity = int(design_capacity_match.group(1).replace(" ", "").replace("\xa0", "")) if design_capacity_match else None
            full_charge_capacity = int(full_charge_capacity_match.group(1).replace(" ", "").replace("\xa0", "")) if full_charge_capacity_match else None
            os.remove(report_path)
            if design_capacity and full_charge_capacity:
                capacity_percentage = round((full_charge_capacity / design_capacity) * 100, 2)
                return f"{capacity_percentage}%"
            else:
                return "Не удалось рассчитать остаточную ёмкость батареи."
            
            
        elif platform.system() == "Darwin":
            # Для macOS
            try:
                # Получаем проектную и максимальную емкость
                design_capacity = int(subprocess.check_output("ioreg -l | grep -i 'DesignCapacity' | awk -F'=' '{print $2}' | tr -d ' ,' | sed -n '2p'", shell=True).decode().strip())
                max_capacity = int(subprocess.check_output("ioreg -l | grep -i 'MaxCapacity' | awk '{print $5}' | tr -d '\"' | sed -n '1p'", shell=True).decode().strip())

                if design_capacity > 0:
                    percent = (max_capacity / design_capacity) * 100
                    battery_status = f"{percent:.2f}%"
                else:
                    battery_status = "Ошибка: Проектная емкость не найдена или равна нулю."
            except CalledProcessError as e:
                print(f"[ERROR] Ошибка при получении состояния батареи на macOS: {e}")
            
            # Для Linux
        elif platform.system() == "Linux":
            try:
                # Получаем состояние батареи через upower
                battery_status = subprocess.check_output("upower -i /org/freedesktop/UPower/devices/battery_BAT0 | grep 'capacity:' | awk '{print $2}'", shell=True).decode().strip()
            except CalledProcessError as e:
                print(f"[ERROR] Ошибка при получении состояния батареи на Linux: {e}")
        else:
            battery_status = "Невозможно определить состояние батареи на этой платформе."

    except Exception as e:
        print(f"[ERROR] Ошибка при получении состояния батареи: {e}")
    
    return battery_status


# Функция получения информации о производителе и модели
def get_manufacturer_and_model():
    manufacturer = "Unknown"
    model = "Unknown"

    try:
        system_platform = platform.system()

        if system_platform == "Linux":
            output = check_output("sudo dmidecode -t system", shell=True).decode()
            for line in output.splitlines():
                if "Manufacturer" in line:
                    manufacturer = line.split(":")[1].strip()
                elif "Product Name" in line:
                    model = line.split(":")[1].strip()

        elif system_platform == "Windows":
            manufacturer = subprocess.check_output(
                ['powershell', '-Command', "(Get-CimInstance Win32_ComputerSystem).Manufacturer"],
                stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()

            model = subprocess.check_output(
                ['powershell', '-Command', "(Get-CimInstance Win32_ComputerSystem).Model"],
                stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()

        elif system_platform == "Darwin":
            output = check_output("system_profiler SPHardwareDataType", shell=True).decode()
            for line in output.splitlines():
                if "Model Name" in line:
                    model = line.split(":")[1].strip()
                elif "Manufacturer" in line:
                    manufacturer = line.split(":")[1].strip()

    except CalledProcessError:
        print("[WARNING] Не удалось получить информацию о производителе/модели.")
    except Exception as e:
        print(f"[ERROR] Ошибка при получении производителя/модели: {e}")

    return manufacturer, model


# Функции для получения информации о системе
def get_ips():
    internal_ip = "Unknown"
    external_ip = "Unknown"  
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        internal_ip = subprocess.check_output("ipconfig getifaddr en0", shell=True).decode().strip()
        external_ip = subprocess.check_output("curl -s --proxy http://192.168.8.2:3128 ifconfig.me", shell=True).decode().strip()
    elif system == "windows":  # Windows
        internal_ip = subprocess.check_output(
            'powershell -Command "(ipconfig | Select-String \\"IPv4\\").ToString().Split(\':\')[-1].Trim()"',
            shell=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW
        ).strip()
        external_ip = subprocess.check_output(
            "curl -s --proxy http://192.168.8.2:3128 ifconfig.me",
            shell=True,
            encoding="utf-8"
        ).strip()
    else:  # Linux
        internal_ip = subprocess.check_output("hostname -I | awk '{print $1}'", shell=True).decode().strip()
        external_ip = subprocess.check_output("curl -s --proxy http://192.168.8.2:3128 ifconfig.me", shell=True).decode().strip()

    return internal_ip, external_ip

def get_mac_address():
    mac_address = "Unknown"
    os_type = platform.system().lower()
    try:        
        if os_type == "windows":
            # Для Windows используем PowerShell команду Get-NetAdapter
            mac_address = subprocess.check_output(
                ["powershell", "-Command", "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | Select-Object -ExpandProperty MacAddress"],
                stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
        elif os_type == "darwin":
            # Для macOS используем команду ifconfig с grep и awk
            command = "ifconfig en0 | grep ether | awk '{print $2}'"
            mac_address = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        elif os_type == "linux":
            # Для Linux используем ip link show с awk
            command = "ip link show | awk '/state UP/ {getline; print $2}'"
            mac_address = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        else:
            raise EnvironmentError("Unsupported OS")

    except Exception as e:
        print(f"Error occurred: {e}")

    return mac_address


def get_cpu_info():
    system = platform.system().lower()
    cpu_arch = platform.architecture()[0] or "Unknown"
    cpu_name = "Unknown"
    
    try:
        if platform.system() == "Windows":
            cpu_name = subprocess.check_output(
                ['powershell', '-Command', "Get-CimInstance -ClassName Win32_Processor | Select-Object -ExpandProperty Name"], 
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
        elif platform.system() == "Darwin":
            cpu_name = subprocess.check_output("sysctl -n machdep.cpu.brand_string", shell=True).decode().strip()
        else:
            cpu_name = subprocess.check_output("lscpu | grep 'Model name' | awk -F: '{print $2}'", shell=True).decode().strip()
    except Exception as e:
        cpu_name = f"Error: {e}"

    return cpu_arch, cpu_name

# Функция получения информации о памяти и хранилище
def get_memory_and_storage():
    ram = psutil.virtual_memory()
    ram_usage = f"{round(ram.used / (1024 ** 3), 2)}G / {round(ram.total / (1024 ** 3), 2)}G"

    storage = psutil.disk_usage('/')
    storage_usage = f"{round(storage.used / (1024 ** 3), 2)}G / {round(storage.total / (1024 ** 3), 2)}G"

    disk_type = "Unknown"
    system = platform.system()

    try:
        if system == "Windows":
            result = subprocess.check_output(
                'powershell "Get-PhysicalDisk | Select-Object -ExpandProperty MediaType | Select-Object -Last 1"',
                shell=True).decode().strip().lower()
            disk_type = result

        elif system == "Darwin":  # macOS
            result = subprocess.check_output(
                ["diskutil", "info", "/"]).decode().lower()
            if "solid state" in result:
                disk_type = "ssd"
            elif "rotational" in result:
                disk_type = "hdd"

        elif system == "Linux":
            # Получаем имя устройства, на котором смонтирован корень
            device_path = subprocess.check_output("df / | tail -1 | awk '{print $1}'", shell=True).decode().strip()
            device_name = os.path.basename(device_path)
            
            # Убираем номер раздела (например, sda1 → sda, nvme0n1p1 → nvme0n1)
            if device_name.startswith("nvme") and "p" in device_name:
                base_device = device_name.split("p")[0]
            else:
                base_device = ''.join(filter(lambda c: not c.isdigit(), device_name))
            
            rotational_path = f"/sys/block/{base_device}/queue/rotational"
            with open(rotational_path, "r") as f:
                rota = f.read().strip()
                disk_type = "hdd" if rota == "1" else "ssd"

    except Exception as e:
        pass  # В случае ошибки оставим "Unknown"

    storage_usage += f" ({disk_type})"
    return ram_usage, storage_usage

    

# Функция для получения serial_number
def get_serial_number():
    serial_number = "Unknown"
    try:
        if platform.system().lower() == "windows":
            # Получаем серийный номер с помощью PowerShell
            serial_number = subprocess.check_output(
                ['powershell', '-Command', "(Get-CimInstance Win32_BIOS).SerialNumber"], 
                stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
            if not serial_number:
                serial_number = "Unknown"

        elif platform.system().lower() == "darwin":
            # Для macOS используем system_profiler
            serial_number = subprocess.check_output(
                "system_profiler SPHardwareDataType | grep 'Serial Number' | awk '{print $4}'", 
                shell=True
            ).decode().strip()
            if not serial_number:
                serial_number = "Unknown"

        else:
            # Для Linux используем lshw
            try:
                serial_number = subprocess.check_output(
                    "sudo lshw -class system | grep -i serial | sed 's/.*: //'", 
                    shell=True
                ).decode().strip()
            except subprocess.CalledProcessError:
                serial_number = "Unknown"
            if not serial_number:
                serial_number = "Unknown"

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка при получении serial_number: {e}")
        serial_number = "Unknown"

    return serial_number

    

# Функция для получения service_tag (UUID)
def get_service_tag():
    service_tag = "Unknown"
    try:
        if platform.system().lower() == "windows":
            # Получаем UUID через PowerShell
            uuid = subprocess.check_output(
                ['powershell', '-Command', "(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID"],
                stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
            ).decode().strip()
            if uuid:
                service_tag = uuid
            else:
                service_tag = "Unknown"

        elif platform.system().lower() == "darwin":
            # Для macOS используем system_profiler
            output = subprocess.check_output(
                "system_profiler SPHardwareDataType | grep 'Hardware UUID'", 
                shell=True
            ).decode().strip()
            if output:
                service_tag = output.split(":")[-1].strip()
            else:
                service_tag = "Unknown"

        else:
            # Для Linux используем lshw
            try:
                service_tag = subprocess.check_output(
                    "sudo lshw -class system | grep -i 'uuid' | sed 's/.*uuid=//'", 
                    shell=True
                ).decode().strip()
            except subprocess.CalledProcessError:
                service_tag = "Unknown"
            
            if not service_tag:
                service_tag = "Unknown"

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Ошибка при получении service_tag: {e}")
        service_tag = "Unknown"
    
    return service_tag



def get_device_info():
    system = platform.system().lower()
    owner = subprocess.check_output("whoami", shell=True).decode().strip() if platform.system().lower() == "darwin" else os.getenv("USERNAME", "Unknown") if  platform.system().lower() == "windows" else os.getenv("USER", "Unknown")

    
    internal_ip, external_ip = get_ips()
    mac_address = get_mac_address() 
    cpu, cpu_model_name = get_cpu_info()
    ram, storage = get_memory_and_storage()
    
    os_info = get_os_info()
    os_installation_date = get_os_installation_date()
    manufacturer, model = get_manufacturer_and_model()
    battery_status = get_battery_status()
    serial_number = get_serial_number()
    service_tag = get_service_tag()
    
    return {
        "Owner": owner,
        "Internal_IP": internal_ip,
        "External_IP": external_ip,
        "MAC": mac_address,
        "CPU": cpu,
        "CPU_Model_Name": cpu_model_name,
        "RAM": ram,
        "Storage": storage,
        "OS": os_info,
        "OS_Installation_Date": os_installation_date,
        "Manufacturer": manufacturer,
        "Model": model,
        "Battery_Status": battery_status,
        "Serial_Number": serial_number,
        "Service_Tag": service_tag,
        "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }


def send_data():
    device_info = get_device_info()
    proxies = {
        "http": "http://192.168.8.2:3128",
        "https": "http://192.168.8.2:3128",
    }
    try:
        response = requests.post(SERVER_URL, json=device_info, proxies=proxies)
        print(f"[INFO] Ответ сервера: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"[ERROR] Ошибка отправки данных: {e}")

if __name__ == "__main__":
    send_data()
