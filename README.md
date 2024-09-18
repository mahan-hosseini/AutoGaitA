![AutoGaitA](https://github.com/mahan-hosseini/AutoGaitA/blob/main/res/autogaita_logo.png?raw=true)
![Repository Active](https://www.repostatus.org/badges/latest/active.svg)
[![Test AutoGaitA](https://github.com/mahan-hosseini/AutoGaitA/actions/workflows/auto_test_gaita.yml/badge.svg)](https://github.com/mahan-hosseini/AutoGaitA/actions/workflows/auto_test_gaita.yml)
![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
[![PyPI - Version](https://img.shields.io/pypi/v/autogaita)](https://pypi.org/project/autogaita/)
![license: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)
[![paper: biorxiv](https://img.shields.io/badge/paper-biorxiv-blue)](https://doi.org/10.1101/2024.04.14.589409) 

![Black](https://img.shields.io/badge/code%20style-black-000000.svg)
# Automated Gait Analysis in Python 🐸

- AutoGaitA simplifies, accelerates, and standardises gait analyses after body posture tracking with [DeepLabCut](https://github.com/DeepLabCut/DeepLabCut) and [Simi Motion](http://www.simi.com/en/products/movement-analysis/simi-motion-2d3d.html?type=rss%2F). 
- AutoGaitA's first-level tools provide a wide range of automated kinematic analyses for each input video and AutoGaitA Group allows the comparison of up to six groups. 
- AutoGaitA enables comparisons to be made across experimental conditions, species, disease states or genotypes. 
- Despite being developed with gait data, AutoGaitA can be utilised for the analysis of any motor behaviour.

## Getting Started

***Note!** [Our documentation](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit?usp=sharing) provides step-by-step walkthroughs of how to install autogaita for **[Windows](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.28j6wu2vamre)** and **[Mac](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit)***

It is strongly recommended that a separate virtual environment for AutoGaitA is created (note that the approach below creates the virtual environment to your current directory):

- Create the virtual environment:
    - `python -m venv env_gaita`

- After creation, activate the virtual environment via:
    - *Windows:* `env_gaita\Scripts\activate`
    - *Mac:* `source env_gaita/bin/activate`

- Once activated, install AutoGaitA in the virtual environment via pip: `pip install autogaita`.

- Access the main user interface via: `python -m autogaita`.

- To update to the latest release (see the *Releases* panel on the right for the latest release) activate the virtual environment and: `pip install autogaita -U`. 

## Demo Video
*Check out the video below for a demonstration of AutoGaitA's main workflow!*
<p><a href="https://youtu.be/_HIZVuUzpzk?feature=shared">
<img src="https://github.com/mahan-hosseini/AutoGaitA/blob/main/res/pic_to_demo_for_repo.png" width="550">

## Tutorials & Examples

### Walkthrough Tutorial Videos  

**[The AutoGaitA YouTube Channel](https://youtube.com/playlist?list=PLCn5T7K_H8K56NIcEsfDK664OP7cN_Bad&si=mV5p2--nYvbofkPh) provides tutorials for file preparation and instructions on how to use AutoGaitA. This includes in-depth explanations of all details, (main & advanced) configurations, possibilities, and outputs.**

*Please note that tutorial videos might not always reflect the most up-to-date version of our toolbox, especially in the beginning when things are regularly changing. We will make sure to record new videos whenever there are major changes though. Last tutorial-update was with v0.4.0. (August 2024).*

### Example Data
We provide an example dataset in the **example data** folder of this repository, with a set of mice walking over differently wide beams and both the beam as well as body coordinates being tracked with DLC. Note that this dataset was used in our tutorial videos introducing *AutoGaitA_DLC*, *AutoGaitA_Group* and in our video explaining file preparation for *AutoGaitA_DLC*.  We further provide a **group** folder there that can be used alongside the *AutoGaitA_Group* tutorial to confirm that users generate the same set of results following our instructions.

### Annotation Table Examples and Templates
Annotation Table example and template files for *AutoGaitA_DLC* and *AutoGaitA_Simi* can be found in the [**annotation tables**](https://github.com/mahan-hosseini/AutoGaitA/tree/main/annotation%20tables) folder of this repository.

Users are advised to read the **General Recommendations** section of that folder, use the template to enter their data's timestamp information and to then compare the resulting table with our example to check formatting. Users working with ImageJ/FIJI are encouraged to check out the [AnnotationTable-Plugin](https://github.com/luca-flemming/AnnotationTable-Plugin) developed by our contributor Luca Flemming.

## Documentation

**[The AutoGaitA Documentation](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit?usp=sharing) provides complete guidelines on installation, file preparation, AutoGaitA GUIs, using AutoGaitA via the command line, installing FFmpeg for rotating 3D PCA videos, lists known issues and FAQ.**  

## Please Note - Two important options!

### 1) Custom joints & angles
**We strongly advise** users to pay attention to the *custom joints and angles* windows of AutoGaitA's first level toolboxes. Please see the relevant links below. These windows allow users to customise which columns of their data should be analysed and how angles should be computed. 

By default, *AutoGaitA DLC* and *AutoGaitA Simi* implement standard values for mouse and human locomotion, respectively. If your analysis deviates from these standards (e.g. by focussing on another behaviour or a different species) **you must change these values!** 

**Find out more about *AutoGaitA's custom joints and angles:***
- [YouTube - AutoGaitA DLC Advanced Configuration](https://youtu.be/MP9g9kXRE_Q?feature=shared) 
- [YouTube - AutoGaitA Simi](https://youtu.be/rTG-Fc9XI9g?feature=shared) 
- [Documentation - AutoGaitA DLC](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.20bg7b7ymt0b)
- [Documentation - AutoGaitA Simi](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.uz61bpmua7qz)

### 2) Bin number of step cycle normalisation
An important step in AutoGaitA is normalising step cycles (or instances of other behaviours) to a uniform length before calculating the video-level average. This uniform length is called *bin number*, must be set by users and defaults to a value of 25 (see the last option in [AutoGaitA DLC's main configuration panel](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.bboivsfqr2lz)). 

Step cycles are normalised via averaging temporally adjacent data points if their original length was larger than the bin number and repeating values if they were shorter originally.

Examples with a bin number of 25 and an original step cycle length of:
- 5: Repeat all 5 values 5 times.
- 20: Repeat the first 5 values once.
- 30: Average the first 10 time points in pairs, then leave the last 20 unchanged
- 50: Average all 50 time points in pairs.
- 51: Average the first 3 points into 1, then average in pairs for the next 48.
- *Note that "averaging in pairs" means:*
    - Average original time point 1 & 2 resulting in normalised time point 1
    - Average original time point 3 & 4 resulting in normalised time point 2
     - And so on

**We strongly advise** users to think carefully about an appropriate bin number for their datasets. The correct value varies and depends strongly on the studied species, behaviour and the frame rate of cameras.

## Analysing other behaviours - AutoCyclA 🚴
Even though AutoGaitA's main focus is to automate and standardise gait analyses, our toolbox can be used to automate the analyses of any rhythmic behaviour of interest. For a proof-of-principle demonstration and an introduction of the general workflow of such analyses, see **[AutoCyclA - Automated Cycling Analysis with AutoGaitA.](https://github.com/mahan-hosseini/AutoGaitA/tree/main/autocycla)**

## Updating AutoGaitA
It is strongly recommended that AutoGaitA is kept up to date since new features and important bugfixes are provided regularly. 

AutoGaitA's cfg files and dictionaries sometimes change as a result, which means that previously generated first-level *Results* folders cannot always be analysed with AutoGaitA Group after an update. In such cases, it is recommended to re-run first-level analyses. 

We document each version's cfg-changes in [AutoGaitA Releases](https://github.com/mahan-hosseini/AutoGaitA/releases), which is particularly relevant for users wrapping custom scripts around AutoGaitA's functions.

## Reference
If you use this code or data please [cite our preprint](https://www.biorxiv.org/content/10.1101/2024.04.14.589409v1).

## License
AutoGaitA is licensed under [GPL v3.0](https://github.com/mahan-hosseini/AutoGaitA/blob/main/LICENSE) and Forschungszentrum Jülich GmbH holds all copyrights. 

The AutoGaitA software is provided without warranty of any kind, express or implied, including, but not limited to, the implied warranty of fitness for a particular purpose.

## Authors
[Mahan Hosseini](https://github.com/mahan-hosseini)

## Contributors
[Luca Flemming](https://github.com/luca-flemming) - Undergraduate Student

[Nicholas del Grosso](https://github.com/nickdelgrosso) - RSE Advisor

## Contributing
If you would like to contribute to the AutoGaitA toolbox, feel free to open a pull request or contact us at autogaita@fz-juelich.de! 

We are looking forward to your input and ideas 😊

## Archive
We have archived the resources of outdated AutoGaitA versions here:

- v0.3.1 - [YouTube Tutorials](https://youtube.com/playlist?list=PLCn5T7K_H8K776DLuXKoPsUpI6Yb0NU33&si=7ZAAvcrPxR7WsB8a) & [Documentation](https://docs.google.com/document/d/11mJd7jUHk7joQ0BdZT98CJRrIANdyosMQMJGFtp6yR4/edit?usp=sharing)
