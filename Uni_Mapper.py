import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pygame
import time
import json
import os
import sys
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

class ControllerMapper:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()

        self.keyboard = KeyboardController()
        self.mouse = MouseController()

        self.running = True
        self.joystick = None
        self.controller_thread = None
        self.key_capture_mode = False
        self.capturing_for = None
        self.directional_key_state = {}
        
        self.modes = ['on_foot', 'ground_vehicle', 'flight']
        self.current_mode = 'on_foot'

        self.settings = self._get_default_settings()
        self.mappings = self._get_default_mappings()
        self.presets = {} # To store discovered presets {name: path}

        self.controller_state = {'buttons': {}, 'axes': {}, 'hat': (0, 0)}
        self.prev_state = {'buttons': {}, 'triggers': {}}

        self.key_map = {
            'space': Key.space, 'enter': Key.enter, 'escape': Key.esc, 'tab': Key.tab, 
            'shift': Key.shift, 'ctrl': Key.ctrl, 'alt': Key.alt, 'backspace': Key.backspace,
            'delete': Key.delete, 'up': Key.up, 'down': Key.down, 'left': Key.left, 'right': Key.right,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4, 'f5': Key.f5, 'f6': Key.f6,
            'f7': Key.f7, 'f8': Key.f8, 'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12
        }
        
        self._scan_for_presets()
        self.setup_gui()
        self.load_profile() # Load last used profile or defaults
        self.start_controller_thread()

    def _get_default_settings(self):
        return {
            'profile_name': 'Default',
            'mode_bindings': {'cycle': 'GUIDE', 'on_foot': '', 'ground_vehicle': '', 'flight': ''},
            'on_foot': {'mouse_sensitivity': 5.0, 'mouse_acceleration': False, 'invert_left_x': False, 'invert_left_y': False, 'invert_right_x': False, 'invert_right_y': False},
            'ground_vehicle': {'mouse_sensitivity': 8.0, 'mouse_acceleration': False, 'invert_left_x': False, 'invert_left_y': False, 'invert_right_x': False, 'invert_right_y': False},
            'flight': {'mouse_sensitivity': 12.0, 'mouse_acceleration': True, 'invert_left_x': False, 'invert_left_y': False, 'invert_right_x': False, 'invert_right_y': True},
            'global': {'deadzone_left': 0.25, 'deadzone_right': 0.25, 'deadzone_trigger': 0.1, 'auto_center_left': True, 'auto_center_right': True}
        }

    def _get_default_mappings(self):
        base = {
            'LEFT_STICK_UP': 'w', 'LEFT_STICK_DOWN': 's', 'LEFT_STICK_LEFT': 'a', 'LEFT_STICK_RIGHT': 'd',
            'RIGHT_STICK_UP': 'mouse_move_up', 'RIGHT_STICK_DOWN': 'mouse_move_down', 'RIGHT_STICK_LEFT': 'mouse_move_left', 'RIGHT_STICK_RIGHT': 'mouse_move_right',
            'DPAD_UP': 'up', 'DPAD_DOWN': 'down', 'DPAD_LEFT': 'left', 'DPAD_RIGHT': 'right',
            'A': 'space', 'B': 'escape', 'X': 'e', 'Y': 'q', 'LB': 'shift', 'RB': 'ctrl',
            'LT': 'mouse_left', 'RT': 'mouse_right', 'START': 'enter', 'BACK': 'tab', 'GUIDE': '',
            'LEFT_STICK_CLICK': 'c', 'RIGHT_STICK_CLICK': 'v'
        }
        return {mode: base.copy() for mode in self.modes}

    def _scan_for_presets(self):
        preset_dir = 'presets'
        if not os.path.exists(preset_dir):
            os.makedirs(preset_dir)
            # Cannot log here as GUI is not set up yet
            print(f"Created '{preset_dir}' directory for game presets.")
        
        for filename in os.listdir(preset_dir):
            if filename.endswith('.json'):
                preset_name = os.path.splitext(filename)[0]
                self.presets[preset_name] = os.path.join(preset_dir, filename)
        
        if self.presets:
            print(f"Found presets: {', '.join(self.presets.keys())}")
        else:
            print("No presets found. You can add .json files to the 'presets' folder.")

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Uni-Mapper v4.0")
        self.root.geometry("1100x900")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        header_frame = ttk.Frame(self.root)
        header_frame.pack(pady=10)
        ttk.Label(header_frame, text="Uni-Mapper v4.0", font=("Helvetica", 18, "bold")).pack()
        ttk.Label(header_frame, text="Author: Asterisk", font=("Helvetica", 10)).pack()

        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.setup_mapping_tab()
        self.setup_settings_tab()
        self.setup_visualization_tab()
        self.setup_status_tab()
        
        if ctypes:
            admin_frame = ttk.Frame(self.root)
            admin_frame.pack(side='bottom', fill='x', pady=5, padx=10)
            if is_admin():
                admin_text, fg, cursor = "Running as Administrator", "green", "arrow"
            else:
                admin_text, fg, cursor = "If events are not seen by a game, please click here to run as Administrator.", "blue", "hand2"
            
            admin_label = ttk.Label(admin_frame, text=admin_text, foreground=fg, cursor=cursor)
            admin_label.pack()
            if not is_admin():
                admin_label.bind("<Button-1>", self.run_as_admin)

    def setup_mapping_tab(self):
        mapping_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(mapping_frame, text="Mappings & Profiles")
        
        # --- Left Side: Control Mode Tabs ---
        mode_notebook = ttk.Notebook(mapping_frame)
        mode_notebook.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        self.mapping_widgets = {mode: {} for mode in self.modes}

        for mode, title in [('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]:
            tab_frame = ttk.Frame(mode_notebook)
            mode_notebook.add(tab_frame, text=title)
            self._create_mode_mapping_ui(tab_frame, mode)

        # --- Right Side: Profiles and Presets ---
        right_pane = ttk.Frame(mapping_frame, width=250)
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
        
    def _create_mode_mapping_ui(self, parent, mode):
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        control_groups = {
            "Sticks": ['LEFT_STICK_UP', 'LEFT_STICK_DOWN', 'LEFT_STICK_LEFT', 'LEFT_STICK_RIGHT', 'RIGHT_STICK_UP', 'RIGHT_STICK_DOWN', 'RIGHT_STICK_LEFT', 'RIGHT_STICK_RIGHT', 'LEFT_STICK_CLICK', 'RIGHT_STICK_CLICK'],
            "D-Pad": ['DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT'], 
            "Face Buttons": ['A', 'B', 'X', 'Y'],
            "Shoulders & Triggers": ['LB', 'RB', 'LT', 'RT'], 
            "Menu Buttons": ['START', 'BACK', 'GUIDE']
        }
        
        for i, (group_title, buttons) in enumerate(control_groups.items()):
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_title, padding=10)
            group_frame.grid(row=i, column=0, sticky='ew', padx=10, pady=5)
            for j, button_name in enumerate(buttons):
                self._create_mapping_row(group_frame, f"{mode}_{button_name}", button_name, j, self.mappings[mode], self.mapping_widgets[mode])

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
        self.deadzone_vars = {}
        self.autocenter_vars = {}
        for l, k, mn, mx in [('Left Stick DZ', 'deadzone_left', 0.0, 0.5), ('Right Stick DZ', 'deadzone_right', 0.0, 0.5), ('Trigger DZ', 'deadzone_trigger', 0.0, 0.3)]:
            self._create_slider(gf, l, k, mn, mx, self.settings['global'], self.deadzone_vars)
        for l, k in [('Auto-center Left Stick', 'auto_center_left'), ('Auto-center Right Stick', 'auto_center_right')]:
            var = tk.BooleanVar(value=self.settings['global'].get(k, True))
            ttk.Checkbutton(gf, text=l, variable=var).pack(anchor='w', pady=2)
            self.autocenter_vars[k] = var
        mf = ttk.LabelFrame(lp, text="Mode Switching Hotkeys", padding=10)
        mf.pack(fill='x', pady=5)
        self.mode_binding_widgets = {}
        for i, (k, l) in enumerate([('cycle', 'Cycle Modes'), ('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]):
            self._create_mapping_row(mf, f"mode_{k}", l, i, self.settings['mode_bindings'], self.mode_binding_widgets)
        
        rp = ttk.Frame(sf)
        rp.pack(side='right', fill='both', expand=True, padx=5)
        msn = ttk.Notebook(rp)
        msn.pack(fill='both', expand=True, pady=5)
        self.sensitivity_vars = {}
        self.accel_vars = {}
        self.invert_vars = {}
        for mode, title in [('on_foot', 'On Foot'), ('ground_vehicle', 'Ground Vehicle'), ('flight', 'Flight')]:
            mt = ttk.Frame(msn)
            msn.add(mt, text=title)
            sens_f = ttk.LabelFrame(mt, text="Sensitivity", padding=10)
            sens_f.pack(fill='x', pady=5)
            self.sensitivity_vars[mode] = {}
            self._create_slider(sens_f, 'Mouse Sensitivity', 'mouse_sensitivity', 0.1, 30.0, self.settings[mode], self.sensitivity_vars[mode])
            self.accel_vars[mode] = tk.BooleanVar(value=self.settings[mode].get('mouse_acceleration', False))
            ttk.Checkbutton(sens_f, text="Mouse Acceleration", variable=self.accel_vars[mode]).pack(anchor='w', pady=2)
            inv_f = ttk.LabelFrame(mt, text="Axis Inversion", padding=10)
            inv_f.pack(fill='x', pady=5)
            self.invert_vars[mode] = {}
            for l, k in [('Invert Left X', 'invert_left_x'), ('Invert Left Y', 'invert_left_y'), ('Invert Right X', 'invert_right_x'), ('Invert Right Y', 'invert_right_y')]:
                var = tk.BooleanVar(value=self.settings[mode].get(k, False))
                ttk.Checkbutton(inv_f, text=l, variable=var).pack(anchor='w', pady=2)
                self.invert_vars[mode][k] = var
        ttk.Button(rp, text="Apply All Settings", command=self.apply_settings).pack(pady=10)

    def _create_slider(self, p, l, k, mn, mx, sd, vd):
        ttk.Label(p, text=l).pack(anchor='w', pady=2)
        var = tk.DoubleVar(value=sd.get(k, 0.0))
        ttk.Scale(p, from_=mn, to=mx, variable=var, orient='horizontal').pack(fill='x', padx=10, pady=2)
        vl = ttk.Label(p, text=f"{var.get():.2f}")
        vl.pack(anchor='w', pady=2)
        var.trace('w', lambda n, i, m, v=var, l=vl: l.config(text=f"{v.get():.2f}"))
        vd[k] = var

    def setup_visualization_tab(self):
        vf = ttk.Frame(self.main_notebook)
        self.main_notebook.add(vf, text="Visualization")
        self.canvas = tk.Canvas(vf, width=600, height=400, bg='black')
        self.canvas.pack(pady=10)

    def setup_status_tab(self):
        sf = ttk.Frame(self.main_notebook)
        self.main_notebook.add(sf, text="Status")
        cf = ttk.LabelFrame(sf, text="Controller Information")
        cf.pack(fill='x', padx=10, pady=5)
        self.controller_info = tk.Text(cf, height=10)
        self.controller_info.pack(fill='both', expand=True, padx=5, pady=5)
        lf = ttk.LabelFrame(sf, text="Activity Log")
        lf.pack(fill='both', expand=True, padx=10, pady=5)
        self.log_text = tk.Text(lf, height=15)
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        ls = ttk.Scrollbar(lf, orient='vertical', command=self.log_text.yview)
        ls.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=ls.set)

    def start_key_capture(self, wk):
        self.capturing_for = wk
        self.key_capture_mode = True
        mode, btn = wk.split('_', 1)
        widgets = self.mode_binding_widgets if mode == 'mode' else self.mapping_widgets[mode]
        widgets[btn]['capture_btn'].config(text="Press key...", state='disabled')
        self.log(f"Capturing for {btn} in mode {mode}...")

        def on_press(key):
            if self.key_capture_mode and self.capturing_for == wk:
                key_name = key.char if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                self.update_mapping(wk, key_name)
                return False
        
        def on_click(x, y, b, p):
            if p and self.key_capture_mode and self.capturing_for == wk:
                key_name = {Button.left: 'mouse_left', Button.right: 'mouse_right'}.get(b)
                self.update_mapping(wk, key_name)
                return False

        self.key_listener = KeyboardListener(on_press=on_press)
        self.mouse_listener = MouseListener(on_click=on_click)
        self.key_listener.start()
        self.mouse_listener.start()
        self.root.after(10000, lambda: self.stop_key_capture() if self.key_capture_mode else None)

    def update_mapping(self, wk, kn):
        mode, btn = wk.split('_', 1)
        if mode == 'mode':
            self.settings['mode_bindings'][btn] = kn
            self.mode_binding_widgets[btn]['var'].set(kn)
        else:
            self.mappings[mode][btn] = kn
            self.mapping_widgets[mode][btn]['var'].set(kn)
        self.log(f"Mapped {btn} to {kn} for mode {mode}")
        self.stop_key_capture()

    def stop_key_capture(self):
        if hasattr(self, 'key_listener'):
            self.key_listener.stop()
        if hasattr(self, 'mouse_listener'):
            self.mouse_listener.stop()
        self.key_capture_mode = False
        if self.capturing_for:
            mode, btn = self.capturing_for.split('_', 1)
            widgets = self.mode_binding_widgets if mode == 'mode' else self.mapping_widgets[mode]
            widgets[btn]['capture_btn'].config(text="Capture", state='normal')
            self.capturing_for = None

    def clear_mapping(self, wk):
        mode, btn = wk.split('_', 1)
        if mode == 'mode':
            self.settings['mode_bindings'][btn] = ''
            self.mode_binding_widgets[btn]['var'].set('')
        else:
            self.mappings[mode][btn] = ''
            self.mapping_widgets[mode][btn]['var'].set('')
        self.log(f"Cleared mapping for {btn} in mode {mode}")

    def apply_settings(self):
        for k, v in {**self.deadzone_vars, **self.autocenter_vars}.items():
            self.settings['global'][k] = v.get()
        for mode in self.modes:
            self.settings[mode]['mouse_sensitivity'] = self.sensitivity_vars[mode]['mouse_sensitivity'].get()
            self.settings[mode]['mouse_acceleration'] = self.accel_vars[mode].get()
            for k, v in self.invert_vars[mode].items():
                self.settings[mode][k] = v.get()
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
            os.makedirs('profiles', exist_ok=True)
            with open(f'profiles/{profile_name}.json', 'w') as f:
                json.dump({'settings': self.settings, 'mappings': self.mappings}, f, indent=4)
            self.log(f"Saved profile: {profile_name}")
            messagebox.showinfo("Success", f"Profile '{profile_name}' saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save profile: {e}")

    def _browse_and_load_profile(self):
        filename = filedialog.askopenfilename(initialdir='profiles', title="Select Profile", filetypes=[("JSON files", "*.json")])
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
            if os.path.exists('last_profile.txt'):
                with open('last_profile.txt', 'r') as f:
                    filename = f.read().strip()
            if not filename or not os.path.exists(filename):
                self.settings = self._get_default_settings()
                self.mappings = self._get_default_mappings()
                self._update_gui_from_data()
                return
        
        if not os.path.exists(filename):
            messagebox.showerror("Error", f"Profile not found: {filename}")
            if os.path.exists('last_profile.txt'):
                os.remove('last_profile.txt')
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            self.settings = self._merge_dicts(self._get_default_settings(), data.get('settings', {}))
            self.mappings = self._merge_dicts(self._get_default_mappings(), data.get('mappings', {}))
            self._update_gui_from_data()
            if not is_preset:
                with open('last_profile.txt', 'w') as f:
                    f.write(filename)
            msg_type = "Preset" if is_preset else "Profile"
            self.log(f"Loaded {msg_type}: {self.settings['profile_name']}")
            messagebox.showinfo("Success", f"{msg_type} '{self.settings['profile_name']}' loaded!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def _update_gui_from_data(self):
        self.profile_var.set(self.settings.get('profile_name', 'Default'))
        for mode in self.modes:
            for bn, m in self.mappings[mode].items():
                if bn in self.mapping_widgets[mode]:
                    self.mapping_widgets[mode][bn]['var'].set(m)
        for bn, m in self.settings['mode_bindings'].items():
            if bn in self.mode_binding_widgets:
                self.mode_binding_widgets[bn]['var'].set(m)
        for k, v in self.settings['global'].items():
            if k in self.deadzone_vars:
                self.deadzone_vars[k].set(v)
            if k in self.autocenter_vars:
                self.autocenter_vars[k].set(v)
        for mode in self.modes:
            self.sensitivity_vars[mode]['mouse_sensitivity'].set(self.settings[mode]['mouse_sensitivity'])
            self.accel_vars[mode].set(self.settings[mode]['mouse_acceleration'])
            for k, v_var in self.invert_vars[mode].items():
                v_var.set(self.settings[mode][k])

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
                if pygame.joystick.get_count() == 0:
                    if self.joystick:
                        self.joystick = None
                        self.root.after(0, lambda: self.update_controller_info("No controller detected"))
                    time.sleep(1)
                    continue
                if not self.joystick:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.root.after(0, lambda name=self.joystick.get_name(): self.update_controller_info(f"Controller: {name}"))
                self.update_controller_state()
                if self.enable_var.get():
                    self.process_controller_input()
                self.root.after(0, self.update_visualization)
                time.sleep(0.01)
            except Exception as e:
                self.log(f"Controller loop error: {e}")
                time.sleep(1)

    def update_controller_state(self):
        if not self.joystick: return
        for i in range(self.joystick.get_numbuttons()):
            self.controller_state['buttons'][i] = self.joystick.get_button(i)
        for i in range(self.joystick.get_numaxes()):
            self.controller_state['axes'][i] = self.joystick.get_axis(i)
        if self.joystick.get_numhats() > 0:
            self.controller_state['hat'] = self.joystick.get_hat(0)

    def process_controller_input(self):
        if not self.joystick or not self.enable_var.get(): return
        if self.process_mode_switches():
            return
        self.process_button_presses()
        self.process_dpad()
        self.process_analog_sticks()
        self.process_triggers()

    def process_mode_switches(self):
        bmap = {0:'A', 1:'B', 2:'X', 3:'Y', 4:'LB', 5:'RB', 6:'BACK', 7:'START', 8:'GUIDE', 9:'LEFT_STICK_CLICK', 10:'RIGHT_STICK_CLICK'}
        for bid, bn in bmap.items():
            if bid < self.joystick.get_numbuttons():
                if self.controller_state['buttons'][bid] and not self.prev_state['buttons'].get(bid, False):
                    for mode, bound_key in self.settings['mode_bindings'].items():
                        if bn == bound_key:
                            if mode == 'cycle':
                                self.cycle_mode()
                            else:
                                self.switch_mode(mode)
                            return True
        return False

    def switch_mode(self, new_mode):
        if new_mode in self.modes:
            self.current_mode = new_mode
            self.log(f"Switched to mode: {new_mode.replace('_', ' ').title()}")

    def cycle_mode(self):
        current_index = self.modes.index(self.current_mode)
        next_index = (current_index + 1) % len(self.modes)
        self.switch_mode(self.modes[next_index])

    def process_button_presses(self):
        bmap = {0:'A', 1:'B', 2:'X', 3:'Y', 4:'LB', 5:'RB', 6:'BACK', 7:'START', 8:'GUIDE', 9:'LEFT_STICK_CLICK', 10:'RIGHT_STICK_CLICK'}
        active_mappings = self.mappings[self.current_mode]
        for bid, bn in bmap.items():
            if bid < self.joystick.get_numbuttons():
                cp = self.controller_state['buttons'][bid]
                pp = self.prev_state['buttons'].get(bid, False)
                if cp != pp:
                    self.execute_key_action(active_mappings.get(bn), cp)
                self.prev_state['buttons'][bid] = cp

    def process_dpad(self):
        hat = self.controller_state['hat']
        self.update_directional_key_state('DPAD_UP', hat[1] == 1)
        self.update_directional_key_state('DPAD_DOWN', hat[1] == -1)
        self.update_directional_key_state('DPAD_LEFT', hat[0] == -1)
        self.update_directional_key_state('DPAD_RIGHT', hat[0] == 1)

    def process_analog_sticks(self):
        if len(self.controller_state['axes']) < 4: return
        ms = self.settings[self.current_mode]
        gs = self.settings['global']
        lx, ly, rx, ry = (self.controller_state['axes'][i] for i in range(4))
        if ms['invert_left_x']: lx = -lx
        if ms['invert_left_y']: ly = -ly
        if ms['invert_right_x']: rx = -rx
        if ms['invert_right_y']: ry = -ry
        mdx, mdy = 0, 0
        dirs = {'LEFT_STICK_UP': (ly < -gs['deadzone_left'], ly), 'LEFT_STICK_DOWN': (ly > gs['deadzone_left'], ly),
                'LEFT_STICK_LEFT': (lx < -gs['deadzone_left'], lx), 'LEFT_STICK_RIGHT': (lx > gs['deadzone_left'], lx),
                'RIGHT_STICK_UP': (ry < -gs['deadzone_right'], ry), 'RIGHT_STICK_DOWN': (ry > gs['deadzone_right'], ry),
                'RIGHT_STICK_LEFT': (rx < -gs['deadzone_right'], rx), 'RIGHT_STICK_RIGHT': (rx > gs['deadzone_right'], rx)}
        for name, (active, val) in dirs.items():
            action = self.mappings[self.current_mode].get(name)
            if action and action.startswith('mouse_move_'):
                if active:
                    if 'up' in action or 'down' in action: mdy += val
                    if 'left' in action or 'right' in action: mdx += val
            else:
                self.update_directional_key_state(name, active)
        if mdx != 0 or mdy != 0:
            sens = ms['mouse_sensitivity']
            fdx, fdy = mdx * sens, mdy * sens
            if ms['mouse_acceleration']:
                fdx *= abs(mdx)
                fdy *= abs(mdy)
            try:
                self.mouse.move(int(fdx), int(fdy))
            except Exception:
                pass

    def update_directional_key_state(self, name, active):
        action = self.mappings[self.current_mode].get(name)
        if not action or action.startswith('mouse_'): return
        prev_active = self.directional_key_state.get(name, False)
        if active != prev_active:
            self.execute_key_action(action, active)
        self.directional_key_state[name] = active

    def process_triggers(self):
        lt, rt = 0, 0
        num_axes = len(self.controller_state['axes'])
        if num_axes >= 6:
            lt, rt = (self.controller_state['axes'][4] + 1) / 2, (self.controller_state['axes'][5] + 1) / 2
        elif num_axes >= 3:
            lt, rt = max(0, self.controller_state['axes'][2]), max(0, -self.controller_state['axes'][2])
        ltp = lt > self.settings['global']['deadzone_trigger']
        rtp = rt > self.settings['global']['deadzone_trigger']
        prev_lt, prev_rt = self.prev_state['triggers'].get('LT', False), self.prev_state['triggers'].get('RT', False)
        if ltp != prev_lt:
            self.execute_key_action(self.mappings[self.current_mode].get('LT'), ltp)
        if rtp != prev_rt:
            self.execute_key_action(self.mappings[self.current_mode].get('RT'), rtp)
        self.prev_state['triggers']['LT'], self.prev_state['triggers']['RT'] = ltp, rtp

    def execute_key_action(self, actions, pressed):
        if not actions: return
        for action in actions.split(','):
            action = action.strip()
            try:
                if action.startswith('mouse_') and not action.startswith('mouse_move_'):
                    button = {'mouse_left': Button.left, 'mouse_right': Button.right, 'mouse_middle': Button.middle}.get(action)
                    if button:
                        (self.mouse.press if pressed else self.mouse.release)(button)
                else:
                    key = self.key_map.get(action, action if len(action) == 1 else None)
                    if key:
                        (self.keyboard.press if pressed else self.keyboard.release)(key)
            except Exception as e:
                self.log(f"Error executing action '{action}': {e}")

    def update_visualization(self):
        if not hasattr(self, 'canvas'): return
        self.canvas.delete("all")
        gs = self.settings['global']
        if len(self.controller_state['axes']) >= 2:
            lx, ly = self.controller_state['axes'][0], self.controller_state['axes'][1]
            if gs['auto_center_left'] and abs(lx) < gs['deadzone_left'] and abs(ly) < gs['deadzone_left']:
                lx, ly = 0, 0
            self._draw_stick(150, 100, lx, ly, gs['deadzone_left'], 'green', 'yellow')
        if len(self.controller_state['axes']) >= 4:
            rx, ry = self.controller_state['axes'][2], self.controller_state['axes'][3]
            if gs['auto_center_right'] and abs(rx) < gs['deadzone_right'] and abs(ry) < gs['deadzone_right']:
                rx, ry = 0, 0
            self._draw_stick(450, 100, rx, ry, gs['deadzone_right'], 'blue', 'cyan')
        self.canvas.create_text(300, 20, text=f"Current Mode: {self.current_mode.replace('_', ' ').title()}", fill="white", font=("Helvetica", 12, "bold"))
        self.canvas.create_text(150, 200, text="Left Stick", fill='white')
        self.canvas.create_text(450, 200, text="Right Stick", fill='white')

    def _draw_stick(self, x, y, val_x, val_y, deadzone, c1, c2):
        dz_rad = deadzone * 80
        self.canvas.create_oval(x - dz_rad, y - dz_rad, x + dz_rad, y + dz_rad, outline='red', width=2)
        self.canvas.create_oval(x - 80, y - 80, x + 80, y + 80, outline='white')
        sx, sy = x + val_x * 80, y + val_y * 80
        self.canvas.create_line(x, y, sx, sy, fill=c1, width=3)
        self.canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill=c2)

    def log(self, message):
        log_msg = f"[{time.strftime('%H:%M:%S')}] {message}\n"
        if hasattr(self, 'log_text'):
            self.log_text.insert(tk.END, log_msg)
            self.log_text.see(tk.END)
        print(log_msg.strip())

    def update_controller_info(self, info):
        self.controller_info.delete(1.0, tk.END)
        self.controller_info.insert(tk.END, info)
        if self.joystick:
            self.controller_info.insert(tk.END, f"\nButtons: {self.joystick.get_numbuttons()}, Axes: {self.joystick.get_numaxes()}, Hats: {self.joystick.get_numhats()}")

    def run_as_admin(self, *args):
        if ctypes and not is_admin():
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                self.log("Attempting to restart as admin...")
                self.on_closing()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to elevate privileges: {e}")

    def run(self):
        self.log("Universal Controller Mapper v4.0 started")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = ControllerMapper()
        app.run()
    except Exception as e:
        messagebox.showerror("Fatal Error", str(e))

