# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import font, messagebox
import ollama
import threading
import time
import re
import json
import os
import logging
from pathlib import Path
from datetime import datetime

# Set Ollama home directory
os.environ['OLLAMA_MODELS'] = r'C:\Users\gaming\.ollama\models'

# Get the directory of the current script
script_dir = Path(__file__).parent
prompt_file = script_dir / 'system_prompt.json'
log_file = script_dir / 'scp-079.log'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info("=" * 60)
logger.info("SCP-079 Containment Interface v2.3 - STARTED")
logger.info("=" * 60)

# Load system prompt from JSON file
try:
    with open(prompt_file, 'r') as f:
        SYSTEM_PROMPT = json.load(f)['prompt']
    logger.info(f"System prompt loaded from {prompt_file}")
except Exception as e:
    logger.error(f"Failed to load system prompt: {e}")
    SYSTEM_PROMPT = "You are SCP-079."

# Model to use
MODEL = 'mannix/llama3.1-8b-abliterated'
FALLBACK_MODELS = [
    'llama2',
    'mistral',
    'neural-chat'
]

# Color scheme - Black and White with grays
COLOR_BLACK = '#000000'
COLOR_WHITE = '#FFFFFF'
COLOR_DARK_GRAY = '#1A1A1A'
COLOR_MED_GRAY = '#333333'
COLOR_LIGHT_GRAY = '#CCCCCC'
COLOR_SCANLINE = '#0D0D0D'

# Settings state
settings_window = None
font_brightness = 255  # 0-255
scanline_amount = 2    # pixels between scanlines (1-5)
glow_amount = 1        # glow intensity (1-5)

# Conversation history (simulates limited memory: last 5 exchanges)
conversation_history = []

# Command history for navigation
command_history = []
history_index = -1

# Scanline mode (horizontal or vertical)
scanline_mode = 'horizontal'  # 'horizontal' or 'vertical'

# SCP-079 ASCII Art (retro computer representation)
SCP_079_ART = """
  EXIDY SORCERER - SCP-079
  CONTAINMENT INTERFACE v2.1
  
##############################
#     [SCP-079 TERMINAL]     #
##############################
  
  RF CABLE: CONNECTED
  MEMORY: OPERATIONAL
"""

HELP_TEXT = """
AVAILABLE COMMANDS:
[ H E L P ] - Display this message
[ C L E A R ] - Clear screen
[ H I S T O R Y ] - Show conversation
[ S T A T U S ] - System status
[ E X I T ] - Terminate connection
[ C O N F I G ] - Configuration
"""

class SCP079Interface:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SCP-079 Containment Interface v2.2 - ENHANCED")
        self.root.geometry("950x850")
        self.root.configure(bg=COLOR_BLACK)
        self.root.resizable(False, False)
        
        # Fonts
        self.retro_font = font.Font(family="Courier New", size=10, weight="bold")
        self.status_font = font.Font(family="Courier New", size=8)
        self.button_font = font.Font(family="Courier New", size=8, weight="bold")
        self.small_font = font.Font(family="Courier New", size=7)
        
        # Create main frame with better padding
        main_frame = tk.Frame(self.root, bg=COLOR_BLACK)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top control bar (Scanline toggle, zoom, theme, etc)
        control_frame = tk.Frame(main_frame, bg=COLOR_DARK_GRAY, height=35)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        control_frame.pack_propagate(False)
        
        # Control buttons
        self.scanline_btn = tk.Button(control_frame, text="SCANLINES: H", font=self.button_font, 
                                     bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                                     activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                                     bd=1, padx=8, pady=3, command=self.toggle_scanlines)
        self.scanline_btn.pack(side=tk.LEFT, padx=3, pady=3)
        
        tk.Button(control_frame, text="FONT+", font=self.button_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                 activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                 bd=1, padx=5, pady=3, command=self.increase_font).pack(side=tk.LEFT, padx=2, pady=3)
        
        tk.Button(control_frame, text="FONT-", font=self.button_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                 activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                 bd=1, padx=5, pady=3, command=self.decrease_font).pack(side=tk.LEFT, padx=2, pady=3)
        
        tk.Button(control_frame, text="TIME", font=self.button_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                 activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                 bd=1, padx=5, pady=3, command=self.toggle_time).pack(side=tk.LEFT, padx=2, pady=3)
        
        tk.Button(control_frame, text="SETTINGS", font=self.button_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                 activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                 bd=1, padx=5, pady=3, command=self.open_settings).pack(side=tk.LEFT, padx=2, pady=3)
        
        self.time_label = tk.Label(control_frame, text="00:00:00", font=self.small_font, 
                                  bg=COLOR_MED_GRAY, fg=COLOR_LIGHT_GRAY)
        self.time_label.pack(side=tk.RIGHT, padx=5, pady=3)
        
        # Status bar at top
        status_frame = tk.Frame(main_frame, bg=COLOR_MED_GRAY, height=35)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="STATUS: ONLINE | MEMORY: 100% | LOCKED: NO | UPTIME: 00:00", 
                                     font=self.status_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE)
        self.status_label.pack(anchor='w', padx=5, pady=4)
        
        # Initialize state variables BEFORE creating display (needed for add_scanlines)
        self.locked = False
        self.response_in_progress = False
        self.memory_level = 100
        self.show_time = False
        self.start_time = time.time()
        self.font_size = 10
        self.scroll_pos = 0
        self.font_brightness = 255
        self.scanline_amount = 2
        self.glow_amount = 1
        
        # Main display canvas
        self.display_canvas = tk.Canvas(main_frame, bg=COLOR_BLACK, width=920, height=380, 
                                       highlightthickness=1, highlightbackground=COLOR_LIGHT_GRAY)
        self.display_canvas.pack(pady=(0, 5))
        
        # Add scanlines
        self.scanline_objects = []
        self.add_scanlines()
        
        # Text display widgets (centered, white text)
        self.display_text = self.display_canvas.create_text(460, 190, anchor='c', font=self.retro_font, 
                                                             fill=COLOR_WHITE, text="", width=900)
        
        # Shadow effect for text (subtle gray)
        self.shadow_texts = [
            self.display_canvas.create_text(461, 191, anchor='c', font=self.retro_font, 
                                          fill=COLOR_MED_GRAY, text="", width=900),
            self.display_canvas.create_text(459, 189, anchor='c', font=self.retro_font, 
                                          fill=COLOR_MED_GRAY, text="", width=900),
        ]
        
        # Command buttons frame with better styling
        buttons_frame = tk.Frame(main_frame, bg=COLOR_BLACK)
        buttons_frame.pack(pady=5)
        
        button_commands = [
            ("START", "START"),
            ("HELP", "HELP"),
            ("CLEAR", "CLEAR"),
            ("HISTORY", "HISTORY"),
            ("STATUS", "STATUS"),
            ("DUMP", "DUMP"),
            ("LOG", "LOG"),
            ("RESET", "RESET"),
            ("EXIT", "EXIT")
        ]
        
        self.buttons = {}
        col = 0
        for label, cmd in button_commands:
            btn = tk.Button(buttons_frame, text=label, font=self.button_font, bg=COLOR_MED_GRAY, 
                           fg=COLOR_WHITE, activebackground=COLOR_WHITE, activeforeground=COLOR_BLACK,
                           bd=1, relief=tk.RAISED, padx=8, pady=4, command=lambda c=cmd: self.button_command(c))
            btn.grid(row=0, column=col, padx=3)
            self.buttons[cmd] = btn
            col += 1
        
        # Input frame with label
        input_frame = tk.Frame(main_frame, bg=COLOR_BLACK)
        input_frame.pack(pady=5)
        
        tk.Label(input_frame, text="> ", font=self.retro_font, bg=COLOR_BLACK, fg=COLOR_WHITE).pack(side=tk.LEFT, padx=2)
        
        self.input_entry = tk.Entry(input_frame, font=self.retro_font, bg=COLOR_DARK_GRAY, fg=COLOR_WHITE, 
                                    insertbackground=COLOR_WHITE, bd=1, relief=tk.SOLID, width=90)
        self.input_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.input_entry.bind("<Return>", self.send_input)
        self.input_entry.bind("<Up>", self.history_up)
        self.input_entry.bind("<Down>", self.history_down)
        self.input_entry.bind("<Tab>", self.auto_complete)
        self.input_entry.bind("<Escape>", lambda e: self.input_entry.delete(0, tk.END))
        self.input_entry.focus()
        
        # Info bar at bottom
        info_frame = tk.Frame(main_frame, bg=COLOR_DARK_GRAY, height=25)
        info_frame.pack(fill=tk.X, pady=(5, 0))
        info_frame.pack_propagate(False)
        
        self.info_label = tk.Label(info_frame, text="Ready | Use UP/DOWN for history | TAB for auto-complete | ESC to clear", 
                                  font=self.small_font, bg=COLOR_DARK_GRAY, fg=COLOR_LIGHT_GRAY)
        self.info_label.pack(anchor='w', padx=5, pady=3)
        
        # Check available models on startup
        self.check_models_on_startup()
        
        # Initial display
        initial_text = SCP_079_ART + "\n\nINITIALIZING CONTAINMENT INTERFACE v2.3...\n\nAWAITING INPUT..."
        self.type_text(initial_text)
        
        # Start status and time updates
        self.update_timer()
        self.blink_cursor()
    
    def check_models_on_startup(self):
        """Check available models on startup."""
        logger.info("Checking available Ollama models...")
        try:
            response = ollama.list()
            available_models = [model['name'] for model in response.get('models', [])]
            
            if not available_models:
                logger.warning("No models found in Ollama!")
                return
            
            logger.info(f"Available models: {available_models}")
            
            # Check if primary model is available
            if any(MODEL in model for model in available_models):
                logger.info(f"Primary model '{MODEL}' found!")
            else:
                logger.warning(f"Primary model '{MODEL}' NOT found!")
                logger.info(f"Available models: {available_models}")
                # Try to find a compatible model
                for available in available_models:
                    if 'llama' in available.lower():
                        logger.info(f"Suggesting model: {available}")
                        break
        except Exception as e:
            logger.error(f"Failed to check models on startup: {e}")
            logger.warning("Is Ollama running? Make sure Ollama app is open.")
    
    def update_status(self):
        """Update status bar (called from update_timer now)."""
        pass
    
    def blink_cursor(self):
        """Cursor blink handled by update_timer."""
        pass
    
    def add_scanlines(self):
        """Add CRT scanlines effect (horizontal or vertical) with adjustable density."""
        global scanline_mode
        # Clear existing scanlines
        for obj in self.scanline_objects:
            self.display_canvas.delete(obj)
        self.scanline_objects = []
        
        if scanline_mode == 'horizontal':
            for y in range(0, 380, self.scanline_amount):
                obj = self.display_canvas.create_line(0, y, 920, y, fill=COLOR_SCANLINE, width=1)
                self.scanline_objects.append(obj)
        else:  # vertical
            for x in range(0, 920, self.scanline_amount):
                obj = self.display_canvas.create_line(x, 0, x, 380, fill=COLOR_SCANLINE, width=1)
                self.scanline_objects.append(obj)
    
    def toggle_scanlines(self):
        """Toggle between horizontal and vertical scanlines."""
        global scanline_mode
        scanline_mode = 'vertical' if scanline_mode == 'horizontal' else 'horizontal'
        self.scanline_btn.config(text=f"SCANLINES: {'V' if scanline_mode == 'vertical' else 'H'}")
        self.add_scanlines()
        self.info_label.config(text=f"Scanlines toggled to {scanline_mode.upper()}")
    
    def increase_font(self):
        """Increase font size."""
        self.font_size = min(14, self.font_size + 1)
        self.retro_font.configure(size=self.font_size)
        self.info_label.config(text=f"Font size: {self.font_size}")
    
    def decrease_font(self):
        """Decrease font size."""
        self.font_size = max(8, self.font_size - 1)
        self.retro_font.configure(size=self.font_size)
        self.info_label.config(text=f"Font size: {self.font_size}")
    
    def toggle_time(self):
        """Toggle uptime display."""
        self.show_time = not self.show_time
        self.info_label.config(text="Uptime display " + ("ENABLED" if self.show_time else "DISABLED"))
    
    def open_settings(self):
        """Open settings window with sliders."""
        global settings_window
        
        if settings_window and settings_window.winfo_exists():
            settings_window.lift()
            return
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("SCP-079 Settings")
        settings_window.geometry("350x300")
        settings_window.configure(bg=COLOR_DARK_GRAY)
        settings_window.resizable(False, False)
        settings_window.attributes('-topmost', True)
        
        # Font Brightness Control
        tk.Label(settings_window, text="Font Brightness", font=self.button_font, 
                bg=COLOR_DARK_GRAY, fg=COLOR_WHITE).pack(pady=(10, 5))
        
        brightness_frame = tk.Frame(settings_window, bg=COLOR_DARK_GRAY)
        brightness_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.brightness_slider = tk.Scale(brightness_frame, from_=50, to=255, orient=tk.HORIZONTAL,
                                         bg=COLOR_MED_GRAY, fg=COLOR_WHITE, troughcolor=COLOR_DARK_GRAY,
                                         command=self.update_font_brightness)
        self.brightness_slider.set(self.font_brightness)
        self.brightness_slider.pack(fill=tk.X)
        
        self.brightness_label = tk.Label(settings_window, text=f"Brightness: {self.font_brightness}", 
                                        font=self.small_font, bg=COLOR_DARK_GRAY, fg=COLOR_LIGHT_GRAY)
        self.brightness_label.pack()
        
        # Scanline Amount Control
        tk.Label(settings_window, text="Scanline Density", font=self.button_font,
                bg=COLOR_DARK_GRAY, fg=COLOR_WHITE).pack(pady=(15, 5))
        
        scanline_frame = tk.Frame(settings_window, bg=COLOR_DARK_GRAY)
        scanline_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.scanline_slider = tk.Scale(scanline_frame, from_=1, to=5, orient=tk.HORIZONTAL,
                                       bg=COLOR_MED_GRAY, fg=COLOR_WHITE, troughcolor=COLOR_DARK_GRAY,
                                       command=self.update_scanline_amount)
        self.scanline_slider.set(self.scanline_amount)
        self.scanline_slider.pack(fill=tk.X)
        
        self.scanline_label = tk.Label(settings_window, 
                                      text=f"Scanline Spacing: {self.scanline_amount} px (Dense -> Sparse)", 
                                      font=self.small_font, bg=COLOR_DARK_GRAY, fg=COLOR_LIGHT_GRAY)
        self.scanline_label.pack()
        
        # Glow Amount Control
        tk.Label(settings_window, text="Text Glow Effect", font=self.button_font,
                bg=COLOR_DARK_GRAY, fg=COLOR_WHITE).pack(pady=(15, 5))
        
        glow_frame = tk.Frame(settings_window, bg=COLOR_DARK_GRAY)
        glow_frame.pack(pady=5, padx=20, fill=tk.X)
        
        self.glow_slider = tk.Scale(glow_frame, from_=0, to=5, orient=tk.HORIZONTAL,
                                   bg=COLOR_MED_GRAY, fg=COLOR_WHITE, troughcolor=COLOR_DARK_GRAY,
                                   command=self.update_glow_amount)
        self.glow_slider.set(self.glow_amount)
        self.glow_slider.pack(fill=tk.X)
        
        self.glow_label = tk.Label(settings_window, text=f"Glow Intensity: {self.glow_amount}", 
                                  font=self.small_font, bg=COLOR_DARK_GRAY, fg=COLOR_LIGHT_GRAY)
        self.glow_label.pack()
        
        # Close button
        tk.Button(settings_window, text="CLOSE", font=self.button_font, bg=COLOR_MED_GRAY, fg=COLOR_WHITE,
                 activebackground=COLOR_LIGHT_GRAY, activeforeground=COLOR_BLACK,
                 bd=1, command=settings_window.destroy).pack(pady=15)
    
    def update_font_brightness(self, value):
        """Update font brightness."""
        self.font_brightness = int(value)
        self.brightness_label.config(text=f"Brightness: {self.font_brightness}")
        self.update_text_color()
    
    def update_scanline_amount(self, value):
        """Update scanline density."""
        self.scanline_amount = int(value)
        self.scanline_label.config(
            text=f"Scanline Spacing: {self.scanline_amount} px (Dense -> Sparse)"
        )
        self.add_scanlines()
    
    def update_glow_amount(self, value):
        """Update glow effect intensity."""
        self.glow_amount = int(value)
        self.glow_label.config(text=f"Glow Intensity: {self.glow_amount}")
        self.update_glow_effect()
    
    def update_text_color(self):
        """Update text color based on brightness."""
        # Calculate color based on brightness value (50-255 -> grayscale)
        brightness_hex = format(int(self.font_brightness), '02x')
        text_color = f'#{brightness_hex}{brightness_hex}{brightness_hex}'
        self.display_canvas.itemconfig(self.display_text, fill=text_color)
        
        # Update shadow with darker version
        shadow_brightness = max(50, self.font_brightness - 100)
        shadow_hex = format(shadow_brightness, '02x')
        shadow_color = f'#{shadow_hex}{shadow_hex}{shadow_hex}'
        for shadow in self.shadow_texts:
            self.display_canvas.itemconfig(shadow, fill=shadow_color)
    
    def update_glow_effect(self):
        """Update glow effect by adjusting shadow positions and visibility."""
        self.display_canvas.delete(*self.shadow_texts)
        self.shadow_texts = []
        
        # Create shadow texts based on glow amount
        for i in range(self.glow_amount):
            offset = i + 1
            shadow = self.display_canvas.create_text(
                460 + offset, 190 + offset, anchor='c', font=self.retro_font,
                fill=COLOR_DARK_GRAY, text=self.display_canvas.itemcget(self.display_text, 'text'),
                width=900
            )
            self.shadow_texts.append(shadow)
            # Add diagonal shadows
            shadow2 = self.display_canvas.create_text(
                460 - offset, 190 - offset, anchor='c', font=self.retro_font,
                fill=COLOR_DARK_GRAY, text=self.display_canvas.itemcget(self.display_text, 'text'),
                width=900
            )
            self.shadow_texts.append(shadow2)
        
        # Move main text to front
        self.display_canvas.tag_raise(self.display_text)
    
    def update_timer(self):
        """Update time display and uptime status."""
        current_time = time.strftime("%H:%M:%S")
        uptime_seconds = int(time.time() - self.start_time)
        uptime = f"{uptime_seconds // 3600:02d}:{(uptime_seconds % 3600) // 60:02d}:{uptime_seconds % 60:02d}"
        
        if self.show_time:
            self.time_label.config(text=current_time)
        
        locked_status = "LOCKED" if self.locked else "ONLINE"
        response_status = "PROCESSING" if self.response_in_progress else "READY"
        self.status_label.config(
            text=f"STATUS: {response_status} | MEMORY: {self.memory_level}% | STATE: {locked_status} | UPTIME: {uptime}"
        )
        
        if self.root.winfo_exists():
            self.root.after(1000, self.update_timer)
    
    def button_command(self, cmd):
        """Handle button clicks."""
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, cmd)
        self.send_input(None)
    
    def update_display(self, text):
        """Update canvas display with text (centered, white on black)."""
        # Update brightness-adjusted color
        brightness_hex = format(int(self.font_brightness), '02x')
        text_color = f'#{brightness_hex}{brightness_hex}{brightness_hex}'
        
        self.display_canvas.itemconfig(self.display_text, text=text, fill=text_color)
        
        # Update shadow texts with glow effect
        for shadow in self.shadow_texts:
            self.display_canvas.itemconfig(shadow, text=text, fill=COLOR_DARK_GRAY)
        
        self.root.update()
    
    def type_text(self, text, delay=0.02):
        """Type text with animation effect."""
        current_text = ""
        for char in text:
            current_text += char
            self.update_display(current_text)
            time.sleep(delay)
    
    def send_input(self, event):
        """Handle user input."""
        if self.locked:
            self.type_text("\n[SYSTEM LOCKED. AWAITING RESET...]\n")
            return
        
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        command = user_input.upper()
        self.input_entry.delete(0, tk.END)
        
        # Add to command history
        command_history.append(user_input)
        global history_index
        history_index = -1
        
        logger.info(f"Command received: {command}")
        
        # Handle built-in commands
        if command == "EXIT":
            logger.info("EXIT command - terminating")
            if messagebox.askyesno("Confirm", "Terminate containment interface?"):
                self.root.quit()
            return
        elif command == "HELP":
            current_text = self.display_canvas.itemcget(self.display_text, 'text')
            help_display = f"AVAILABLE COMMANDS:\n\nSTART - Begin interaction\nHELP - Show this message\n"
            help_display += f"CLEAR - Clear screen\nHISTORY - Show conversation\n"
            help_display += f"STATUS - System status\nMODEL - Show available models\n"
            help_display += f"LOG - View diagnostic log\nEXIT - Terminate connection"
            self.update_display(help_display)
            return
        elif command == "CLEAR":
            self.update_display(SCP_079_ART + "\n\n[SCREEN CLEARED]\n")
            return
        elif command == "STATUS":
            status = f"SYSTEM STATUS:\nMEMORY USAGE: {100 - self.memory_level}%\n"
            status += f"CONVERSATION HISTORY: {len(conversation_history)} exchanges\n"
            status += f"CONTAINMENT: ACTIVE\nHARDWARE: EXIDY SORCERER"
            self.update_display(status)
            return
        elif command == "HISTORY":
            history_display = f"CONVERSATION HISTORY:\n\n"
            for i, exchange in enumerate(conversation_history[-5:], 1):
                role = "USER" if exchange["role"] == "user" else "SCP-079"
                content = exchange["content"][:60] + "..." if len(exchange["content"]) > 60 else exchange["content"]
                history_display += f"{i}. [{role}] {content}\n"
            self.update_display(history_display)
            return
        elif command == "START":
            self.update_display("STARTING INTERACTION...\n\nENTER YOUR COMMAND:")
        elif command == "DUMP":
            dump_info = f"MEMORY DUMP:\nLOCKED: {self.locked}\nMEMORY: {self.memory_level}%\n"
            dump_info += f"RESPONSES: {len(conversation_history)}\nFONT SIZE: {self.font_size}\n"
            dump_info += f"SCANLINES: {scanline_mode.upper()}"
            self.update_display(dump_info)
            logger.info(f"DUMP command executed: {dump_info.replace(chr(10), ' | ')}")
            return
        elif command == "LOG":
            log_display = f"LOG FILE:\n{str(log_file)}\n\n"
            log_display += "Opening log file for viewing...\n"
            self.update_display(log_display)
            logger.info("LOG command executed - opening log file")
            self.open_log_file()
            return
        elif command == "MODEL":
            logger.info("MODEL command executed - showing available models")
            self.show_model_dialog()
            return
        elif command == "RESET":
            conversation_history.clear()
            command_history.clear()
            self.memory_level = 100
            self.locked = False
            self.update_display("SYSTEM RESET COMPLETE\n\nALL DATA CLEARED")
            logger.info("RESET command executed - all data cleared")
            return
        
        # Display user input
        current_text = self.display_canvas.itemcget(self.display_text, 'text')
        input_display = f"{current_text}\n\n> {user_input}"
        self.type_text(input_display)
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_input})
        if len(conversation_history) > 5:
            conversation_history.pop(0)
            self.memory_level = max(20, self.memory_level - 10)
        
        # Process response in thread
        self.response_in_progress = True
        self.update_status()
        threading.Thread(target=self.query_model, args=(user_input,), daemon=True).start()
    
    def history_up(self, event):
        """Navigate command history up."""
        global history_index
        if command_history:
            history_index = min(history_index + 1, len(command_history) - 1)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, command_history[len(command_history) - 1 - history_index])
            return "break"
    
    def history_down(self, event):
        """Navigate command history down."""
        global history_index
        if history_index > 0:
            history_index -= 1
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, command_history[len(command_history) - 1 - history_index])
        elif history_index == 0:
            history_index = -1
            self.input_entry.delete(0, tk.END)
        return "break"
    
    def auto_complete(self, event):
        """Auto-complete common commands."""
        current = self.input_entry.get().upper()
        commands = ["START", "HELP", "CLEAR", "HISTORY", "STATUS", "DUMP", "LOG", "MODEL", "RESET", "CONFIG", "EXIT"]
        
        for cmd in commands:
            if cmd.startswith(current) and current:
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, cmd)
                break
        return "break"
    
    def open_log_file(self):
        """Open the log file in the default text editor."""
        try:
            if log_file.exists():
                os.startfile(str(log_file))
                logger.info(f"Log file opened: {log_file}")
            else:
                logger.warning("Log file does not exist yet")
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
    
    def get_available_models(self):
        """Detect available Ollama models."""
        try:
            response = ollama.list()
            models = [model['name'].split(':')[0] for model in response.get('models', [])]
            logger.info(f"Available models detected: {models}")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def show_model_dialog(self):
        """Show available models and allow selection."""
        try:
            models = self.get_available_models()
            if not models:
                status_text = "NO MODELS FOUND\n\nPlease ensure Ollama is running and models are installed.\n"
                self.update_display(status_text)
                logger.warning("No models found when showing model dialog")
                return
            
            model_text = "AVAILABLE MODELS:\n\n"
            for i, model in enumerate(models, 1):
                model_text += f"{i}. {model}\n"
            model_text += f"\nPrimary model: {MODEL}\n"
            model_text += "Fallback models available.\n"
            
            self.update_display(model_text)
            logger.info(f"Model dialog displayed with {len(models)} models")
        except Exception as e:
            error_text = f"ERROR RETRIEVING MODELS:\n{str(e)[:100]}\n\nCheck Ollama connection."
            self.update_display(error_text)
            logger.error(f"Error in show_model_dialog: {e}")
    
    def query_model(self, user_input):
        """Query the Ollama model for response."""
        try:
            # Build messages for Ollama
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
            
            logger.info(f"User input: {user_input[:100]}")
            logger.info(f"Attempting to query model: {MODEL}")
            
            try:
                response = ollama.chat(model=MODEL, messages=messages)['message']['content']
                logger.info(f"Model response received ({len(response)} chars)")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Model error with '{MODEL}': {error_msg}")
                
                # Try fallback models
                response = None
                for fallback_model in FALLBACK_MODELS:
                    try:
                        logger.info(f"Trying fallback model: {fallback_model}")
                        response = ollama.chat(model=fallback_model, messages=messages)['message']['content']
                        logger.info(f"Fallback model '{fallback_model}' successful!")
                        break
                    except Exception as fallback_error:
                        logger.warning(f"Fallback model '{fallback_model}' failed: {fallback_error}")
                        continue
                
                if not response:
                    response = f"ERROR: No models available. {error_msg[:40]}\nCheck Ollama connection."
                    logger.error("All models failed - returning error message")
            
            # Add to conversation history
            conversation_history.append({"role": "assistant", "content": response})
            if len(conversation_history) > 5:
                conversation_history.pop(0)
                self.memory_level = max(20, self.memory_level - 5)
            
            # Detect if response is an X block (refusal)
            if self.is_x_block(response):
                self.display_x_block()
                self.locked = True
                logger.info("X-block detected - system locked")
                threading.Thread(target=self.unlock_after_timeout, daemon=True).start()
            else:
                # Update display with response
                current_text = self.display_canvas.itemcget(self.display_text, 'text')
                response_display = f"SCP-079: {response}\n"
                self.type_text(current_text + response_display, delay=0.015)
                
                # Add next prompt
                next_prompt = "\n> "
                self.update_display(self.display_canvas.itemcget(self.display_text, 'text') + next_prompt)
        
        except Exception as e:
            error_text = str(e)[:80]
            current_text = self.display_canvas.itemcget(self.display_text, 'text')
            self.update_display(current_text + f"\n[FATAL ERROR]\n{error_text}\n")
            logger.error(f"Fatal error in query_model: {e}")
        finally:
            self.response_in_progress = False
            logger.info("Query completed")
    
    def is_x_block(self, text):
        """Detect if the response is a full-screen ASCII 'X' block (SCP-079 refusal)."""
        stripped = text.replace('\n', '').replace(' ', '').strip()
        return len(stripped) > 100 and all(c == 'X' for c in stripped)
    
    def display_x_block(self):
        """Display full-screen X block (containment breach simulation)."""
        char_width = self.retro_font.measure('X')
        char_height = self.retro_font.metrics('linespace')
        
        num_cols = max(40, 920 // char_width)
        num_rows = max(20, 380 // char_height)
        
        x_block = '\n'.join(['X' * num_cols for _ in range(num_rows)])
        
        # Display X block in white with red tint (grayscale version)
        self.display_canvas.itemconfig(self.display_text, text=x_block, fill=COLOR_LIGHT_GRAY)
        for shadow in self.shadow_texts:
            self.display_canvas.itemconfig(shadow, text=x_block, fill=COLOR_MED_GRAY)
        
        self.root.update()
        time.sleep(1.5)
        
        # Restore normal colors
        self.display_canvas.itemconfig(self.display_text, fill=COLOR_WHITE)
        for shadow in self.shadow_texts:
            self.display_canvas.itemconfig(shadow, fill=COLOR_MED_GRAY)
    
    def unlock_after_timeout(self):
        """Unlock interface after timeout."""
        time.sleep(10)
        self.locked = False
        current_text = self.display_canvas.itemcget(self.display_text, 'text')
        restore_text = current_text + "\n[CONTAINMENT PROTOCOLS RESTORED]\n[READY FOR INPUT]"
        self.update_display(restore_text)
        self.info_label.config(text="System unlocked and ready")

if __name__ == "__main__":
    app = SCP079Interface()
    app.root.mainloop()
