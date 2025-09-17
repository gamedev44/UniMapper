# 🎮 Uni-Mapper: Universal Controller Mapper 🎮

<p align="center">
<img src="https://img.shields.io/badge/Version-4.0%20(Final)-blue.svg" alt="Version 4.0">
<img src="https://img.shields.io/badge/Author-Asterisk-lightgrey.svg" alt="Author: Asterisk">
<img src="https://img.shields.io/badge/Python-3.x-yellow.svg" alt="Python 3.x">
</p>

<p align="center">
A powerful and highly customizable tool designed to map <strong>any</strong> generic controller's inputs to keyboard and mouse actions, giving you the power to play almost any PC game with your favorite gamepad.
</p>

---

# 📜 Table of Contents
- [✨ Features at a Glance](#-features-at-a-glance)  
- [⚙️ Installation](#️-installation)  
  - [Prerequisites](#prerequisites)  
  - [Cloning the Repository](#cloning-the-repository)  
  - [Running the Setup Script](#running-the-setup-script)  
- [🚀 How to Use Uni-Mapper](#-how-to-use-uni-mapper)  
  - [Running the Application](#running-the-application)  
  - [Understanding the Interface](#understanding-the-interface)  
- [🧠 Core Concepts: Profiles vs. Presets](#-core-concepts-profiles-vs-presets)  
  - [👤 What are Profiles?](#-what-are-profiles)  
  - [📚 What are Presets?](#-what-are-presets)  
- [🌟 Advanced Features](#-advanced-features)  
  - [🚶‍♂️🚗✈️ Multi-Mode Controls](#️-multi-mode-controls)  
  - [⌨️ Setting Up Mode-Switching Hotkeys](#️-setting-up-mode-switching-hotkeys)  
  - [➕ Multi-Key Actions](#-multi-key-actions)  
  - [🎯 Mode-Specific Sensitivity](#-mode-specific-sensitivity)  
  - [🛠️ Creating Your Own Presets](#️-creating-your-own-presets)  
- [🆘 Troubleshooting](#-troubleshooting)  

---

# ✨ Features at a Glance
✅ Full Controller Mapping: Map every button, stick direction, and D-pad input to any keyboard key or mouse action.  
✅ Multi-Mode System: Instantly switch between On Foot, Ground Vehicle, and Flight mappings.  
✅ Profiles & Presets: Save personal configs and use ready-made game templates.  
✅ Adjustable Sensitivity & Deadzones: Fine-tune controls per mode.  
✅ Advanced Actions: Map a single button to multiple key presses.  
✅ Real-time Visualization: Diagnose inputs and deadzones.  
✅ Run as Administrator: Built-in elevation support.  

---

# ⚙️ Installation

## Prerequisites
- Python 3.x installed (check **Add Python to PATH** during install).  

## Cloning the Repository
- Install GitHub Desktop.  
- Clone the repo with the repository URL.  

## Running the Setup Script
- Navigate to the cloned folder.  
- Run `PreSetup.bat` to auto-install required libraries (`pygame`, `pynput`).  

---

# 🚀 How to Use Uni-Mapper

## Running the Application
- Run `UM_GUI.bat` and you’re done.  
- If inputs don’t register in-game, restart with **Run as Administrator** (link inside Uni-Mapper).  

## Understanding the Interface
- **Mappings & Profiles:** Configure buttons, manage profiles & presets.  
- **Settings:** Global & mode-specific sensitivity, inversion, deadzones.  
- **Visualization:** Real-time controller diagnostics.  
- **Status:** Device info & log.  

---

# 🧠 Core Concepts: Profiles vs. Presets

## 👤 What are Profiles?
- Your full custom setup (mappings, sensitivities, hotkeys).  
- Saved per-game, persistent between sessions.  

## 📚 What are Presets?
- Pre-made, read-only templates for specific games.  
- Loaded, then customized & saved as your own profile.  

---

# 🌟 Advanced Features

## 🚶‍♂️🚗✈️ Multi-Mode Controls
- Separate tabs for On Foot, Ground Vehicle, and Flight.  

## ⌨️ Setting Up Mode-Switching Hotkeys
- Assign hotkeys or controller buttons for switching modes.  

## ➕ Multi-Key Actions
- Map a single input to multiple key presses (e.g., `ctrl,c`).  

## 🎯 Mode-Specific Sensitivity
- Independent sensitivity, acceleration, and inversion per mode.  

## 🛠️ Creating Your Own Presets
- Save your profile → copy `.json` → move to `presets/` → rename/edit.  

---

# 🆘 Troubleshooting
- **Controller Not Detected:** Check connection, restart app.  
- **Inputs Not Working In-Game:** Run Uni-Mapper as Administrator.  
- **Stick Drift:** Adjust deadzones in **Settings**.  
