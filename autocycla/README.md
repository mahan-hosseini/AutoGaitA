# AutoCyclA – Automated Cycling Analysis with AutoGaitA

Despite AutoGaitA being developed to facilitate and automate gait analyses after successful body posture tracking, we demonstrate with this project, AutoCyclA, that our toolbox can be adopted to any behaviour of interest as long as the kinematic features extracted in coordinate space are meaningful to the user (e.g. the 2D coordinates recorded from a lateral view of somebody cycling can generate angles of interest). This demonstration further serves as a broad manual for analysing any rhythmic behaviour using AutoGaitA.

## Aim

For enthusiastic cyclists the correct set up of their bike is critical to ensure optimal and injury free performance. An important aspect that requires careful adjustments is the positioning of the saddle and handlebar. The optimal position can be derived from various angles, such as that of the hip and the knee. To identify these angles one traditionally visits a bike shop and pays a substantial sum for a professional bike fitting.

With [AutoGaitA](https://github.com/mahan-hosseini/AutoGaitA) and [Deeplabcut (DLC)](https://github.com/DeepLabCut/DeepLabCut) we have been able to measure cyclists’ body angles in a home set up. With this approach, cyclists can fine tune their own bike set up independently without depending on bike shops. \
One of the main results our approach generates is a figure plotting the leg’s three angles (ankle, knee, and hip) over the cyclist’s average pedal cycle.

<div align="center">

|<img src=images/figure_1.png alt="figure 1" width="500" height="397">|
|:--:|
| ***Figure 1**: Analysis of one video in the sitting/hands-high condition; graph showing ankle, knee and hip angles throughout an average pedal cycle* |

</div>

## Tools

-	Camera (smartphone camera suffices)
-	Indoor bike trainer
-	A PC with DLC, AutoGaitA and Excel (or Excel like program) installed

## Workflow

### Deeplabcut

After installing and setting up [Python](https://www.python.org/downloads/) and [Deeplabcut](https://deeplabcut.github.io/DeepLabCut/docs/installation.html), a side view video of a person cycling in a home set up was recorded. It was filmed with a smartphone camera at 30 FPS and good lighting conditions. Consistent lighting conditions facilitate AI model training and subsequent analysis substantially.

The DeepLabCut workflow for model training was followed, which involved extracting frames from the video, labeling them, and then starting the training process. The following labels were tracked:
1 wrist,
2 elbow,
3 shoulder,
4 hip,
5 knee,
6 ankle,
7 heel
and the
8 ball of the foot.

Since the cycling motion is simple and repeated in a constant and narrow area of the video frame, good tracking results were achieved quickly (i.e., requiring a small number of labeled frames). In total, 40 frames sufficed. Model training was similarly straightforward and quick, requiring just 40.000 iterations until the loss plateaued.

Please note that the same set up for training and later analysis was used in this demonstration. Users planning to use different bikes, clothes, lighting or even locations most likely need to record multiple videos, extract and label more frames and train the model for a longer time.

After the loss plateaued the network was evaluated and reached a train and test error of about 2.25-2.5 pixel.

<div align="center">


|<img src=images/table_1.png alt="table 1" width="600" height="100">|
|:--:|
| ***Table 1**: Model evaluation results* |

</div>

In the next step videos were analysed to generate kinematic data. Here it is important to save the file as a .CSV file in order to use AutoGaitA DLC. It is further important to name video files according to [the AutoGaitA DLC file naming convention](https://docs.google.com/document/d/1Y4wrrsjs0ybLDKPzE2LAatqPDq9jtwjIuk4M0jRZ3wE/edit#heading=h.7sftrmrzayvk). Following the convention’s [A]\_[B]\_[C]_[D] structure an example filename could be "bike1_me_setting1_video1". In case another video with a different saddle position should be recorded you could for example change setting1 to setting2 and so on.

After this analysis a labeled video was additionally generated for visually inspecting how successful the tracking was overall. 

<div align="center">

|<img src=images/figure_2.png alt="figure 2" width="400" height="400">|
|:--:|
| ***Figure 2**: Illustration of cyclist with DLC-tracked joints. Each point represent an AI generated marker that is tracked throughout the entire video. Note that AutoCyclA's real videos are not provided to preserve privacy*. Photo by <a href="https://unsplash.com/@cathus?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Garry Neesam</a> on <a href="https://unsplash.com/photos/timelapse-photography-of-man-riding-bicycle-XgWBNUsIvOE?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Unsplash</a>
   
</div>

### AutoGaitA

After successful tracking with DLC the generated videos and .CSV files can now be analysed with AutoGaitA. AutoGaitA DLC’s workflow was followed to analyse all tracked videos. Subsequently, AutoGaitA Group was used to compare different cycling positions (standing versus sitting on the saddle with two different positions of the hands on the handle bar (high or low)) to assess how the angles of interest would change. Different cycling configurations were used as different “groups” while configuring AutoGaitA Group. 

AutoGaitA Group generates various figures. Some of these figures are particularly relevant in the context of AutoCyclA and bike fitting, such as the figures of joint angles across the average pedal cycle for a given cycling position (see Figure 3 for the “sitting low” configuration) or the comparison of a given angle across different cycling positions (see Figure 4 for the hip).

<div align="center">

|<img src=images/figure_3.png alt="figure 3" width="500" height="397">|
|:--:|
| ***Figure 3**: Analysis of one video in the sitting/hands-low condition; plot showing ankle, knee and hip angles throughout an average pedal cycle* |

|<img src=images/figure_4.png alt="figure 4" width="500" height="397">|
|:--:|
| ***Figure 4**: Group comparison of three videos, sitting/hands-low, sitting/hands-high and standing; plot shows the hip angle throughout an average pedal cycle for each condition* |

</div>

The “Average Stepcycle.xlsx” file can further be used to get the precise angles for each time bin across the average pedal cycle.

### Adjust, Analyse, Repeat

These angles can now be evaluated and the bike can be adjusted to get closer to optimal values. Naturally, these optima vary from person to person and depend on many factors, such as flexibility, body proportions and the bike itself. Nonetheless, and while keeping individual differences in mind, there are still ranges or typical optima that can be found online that serve as useful starting points. From there onwards, the bike can be further adjusted to fit personal needs.

## Conclusion

AutoCyclA showcases that AutoGaitA is not only useful for automating gait analysis further but also for the analysis of any other behaviour of interest.  We hope to have provided a useful general manual for analysing non-gait behaviour using AutoGaitA. 

Have you performed non-gait analyses using AutoGaitA or need assistance doing so? Feel free to let us know at autogaita@fz-juelich.de 😊
