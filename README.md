# AEye Typer

An open-source work in progress.

This application was conceived in early 2020 following my Amyotrophic Lateral Sclerosis (ALS, AKA Lou-Gehrig's Disease) diagnosis. It is intended to provide a means of continuing my Software Engineering/Artificial Intelligence work long after the disease progresses to the point that I'm unable able to operate a physical keyboard and mouse. Development is in the spirit that, if successful, the technology may be beneficial to others.

Author: Dustin Fast <dustin.fast@outlook.com>, 2020

## Overview

AEye Typer is an accessibility tool with the goal of allowing hands-free use of a virtual mouse (vMouse) and keyboard (vKeyb) via a screen-mounted gaze-tracking device (or possibly, in the future, a wearable brain-computing interface (BCI). It is intended to be different from existing solutions in that it

* May be utilized by a fully paralyzed but conscious (i.e. "locked-in") individual.
* Provides a fully-featured on-screen keyboard supporting complex keystrokes and combinations.
* Allows precision and throughput comparable to physical keyboard/mice resolution/rates.
* Is robust enough to support a text-heavy workflow in a graphical linux environment. 

This will be accomplished by

* Implementing the vKeyb [STATUS: **Functional**]
* Creating data collection pipelines for associating physical mouse-clicks/keystrokes with the users gaze activity [STATUS: **Functional**]
* Improving, through the use of machine learning (ML), the inherent inaccuracy of modern gaze-tracking devices [STATUS: Partially Implemented (~75%)]
* Developing a mouse-click inference model and pipeline, accepting as input the user's gaze activity [STATUS: Not Implemented]
* Ensuring setup and calibration are intuitive enough to be performed by, say, some other disabled individual or their caretaker.  [STATUS: Ongoing]

With this solution in place, a user may then "click" the vMouse at any desired screen coordinate through the use of eye-movement alone. "Clicking" a vKeyb button (or combination of buttons) in this way is then equivelant to a physical keystroke (or keystroke combo). Rapid typing may then be performed by flitting one's gaze to the intended vKeyb keys.

#### Future Functionality

The codebase currently contains modules for associating, in real-time through the use of a wearable BCI, the user's physical mouse/keystroke/gaze activity with their electroencephalogram (EEG). These modules are functional but have not yet been integrated into the main data collection pipeline described by [Data Collection](#data-collection).

EEG input does not currently affect application functionality, but the hope is that data collected in this way may faciliate future extensions of this technology.

## Dependencies

(Tested on Ubuntu 18.04. Assumes a US-standard keyboard format.

* [Docker](https://docs.docker.com/engine/install/ubuntu/) v.18.09.7
* [Nvidia-Docker](https://github.com/NVIDIA/nvidia-docker)
* [Tobii 4L Eyetracking Device](https://tech.tobii.com/products/#4L) (Pro license)
* Optional: [OpenBCI Mark IV EEG Headset](https://shop.openbci.com/collections/frontpage/products/ultracortex-mark-iv) with [8-channel Cyton board](https://shop.openbci.com/collections/frontpage/products/cyton-biosensing-board-8-channel?variant=38958638542)

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

Device installation is handled by the docker build process. To verify functionality, connect your eye-tracker via USB and run `./test_eyetracker.py`. 

The eyetracker must now be calibrated with `./aeye_typer --calibrate`.

You may now wish to commit this calibration to the docker container with (from outside the container) `docker commit aeye_typer_c aeye_typer:latest`. If not, calibration will be lost when the container is closed.

#### BCI / EEG

NOTE: The EEG device is optional and does not currently affect performance. For more info, see [Future Functionality](#future-functionality).

Device installation is handled by the docker build process. To verify functionality, ensure your device is connected via its wireless USB dongle and run `./test_eeg.sh`.

### Training Data Collection

The application relies on a self-generated corpus of training data. To start this process, run `./aeye_typer.py --data_collect`. The vKeyb is then displayed, and a red highlight denotes operation in this mode. Using a physical mouse the user (or caretaker, as needed) must then enter some number of "virtual" keystrokes by clicking vKeyb buttons. During this time, the user is assumed to be gazing at the center of each vKeyb button as it is clicked. In this way, a training corpus is generated.

WARNING: The "virtual" keystrokes are logged as part of this process. Please ensure no sensitive information is entered into the vkeyb during this time.

### Training

Assuming a sufficiently sized training corpus, the gaze-point accuracy improvement models may be trained with `./aeye_typer.py --train_ml`.

Mouse-click inference model training is currently not implemented.

### Inference

Not Implemented
