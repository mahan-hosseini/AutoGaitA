# import
from setuptools import setup
import platform

# list of across-platform dependencies
install_requires = [
    "customtkinter>=5.2",
    "pandas>=2.0",
    "numpy>=1.24",
    "seaborn>=0.13",
    "matplotlib>=3.7",
    "scikit-learn>=1.2",
    "pingouin>=0.5",
    "scipy>=1.11",
    "ffmpeg-python>=0.2",
    "openpyxl>=3.1",
    "pillow>=10.3",
]

# add platform-specific dependencies
if platform.system() == "Darwin":
    install_requires.append("pyobjc")

# call setup function
setup(
    name="autogaita",
    python_requires=">=3.10",
    version="0.4.1",  # rc == release candidate (before release is finished)
    author="Mahan Hosseini",
    description="Automatic Gait Analysis in Python. A toolbox to streamline and standardise the analysis of kinematics across species after ML-based body posture tracking. Despite being optimised for gait analyses, AutoGaitA has the potential to be used for any kind of kinematic analysis.",
    packages=["autogaita", "autogaita.batchrun_scripts"],
    include_package_data=True,
    package_data={"": ["*.txt", "*.rst", "*.png", "*.icns", "*.ico", "*.json"]},
    install_requires=install_requires,
    extras_require={"dev": ["pytest", "hypothesis"]},
    license="GPLv3",
    url="https://github.com/mahan-hosseini/AutoGaitA/",
)
