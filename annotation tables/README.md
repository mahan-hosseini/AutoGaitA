# Annotation Tables

In this folder we provide template and example Annotation Tables for *AutoGaitA DLC* and *AutoGaitA Universal 3D*. Users are advised to first watch our **[instruction videos on YouTube](https://youtube.com/playlist?list=PLCn5T7K_H8K56NIcEsfDK664OP7cN_Bad&si=mV5p2--nYvbofkPh)**, then fill out a template Annotation Table with their time information and use the example Annotation Tables to confirm correct formatting.

## General Recommendations
1. Enter time in seconds with time of videos starting at zero (i.e., the first frame corresponds to 1 / sampling rate (in Hz) seconds) 
2. Please save .xlsx files.
3. Please use numeric columns for time stamps (text columns are not recommended but in theory work if you use dots for decimals (e.g. 2.58)).
4. Please define step-cycles as the start of one swing-phase to the end of the subsequent stance-phase/start of the next swing-phase.
5. If you analyse behaviour other than gait, just use the swing(ti) and stance(te) columns for entering the start and end times of each occurrence of the behaviour of interest.
6. We recommend that you have separate Annotation Tables and data-folders (!) for separate conditions (genotypes, task, age, etc.)

## About Universal 3D's Annotation Tables
AutoGaitA Universal 3D was developed using locomotion data in which human subjects walked back and forth along the Y-dimension. We therefore implemented different rows of annotation table entries for a given subject to reflect runs of "back and forth behaviour", i.e. after each turn a new "run" of that subject would start and the timestamps of that run would be entered in a new row of the annotation table. The option to standardise the direction of movement [section A.4. in the documentation](https://docs.google.com/document/d/1iQxSwqBW3VdIXHm-AtV4TGlgpJPDldogVx6qzscsGxA/edit?tab=t.0#heading=h.q1788xctph82) then allows different runs to be compared (see the documentation for details). 
- **Important** If you do not have such a "back and forth" design, either uncheck the option to standardise the direction of movement or simply enter all timestamps in the first row for each subject.

## A helpful tool
Users working with ImageJ/FIJI are encouraged to use the lightweight and open-source [AnnotationTable-Plugin](https://github.com/luca-flemming/AnnotationTable-Plugin) developed by our contributor Luca Flemming. This plugin is easy to set up and simplifies the creation of Annotation Tables drastically by removing the necessity of noting down timestamps by hand. 

## Contents
- DLC Annotation Table Template
- DLC Annotation Table Example 
- Universal 3D Annotation Table Template
- Universal 3D Annotation Table Example