import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pygame
import time
import json
import os
import sys
import subprocess
import urllib.request

try:
    import ctypes
except ImportError:
    ctypes = None

from pynput.keyboard import Controller as KeyboardController, Key
from pynput.mouse import Controller as MouseController, Button, Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener

def is_admin():
    """Check if the script is running with administrative privileges."""
    if ctypes:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    return False

def check_pip_module(module_name):
    """Check if a pip module is installed."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

class ControllerMapper:
    def __init__(self):
        # --- Pathing Setup ---
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        self.presets_path = os.path.join(self.base_path, 'presets')
        self.profiles_path = os.path.join(self.base_path, 'profiles')
        self.last_profile_file = os.path.join(self.base_path, 'last_profile.txt')
        self.drivers_path = os.path.join(self.base_path, 'drivers')

        pygame.init()
        pygame.joystick.init()

        self.keyboard = KeyboardController()
        self.mouse = MouseController()

        self.running = True
        self.joystick = None
        self.joystick_info = {}
        self.controller_thread = None
        self.key_capture_mode = False
        self.capturing_for = None
        self.directional_key_state = {}
        
        self.modes = ['on_foot', 'ground_vehicle', 'flight']
        self.current_mode = 'on_foot'

        self.settings = self._get_default_settings()
        self.mappings = self._get_default_mappings()
        self.presets = {}

        self.controller_state = {'buttons': {}, 'axes': {}, 'hats': {}}
        self.prev_state = {'buttons': {}, 'axes': {}}

        self.key_map = {
            'space': Key.space, 'enter': Key.enter, 'escape': Key.esc, 'tab': Key.tab, 
            'shift': Key.shift, 'ctrl': Key.ctrl, 'alt': Key.alt, 'backspace': Key.backspace,
            'delete': Key.delete, 'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12
        }
        
        self._scan_for_presets()
        self.setup_gui()
        self.load_profile()
        self.start_controller_thread()

    def _get_default_settings(self):
        return {
            'profile_name': 'Default',
            'mode_bindings': {'cycle': '', 'on_foot': '', 'ground_vehicle': '', 'flight': ''},
            'on_foot': {'mouse_sensitivity': 5.0, 'mouse_acceleration': False, 'invert_axes': {}},
            'ground_vehicle': {'mouse_sensitivity': 8.0, 'mouse_acceleration': False, 'invert_axes': {}},
            'flight': {'mouse_sensitivity': 12.0, 'mouse_acceleration': True, 'invert_axes': {}},
            'global': {'deadzone': 0.15, 'axis_to_button_threshold': 0.75}
        }

    def _get_default_mappings(self):
        base = {}
        for i in range(32): base[f'button_{i}'] = ""
        for i in range(8):
            base[f'axis_{i}'] = ""
        for i in range(4):
            base[f'hat_{i}_up'] = ""
            base[f'hat_{i}_down'] = ""
            base[f'hat_{i}_left'] = ""
            base[f'hat_{i}_right'] = ""
        return {mode: base.copy() for mode in self.modes}

    def _scan_for_presets(self):
        if not os.path.exists(self.presets_path):
            os.makedirs(self.presets_path)
            print(f"Created '{self.presets_path}' directory.")
        
        for filename in os.listdir(self.presets_path):
            if filename.endswith('.json'):
                preset_name = os.path.splitext(filename)[0]
                self.presets[preset_name] = os.path.join(self.presets_path, filename)

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Uni-Mapper v7.0")
        self.root.geometry("1200x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=10)
        ttk.Label(header_frame, text="Uni-Mapper +Plus", font=("Helvetica", 18, "bold")).pack()
        ttk.Label(header_frame, text="Author: Asterisk", font=("Helvetica", 10)).pack()

        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.setup_mapping_tab()
        self.setup_settings_tab()
        self.setup_drivers_tab()
        self.setup_visualization_tab()
        self.setup_status_tab()
        
        if ctypes:
            admin_frame = ttk.Frame(self.root)
            admin_frame.pack(side='bottom', fill='x', pady=5, padx=10)
            text, fg, cur = ("Running as Administrator", "green", "arrow") if is_admin() else ("Click here to run as Administrator for game compatibility.", "blue", "hand2")
            admin_label = ttk.Label(admin_frame, text=text, foreground=fg, cursor=cur)
            admin_label.pack()
            if not is_admin():
                admin_label.bind("<Button-1>", self.run_as_admin)

    def setup_mapping_tab(self):
        self.mapping_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.mapping_frame, text="Mappings & Profiles")
        
        self.mode_notebook = ttk.Notebook(self.mapping_frame)
        self.mode_notebook.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        self.mapping_widgets = {mode: {} for mode in self.modes}

        # Placeholder until a controller is detected
        for mode, title in [('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]:
            tab_frame = ttk.Frame(self.mode_notebook)
            self.mode_notebook.add(tab_frame, text=title)
            ttk.Label(tab_frame, text="Connect a controller and press 'Refresh Controllers' in the Status tab.").pack(padx=20, pady=20)

        right_pane = ttk.Frame(self.mapping_frame, width=250)
        right_pane.pack(side='right', fill='y', padx=5, pady=5)
        
        profile_frame = ttk.LabelFrame(right_pane, text="Profiles", padding=10)
        profile_frame.pack(fill='x', pady=5)
        ttk.Label(profile_frame, text="Profile Name:").pack(anchor='w')
        self.profile_var = tk.StringVar()
        ttk.Entry(profile_frame, textvariable=self.profile_var).pack(fill='x', pady=2)
        ttk.Button(profile_frame, text="Save Profile", command=self.save_profile).pack(fill='x', pady=2)
        ttk.Button(profile_frame, text="Load Profile from File...", command=self._browse_and_load_profile).pack(fill='x', pady=2)
        
        preset_frame = ttk.LabelFrame(right_pane, text="Game Presets", padding=10)
        preset_frame.pack(fill='x', pady=5)
        self.preset_combo = ttk.Combobox(preset_frame, values=list(self.presets.keys()), state='readonly')
        self.preset_combo.pack(fill='x', pady=2)
        if self.presets:
            self.preset_combo.current(0)
        ttk.Button(preset_frame, text="Load Selected Preset", command=self._load_selected_preset).pack(fill='x', pady=2)

        control_frame = ttk.LabelFrame(right_pane, text="Controls", padding=10)
        control_frame.pack(fill='x', pady=5)
        self.enable_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Enable Mapping", variable=self.enable_var).pack(anchor='w')

    def rebuild_mapping_ui(self):
        for i in reversed(range(self.mode_notebook.index('end'))):
            self.mode_notebook.forget(i)
        
        self.mapping_widgets = {mode: {} for mode in self.modes}

        for mode, title in [('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]:
            tab_frame = ttk.Frame(self.mode_notebook)
            self.mode_notebook.add(tab_frame, text=title)
            self._create_mode_mapping_ui(tab_frame, mode)
        
        self._update_gui_from_data()

    def _create_mode_mapping_ui(self, parent, mode):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        num_buttons = self.joystick_info.get('buttons', 0)
        num_axes = self.joystick_info.get('axes', 0)
        num_hats = self.joystick_info.get('hats', 0)

        if num_buttons == 0 and num_axes == 0 and num_hats == 0:
             ttk.Label(scrollable_frame, text="No controller detected. Please connect one and refresh.").pack(padx=20, pady=20)
             return

        btn_frame = ttk.LabelFrame(scrollable_frame, text=f"Buttons (0-{num_buttons-1})", padding=10)
        btn_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=5)
        for i in range(num_buttons):
            self._create_mapping_row(btn_frame, f"{mode}_button_{i}", f"Button {i}", i, self.mappings[mode], self.mapping_widgets[mode])

        axe_frame = ttk.LabelFrame(scrollable_frame, text=f"Axes (0-{num_axes-1})", padding=10)
        axe_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        for i in range(num_axes):
            self._create_mapping_row(axe_frame, f"{mode}_axis_{i}", f"Axis {i}", i, self.mappings[mode], self.mapping_widgets[mode])
        
        hat_frame = ttk.LabelFrame(scrollable_frame, text=f"POV Hats (0-{num_hats-1})", padding=10)
        hat_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=5)
        for i in range(num_hats):
             self._create_mapping_row(hat_frame, f"{mode}_hat_{i}_up", f"Hat {i} Up", i*4, self.mappings[mode], self.mapping_widgets[mode])
             self._create_mapping_row(hat_frame, f"{mode}_hat_{i}_down", f"Hat {i} Down", i*4+1, self.mappings[mode], self.mapping_widgets[mode])
             self._create_mapping_row(hat_frame, f"{mode}_hat_{i}_left", f"Hat {i} Left", i*4+2, self.mappings[mode], self.mapping_widgets[mode])
             self._create_mapping_row(hat_frame, f"{mode}_hat_{i}_right", f"Hat {i} Right", i*4+3, self.mappings[mode], self.mapping_widgets[mode])

    def _create_mapping_row(self, parent, widget_key, button_name, row, mapping_dict, widget_dict):
        ttk.Label(parent, text=f"{button_name}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
        var = tk.StringVar(value=mapping_dict.get(button_name, ''))
        entry = ttk.Entry(parent, textvariable=var, width=30)
        entry.grid(row=row, column=1, padx=5, pady=2)
        capture_btn = ttk.Button(parent, text="Capture", command=lambda k=widget_key: self.start_key_capture(k))
        capture_btn.grid(row=row, column=2, padx=5, pady=2)
        clear_btn = ttk.Button(parent, text="Clear", command=lambda k=widget_key: self.clear_mapping(k))
        clear_btn.grid(row=row, column=3, padx=5, pady=2)
        widget_dict[button_name] = {'var': var, 'entry': entry, 'capture_btn': capture_btn}

    def setup_settings_tab(self):
        sf = ttk.Frame(self.main_notebook)
        self.main_notebook.add(sf, text="Settings")
        lp = ttk.Frame(sf)
        lp.pack(side='left', fill='both', expand=True, padx=5)
        gf = ttk.LabelFrame(lp, text="Global Settings", padding=10)
        gf.pack(fill='x', pady=5)
        
        self.setting_vars = {'global': {}}
        self._create_slider(gf, "Axis Deadzone", 'deadzone', 0.0, 1.0, self.settings['global'], self.setting_vars['global'])
        self._create_slider(gf, "Axis to Button Threshold", 'axis_to_button_threshold', 0.1, 1.0, self.settings['global'], self.setting_vars['global'])
        
        mf = ttk.LabelFrame(lp, text="Mode Switching Hotkeys", padding=10)
        mf.pack(fill='x', pady=5)
        self.mode_binding_widgets = {}
        for i, (k, l) in enumerate([('cycle', 'Cycle Modes'), ('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]):
            self._create_mapping_row(mf, f"mode_{k}", l, i, self.settings['mode_bindings'], self.mode_binding_widgets)
        
        rp = ttk.Frame(sf)
        rp.pack(side='right', fill='both', expand=True, padx=5)
        msn = ttk.Notebook(rp)
        msn.pack(fill='both', expand=True, pady=5)
        
        for mode, title in [('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]:
            self.setting_vars[mode] = {'invert_axes': {}}
            mt = ttk.Frame(msn)
            msn.add(mt, text=title)
            sens_f = ttk.LabelFrame(mt, text="Sensitivity", padding=10)
            sens_f.pack(fill='x', pady=5)
            self._create_slider(sens_f, 'Mouse Sensitivity', 'mouse_sensitivity', 0.1, 30.0, self.settings[mode], self.setting_vars[mode])
            
            var = tk.BooleanVar(value=self.settings[mode].get('mouse_acceleration', False))
            ttk.Checkbutton(sens_f, text="Mouse Acceleration", variable=var).pack(anchor='w', pady=2)
            self.setting_vars[mode]['mouse_acceleration'] = var
            
            inv_f = ttk.LabelFrame(mt, text="Axis Inversion", padding=10)
            inv_f.pack(fill='x', pady=5)
            for i in range(8): # Max 8 axes
                var = tk.BooleanVar(value=self.settings[mode]['invert_axes'].get(str(i), False))
                ttk.Checkbutton(inv_f, text=f"Invert Axis {i}", variable=var).pack(anchor='w', pady=1)
                self.setting_vars[mode]['invert_axes'][str(i)] = var
                
        ttk.Button(rp, text="Apply All Settings", command=self.apply_settings).pack(pady=10)

    def _create_slider(self, p, l, k, mn, mx, sd, vd):
        ttk.Label(p, text=l).pack(anchor='w', pady=2)
        var = tk.DoubleVar(value=sd.get(k, 0.0))
        ttk.Scale(p, from_=mn, to=mx, variable=var, orient='horizontal').pack(fill='x', padx=10, pady=2)
        vl = ttk.Label(p, text=f"{var.get():.2f}")
        vl.pack(anchor='w', pady=2)
        var.trace('w', lambda n, i, m, v=var, l=vl: l.config(text=f"{v.get():.2f}"))
        vd[k] = var

    def setup_drivers_tab(self):
        df = ttk.Frame(self.main_notebook)
        self.main_notebook.add(df, text="Driver Management")

        drivers = {
            "ps4": {"name": "PS4 Controller Support (ps4-controller)", "pip_name": "ps4-controller", "check_name": "pyPS4Controller"},
            "dualsense": {"name": "PS5 DualSense Support (dualsense-controller)", "pip_name": "dualsense-controller", "check_name": "dualsense_controller"},
            "x52": {"name": "Logitech X52 HOTAS Drivers", "url": "https://download01.logi.com/web/ftp/pub/techsupport/simulation/X52_HOTAS_x64_8_0_213_0.exe"}
        }

        for key, info in drivers.items():
            frame = ttk.LabelFrame(df, text=info["name"], padding=10)
            frame.pack(fill='x', padx=10, pady=5)
            
            status_label = ttk.Label(frame, text="Status: Checking...")
            status_label.pack(side='left', padx=5)
            
            action_button = ttk.Button(frame, text="Install")
            action_button.pack(side='right', padx=5)

            if "pip_name" in info:
                is_installed = check_pip_module(info["check_name"])
                status_label.config(text=f"Status: {'Installed' if is_installed else 'Not Installed'}", foreground='green' if is_installed else 'red')
                if not is_installed:
                    action_button.config(command=lambda p=info["pip_name"], s=status_label, b=action_button: self.install_pip_package(p, s, b))
                else:
                    action_button.config(state='disabled')
            elif "url" in info:
                status_label.config(text="Status: Official driver installer.")
                progress = ttk.Progressbar(frame, orient='horizontal', length=200, mode='determinate')
                progress.pack(side='right', padx=5)
                progress.pack_forget() # Hide until needed
                action_button.config(text="Download & Install", command=lambda u=info["url"], s=status_label, b=action_button, p=progress: self.download_and_run_exe(u, s, b, p))

    def install_pip_package(self, package_name, status_label, button):
        status_label.config(text="Status: Installing...", foreground='orange')
        button.config(state='disabled')
        threading.Thread(target=self._pip_install_worker, args=(package_name, status_label, button), daemon=True).start()

    def _pip_install_worker(self, package_name, status_label, button):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            self.root.after(0, lambda: status_label.config(text="Status: Installed", foreground='green'))
            self.log(f"Successfully installed {package_name}.")
        except subprocess.CalledProcessError as e:
            self.root.after(0, lambda: status_label.config(text="Status: Installation Failed", foreground='red'))
            self.root.after(0, lambda: button.config(state='normal'))
            self.log(f"Failed to install {package_name}. Error: {e}")

    def download_and_run_exe(self, url, status_label, button, progress_bar):
        status_label.config(text="Status: Downloading...", foreground='orange')
        button.config(state='disabled')
        progress_bar.pack(side='right', padx=5)
        threading.Thread(target=self._download_worker, args=(url, status_label, button, progress_bar), daemon=True).start()

    def _download_worker(self, url, status_label, button, progress_bar):
        try:
            if not os.path.exists(self.drivers_path):
                os.makedirs(self.drivers_path)
            
            filename = os.path.join(self.drivers_path, url.split('/')[-1])
            
            with urllib.request.urlopen(url) as response, open(filename, 'wb') as out_file:
                total_length = int(response.info().get('Content-Length'))
                progress_bar['maximum'] = total_length
                
                chunk_size = 8192
                bytes_read = 0
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk: break
                    out_file.write(chunk)
                    bytes_read += len(chunk)
                    progress_bar['value'] = bytes_read
                    self.root.update_idletasks()

            self.log(f"Downloaded '{os.path.basename(filename)}'.")
            self.root.after(0, lambda: status_label.config(text="Status: Download Complete. Running installer...", foreground='blue'))
            os.startfile(filename)
            self.root.after(5000, lambda: status_label.config(text="Status: Official driver installer.", foreground='black'))
            self.root.after(5000, lambda: button.config(state='normal'))
            self.root.after(5000, lambda: progress_bar.pack_forget())

        except Exception as e:
            self.log(f"Failed to download or run driver. Error: {e}")
            self.root.after(0, lambda: status_label.config(text="Status: Download Failed.", foreground='red'))
            self.root.after(0, lambda: button.config(state='normal'))
            self.root.after(0, lambda: progress_bar.pack_forget())

    def setup_visualization_tab(self):
        vf = ttk.Frame(self.main_notebook)
        self.main_notebook.add(vf, text="Visualization")
        self.canvas = tk.Canvas(vf, width=800, height=600, bg='black')
        self.canvas.pack(pady=10, fill='both', expand=True)

    def setup_status_tab(self):
        sf=ttk.Frame(self.main_notebook)
        self.main_notebook.add(sf,text="Status")
        cf=ttk.LabelFrame(sf,text="Controller Information", padding=10)
        cf.pack(fill='x',padx=10,pady=5)
        self.controller_info=tk.Text(cf,height=6, width=80)
        self.controller_info.pack(fill='both',expand=True,padx=5,pady=5)
        ttk.Button(cf, text="Refresh Controllers", command=self.refresh_controllers).pack(pady=5)
        
        lf=ttk.LabelFrame(sf,text="Activity Log", padding=10)
        lf.pack(fill='both',expand=True,padx=10,pady=5)
        self.log_text=tk.Text(lf,height=15)
        self.log_text.pack(fill='both',expand=True,padx=5,pady=5)
        ls=ttk.Scrollbar(lf,orient='vertical',command=self.log_text.yview)
        ls.pack(side='right',fill='y')
        self.log_text.config(yscrollcommand=ls.set)
    
    def refresh_controllers(self):
        self.log("Refreshing controller list...")
        pygame.joystick.quit()
        time.sleep(0.5)
        pygame.joystick.init()
        self.joystick = None

    def start_key_capture(self, wk):
        self.capturing_for = wk
        self.key_capture_mode = True
        
        parts = wk.split('_')
        mode, btn_key = parts[0], '_'.join(parts[1:])
        
        widgets = self.mode_binding_widgets if mode == 'mode' else self.mapping_widgets[mode]
        widgets[btn_key]['capture_btn'].config(text="Press key...", state='disabled')
        self.log(f"Capturing for {btn_key} in mode {mode}...")

        def on_press(key):
            if self.key_capture_mode and self.capturing_for == wk:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                self.update_mapping(wk, key_name)
                return False
        
        def on_click(x, y, b, p):
            if p and self.key_capture_mode and self.capturing_for == wk:
                key_name = {Button.left: 'mouse_left', Button.right: 'mouse_right', Button.middle: 'mouse_middle'}.get(b)
                if key_name: self.update_mapping(wk, key_name)
                return False

        self.key_listener = KeyboardListener(on_press=on_press)
        self.mouse_listener = MouseListener(on_click=on_click)
        self.key_listener.start()
        self.mouse_listener.start()
        self.root.after(10000, lambda: self.stop_key_capture() if self.key_capture_mode else None)

    def update_mapping(self, wk, kn):
        parts = wk.split('_')
        mode, btn_key = parts[0], '_'.join(parts[1:])
        
        if mode == 'mode':
            self.settings['mode_bindings'][btn_key] = kn
            self.mode_binding_widgets[btn_key]['var'].set(kn)
        else:
            self.mappings[mode][btn_key] = kn
            self.mapping_widgets[mode][btn_key]['var'].set(kn)
        
        self.log(f"Mapped {btn_key} to {kn} for mode {mode}")
        self.stop_key_capture()

    def stop_key_capture(self):
        if hasattr(self, 'key_listener'): self.key_listener.stop()
        if hasattr(self, 'mouse_listener'): self.mouse_listener.stop()
        self.key_capture_mode = False
        if self.capturing_for:
            parts = self.capturing_for.split('_')
            mode, btn_key = parts[0], '_'.join(parts[1:])
            widgets = self.mode_binding_widgets if mode == 'mode' else self.mapping_widgets[mode]
            if btn_key in widgets:
                widgets[btn_key]['capture_btn'].config(text="Capture", state='normal')
            self.capturing_for = None
    
    def clear_mapping(self, wk):
        parts = wk.split('_')
        mode, btn_key = parts[0], '_'.join(parts[1:])
        
        if mode == 'mode':
            self.settings['mode_bindings'][btn_key] = ''
            self.mode_binding_widgets[btn_key]['var'].set('')
        else:
            self.mappings[mode][btn_key] = ''
            self.mapping_widgets[mode][btn_key]['var'].set('')
        self.log(f"Cleared mapping for {btn_key} in mode {mode}")

    def apply_settings(self):
        for k, v in self.setting_vars['global'].items():
            self.settings['global'][k] = v.get()
        
        for mode in self.modes:
            self.settings[mode]['mouse_sensitivity'] = self.setting_vars[mode]['mouse_sensitivity'].get()
            self.settings[mode]['mouse_acceleration'] = self.setting_vars[mode]['mouse_acceleration'].get()
            for i, v in self.setting_vars[mode]['invert_axes'].items():
                self.settings[mode]['invert_axes'][i] = v.get()
        
        self.log("Applied all settings")
        self.save_profile()

    def save_profile(self):
        profile_name = self.profile_var.get()
        if not profile_name:
            messagebox.showerror("Error", "Please enter a profile name")
            return
        
        self.settings['profile_name'] = profile_name
        
        for mode in self.modes:
            for bn, wd in self.mapping_widgets[mode].items():
                self.mappings[mode][bn] = wd['var'].get()
        
        for bn, wd in self.mode_binding_widgets.items():
            self.settings['mode_bindings'][bn] = wd['var'].get()
        
        try:
            os.makedirs(self.profiles_path, exist_ok=True)
            profile_path = os.path.join(self.profiles_path, f'{profile_name}.json')
            with open(profile_path, 'w') as f:
                json.dump({'settings': self.settings, 'mappings': self.mappings}, f, indent=4)
            
            self.log(f"Saved profile: {profile_name}")
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

    def _browse_and_load_profile(self):
        filename = filedialog.askopenfilename(initialdir=self.profiles_path, title="Select Profile", filetypes=[("JSON files", "*.json")])
        if filename:
            self.load_profile(filename)

    def _load_selected_preset(self):
        preset_name = self.preset_combo.get()
        if not preset_name:
            messagebox.showwarning("Warning", "No preset selected.")
            return
        self.load_profile(self.presets[preset_name], is_preset=True)

    def load_profile(self, filename=None, is_preset=False):
        if filename is None:
            if os.path.exists(self.last_profile_file):
                with open(self.last_profile_file, 'r') as f:
                    filename = f.read().strip()
            if not filename or not os.path.exists(filename):
                self.settings = self._get_default_settings()
                self.mappings = self._get_default_mappings()
                self._update_gui_from_data()
                return
        
        if not os.path.exists(filename):
            messagebox.showerror("Error", f"Profile not found: {filename}")
            if os.path.exists(self.last_profile_file):
                os.remove(self.last_profile_file)
            return
        
        try:
            with open(filename, 'r') as f: data = json.load(f)
            self.settings = self._merge_dicts(self._get_default_settings(), data.get('settings', {}))
            self.mappings = self._merge_dicts(self._get_default_mappings(), data.get('mappings', {}))
            self._update_gui_from_data()
            if not is_preset:
                with open(self.last_profile_file, 'w') as f: f.write(filename)
            msg_type = "Preset" if is_preset else "Profile"
            self.log(f"Loaded {msg_type}: {self.settings['profile_name']}")
            messagebox.showinfo("Success", f"{msg_type} '{self.settings['profile_name']}' loaded!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def _update_gui_from_data(self):
        self.profile_var.set(self.settings.get('profile_name', 'Default'))
        for mode in self.modes:
            for bn, m in self.mappings[mode].items():
                if bn in self.mapping_widgets.get(mode, {}):
                    self.mapping_widgets[mode][bn]['var'].set(m)
        for bn, m in self.settings['mode_bindings'].items():
            if bn in self.mode_binding_widgets:
                self.mode_binding_widgets[bn]['var'].set(m)
        
        for k, v in self.settings['global'].items():
            if k in self.setting_vars['global']:
                self.setting_vars['global'][k].set(v)

        for mode in self.modes:
            if mode in self.setting_vars:
                self.setting_vars[mode]['mouse_sensitivity'].set(self.settings[mode]['mouse_sensitivity'])
                self.setting_vars[mode]['mouse_acceleration'].set(self.settings[mode]['mouse_acceleration'])
                for i, v_var in self.setting_vars[mode]['invert_axes'].items():
                    v_var.set(self.settings[mode]['invert_axes'].get(i, False))
                    
    def _merge_dicts(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                d[k] = self._merge_dicts(d[k], v)
            else:
                d[k] = v
        return d

    def on_closing(self):
        self.running = False
        self.stop_key_capture()
        self.save_profile()
        if self.controller_thread and self.controller_thread.is_alive():
            time.sleep(0.1)
        self.root.destroy()
    
    def start_controller_thread(self):
        self.controller_thread = threading.Thread(target=self.controller_loop, daemon=True)
        self.controller_thread.start()

    def controller_loop(self):
        while self.running:
            try:
                pygame.event.pump()
                if not self.joystick and pygame.joystick.get_count() > 0:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.joystick_info = {
                        'name': self.joystick.get_name(),
                        'buttons': self.joystick.get_numbuttons(),
                        'axes': self.joystick.get_numaxes(),
                        'hats': self.joystick.get_numhats()
                    }
                    self.log(f"Connected: {self.joystick_info['name']}")
                    self.root.after(0, self.rebuild_mapping_ui)
                elif pygame.joystick.get_count() == 0 and self.joystick:
                    self.log(f"Disconnected: {self.joystick_info['name']}")
                    self.joystick = None
                    self.joystick_info = {}
                    self.root.after(0, self.rebuild_mapping_ui)

                if self.joystick:
                    self.update_controller_state()
                    if self.enable_var.get():
                        self.process_controller_input()
                    self.root.after(0, self.update_visualization)
                
                time.sleep(0.01)
            except Exception as e:
                self.log(f"Controller loop error: {e}")
                self.joystick = None
                time.sleep(1)

    def update_controller_state(self):
        if not self.joystick: return
        for i in range(self.joystick_info.get('buttons',0)): self.controller_state['buttons'][i] = self.joystick.get_button(i)
        for i in range(self.joystick_info.get('axes',0)): self.controller_state['axes'][i] = self.joystick.get_axis(i)
        for i in range(self.joystick_info.get('hats',0)): self.controller_state['hats'][i] = self.joystick.get_hat(i)

    def process_controller_input(self):
        if not self.joystick: return
        if self.process_mode_switches(): return
        self.process_buttons()
        self.process_axes()
        self.process_hats()
    
    def process_buttons(self):
        for i in range(self.joystick_info.get('buttons', 0)):
            pressed = self.controller_state['buttons'].get(i, 0)
            was_pressed = self.prev_state['buttons'].get(i, 0)
            if pressed != was_pressed:
                self.execute_key_action(self.mappings[self.current_mode].get(f'button_{i}'), pressed)
            self.prev_state['buttons'][i] = pressed
    
    def process_axes(self):
        gs = self.settings['global']
        ms = self.settings[self.current_mode]
        mouse_dx, mouse_dy = 0, 0

        for i in range(self.joystick_info.get('axes', 0)):
            axis_val = self.controller_state['axes'].get(i, 0.0)
            if ms['invert_axes'].get(str(i), False):
                axis_val = -axis_val
            
            action = self.mappings[self.current_mode].get(f'axis_{i}')

            if action == 'mouse_x_axis':
                if abs(axis_val) > gs['deadzone']: mouse_dx += axis_val
            elif action == 'mouse_y_axis':
                if abs(axis_val) > gs['deadzone']: mouse_dy += axis_val
            elif action == 'throttle_fwd':
                 self.update_directional_key_state('w', axis_val < -gs['deadzone']) # W for forward throttle
                 self.update_directional_key_state('s', False)
            elif action == 'throttle_rev':
                 self.update_directional_key_state('s', axis_val > gs['deadzone']) # S for reverse throttle
                 self.update_directional_key_state('w', False)
            else:
                threshold = gs['axis_to_button_threshold']
                pressed = axis_val > threshold
                was_pressed = self.prev_state.get('axes', {}).get(i, 0.0) > threshold
                if pressed != was_pressed:
                    self.execute_key_action(action, pressed)
            
            self.prev_state.setdefault('axes', {})[i] = axis_val
        
        if mouse_dx != 0 or mouse_dy != 0:
            sens = ms['mouse_sensitivity']
            fdx, fdy = mouse_dx * sens, mouse_dy * sens
            if ms['mouse_acceleration']:
                fdx *= abs(mouse_dx)
                fdy *= abs(mouse_dy)
            try: self.mouse.move(int(fdx), int(fdy))
            except: pass
            
    def process_hats(self):
        for i in range(self.joystick_info.get('hats', 0)):
            hat_val = self.controller_state['hats'].get(i, (0, 0))
            self.update_directional_key_state(f'hat_{i}_up', hat_val[1] == 1)
            self.update_directional_key_state(f'hat_{i}_down', hat_val[1] == -1)
            self.update_directional_key_state(f'hat_{i}_left', hat_val[0] == -1)
            self.update_directional_key_state(f'hat_{i}_right', hat_val[0] == 1)
        
    def process_mode_switches(self):
        for i in range(self.joystick_info.get('buttons', 0)):
            if self.controller_state['buttons'].get(i, 0) and not self.prev_state['buttons'].get(i, 0):
                button_name = f'button_{i}'
                for mode, bound_key in self.settings['mode_bindings'].items():
                    if button_name == bound_key:
                        if mode == 'cycle': self.cycle_mode()
                        else: self.switch_mode(mode)
                        return True
        return False
    
    def cycle_mode(self):
        current_index = self.modes.index(self.current_mode)
        next_index = (current_index + 1) % len(self.modes)
        self.switch_mode(self.modes[next_index])

    def switch_mode(self, new_mode):
        if new_mode in self.modes:
            self.current_mode = new_mode
            self.log(f"Switched to mode: {new_mode.replace('_', ' ').title()}")
        
    def update_directional_key_state(self, key_or_action, active):
        is_action = '_' in key_or_action
        
        action = self.mappings[self.current_mode].get(key_or_action) if is_action else key_or_action
        if not action: return
            
        prev_active = self.directional_key_state.get(key_or_action, False)
        if active != prev_active:
            self.execute_key_action(action, active)
        self.directional_key_state[key_or_action] = active
        
    def execute_key_action(self, actions, pressed):
        if not actions: return
        for action in actions.split(','):
            action = action.strip()
            try:
                if action.startswith('mouse_') and not action.startswith('mouse_move_'):
                    button = {'mouse_left': Button.left, 'mouse_right': Button.right, 'mouse_middle': Button.middle}.get(action)
                    if button: (self.mouse.press if pressed else self.mouse.release)(button)
                else:
                    key = self.key_map.get(action, action if len(action) == 1 else None)
                    if key: (self.keyboard.press if pressed else self.keyboard.release)(key)
            except Exception as e:
                self.log(f"Error executing action '{action}': {e}")

    def update_visualization(self):
        if not hasattr(self, 'canvas'): return
        self.canvas.delete("all")
        if not self.joystick_info: return
        
        cols = 4
        width = 800 / cols
        height = 60
        
        for i in range(self.joystick_info.get('axes', 0)):
            row, col = divmod(i, cols)
            x, y = col * width, row * height
            axis_val = self.controller_state['axes'].get(i, 0.0)
            self._draw_axis(x + 10, y + 10, width - 20, height - 20, f"Axis {i}", axis_val)

        self.canvas.create_text(400, 580, text=f"Current Mode: {self.current_mode.replace('_', ' ').title()}", fill="white", font=("Helvetica", 12, "bold"))

    def _draw_axis(self, x, y, w, h, label, value):
        self.canvas.create_text(x + w / 2, y + h - 5, text=label, fill='white')
        # Background bar
        self.canvas.create_rectangle(x, y, x + w, y + h - 15, outline='grey')
        # Value bar
        fill_w = (value + 1) / 2 * w
        self.canvas.create_rectangle(x, y, x + fill_w, y + h - 15, fill='cyan', outline='')
        # Center line
        self.canvas.create_line(x + w / 2, y, x + w / 2, y + h - 15, fill='red')

    def log(self, message):
        log_msg = f"[{time.strftime('%H:%M:%S')}] {message}\n"
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_msg)
            self.log_text.see(tk.END)
        print(log_msg.strip())

    def update_controller_info(self, info):
        self.controller_info.delete(1.0, tk.END)
        self.controller_info.insert(tk.END, info)
        if self.joystick_info:
             self.controller_info.insert(tk.END, f"\nButtons: {self.joystick_info['buttons']}, Axes: {self.joystick_info['axes']}, Hats: {self.joystick_info['hats']}")

    def run_as_admin(self, *args):
        if ctypes and not is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                self.log("Attempting to restart as admin...")
                self.on_closing()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to elevate privileges: {e}")

    def run(self):
        self.log("Uni-Mapper v7.0")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = ControllerMapper()
        app.run()
    except Exception as e:
        messagebox.showerror("Fatal Error", str(e))

