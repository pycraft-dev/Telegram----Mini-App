"""Графический мастер: ввод переменных .env и запуск API / ngrok / бота (Windows)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tkinter import Entry, Label, Menu, StringVar, TclError, Tk, messagebox, ttk

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"

# Порядок ключей при сохранении (как в .env.example)
ENV_KEYS_ORDER = [
    "BOT_TOKEN",
    "DATABASE_URL",
    "SECRET_KEY",
    "SKIP_INIT_DATA_VALIDATION",
    "ADMIN_IDS",
    "DEMO_MODE",
    "WEBAPP_URL",
    "CORS_ORIGINS",
    "LOG_LEVEL",
    "SQL_ECHO",
    "LOG_JSON",
]

DEFAULTS: dict[str, str] = {
    "BOT_TOKEN": "",
    "DATABASE_URL": "sqlite+aiosqlite:///./demo.db",
    "SECRET_KEY": "",
    "SKIP_INIT_DATA_VALIDATION": "false",
    "ADMIN_IDS": "",
    "DEMO_MODE": "false",
    "WEBAPP_URL": "",
    "CORS_ORIGINS": "",
    "LOG_LEVEL": "INFO",
    "SQL_ECHO": "false",
    "LOG_JSON": "false",
}


def parse_env_file(path: Path) -> dict[str, str]:
    """Читает .env в словарь (без комментариев и пустых строк)."""
    result: dict[str, str] = {}
    if not path.is_file():
        return result
    text = path.read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key:
            result[key] = value.strip()
    return result


def write_env_file(path: Path, data: dict[str, str]) -> None:
    """Записывает .env в UTF-8 с фиксированным порядком ключей."""
    lines: list[str] = [
        "# Сгенерировано / обновлено launch_gui.py — можно править вручную.",
        "",
    ]
    for key in ENV_KEYS_ORDER:
        val = data.get(key, DEFAULTS.get(key, ""))
        lines.append(f"{key}={val}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def spawn_in_new_console(args: list[str]) -> None:
    """
    Запускает команду в новом окне консоли.

    На Windows: ``cmd /k``, чтобы окно не закрывалось сразу при ошибке (ngrok, uvicorn).

    Важно: нельзя вызывать ``Popen([\"cmd.exe\", \"/k\", list2cmdline(args)])`` — subprocess
    снова экранирует второй аргумент, появляются вложенные ``\"`` и путь к скрипту ломается
    (``Invalid argument``, в имени файла видно ``...\\"C:\\Users\\...``).
    Поэтому одна строка для ``cmd`` через ``shell=True`` и ``start ... /D ...``.
    """
    cwd = str(ROOT)
    if sys.platform == "win32":
        inner = subprocess.list2cmdline(args)
        cwd_q = cwd.replace('"', '""')
        subprocess.Popen(
            f'start "demo-launch" /D "{cwd_q}" cmd /k {inner}',
            shell=True,
        )
    else:
        subprocess.Popen(args, cwd=cwd)


class LaunchApp:
    """Окно мастера запуска."""

    def __init__(self) -> None:
        self.root = Tk()
        self.root.title("Демо: запуск бота и API")
        self.root.geometry("720x520")
        self.root.minsize(640, 480)

        self.vars: dict[str, StringVar] = {}

        hint = (
            "1) Заполните обязательные поля и нажмите «Сохранить .env».\n"
            "2) «Запустить API» — откроется консоль с uvicorn.\n"
            "3) «Запустить ngrok» — окно cmd останется открытым; один раз выполните: ngrok config add-authtoken …\n"
            "   Скопируйте https-URL в WEBAPP_URL и снова «Сохранить .env».\n"
            "4) «Запустить бота» — отдельная консоль с polling.\n"
            "Вставка в поля: Ctrl+V или Shift+Ins (кликните в поле перед вставкой)."
        )
        Label(self.root, text=hint, justify="left", wraplength=680).pack(anchor="w", padx=8, pady=6)

        form = ttk.Frame(self.root, padding=8)
        form.pack(fill="both", expand=True)

        loaded = parse_env_file(ENV_PATH)
        row = 0
        for key in ENV_KEYS_ORDER:
            ttk.Label(form, text=key + ":").grid(row=row, column=0, sticky="ne", padx=4, pady=3)
            var = StringVar(value=loaded.get(key, DEFAULTS.get(key, "")))
            self.vars[key] = var
            ent = Entry(
                form,
                textvariable=var,
                width=72,
                font=("Segoe UI", 10),
                insertwidth=2,
            )
            ent.grid(row=row, column=1, sticky="ew", padx=4, pady=3)
            self._attach_paste_bindings(ent)
            row += 1

        form.columnconfigure(1, weight=1)

        btn_row = ttk.Frame(self.root, padding=8)
        btn_row.pack(fill="x")

        ttk.Button(btn_row, text="Сохранить .env", command=self.on_save).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Сохранить и запустить API", command=self.on_save_and_api).pack(
            side="left",
            padx=4,
        )
        ttk.Button(btn_row, text="Запустить API", command=self.on_start_api).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Запустить ngrok", command=self.on_start_ngrok).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Запустить бота", command=self.on_start_bot).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Выход", command=self.root.quit).pack(side="right", padx=4)

        self._build_menu()

    def _paste_from_clipboard(self, event: object) -> str:
        """Вставляет текст из буфера обмена в активное поле (обход сбоев Ctrl+V на Windows)."""
        w = getattr(event, "widget", None)
        if w is None:
            return "break"
        try:
            clip = self.root.clipboard_get()
        except TclError:
            return "break"
        try:
            w.delete("sel.first", "sel.last")  # type: ignore[attr-defined]
        except TclError:
            pass
        try:
            w.insert("insert", clip)  # type: ignore[attr-defined]
        except TclError:
            return "break"
        return "break"

    def _attach_paste_bindings(self, ent: Entry) -> None:
        """Явные сочетания для вставки (ttk.Entry на части сборок Windows ломает стандартную вставку)."""
        ent.bind("<Control-v>", self._paste_from_clipboard)
        ent.bind("<Control-V>", self._paste_from_clipboard)
        ent.bind("<Shift-Insert>", self._paste_from_clipboard)

    def _build_menu(self) -> None:
        """Меню «Файл» с открытием папки проекта."""
        menubar = Menu(self.root)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Открыть папку проекта", command=self._open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.root.config(menu=menubar)

    def _open_folder(self) -> None:
        """Открывает каталог проекта в проводнике."""
        if sys.platform == "win32":
            subprocess.Popen(["explorer", str(ROOT)])
        else:
            messagebox.showinfo("Папка проекта", str(ROOT))

    def _collect(self) -> dict[str, str]:
        """Собирает значения полей в словарь."""
        return {k: v.get().strip() for k, v in self.vars.items()}

    def _validate_required(self, data: dict[str, str]) -> str | None:
        """Возвращает текст ошибки или None."""
        if not data.get("BOT_TOKEN"):
            return "Укажите BOT_TOKEN."
        if not data.get("SECRET_KEY") or len(data["SECRET_KEY"]) < 8:
            return "SECRET_KEY должен быть не короче 8 символов."
        if not data.get("WEBAPP_URL"):
            return "Укажите WEBAPP_URL (https-адрес Mini App, например ngrok)."
        db = (data.get("DATABASE_URL") or "").strip()
        if db:
            dbl = db.lower()
            if dbl.startswith("http://") or dbl.startswith("https://"):
                return (
                    "В DATABASE_URL попал URL сайта (http/https). "
                    "Очистите поле или укажите: sqlite+aiosqlite:///./demo.db — "
                    "https-адрес ngrok вносите только в WEBAPP_URL."
                )
            if not dbl.startswith("sqlite"):
                return "DATABASE_URL для демо должен начинаться с sqlite (например sqlite+aiosqlite:///./demo.db)."
        return None

    def on_save(self) -> bool:
        """Сохраняет .env с проверкой обязательных полей. Возвращает True при успехе."""
        data = self._collect()
        err = self._validate_required(data)
        if err:
            messagebox.showerror("Проверка", err)
            return False
        try:
            write_env_file(ENV_PATH, data)
        except OSError as exc:
            messagebox.showerror("Ошибка записи", str(exc))
            return False
        messagebox.showinfo("Готово", f"Файл сохранён:\n{ENV_PATH}")
        return True

    def on_save_and_api(self) -> None:
        """Сохраняет .env и запускает API в новой консоли."""
        if not self.on_save():
            return
        self.on_start_api()

    def on_start_api(self) -> None:
        """Запуск uvicorn в новом окне (перед запуском записывает текущие поля в .env)."""
        data = self._collect()
        err = self._validate_required(data)
        if err:
            messagebox.showwarning("Проверка", err)
            return
        try:
            write_env_file(ENV_PATH, data)
        except OSError as exc:
            messagebox.showerror("Ошибка записи .env", str(exc))
            return
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ]
        spawn_in_new_console(cmd)
        messagebox.showinfo("API", "Запущено новое окно консоли с uvicorn (порт 8000).")

    def on_start_ngrok(self) -> None:
        """Запуск ngrok в новом окне."""
        spawn_in_new_console(["ngrok", "http", "8000"])
        messagebox.showinfo(
            "ngrok",
            "Откроется окно cmd: при ошибке текст останется на экране.\n"
            "Проверьте: ngrok в PATH, один раз «ngrok config add-authtoken ВАШ_ТОКЕН».\n"
            "Рабочий https-URL скопируйте в WEBAPP_URL и нажмите «Сохранить .env».",
        )

    def on_start_bot(self) -> None:
        """Запуск бота в новом окне (перед запуском записывает текущие поля в .env)."""
        data = self._collect()
        err = self._validate_required(data)
        if err:
            messagebox.showwarning("Проверка", err)
            return
        try:
            write_env_file(ENV_PATH, data)
        except OSError as exc:
            messagebox.showerror("Ошибка записи .env", str(exc))
            return
        spawn_in_new_console([sys.executable, str(ROOT / "main.py")])
        messagebox.showinfo("Бот", "Запущено новое окно консоли с python main.py.")

    def run(self) -> None:
        """Главный цикл tkinter."""
        self.root.mainloop()


def main() -> None:
    """Точка входа."""
    app = LaunchApp()
    app.run()


if __name__ == "__main__":
    main()
