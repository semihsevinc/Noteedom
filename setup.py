import sys
import os
from cx_Freeze import setup, Executable

files =["newgui.ui","HTR_text.txt","segmented/","icon/","image/"]

target = Executable(
    script ="gui.py",
    base = "Win32GUI",
    icon = "icon/icon.ico"
)

setup(
    name = "NOTEEDOM",
    version = "1.0",
    description = "NOTEEDOM APP - Optical Character and Handwritten Text Recognition",
    author = "Semih SEVINC",
    options = {'build_exe':{'include_files':files}},
    executables =[target]
)