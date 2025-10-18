import tkinter as tk
from tkinter import scrolledtext
import os
import sys
import argparse # Парсинг аргументов
import shlex # Выполнение команд из строки
from typing import List

# Название виртуальной файловой системы — используется в приглашении
VFS_NAME = os.environ.get('VFS_NAME', 'myvfs')
# Глобальные переменные
VFS_ROOT = None # корневая папка виртуальной файловой системы
current_dir = os.getcwd() # текущая директория

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
            show(entry)
    except FileNotFoundError:
        show(f"ls: cannot access '{path}': No such file or directory")
    except PermissionError:
        show(f"ls: cannot open directory '{path}': Permission denied")

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
        show(f"cd: '{target}': Out of VFS root")
        return

    if os.path.isdir(new_path):
        current_dir = new_path
        os.chdir(current_dir)
    else:
        show(f"cd: no such directory: {target}")

def cmd_cat(args: List[str]):
    "Вывод содержимого файла"
    if not args:
        show("cat: missing operand")
        return
    path = os.path.join(current_dir, args[0])
    path = os.path.abspath(path)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            show(f.read())
    except FileNotFoundError:
        show(f"cat: no such file: {args[0]}")
    except PermissionError:
        show(f"cat: cannot open file: {args[0]}")
    except UnicodeDecodeError:
        show(f"cat: cannot read binary file: {args[0]}")

def cmd_pwd(args: List[str]):
    show(current_dir)

def execute_command(line: str, echo: bool = True):
    "Главный обработчик команд"
    if echo:
        show(f"{VFS_NAME}$ {line}")

    try:
        args = parse_command(line)
    except ValueError as e:
        show(f"parse error: {e}")
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
                show(f"exit: invalid status '{cmd_args[0]}', using 0")
        show(f"Exiting with code {code}")
        sys.exit(code)

    elif cmd == 'ls':
        cmd_ls(cmd_args)
    elif cmd == 'cd':
        cmd_cd(cmd_args)
    elif cmd == 'cat':
        cmd_cat(cmd_args)
    elif cmd == 'pwd':
        cmd_pwd(cmd_args)
    else:
        show(f"{cmd}: command not found")

def start_tkinter_shell():
    root = tk.Tk()
    root.title(f"{VFS_NAME} Shell Emulator")

    # Основное окно
    output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=25, bg="black", fg="lime", insertbackground="white")
    output.pack(padx=10, pady=10)

    entry = tk.Entry(root, bg="gray15", fg="white", insertbackground="white")
    entry.pack(fill=tk.X, padx=10, pady=(0,10))

    def run_command(event=None):
        line = entry.get().strip()
        if not line:
            return
        entry.delete(0, tk.END)
        output.insert(tk.END, f"{VFS_NAME}$ {line}\n")

        # Перехватываем вывод show()
        import io, sys
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
            execute_command(line, echo=False)
        except SystemExit:
            root.destroy()
        except Exception as e:
            show(f"[ERROR] {e}")
        finally:
            sys.stdout = old_stdout
        output.insert(tk.END, buffer.getvalue())
        output.see(tk.END)

    entry.bind("<Return>", run_command)
    entry.focus()

    output.insert(tk.END, "Shell emulator started (type 'exit' to quit)\n")
    root.mainloop()

def run_script(path: str): # Функция запускает команды из файла.
    show(f"[DEBUG] Running script: {path}")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f: # Читаем файл построчно.
                line = line.strip() # Убирает пробелы и переносы строк в начале и конце.
                if not line:
                    continue
                try:
                    execute_command(line, echo=True)
                except Exception as e:
                    show(f"[DEBUG] Skipping line due to error: {e}")
    except FileNotFoundError:
        show(f"Script not found: {path}")

if __name__ == '__main__':
    import tkinter as tk
    from tkinter.scrolledtext import ScrolledText

    parser = argparse.ArgumentParser(description="Shell Emulator Stage 3")
    parser.add_argument('--vfs', help="Path to Virtual File System root")
    parser.add_argument('--script', help="Path to startup script")
    args = parser.parse_args()

    # --- Tkinter окно и текстовое поле ---
    root = tk.Tk()
    root.title(f"{VFS_NAME} Shell Emulator")
    text = ScrolledText(root, width=100, height=30, bg="black", fg="lime")
    text.pack(padx=10, pady=10)
    text.config(state=tk.DISABLED)  # <- запрещаем редактирование пользователем

    # --- функция для вывода вместо show ---
    def show(msg):
        text.config(state=tk.NORMAL)  # включаем
        text.insert(tk.END, msg + '\n')
        text.see(tk.END)
        text.config(state=tk.DISABLED)  # снова запрещаем

    # --- вывод debug информации ---
    show("[DEBUG] Parameters:")
    show(f"  VFS path: {args.vfs}")
    show(f"  Script path: {args.script}")
    show("Пример директории: C:/Users/DenTs/Desktop")

    # --- запуск скрипта, если указан ---
    if args.script:
        run_script(args.script)

    # --- установка VFS и текущей директории ---
    VFS_ROOT = args.vfs if args.vfs else None
    current_dir = VFS_ROOT or os.getcwd()
    if current_dir:
        os.chdir(current_dir)

    # --- строка ввода команд ---
    entry = tk.Entry(root, bg="gray15", fg="white", insertbackground="white")
    entry.pack(fill=tk.X, padx=10, pady=(0,10))

    def run_command(event=None):
        line = entry.get().strip()
        entry.delete(0, tk.END)
        show(f"{VFS_NAME}$ {line}")
        execute_command(line, echo=False)

    entry.bind("<Return>", run_command)
    entry.focus()

    show("Shell emulator started (type 'exit' to quit)")

    # --- запуск Tkinter цикла ---
    root.mainloop()
