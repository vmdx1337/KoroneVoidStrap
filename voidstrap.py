import os
import subprocess
import sys
import json
import platform
import glob
import shutil
import urllib.request
import urllib.error
import threading
import tempfile
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font, simpledialog

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

VERSION = "1.1-STABLE"
FASTFLAGS_FILE  = "fastFlags.json"
PEKORA_VERSION_HASH = "version-cde8fee1a1e747d4"
PEKORA_2020L_FOLDER  = "2020L"
PEKORA_2021M_FOLDER  = "2021M"
PEKORA_FONTS_SUBPATH = os.path.join("content", "fonts")
PEKORA_TEXT_SUBPATH  = os.path.join("content", "textures")

LOGO_URL = "https://github.com/vmdx1337/KoroneVoidStrap/blob/main/assets/imazge.png?raw=true"
ICON_URL = "https://raw.githubusercontent.com/vmdx1337/KoroneVoidStrap/refs/heads/main/assets/image.ico"

THEMES = {
    "Void": {"bg": "#000000", "surface": "#080808", "border": "#121212", "accent": "#ffffff", "text": "#e0e0e0", "muted": "#444444", "active_text": "#000000"},
    "Cyberpunk": {"bg": "#000505", "surface": "#001a1a", "border": "#00f2ff", "accent": "#00f2ff", "text": "#00f2ff", "muted": "#006666", "active_text": "#000000"},
    "Crimson": {"bg": "#0d0000", "surface": "#1a0000", "border": "#ff0000", "accent": "#ff3333", "text": "#ffe0e0", "muted": "#660000", "active_text": "#ffffff"},
    "Nord": {"bg": "#2e3440", "surface": "#3b4252", "border": "#4c566a", "accent": "#88c0d0", "text": "#eceff4", "muted": "#616e88", "active_text": "#2e3440"},
    "Sakura": {"bg": "#1a1012", "surface": "#2d1b1e", "border": "#4a2c31", "accent": "#ffb7c5", "text": "#ffeef0", "muted": "#855a62", "active_text": "#1a1012"},
    "Oceanic": {"bg": "#011627", "surface": "#0b2942", "border": "#1d3b53", "accent": "#2ec4b6", "text": "#fdfffc", "muted": "#5f7e97", "active_text": "#011627"},
    "Midnight Gold": {"bg": "#0a0a0a", "surface": "#141414", "border": "#262626", "accent": "#d4af37", "text": "#ffffff", "muted": "#555555", "active_text": "#000000"},
    "Purple": {"bg": "#0a0014", "surface": "#16002b", "border": "#2d0052", "accent": "#b366ff", "text": "#f2e6ff", "muted": "#7d6a96", "active_text": "#f2e6ff"},
    "Emerald": {"bg": "#000803", "surface": "#001207", "border": "#00ff62", "accent": "#00ff62", "text": "#d4ffdf", "muted": "#004d1e", "active_text": "#000000"}
}

class ClientLoader(tk.Toplevel):
    def __init__(self, parent, logo, theme):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="#000000")
        
        w, h = 420, 280
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        if logo: tk.Label(self, image=logo, bg="#000000").pack(pady=(30, 10))
        
        tk.Label(self, text="STARTING VOID CLIENT", font=("Consolas", 12, "bold"), fg="white", bg="#000000").pack()
        self.status = tk.Label(self, text="Preparing session...", font=("Consolas", 9), fg=theme["accent"], bg="#000000")
        self.status.pack(pady=15)

        self.progress = tk.Canvas(self, width=320, height=3, bg="#111111", highlightthickness=0)
        self.progress.pack()
        self.bar = self.progress.create_rectangle(-100, 0, 0, 3, fill=theme["accent"], outline="")
        
        self.pos = -100
        self.animate()

    def animate(self):
        self.pos += 5
        if self.pos > 320: self.pos = -100
        self.progress.coords(self.bar, self.pos, 0, self.pos + 100, 3)
        self.after(15, self.animate)

def download_resource(url, filename):
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        try: urllib.request.urlretrieve(url, path)
        except: return None
    return path

def get_version_roots():
    roots = [os.path.expandvars(r"%localappdata%\ProjectX\Versions"), os.path.expandvars(r"%localappdata%\Pekora\Versions")]
    return list(set([p for p in roots if os.path.isdir(p)]))

def iter_version_dirs():
    for root in get_version_roots():
        for d in sorted(glob.glob(os.path.join(root,"*"))):
            if os.path.isdir(d): yield d

def get_executable_paths(folder):
    return [os.path.join(ver, folder, "ProjectXPlayerBeta.exe") for ver in iter_version_dirs()]

def load_fastflags():
    if os.path.exists(FASTFLAGS_FILE):
        try:
            with open(FASTFLAGS_FILE,"r") as f: return json.load(f)
        except: pass
    return {}

def save_fastflags(ff):
    with open(FASTFLAGS_FILE,"w") as f: json.dump(ff, f, indent=2)

def apply_fastflags(ff):
    for ver in iter_version_dirs():
        for folder in [PEKORA_2020L_FOLDER, PEKORA_2021M_FOLDER]:
            fp = os.path.join(ver, folder)
            if os.path.isdir(fp):
                cd = os.path.join(fp, "ClientSettings")
                os.makedirs(cd, exist_ok=True)
                with open(os.path.join(cd, "ClientAppSettings.json"), "w") as f: json.dump(ff, f, indent=2)
    return True

class KoroneVoidStrap(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KoroneVoidStrap")
        self.geometry("880x500")
        self.resizable(False, False)
        self.theme = THEMES["Void"]

        self.f_main = font.Font(family="Consolas", size=10)
        self.f_lg   = font.Font(family="Consolas", size=13, weight="bold")
        self.f_xl   = font.Font(family="Consolas", size=15, weight="bold")
        self.f_sm   = font.Font(family="Consolas", size=9)

        self._load_resources()
        self._build_ui()

    def _load_resources(self):
        logo_path = download_resource(LOGO_URL, "kstrap_logo.jpg")
        self.logo_img = None
        if logo_path and HAS_PIL:
            try:
                img = Image.open(logo_path).resize((120, 120), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
            except: pass
        icon_path = download_resource(ICON_URL, "kstrap_icon.ico")
        if icon_path and platform.system().lower() == "windows":
            try: self.iconbitmap(icon_path)
            except: pass

    def _build_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        self.configure(bg=self.theme["bg"])

        self.sidebar = tk.Frame(self, bg=self.theme["surface"], width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        if self.logo_img:
            tk.Label(self.sidebar, image=self.logo_img, bg=self.theme["surface"]).pack(pady=20)

        self.content = tk.Frame(self, bg=self.theme["bg"])
        self.content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        nav = [("launch", "▶  Launch"), ("fastflags", "⚙  FastFlags"), ("editfont", "✎  Fonts"), 
               ("editcursor", "🖱  Cursor"), ("appearance", "🎨  Design"), ("credits", "★  Credits")]

        self._btns = {}
        for k, l in nav:
            b = tk.Button(self.sidebar, text=l, font=self.f_main, anchor="w", padx=20, bg=self.theme["surface"],
                          fg=self.theme["muted"], bd=0, relief=tk.FLAT, cursor="hand2", 
                          activebackground=self.theme["accent"], command=lambda x=k: self.show(x))
            b.pack(fill=tk.X, pady=2)
            self._btns[k] = b

        self.pages = {
            "launch": LaunchPage(self.content, self),
            "fastflags": FastFlagsPage(self.content, self),
            "editfont": EditFontPage(self.content, self),
            "editcursor": EditCursorPage(self.content, self),
            "appearance": AppearancePage(self.content, self),
            "credits": CreditsPage(self.content, self)
        }
        for p in self.pages.values(): p.place(relwidth=1, relheight=1)
        self.show("launch")

    def show(self, key):
        for k, b in self._btns.items():
            act = (k == key)
            b.configure(bg=self.theme["accent"] if act else self.theme["surface"],
                        fg=self.theme["active_text"] if act else self.theme["muted"])
        self.pages[key].tkraise()
        self.pages[key].on_show()

    def change_theme(self, name):
        self.theme = THEMES[name]
        self._build_ui()
        self.show("appearance")

class BasePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.theme["bg"])
        self.app = app
    def on_show(self): pass
    def _title(self, t, s=""):
        f = tk.Frame(self, bg=self.app.theme["bg"])
        f.pack(fill=tk.X, padx=24, pady=(20,0))
        tk.Label(f, text=t, font=self.app.f_xl, fg=self.app.theme["text"], bg=self.app.theme["bg"]).pack(anchor="w")
        if s: tk.Label(f, text=s, font=self.app.f_sm, fg=self.app.theme["muted"], bg=self.app.theme["bg"]).pack(anchor="w")
        tk.Frame(self, bg=self.app.theme["border"], height=1).pack(fill=tk.X, padx=24, pady=(8,20))
    def _btn(self, p, t, c, clr=None):
        bg = clr if clr else self.app.theme["accent"]
        return tk.Button(p, text=t, font=self.app.f_main, bg=bg, fg=self.app.theme["active_text"], 
                         relief=tk.FLAT, bd=0, padx=15, pady=10, cursor="hand2", command=c)

class LaunchPage(BasePage):
    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("Launch", "Ascend into the Void")
        
        container = tk.Frame(self, bg=self.app.theme["bg"])
        container.pack(fill=tk.X, padx=24)

        for yr, fld in [("2021M", PEKORA_2021M_FOLDER), ("2020L", PEKORA_2020L_FOLDER)]:
            card = tk.Frame(container, bg=self.app.theme["surface"], padx=20, pady=20)
            card.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
            
            tk.Label(card, text=f"Client {yr}", font=self.app.f_lg, fg=self.app.theme["text"], bg=self.app.theme["surface"]).pack(anchor="w")
            tk.Label(card, text="Standard play mode", font=self.app.f_sm, fg=self.app.theme["muted"], bg=self.app.theme["surface"]).pack(anchor="w", pady=(0, 15))
            
            self._btn(card, "▶  Launch", lambda f=fld: self._start(f)).pack(fill=tk.X)

    def _start(self, fld):
        paths = get_executable_paths(fld)
        exe = next((p for p in paths if os.path.isfile(p)), None)
        if not exe: 
            messagebox.showerror("Error", "Client not found!"); return
        
        loader = ClientLoader(self.app, self.app.logo_img, self.app.theme)
        
        def run():
            apply_fastflags(load_fastflags())
            subprocess.Popen([exe, "--app"])
            time.sleep(5)
            loader.destroy()
            
        threading.Thread(target=run, daemon=True).start()

class AppearancePage(BasePage):
    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("Design Settings")
        grid = tk.Frame(self, bg=self.app.theme["bg"])
        grid.pack(fill=tk.BOTH, expand=True, padx=24)
        for i, (n, d) in enumerate(THEMES.items()):
            c = tk.Frame(grid, bg=self.app.theme["surface"], padx=10, pady=10)
            c.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            tk.Label(c, text=n, font=self.app.f_main, fg=d["accent"], bg=self.app.theme["surface"]).pack(pady=5)
            self._btn(c, "Apply", lambda x=n: self.app.change_theme(x)).pack(fill=tk.X)
        for j in range(3): grid.grid_columnconfigure(j, weight=1)

class FastFlagsPage(BasePage):
    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("FastFlags")
        bar = tk.Frame(self, bg=self.app.theme["bg"]); bar.pack(fill=tk.X, padx=24, pady=10)
        self._btn(bar, "+ Add Flag", self._add).pack(side=tk.LEFT)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=self.app.theme["surface"], foreground=self.app.theme["text"], fieldbackground=self.app.theme["surface"], borderwidth=0)
        style.map("Treeview", background=[('selected', self.app.theme["accent"])])

        self.tree = ttk.Treeview(self, columns=("K", "V"), show="headings", height=12)
        self.tree.heading("K", text="Flag Name"); self.tree.heading("V", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=24, pady=10)
        
        ff = load_fastflags()
        for k, v in ff.items(): self.tree.insert("", "end", values=(k, v))

    def _add(self):
        k = simpledialog.askstring("Add", "Flag Key:")
        v = simpledialog.askstring("Add", "Value:")
        if k:
            ff = load_fastflags(); ff[k] = v; save_fastflags(ff)
            self.on_show()

class EditFontPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_ver = tk.StringVar(value=PEKORA_2021M_FOLDER)

    def _set_ver(self, v):
        self.selected_ver.set(v)
        self.on_show()

    def _get_font_dest(self):
        roots = [
            os.path.expandvars(r"%localappdata%\ProjectX\Versions"),
            os.path.expandvars(r"%localappdata%\Pekora\Versions")
        ]
        for root in roots:
            dest_dir = os.path.join(root, PEKORA_VERSION_HASH, self.selected_ver.get(), PEKORA_FONTS_SUBPATH)
            if os.path.isdir(dest_dir):
                return dest_dir
        return None

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("Font Settings", "Direct mirror replacement (No backups)")
        
        card = tk.Frame(self, bg=self.app.theme["surface"], padx=20, pady=20)
        card.pack(fill=tk.X, padx=24)

        v_box = tk.Frame(card, bg=self.app.theme["surface"])
        v_box.pack(fill=tk.X, pady=(0, 20))
        for text, val in [("2021 Client", PEKORA_2021M_FOLDER), ("2020 Client", PEKORA_2020L_FOLDER)]:
            is_sel = (val == self.selected_ver.get())
            tk.Button(v_box, text=text, font=self.app.f_main, 
                      bg=self.app.theme["accent"] if is_sel else self.app.theme["bg"],
                      fg=self.app.theme["active_text"] if is_sel else self.app.theme["text"],
                      bd=0, padx=20, cursor="hand2",
                      command=lambda v=val: self._set_ver(v)).pack(side=tk.LEFT, padx=2)

        self._btn(card, "✎ Select Font & Overwrite All", self._do_font_mirror).pack(fill=tk.X)

    def _do_font_mirror(self):
        ft = filedialog.askopenfilename(title="Select Font", filetypes=[("Font Files", "*.ttf *.otf")])
        if not ft: return
        
        dest_dir = self._get_font_dest()
        if not dest_dir:
            messagebox.showerror("Error", "Version directory not found!"); return

        try:
            count = 0
            for f in os.listdir(dest_dir):
                if f.lower().endswith((".ttf", ".otf")):
                    shutil.copy2(ft, os.path.join(dest_dir, f))
                    count += 1
            messagebox.showinfo("Success", f"Replaced {count} fonts.")
        except Exception as e: 
            messagebox.showerror("Error", str(e))

class EditCursorPage(BasePage):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.selected_ver = tk.StringVar(value=PEKORA_2021M_FOLDER)

    def _set_ver(self, v):
        self.selected_ver.set(v)
        self.on_show()

    def _get_cursor_dest(self):
        roots = [
            os.path.expandvars(r"%localappdata%\ProjectX\Versions"),
            os.path.expandvars(r"%localappdata%\Pekora\Versions")
        ]
        for root in roots:
            cursor_dir = os.path.join(root, PEKORA_VERSION_HASH, self.selected_ver.get(), 
                                      PEKORA_TEXT_SUBPATH, "Cursors", "KeyboardMouse")
            if os.path.isdir(cursor_dir):
                return cursor_dir
        return None

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("Cursor Settings", "Direct replacement (64x64)")
        
        card = tk.Frame(self, bg=self.app.theme["surface"], padx=20, pady=20)
        card.pack(fill=tk.X, padx=24)

        v_box = tk.Frame(card, bg=self.app.theme["surface"])
        v_box.pack(fill=tk.X, pady=(0, 20))
        for text, val in [("2021 Client", PEKORA_2021M_FOLDER), ("2020 Client", PEKORA_2020L_FOLDER)]:
            is_sel = (val == self.selected_ver.get())
            tk.Button(v_box, text=text, font=self.app.f_main, 
                      bg=self.app.theme["accent"] if is_sel else self.app.theme["bg"],
                      fg=self.app.theme["active_text"] if is_sel else self.app.theme["text"],
                      bd=0, padx=20, cursor="hand2",
                      command=lambda v=val: self._set_ver(v)).pack(side=tk.LEFT, padx=2)

        self._btn(card, "🖱 Select Image & Apply", self._do_cursor_replace).pack(fill=tk.X)

    def _do_cursor_replace(self):
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow required!"); return
            
        img_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not img_path: return

        cursor_dir = self._get_cursor_dest()
        if not cursor_dir:
            messagebox.showerror("Error", "Cursor folder not found!"); return

        try:
            img = Image.open(img_path).resize((64, 64), Image.Resampling.LANCZOS)
            for name in ["ArrowCursor.png", "ArrowFarCursor.png"]:
                img.save(os.path.join(cursor_dir, name), "PNG")
            messagebox.showinfo("Success", "Cursor updated.")
        except Exception as e: 
            messagebox.showerror("Error", str(e))
            
class CreditsPage(BasePage):
    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._title("Credits", f"Running version {VERSION}")
        c = tk.Frame(self, bg=self.app.theme["surface"], padx=20, pady=20); c.pack(fill=tk.X, padx=24)
        tk.Label(c, text="VMDX1337 - Lead Developer\nPonuss - UI Design", font=self.app.f_lg, fg=self.app.theme["accent"], bg=self.app.theme["surface"]).pack(anchor="w")
        tk.Label(self, text="github.com/vmdx1337/KoroneVoidStrap", font=self.app.f_sm, fg=self.app.theme["muted"], bg=self.app.theme["bg"]).pack(side=tk.BOTTOM, pady=20)

if __name__ == "__main__":
    KoroneVoidStrap().mainloop()