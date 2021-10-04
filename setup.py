import sys
import os
from cx_Freeze import setup, Executable

files =["main.ui","HTR_text.txt","segmented/","icon/","image/"]

target = Executable(
    script ="gui.py",
    base = "Win32GUI",
    icon = "icon/icon.ico"
)

setup(
    name = "NOTEEDOM",
    version = "1.0",
    description = "Handwritten Text Recognition App",
    author = "Semih SEVINC",
    options = {'build_exe':{'include_files':files}},
    executables =[target]
)