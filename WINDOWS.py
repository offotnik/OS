import ctypes
from ctypes import wintypes
import win32api
import os
import sys


def get_os_version():
    """Получение версии операционной системы"""
    try:
        # Для Windows 10 и выше
        if sys.getwindowsversion().major >= 10:
            return "Windows 10 or Greater"
        elif sys.getwindowsversion().major == 6:
            if sys.getwindowsversion().minor == 3:
                return "Windows 8.1"
            elif sys.getwindowsversion().minor == 2:
                return "Windows 8"
            elif sys.getwindowsversion().minor == 1:
                return "Windows 7"
            elif sys.getwindowsversion().minor == 0:
                return "Windows Vista"
        elif sys.getwindowsversion().major == 5:
            return "Windows XP"
        else:
            return f"Windows {sys.getwindowsversion().major}.{sys.getwindowsversion().minor}"
    except:
        return "Unknown Windows Version"


def get_memory_info():
    """Получение корректной информации о памяти"""

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    memory_status = MEMORYSTATUSEX()
    memory_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory_status)):
        total_phys_mb = memory_status.ullTotalPhys // (1024 * 1024)
        avail_phys_mb = memory_status.ullAvailPhys // (1024 * 1024)
        used_phys_mb = total_phys_mb - avail_phys_mb
        memory_load = memory_status.dwMemoryLoad

        # Фактически доступная виртуальная память (физическая + файл подкачки)
        total_available_virtual_mb = (memory_status.ullTotalPhys + memory_status.ullTotalPageFile) // (1024 * 1024)

        return {
            'total_phys_mb': total_phys_mb,
            'avail_phys_mb': avail_phys_mb,
            'used_phys_mb': used_phys_mb,
            'memory_load': memory_load,
            'available_virtual_mb': total_available_virtual_mb,  # Фактически доступно
            'total_pagefile_mb': memory_status.ullTotalPageFile // (1024 * 1024),
            'avail_pagefile_mb': memory_status.ullAvailPageFile // (1024 * 1024)
        }
    return None


def get_processor_info():
    """Получение информации о процессоре"""
    # Количество ядер
    import multiprocessing
    cores = multiprocessing.cpu_count()

    # Архитектура
    architecture = "x64" if sys.maxsize > 2 ** 32 else "x86"

    # Дополнительная информация об архитектуре
    try:
        import platform
        arch_full = platform.machine()
        if "AMD64" in arch_full:
            architecture = "x64 (AMD64)"
        elif "ARM64" in arch_full:
            architecture = "ARM64"
        elif "ARM" in arch_full:
            architecture = "ARM"
    except:
        pass

    return cores, architecture


def get_computer_and_user_info():
    """Получение имени компьютера и пользователя"""
    computer_name = os.environ.get('COMPUTERNAME', 'Unknown')

    # Получение имени текущего пользователя
    try:
        user_name = win32api.GetUserName()
    except:
        user_name = os.environ.get('USERNAME', 'Unknown')

    return computer_name, user_name


def get_performance_info():
    """Получение информации о файле подкачки через GetPerformanceInfo"""

    class PERFORMANCE_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("CommitTotal", ctypes.c_size_t),
            ("CommitLimit", ctypes.c_size_t),
            ("CommitPeak", ctypes.c_size_t),
            ("PhysicalTotal", ctypes.c_size_t),
            ("PhysicalAvailable", ctypes.c_size_t),
            ("SystemCache", ctypes.c_size_t),
            ("KernelTotal", ctypes.c_size_t),
            ("KernelPaged", ctypes.c_size_t),
            ("KernelNonpaged", ctypes.c_size_t),
            ("PageSize", ctypes.c_size_t),
            ("HandleCount", wintypes.DWORD),
            ("ProcessCount", wintypes.DWORD),
            ("ThreadCount", wintypes.DWORD),
        ]

    performance_info = PERFORMANCE_INFORMATION()
    performance_info.cb = ctypes.sizeof(PERFORMANCE_INFORMATION)

    if ctypes.windll.psapi.GetPerformanceInfo(ctypes.byref(performance_info), performance_info.cb):
        page_size = performance_info.PageSize
        commit_total = performance_info.CommitTotal * page_size // (1024 * 1024)  # MB
        commit_limit = performance_info.CommitLimit * page_size // (1024 * 1024)  # MB

        return {
            'commit_total': commit_total,
            'commit_limit': commit_limit
        }
    return None


def get_drives_info():
    """Получение информации о логических дисках"""
    drives_info = []

    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if bitmask & 1:
            drives.append(f"{letter}:\\")
        bitmask >>= 1

    for drive in drives:
        try:
            # Получаем информацию о свободном и общем месте
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)

            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(drive),
                None,
                ctypes.pointer(total_bytes),
                ctypes.pointer(free_bytes)
            )

            # Конвертируем в гигабайты
            total_gb = total_bytes.value / (1024 ** 3)
            free_gb = free_bytes.value / (1024 ** 3)
            used_gb = total_gb - free_gb

            # Рассчитываем процент использования
            usage_percent = (used_gb / total_gb * 100) if total_gb > 0 else 0

            drives_info.append({
                'drive': drive,
                'total_gb': round(total_gb, 2),
                'free_gb': round(free_gb, 2),
                'used_gb': round(used_gb, 2),
                'usage_percent': round(usage_percent, 2),
                'file_system': 'NTFS'  # Для простоты, можно определить реальную ФС
            })

        except Exception as e:
            print(f"Ошибка при получении информации о диске {drive}: {e}")

    return drives_info


def main():
    """Основная функция"""
    print("System Information:")
    print("=" * 50)

    # Версия ОС
    os_version = get_os_version()
    print(f"OS: {os_version}")

    # Имя компьютера и пользователя
    computer_name, user_name = get_computer_and_user_info()
    print(f"Computer Name: {computer_name}")
    print(f"User: {user_name}")

    # Архитектура процессора
    cores, architecture = get_processor_info()
    print(f"Architecture: {architecture}")
    print(f"Processors: {cores}")

    # Информация о памяти
    memory_info = get_memory_info()
    if memory_info:
        print(f"\nMemory Information:")
        print(f"  Physical RAM: {memory_info['used_phys_mb']}MB / {memory_info['total_phys_mb']}MB ({memory_info['memory_load']}% used)")
        print(f"  Available RAM: {memory_info['avail_phys_mb']}MB")
        print(f"  Page File: {memory_info['avail_pagefile_mb']}MB / {memory_info['total_pagefile_mb']}MB available")
        print(f"  Available Virtual Memory: {memory_info['available_virtual_mb']}MB")

    # Информация о дисках
    print(f"\nDrives:")
    drives = get_drives_info()
    for drive in drives:
        print(f"  - {drive['drive']}: {drive['free_gb']}GB free / {drive['total_gb']}GB total ({drive['usage_percent']}% used)")

if __name__ == "__main__":
    main()