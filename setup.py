import sys
import os
from cx_Freeze import setup, Executable

files =["HTR_text.txt","segmented/","icon/","image/"]

target = Executable(
    script ="noteedom.py",
    base = "Win32GUI",
    icon = "icon/icon.ico"
)

setup(
    name = "NOTEEDOM",
    version = "1.2.0",
    description = "Optical Character and Handwritten Text Recognition",
    author = "Semih SEVINC",
    options = {'build_exe':{'include_files':files}},
    executables =[target]
)