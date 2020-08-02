# AEye Typer

Hands-free Artificial Intelligence-assisted keyboard and mouse.... An open-source work in progress.

This application, conceived in early 2020 following my Amyotrophic Lateral Sclerosis (ALS, AKA Lou-Gehrig's Disease) diagnosis, is intended to provide a mechanism by which I may continue my Software Engineering and Artificial Intelligence work after I lose the use of my hands to the disease.  

Development is in the spirit that, if succesful, the technology may be beneficial to others.

Author: Dustin Fast <dustin.fast@outlook.com>, 2020

## Overview

AEye Typer is an accessibility tool with the goal of allowing hands-free use of a virtual mouse (vMouse) and keyboard (vKeyb) via a screen-mounted gaze-point (GP) tracking device. It is intended to be different from existing solutions in that it

* May be utilized by a fully paralyzed but conscious (i.e. "locked-in") individual.
* Provides a fully-featured on-screen keyboard supporting complex keystrokes and combinations.
* Allows precision and throughput comparable to physical keyboard/mice resolution/rates.
* Is robust enough to support a text-heavy workflow in a graphical linux environment. 

This will be accomplished by

* Implementing the vKeyb [STATUS: **Functional**]
* Creating a data collection pipeline for associating physical mouse-clicks with the users GP [STATUS: **Functional**]
* Improving, through the use of machine learning (ML), the inherent inaccuracy of modern gaze-tracking devices [STATUS: **Functional**]
* Developing a mouse-click inference model and pipeline, accepting as input the user's gaze activity [STATUS: Not Implemented]
* Ensuring setup and calibration are intuitive enough to be performed by, say, some other disabled individual and/or their caretaker [STATUS: Ongoing]

With this solution in place, a user may then "click" the vMouse at any desired screen coordinate through the use of eye-movement alone. "Clicking" a vKeyb button (or combination of buttons) in this way is then equivelant to a physical keystroke (or keystroke combo). Rapid typing may then be performed by flitting one's gaze to the intended vKeyb keys.

## Dependencies

(Tested on Ubuntu 18.04. Assumes a US-standard keyboard format.

* [Docker](https://docs.docker.com/engine/install/ubuntu/) v.18.09.7
* [Nvidia-Docker](https://github.com/NVIDIA/nvidia-docker)
* [Tobii 4L Eyetracking Device](https://tech.tobii.com/products/#4L) (Pro license)

## Installation

Clone this repository and build the application's docker image with  

```bash
git clone git@github.com:dustinfast/aeye_typer.git
cd aeye_typer/docker
./build.sh
cd ../
```

## Usage

Start and enter the docker container with `./aeye_docker_start.sh LOCAL_APP_DATA_DIRECTORY_PATH`, where `LOCAL_APP_DATA_DIRECTORY_PATH` is an existing local directory the application may write to. (Create one first, if necessary).

**All steps described below are in the context of this container unless otherwise noted.**

### Setup 

#### Display Device

Modify fields `DISP_WIDTH_MM`, `DISP_HEIGHT_MM`, `DISP_WIDTH_PX`, and `DISP_HEIGHT_PX` in `_config.yaml` with your display device's dimensions. Note that A) The use of multiple workspaces is supported, and B) Use with multiple display devices has not been tested.

#### Eye Tracker

Device installation is handled by the docker build process, but the eyetracker must first be calibrated. To do so, ensure your device is plugged in via USB and run `./aeye_typer --calibrate`.

WARN: If calibration has previously been performed, you will be prompted to overwrite. Overwriting is not recommended unless re-training of the application's ML models will also be performed.

### Training Data Collection

The application relies on a self-generated corpus of training data. To start this process, run `./aeye_typer.py --data_collect`. Using a physical mouse the user (or caretaker, as needed) must then perform some number of mouse-clicks while gazing at the mouse cursor.

### Training

Assuming a sufficiently sized training corpus, the gaze-point accuracy-assist models may be trained with `./aeye_typer.py --train_ml`.

Note: Mouse-click inference model training is currently not implemented.

### Inference

Assuming the gaze-point accuracy improvement models have been succesfully trained, run the application in inference moe with `./aeye_typer.py --infer`.

Note: Mouse-click inference is currently not implemented.
