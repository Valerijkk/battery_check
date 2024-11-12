import psutil
import sys
import platform
import subprocess
import datetime
import wmi

def get_basic_battery_info():
    battery = psutil.sensors_battery()
    if battery is None:
        return "Информация о батарее недоступна. Возможно, вы используете настольный компьютер.\n"

    percent = battery.percent
    is_plugged = battery.power_plugged

    # Время работы от батареи в секундах
    secs_left = battery.secsleft

    # Преобразуем время в удобный формат
    if secs_left == psutil.POWER_TIME_UNLIMITED:
        time_left = "Бесконечное время (подключено к сети)"
    elif secs_left == psutil.POWER_TIME_UNKNOWN:
        time_left = "Время работы неизвестно"
    else:
        hours = secs_left // 3600
        minutes = (secs_left % 3600) // 60
        time_left = f"{hours} ч {minutes} мин"

    status = "Подключено к сети" if is_plugged else "Работает от батареи"

    basic_info = (
        f"--- БАЗОВАЯ ИНФОРМАЦИЯ О БАТАРЕЕ ---\n"
        f"Уровень заряда батареи: {percent}%\n"
        f"Статус питания: {status}\n"
        f"Оставшееся время работы: {time_left}\n"
    )
    return basic_info

def get_detailed_battery_info():
    current_platform = platform.system()
    detailed_info = "\n--- ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О БАТАРЕЕ ---\n"
    if current_platform == "Windows":
        detailed_info += get_battery_info_windows()
    elif current_platform == "Linux":
        detailed_info += get_battery_info_linux()
    elif current_platform == "Darwin":
        detailed_info += get_battery_info_macos()
    else:
        detailed_info += f"Данная платформа ({current_platform}) не поддерживается для детальной информации о батарее.\n"
    return detailed_info

def get_battery_info_windows():
    try:
        import wmi
    except ImportError:
        return "Библиотека 'wmi' не установлена. Установите её с помощью 'pip install wmi'.\n"

    c = wmi.WMI()
    info = ""
    for battery in c.Win32_Battery():
        info += (
            f"Имя: {battery.Name}\n"
            f"Статус: {battery.BatteryStatus}\n"
            f"Полная зарядная емкость: {battery.FullChargeCapacity} mWh\n"
            f"Проектная емкость: {battery.DesignCapacity} mWh\n"
        )
    # Генерация отчета через powercfg
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"battery_report_{timestamp}.html"
        subprocess.run(["powercfg", "/batteryreport", f"/output", report_filename], check=True)
        info += f"Отчет о батарее сохранен в файле: {report_filename}\n"
    except subprocess.CalledProcessError as e:
        info += f"Не удалось сгенерировать отчет о батарее: {e}\n"
    return info

def get_battery_info_linux():
    battery_path = "/sys/class/power_supply/BAT0/"
    info = ""
    try:
        with open(battery_path + "uevent", "r") as f:
            data = f.readlines()
        battery_info = {}
        for line in data:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                battery_info[key] = value

        info += (
            f"Модель: {battery_info.get('MODEL_NAME', 'Неизвестно')}\n"
            f"Текущее напряжение: {int(battery_info.get('POWER_SUPPLY_VOLTAGE_NOW', 0)) / 1e6} V\n"
            f"Емкость: {int(battery_info.get('POWER_SUPPLY_ENERGY_NOW', 0)) / 1e3} mWh\n"
            f"Полная емкость: {int(battery_info.get('POWER_SUPPLY_ENERGY_FULL', 0)) / 1e3} mWh\n"
            f"Текущий статус: {battery_info.get('POWER_SUPPLY_STATUS', 'Неизвестно')}\n"
        )
        # Информация о циклах зарядки может находиться в файле "cycle_count"
        try:
            with open(battery_path + "cycle_count", "r") as f:
                cycle_count = f.read().strip()
            info += f"Количество циклов зарядки-разрядки: {cycle_count}\n"
        except FileNotFoundError:
            info += "Информация о циклах зарядки-разрядки недоступна.\n"
    except FileNotFoundError:
        info += "Информация о батарее недоступна или путь к батарее неверный.\n"
    return info

def get_battery_info_macos():
    try:
        # Используем system_profiler для получения информации о батарее
        output = subprocess.check_output(["system_profiler", "SPPowerDataType"], universal_newlines=True)
        battery_info = {}
        for line in output.split("\n"):
            if ": " in line:
                key, value = line.strip().split(": ", 1)
                battery_info[key] = value

        info = (
            f"Имя: {battery_info.get('Name', 'Неизвестно')}\n"
            f"Состояние: {battery_info.get('Condition', 'Неизвестно')}\n"
            f"Циклы зарядки: {battery_info.get('Cycle Count', 'Неизвестно')}\n"
            f"Полный зарядный ресурс: {battery_info.get('Full Charge Capacity (mAh)', 'Неизвестно')} mAh\n"
            f"Текущее зарядное состояние: {battery_info.get('Charge Remaining (mAh)', 'Неизвестно')} mAh\n"
        )
    except Exception as e:
        info = f"Не удалось получить детальную информацию о батарее: {e}\n"
    return info

def generate_report():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"--- ОТЧЕТ О БАТАРЕЕ ---\nДата и время: {timestamp}\n\n"
    report_content += get_basic_battery_info()
    report_content += get_detailed_battery_info()

    # Сохранение отчета в файл
    report_filename = f"battery_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, "w", encoding="utf-8") as report_file:
            report_file.write(report_content)
        print(f"Отчет о батарее успешно сохранен в файле: {report_filename}")
    except Exception as e:
        print(f"Не удалось сохранить отчет о батарее: {e}")

    # Также выводим отчет в консоль
    print("\n" + report_content)

if __name__ == "__main__":
    generate_report()
