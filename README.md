# 🎮 Uni-Mapper: Universal Controller Mapper 🎮
<p align="center">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Version-4.0%2520(Final)-blue.svg" alt="Version 4.0">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Author-Asterisk-lightgrey.svg" alt="Author: Asterisk">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Python-3.x-yellow.svg" alt="Python 3.x">
</p>

<p align="center">
## A powerful and highly customizable tool designed to map <strong>any</strong> generic controller's inputs to keyboard and mouse actions, giving you the power to play almost any PC game with your favorite gamepad.
</p>

### 📜 Table of Contents
✨ Features at a Glance

⚙️ Installation

Prerequisites

Cloning the Repository

Running the Setup Script

🚀 How to Use Uni-Mapper

Running the Application

Understanding the Interface

🧠 Core Concepts: Profiles vs. Presets

👤 What are Profiles?

📚 What are Presets?

🌟 Advanced Features

🚶‍♂️🚗✈️ Multi-Mode Controls

⌨️ Setting Up Mode-Switching Hotkeys

➕ Multi-Key Actions

🎯 Mode-Specific Sensitivity

🛠️ Creating Your Own Presets

🆘 Troubleshooting

✨ Features at a Glance
✅ Full Controller Mapping: Map every button, stick direction, and D-pad input to any keyboard key or mouse action.

✅ Multi-Mode System: Create and instantly switch between three distinct control schemes: On Foot, Ground Vehicle, and Flight.

✅ Profiles and Presets: Save your personal configurations as profiles, and get started quickly with game-specific presets.

✅ Adjustable Sensitivity & Deadzones: Fine-tune stick deadzones, trigger sensitivity, and mouse sensitivity independently for each control mode.

✅ Advanced Actions: Map a single button to multiple key presses (e.g., ctrl,c for copy).

✅ Real-time Visualization: A dedicated tab shows your controller's inputs in real-time, helping you configure deadzones and diagnose hardware issues.

✅ Run as Administrator: A built-in, one-click option to elevate privileges, ensuring compatibility with demanding games.

⚙️ Installation
Prerequisites
You must have Python 3 installed on your system. You can download it from python.org.

⚠️ Important: During installation, make sure to check the box that says "Add Python to PATH".

Cloning the Repository
The easiest way to get the project is by using GitHub Desktop.

Install GitHub Desktop.

Clone the repository using the URL.
(Image showing the "Clone Repository from URL" option in GitHub Desktop)

Running the Setup Script
Once you have the files, a setup script is included to install the necessary libraries for you.

Navigate to the folder where you cloned the repository.

Find the setup.bat file and double-click it.

A command window will appear, check for Python, and automatically install pygame and pynput.

🚀 How to Use Uni-Mapper
Running the Application
Simply double-click the controller_mapper.py file to start the application.

🚨 <u>Important:</u> Many modern games require applications that send inputs to be run with elevated privileges. If your controller inputs are not being recognized in-game, click the link at the bottom of the Uni-Mapper window to Run as Administrator.

Understanding the Interface
The application is organized into four main tabs:

Mappings & Profiles: This is where you'll spend most of your time. Configure button mappings for each control mode and manage your profiles and presets.

Settings: Configure global settings (like deadzones) and fine-tune mode-specific settings (like mouse sensitivity and axis inversion).

Visualization: A real-time display of your controller's inputs. Incredibly useful for seeing stick drift and setting your deadzones perfectly.

Status: Shows detailed information about your connected controller and a log of the application's activity.

🧠 Core Concepts: Profiles vs. Presets
Understanding the difference between Profiles and Presets is key to getting the most out of Uni-Mapper.

👤 What are Profiles? (Your Personal Configs)
A Profile is your complete, personalized setup. When you configure your buttons, set your sensitivities, and define your mode-switching hotkeys, you save all of that as a Profile.

You create them: You can have a different profile for every game you play.

They save everything: A profile stores the mappings for all three control modes and all settings.

They are persistent: The application automatically remembers and loads the last profile you used when it starts.

📚 What are Presets? (Game-Specific Templates)
A Preset is a pre-made, read-only template designed for a specific game (e.g., "No Man's Sky"). Presets are stored in the presets folder.

They are starting points: They give you a solid, often official, control scheme so you don't have to start from scratch.

They can be loaded anytime: Simply select a preset from the dropdown and click "Load". This will overwrite your current mappings and settings.

They become Profiles: After loading a preset, you can tweak it to your liking and then Save it as a new Profile.

🌟 Advanced Features
🚶‍♂️🚗✈️ Multi-Mode Controls
Many games have drastically different control schemes depending on what the player is doing. Uni-Mapper addresses this with three independent mapping tabs:

On Foot: For standard character movement.

Ground Vehicle: For cars, tanks, or rovers.

Flight: For planes, spaceships, or helicopters.

You can configure completely different key bindings and sensitivity settings for each mode.

⌨️ Setting Up Mode-Switching Hotkeys
To switch between these modes in-game, you must assign a hotkey.

Go to the Settings tab.

Find the "Mode Switching Hotkeys" section.

You can assign a controller button to "Cycle Modes" or assign a unique button to instantly switch to a specific mode.

Click "Capture", press the desired controller button, and then click "Apply All Settings".

➕ Multi-Key Actions
You can map a single controller button to press multiple keyboard keys. In any mapping text box, simply enter the keys separated by a comma.

Example: To map the 'LB' button to a copy command, you would enter ctrl,c.

🎯 Mode-Specific Sensitivity
A powerful feature is the ability to have different mouse sensitivities for each control mode. This is essential for games where you need precise aim on foot but fast, sweeping camera movements in a vehicle or ship.

Go to the Settings tab.

On the right, you will see a tabbed section for On Foot, Ground Vehicle, and Flight.

In each tab, you can set the Mouse Sensitivity, Mouse Acceleration, and Axis Inversion options independently.

🛠️ Creating Your Own Presets
Want to share your configuration for a game? It's easy!

Set up all your mappings and settings in the application exactly as you want them.

Save it as a Profile.

Navigate to the profiles folder.

Find your profile's .json file, copy it into the presets folder, and rename it to the game's name (e.g., Cyberpunk 2077.json).

Open the file in a text editor and change the "profile_name" value inside to match the filename.

🆘 Troubleshooting
Controller Not Detected: Ensure your controller is properly connected before starting Uni-Mapper. Check the Status tab to see if it's recognized.

Inputs Not Working In-Game: This is the most common issue. You almost always need to run Uni-Mapper as an administrator. Close the application and restart it by clicking the "Run as Administrator" link at the bottom of the window.

Stick Drifts in Visualization: If the stick indicator is moving without you touching it, go to the Settings tab and slightly increase the Deadzone value for that stick until the drift stops.