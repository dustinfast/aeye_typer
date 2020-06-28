# AEye Typer

In early 2020 I was diagnosed with Amyotrophic Lateral Sclerosis (ALS, AKA Lou-Gehrig's Disease). This application is intended to give myself the ability to continue my Computer Science and Artificial Intelligence (AI) work long after I lose the dexterity required to operate a physical mouse and keyboard. It is a work in progress.

Author: Dustin Fast <dustin.fast@outlook.com>, 2020

## Overview

This application is an accessibility tool for allowing hands free use of a virtual mouse and keyboard via a screen-mounted eyetracker and (possibly) a wearable brain-computing interface (BCI). It is intended to differ from existing solutions in that it

* May be utilized by a fully paralyzed but conscious (i.e. "locked-in") individual.
* Exposes a virtual, fully-featured keyboard capable of accepting complex keystroke combinations.
* Allows virtual typing/clicking at rates/precisions comparable to physical keyboards/mice.
* Does not constrain the user to a collection of pre-defined words/phrases.
* Supports a text-heavy workflow in a graphical linux environment. 
* In the context of gaze-tracking accuracy, is display-size and user-position agnsotic.

This will be accomplished by

* Implementing a fully-featured on-screen virtual keyboard. [STATUS: Functional]
* Creating data collection pipelines for associating physical mouse-clicks/keystrokes with the users gaze activity. [STATUS: Functional]
* Improving, through the use of machine learning, the inherent inaccuracy of modern "one-size fits all" gaze-tracking devices. [STATUS: Partially Implemented]
* Developing mouse-click inference models, accepting as input the user's gaze activity. [STATUS: Not Implemented]

In this way, a user may click the mouse at any location using eye-movement alone. If the user chooses to click a virtual keyboard button, that key is then "virtually" pressed as if it were a physical keystroke.  

## Dependencies

(Tested on Ubuntu 18.04, dockerized with Docker 18.09.7)

* [Docker](https://docs.docker.com/engine/install/ubuntu/)
* [Nvidia-Docker](https://github.com/NVIDIA/nvidia-docker)
* [Tobii 4L IS4](https://tech.tobii.com/products/#4L) Eyetracking Device and license file
* Optional: [OpenBCI Mark IV EEG Headset](https://shop.openbci.com/collections/frontpage/products/ultracortex-mark-iv) with [8-channel Cyton board](https://shop.openbci.com/collections/frontpage/products/cyton-biosensing-board-8-channel?variant=38958638542)

## Installation

Clone this repo and build the application's docker image with  

```bash
git clone git@github.com:dustinfast/aeye_typer.git
cd aeye_typer/docker
./build.sh
cd ../
```

## Usage

Start and enter the docker container with `./aeye_docker_start.sh LOCAL_APP_DATA_DIRECTORY_PATH`, where `LOCAL_APP_DATA_DIRECTORY_PATH` is an existing local directory the application may write to.

**All steps described below are in the context of this container unless otherwise noted.**

### Setup 

#### Configuration

Modify fields `DISP_WIDTH_MM`, `DISP_HEIGHT_MM`, `DISP_WIDTH_PX`, and `DISP_HEIGHT_PX` in `_config.yaml` with your display device's dimensions. Note that A) The use of multiple workspaces is supported, and B) Use with multiple display devices has not been tested.

#### Eye-Tracker

Device installation was performed during the docker build process. To verify functionality, use `./test_eyetracker.py`. 

The eyetracker must now be calibrated with `./aeye_typer --calibrate`.

After this process, you may wish to commit calibration to the docker container with (from outside the container) `docker commit aeye_typer_c aeye_typer:latest`.

#### EEG

Device installation was performed during the docker build process. To verify your BCI installation, run `./test_eeg.sh`.

NOTE: The EEG device is optional and does not currently affect application performance. 

### Data Collection

Start data collection with `./aeye_typer.py --data_collect`. The virtual keyboard is then displayed with a red highlight to denote operation in this mode... The user (or caretaker, if needed) must then use a physical mouse to enter "virtual" keystrokes by clicking virtual keyboard buttons. During this time, the user is assumed to be gazing at each virtual keyboard button as it is clicked. In this way, a training corpus is generated.

### Training

Assuming a sufficiently sized training corpus, the gaze-point accuracy improvement models may be trained with `./aeye_typer.py --train_ml`.

Mouse-click inference model training is currently not implemented.

### Inference

Not Implemented
