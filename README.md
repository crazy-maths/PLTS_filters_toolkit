# PLTS Editor

A Python-based graphical toolkit for constructing, visualizing, and analyzing Paraconsistent Transition Systems (PLTS) based on Twist Structures.

## Overview

The **PLTS Editor:** is an interactive GUI application designed for researchers and students working with non-classical logics. It allows users to define algebraic foundations (Complete Distributive Residuated Lattices and Filters), construct PLTSs where transitions and valuations are weighted by truth pairs, and evaluate modal formulas using the algebraic semantics of Twist Structures.

## Features

### 1. Algebraic Structure Creation

- **Complete Distributive Residuated Lattices:** Define custom finite Complete Distributive Residuated Lattices.
- **Twist Structures:** Automatically generate Twist Structures ($A^2$) from a base Lattice. Truth values are represented as pairs $(t, f)$ (evidence for, evidence against).
- **Filters:** Define custom filters for Lattices and automatically generate filters for Twist Structures.
- **Hasse Diagrams:** Visualize the partial order of any Lattice or Twist Structure using Hasse diagrams.

### 2. Paraconsistent Modeling

- **Batch State Creation:** Efficiently create multiple states with valuations assigned from the underlying Twist Structure.
- **Weighted Accessibility Relations:** Build Kripke-style models where transitions are not just present/absent but carry a **weight** $(t, f)$ from the algebra.
- **PLTS Visualization:** View PLTSs as directed graphs with support for bidirectional edges, self-loops, and clear labeling of actions and weights.

### 3. Local and Global Satisfaction

- **Formula Parser:** Interpret complex formulas using the specific semantics of Paraconsistent Modal Logic. Supported operators include:
  - **Modal:** Box (`[]`), Diamond (`<>` - weighted by relation)
  - **Lattice:** Weak Meet (`&`), Weak Join (`|`)
  - **Material:** Material Implication (`->`), Material Equivalence (`<->`)
  - **Unary:** Paraconsistent Negation (`~`)
  - **Constants:** Top (`1`), Bottom (`0`)

- **Global Satisfaction:** Compute the global satisfaction and get the interpretation of formulas in all worlds.
- **Filters:** Check if the result of the satisfaction relation is in the filter.

### 4. User Interface

- **Dark Mode:** Toggle between Light and Dark themes for comfortable viewing in different lighting conditions.
- **JSON Persistence:** Save and Load your Lattices, Filters, Structures, States, and PLTSs to JSON files to preserve your workspace.
- **Definitions & Legend:** Built-in reference guides for mathematical definitions and logic symbols.

## Installation

### Requirements

- Python 3.11.2 or higher
- PyQt6 Version 6.10.2 or higher (Check Install Dependecies)

### Install Dependencies

Choose one of the following to install the dependencies:

#### Windows (pip)

Run the following command to install the required libraries:

```bash
pip install PyQt6 networkx matplotlib
```

Navigate to the project directory and execute the main application script:

```bash
python app.py
```

#### Windows (scripts to configure the environment, install python,if needed, create venv and install all dependencies):

Run the following command to install the required libraries:

```bash
setup.bat:
@echo off
setlocal

:: Verifies if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Trying to install Python 3.12 via winget...
    winget install -e --id Python.Python.3.12
    echo Please, close the terminal and open it again to update the PATH.
    pause
    exit
)

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing dependencies...
python -m pip install --upgrade pip
pip install PyQt6 networkx matplotlib

echo.
echo Done! To run the app, use: python app.py
pause
```

#### Linux (scripts to configure the environment, install python,if needed, create venv and install all dependencies):

Run the following command to install the required libraries:

```bash
setup.sh:

#!/bin/bash

detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)
echo "Distribution detected: $DISTRO"

case $DISTRO in
    ubuntu|debian|pop|linuxmint|kali)
        echo "Configuring to Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y python3.12 python3.12-venv python3-pip \
        libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
        libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-xinput0
        PYTHON_BIN="python3.12"
        ;;

    fedora)
        echo "Configuring to Fedora..."
        sudo dnf install -y python3.12 python3-pip \
        libxcb libxkbcommon-x11 qt6-qtbase-gui
        PYTHON_BIN="python3.12"
        ;;

    arch|manjaro)
        echo "Configuring to Arch Linux..."
        sudo pacman -Syu --noconfirm python python-pip \
        libxcb libxkbcommon-x11
        PYTHON_BIN="python"
        ;;

    alpine)
        echo "Configurando para Alpine..."
        # Note: PyQt6 in Alpine could be hard due to musl library
        sudo apk add python3 py3-pip libxcb libxkbcommon
        PYTHON_BIN="python3"
        ;;

    *)
        echo "Distribution not suported automatically."
        echo "Please, install the Python 3.12 and the XCB libraries manually."
        exit 1
        ;;
esac

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment with $PYTHON_BIN..."
    $PYTHON_BIN -m venv .venv
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment and e installing Python dependencies ..."
source .venv/bin/activate

pip install --upgrade pip
pip install PyQt6 networkx matplotlib

echo -e "\n===================================================="
echo "Done!"
echo "To run the app:"
echo "1. Activate the venv: source .venv/bin/activate"
echo "2. Execute: python app.py"
echo "===================================================="
```

#### If the previous steps failed to install PyQt6, follow the instructions in:

[Link to PythonGUIs website](https://www.pythonguis.com/pyqt6/)

## Contact

Created by [Rodrigo Alves](rodrigoalves@ua.pt), [Juliana Cunha](juliana.cunha@ua.pt), [Alexandre Madeira](madeira@ua.pt)
Feel free to reach out with questions or suggestions.
