import os
import sys
import argparse # Парсинг аргументов
import shlex # Выполнение команд из строки
from typing import List

# Название виртуальной файловой системы — используется в приглашении
VFS_NAME = os.environ.get('VFS_NAME', 'myvfs')
# Глобальные переменные
VFS_ROOT = None
current_dir = None

def expand_env_vars(raw: str) -> str: # Функция получает строку на вход и возвращает строку на выход.
    return os.path.expandvars(raw) # Заменяет $HOME, $USER и т.п. на реальные значения ОС.

def parse_command(line: str) -> List[str]: # Возвращает список строк, то есть разобранные куски команды.
    expanded = expand_env_vars(line) # Заменяет переменные окружения на их реальные значения.
    return shlex.split(expanded) # модуль shlex — это разделитель строк, как в шелле

def cmd_ls(args: List[str]): # Вывод содержимого текущей директории.
    global current_dir
    path = args[0] if args else '.'
    full_path = os.path.join(current_dir, path) if not os.path.isabs(path) else path
    full_path = os.path.abspath(full_path)

    try:
        entries = os.listdir(full_path)
        for entry in entries:
            print(entry)
    except FileNotFoundError:
        print(f"ls: cannot access '{path}': No such file or directory")
    except PermissionError:
        print(f"ls: cannot open directory '{path}': Permission denied")

def cmd_cd(args: List[str]): # смена директории. Пока что заглушка
    global current_dir
    if not args:
        target = os.path.expanduser('~')  # если аргумент не указан — домой
    else:
        target = args[0]

    # Поддержка переменных окружения
    target = os.path.expandvars(target)

    # Формируем новый путь
    new_path = os.path.join(current_dir, target) if not os.path.isabs(target) else target
    new_path = os.path.abspath(new_path)

    # Проверяем границы VFS (если используется)
    if VFS_ROOT and not new_path.startswith(VFS_ROOT):
        print(f"cd: '{target}': Out of VFS root")
        return

    if os.path.isdir(new_path):
        current_dir = new_path
        os.chdir(current_dir)
    else:
        print(f"cd: no such directory: {target}")

def cmd_cat(args: List[str]):
    "Вывод содержимого файла"
    if not args:
        print("cat: missing operand")
        return
    path = os.path.join(current_dir, args[0])
    path = os.path.abspath(path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            print(f.read())
    except FileNotFoundError:
        print(f"cat: no such file: {args[0]}")
    except PermissionError:
        print(f"cat: cannot open file: {args[0]}")
    except UnicodeDecodeError:
        print(f"cat: cannot read binary file: {args[0]}")


def execute_command(line: str, echo: bool = True):
    "Главный обработчик команд"
    if echo:
        print(f"{VFS_NAME}$ {line}")

    try:
        args = parse_command(line)
    except ValueError as e:
        print(f"parse error: {e}")
        return

    if not args:
        return

    cmd, cmd_args = args[0], args[1:]

    if cmd == 'exit':
        code = 0
        if cmd_args:
            try:
                code = int(cmd_args[0])
            except Exception:
                print(f"exit: invalid status '{cmd_args[0]}', using 0")
        print(f"Exiting with code {code}")
        sys.exit(code)

    elif cmd == 'ls':
        cmd_ls(cmd_args)
    elif cmd == 'cd':
        cmd_cd(cmd_args)
    elif cmd == 'cat':
        cmd_cat(cmd_args)
    else:
        print(f"{cmd}: command not found")

def repl():
    print("Shell emulator started (type 'exit' to quit)")
    while True:
        try:
            line = input(f"{VFS_NAME}$ ")
        except (EOFError, KeyboardInterrupt):
            print()  # переход на новую строку
            break
        if not line.strip():
            continue
        execute_command(line, echo=False)

def run_script(path: str): # Функция запускает команды из файла.
    print(f"[DEBUG] Running script: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f: # Читаем файл построчно.
                line = line.strip() # Убирает пробелы и переносы строк в начале и конце.
                if not line:
                    continue
                try:
                    execute_command(line, echo=True)
                except Exception as e:
                    print(f"[DEBUG] Skipping line due to error: {e}")
    except FileNotFoundError:
        print(f"Script not found: {path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Shell Emulator Stage 3")
    parser.add_argument('--vfs', help="Path to Virtual File System root")
    parser.add_argument('--script', help="Path to startup script")
    args = parser.parse_args()

    print("[DEBUG] Parameters:")
    print(f"  VFS path: {args.vfs}")
    print(f"  Script path: {args.script}")

    if args.script:
        run_script(args.script)

    # Устанавливаем корень и текущую директорию
    VFS_ROOT = args.vfs if args.vfs else None
    current_dir = VFS_ROOT or os.getcwd()
    if current_dir:
        os.chdir(current_dir)

    repl()