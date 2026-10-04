import telebot
from telebot import types
import psutil
import platform
import os

# Вставь сюда свой токен от @BotFather
BOT_TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"

bot = telebot.TeleBot(BOT_TOKEN)


def get_cpu_usage() -> float:
    """
    Возвращает текущую загрузку CPU в процентах.
    interval=1 даёт более точное среднее за 1 секунду.
    """
    return psutil.cpu_percent(interval=1)


def get_ram_usage() -> dict:
    """
    Возвращает информацию об использовании оперативной памяти.
    Результат: словарь с total, used, free, percent.
    """
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "used": mem.used,
        "free": mem.free,
        "percent": mem.percent
    }


def get_disk_usage(path: str = "/") -> dict:
    """
    Возвращает статистику по диску (или разделу) по указанному пути.
    Для Windows можно передать 'C:\\'.
    """
    disk = psutil.disk_usage(path)
    return {
        "path": path,
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent
    }


def get_temperatures() -> dict | None:
    """
    Пытается получить температуры сенсоров.
    Не на всех ОС/конфигурациях это доступно (например, Windows без дополнительных драйверов).
    Возвращает словарь или None, если сенсоры не найдены.
    """
    if hasattr(psutil, "sensors_temperatures"):
        temps = psutil.sensors_temperatures()
        if temps:
            return temps
    return None


def format_bytes(size_bytes: int) -> str:
    """
    Преобразует размер в байтах в читаемый формат (KB, MB, GB и т.д.).
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def generate_system_report() -> str:
    """
    Собирает все параметры системы и формирует читаемый отчёт.
    Всегда возвращает минимум 4 параметра; если есть температура — она тоже включается.
    """
    cpu_percent = get_cpu_usage()
    ram = get_ram_usage()
    disk = get_disk_usage("/")  # для Windows замените на "C:\\"
    temps = get_temperatures()

    report_lines = [
        "🖥️ Отчёт о состоянии системы",
        "",
        f"🧠 CPU: {cpu_percent}%",
        f"💾 RAM: {format_bytes(ram['used'])} / {format_bytes(ram['total'])} ({ram['percent']}%)",
        f"💿 Диск ({disk['path']}): {format_bytes(disk['used'])} / {format_bytes(disk['total'])} ({disk['percent']}%)",
    ]

    if temps:
        report_lines.append("")
        report_lines.append("🌡️ Температуры (сенсоры):")
        for name, entries in temps.items():
            for entry in entries:
                report_lines.append(f"   • {entry.label or name}: {entry.current:.1f}°C")
    else:
        report_lines.append("")
        report_lines.append("⚠️ Температуры: недоступны (нет сенсоров или ОС не поддерживает)")

    report_lines.append("")
    report_lines.append(f"🖥️ ОС: {platform.system()} {platform.release()}")
    report_lines.append(f"💻 Хост: {platform.node()}")

    return "\n".join(report_lines)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Обработчик команды /start.
    Отправляет приветствие и инструкцию.
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_report = types.KeyboardButton("📊 Получить отчёт о системе")
    markup.add(btn_report)
    bot.reply_to(
        message,
        "Привет! Я бот для мониторинга системы. Нажми кнопку или отправь /report, чтобы получить отчёт.",
        reply_markup=markup
    )


@bot.message_handler(commands=["report"])
def send_report_command(message):
    """
    Обработчик команды /report.
    Генерирует и отправляет отчёт о системе.
    """
    report = generate_system_report()
    bot.reply_to(message, report)


@bot.message_handler(func=lambda m: m.text and "отчёт" in m.text.lower() or "report" in m.text.lower())
def send_report_text(message):
    """
    Реагирует на сообщения со словами «отчёт» или «report».
    Удобно, если пользователь просто пишет «дай отчёт» вместо команды.
    """
    report = generate_system_report()
    bot.reply_to(message, report)


if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)