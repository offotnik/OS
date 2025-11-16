import os
import platform
import socket
import subprocess


def get_os_info():
    """Получение информации об ОС"""
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=', 1)[1].strip().strip('"')
    except:
        pass
    return "Unknown"


def get_memory_info():
    """Получение информации о памяти из /proc/meminfo"""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            mem_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = value.strip()

            total_kb = int(mem_info.get('MemTotal', '0 kB').split()[0])
            free_kb = int(mem_info.get('MemAvailable', '0 kB').split()[0])
            swap_total_kb = int(mem_info.get('SwapTotal', '0 kB').split()[0])
            swap_free_kb = int(mem_info.get('SwapFree', '0 kB').split()[0])

            return (free_kb // 1024, total_kb // 1024), (swap_total_kb // 1024, swap_free_kb // 1024)
    except:
        return (0, 0), (0, 0)


def get_drives_info():
    """Получение информации о дисках с помощью df"""
    try:
        result = subprocess.run(['df', '-B1', '-T'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок

        drives = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 7:
                filesystem = parts[0]
                fstype = parts[1]
                total_bytes = int(parts[2])
                used_bytes = int(parts[3])
                available_bytes = int(parts[4])
                mountpoint = parts[6]

                # Пропускаем специальные файловые системы
                if fstype in ['tmpfs', 'devtmpfs', 'squashfs', 'overlay']:
                    continue

                # Конвертируем байты в GB
                free_gb = available_bytes // (1024 * 1024 * 1024)
                total_gb = total_bytes // (1024 * 1024 * 1024)

                drives.append({
                    'mountpoint': mountpoint,
                    'fstype': fstype,
                    'free_gb': free_gb,
                    'total_gb': total_gb
                })

        return drives
    except Exception as e:
        print(f"Error getting drives info: {e}")
        return []

def main():
    print("System Information:")
    print("=" * 50)

    # Основная информация
    print(f"OS: {get_os_info()}")
    print(f"Kernel: Linux {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Hostname: {socket.gethostname()}")
    print(f"User: {os.getlogin()}")

    # Память
    (free_ram, total_ram), (swap_total, swap_free) = get_memory_info()
    print(f"RAM: {free_ram}MB free / {total_ram}MB total")
    print(f"Swap: {swap_total}MB total / {swap_free}MB free")

    # Виртуальная память (аппроксимация)
    virtual_mem = 134217 if platform.architecture()[0] == '64bit' else 3072
    print(f"Virtual memory: {virtual_mem} MB")

    # Процессоры и загрузка
    print(f"Processors: {os.cpu_count()}")
    load = os.getloadavg()
    print(f"Load average: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}")

    # Диски
    print("Drives:")
    drives = get_drives_info()
    for drive in drives:
        print(f"  {drive['mountpoint']:10} {drive['fstype']:8} {drive['free_gb']}GB free / {drive['total_gb']}GB total")

main()