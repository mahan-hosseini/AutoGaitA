# import
from setuptools import setup
import platform

# list of across-platform dependencies
install_requires=[
    'customtkinter==5.2.0',
    'pandas==2.0.3',
    'numpy==1.24.2',
    'matplotlib==3.7.1',
    'scikit-learn==1.2.2',
    'pingouin==0.5.3',
    'scipy==1.11.1',
    'ffmpeg-python==0.2.0',
    'openpyxl==3.1.2',
    'pillow==10.0.0'
]

# add platform-specific dependencies
if platform.system() == "Darwin":
    install_requires.append("pyobjc")

# call setup function
setup(
    name='autogaita',
    version='0.0.5',
    author="Mahan Hosseini",
    description="Automatic Gait Analysis in Python",
    packages=["autogaita"],
    include_package_data=True,
    package_data={'': ['*.txt', '*.rst', '*.png', "*.icns", "*.ico"]},
    install_requires=install_requires,
    license="GPLv3",
    url="https://github.com/mahan-hosseini/AutoGaitA/",
)
