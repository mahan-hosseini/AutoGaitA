![AutoGaitA](https://github.com/mahan-hosseini/AutoGaitA/blob/main/res/autogaita_logo.png?raw=true)
![Python](https://img.shields.io/badge/python-v3.6+-blue.svg)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
# Automated Gait Analysis in Python 🐸

- AutoGaitA simplifies, accelerates, and standardises gait analyses after body posture tracking with [DeepLabCut](https://github.com/DeepLabCut/DeepLabCut) and [Simi Motion](http://www.simi.com/en/products/movement-analysis/simi-motion-2d3d.html?type=rss%2F). 
- AutoGaitA's first-level tools provide a wide range of automated kinematic analyses for each input video and AutoGaitA Group allows the comparison of up to six groups. 
- AutoGaitA enables comparisons to be made across experimental conditions, species, disease states or genotypes. 
- Despite being developed with gait data, AutoGaitA can be utilised for the analysis of any motor behaviour.

## Getting Started

***Note!** Our documentation provides step-by-step walkthroughs of how to install autogaita for **[Windows](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.28j6wu2vamre)** and **[Mac](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit)***

It is strongly recommended that a separate virtual environment for AutoGaitA is created (note that the approach below creates the virtual environment to your current directory):

- Create the virtual environment
    - `python -m venv env_gaita`

- After creation, activate the virtual environment via:
    - *Windows:* `env_gaita\Scripts\activate`
    - *Mac:* `source env_gaita/bin/activate`

- Once activated, install AutoGaitA in the virtual environment via pip: `pip install autogaita`.

- Access The main user interface via `python -m autogaita`.

## Tutorials and Examples

### Video Walkthrough Tutorials

**[The AutoGaitA YouTube Channel](https://youtube.com/playlist?list=PLCn5T7K_H8K56NIcEsfDK664OP7cN_Bad&si=mV5p2--nYvbofkPh) provides tutorials for file preparation and instructions on how to use AutoGaitA**

### Example Data
We provide an example dataset in the **example data** folder of this repository, with a set of mice walking over differently wide beams and both the beam as well as body coordinates being tracked with DLC. Note that this dataset was used in our tutorial videos introducing *AutoGaitA_DLC*, *AutoGaitA_Group* and in our video explaining file preparation for *AutoGaitA_DLC*.  We further provide a **group** folder there that can be used alongside the *AutoGaitA_Group* tutorial to confirm that users generate the same set of results following our instructions.

### Annotation Table Examples and Templates
Annotation Table example and template files for *AutoGaitA_DLC* and *AutoGaitA_Simi* can be found in the [**annotation tables**](https://github.com/mahan-hosseini/AutoGaitA/tree/main/annotation%20tables) folder of this repository.

Users are advised to read the ***important note*** of that folder, use the template to enter their data's timestamp information and to then compare the resulting table with our example to check formatting.

## Documentation

**[The AutoGaitA Documentation](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit?usp=sharing) provides complete guidelines on installation, file preparation, AutoGaitA GUIs, using AutoGaitA via the command line, installing FFmpeg for rotating 3D PCA videos, lists known issues and FAQ.**  

## Please Note: Custom Joints and Angles!
**We strongly recommend** users to pay attention to the *custom joints and angles* windows of AutoGaitA's first level toolboxes. Please see the relevant links below. These windows allow users to customise which columns of their data should be analysed and how angles should be computed. 

By default, *AutoGaitA DLC* and *AutoGaitA Simi* implement standard values for mouse and human locomotion, respectively. If your analysis deviates from these standards (e.g. by focussing on another limb or a different species) **you must change these values!** You can find the window in the *advanced configuration* sections and once values are customised they remain for subsequent executions of AutoGaitA (i.e., until the program is closed). 

**Find out more about *AutoGaitA's custom joints and angles:***
- [YouTube - AutoGaitA DLC Advanced Configuration](https://youtu.be/YABoQMOqChk?feature=shared) 
- [YouTube - AutoGaitA Simi](https://youtu.be/fJhnjrJbA5c?feature=shared) 
- [Documentation - AutoGaitA DLC](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.20bg7b7ymt0b)
- [Documentation - AutoGaitA Simi](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.uz61bpmua7qz)

## Reference
If you use this code or data please [cite our preprint](https://www.biorxiv.org/content/10.1101/2024.04.14.589409v1).

## License
AutoGaitA is licensed under [GPL v3.0](https://github.com/mahan-hosseini/AutoGaitA/blob/main/LICENSE) and Forschungszentrum Jülich GmbH holds all copyrights. 

The AutoGaitA software is provided without warranty of any kind, express or implied, including, but not limited to, the implied warranty of fitness for a particular purpose.

## Authors
Mahan Hosseini
