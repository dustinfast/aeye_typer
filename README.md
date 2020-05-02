# Fast AEye TypeR

This application is a work in progress.  

An accessibility tool for allowing hands free use of a mouse and keyboard via a screen-mounted eyetracker and wearable brain-scanner.

This tool is intended to differ from existing accessibility solutions in that

* It is inteded for use in a linux environment
* Use is based on eye movement and thought alone - i.e. a paralyzed but fully conscious person may use it.
* The rate of typing (WPM) is intended to be on par with that of a proficient typist's.

Proof of concept will be accomplished through the following steps:

1. Keystrokes, mouse clicks, EEG signals, and gaze-point data are recorded while a participant uses the application in Data Collection mode.

2. Machine learning models will be built and trained to infer when user is typing, clicking, or scroll-wheeling from the EEG and eyetracker data streams.

3. Machine learning models will be built and trained to infer keystrokes, mouse clicks/scrolls, and cursor location from the EEG and eyetracker data streams.

Author: Dustin Fast <dustin.fast@hotmail.com>

## Setup

Clone this repo, then build the application's docker image with  

```bash
cd docker
./build.sh
```

Tested on Ubuntu 18.04 with Docker 18.09.7

## Usage

Enter the docker container with  

```bash
./run_docker_cont.sh LOCAL_APP_DATA_DIRECTORY_PATH
```  

#### Eye-Tracker Installation

Device: Tobii 4L  

Device installation is handled by the docker build process. To verify installation, run `test_eyetracker.py`. 

The eyetracker must now be calibrated with `tobiiproeyetrackermanager`.

#### EEG Installation

Device: OpenBCI Cyton  

Device installation is handled by the docker build process. To verify your BCI installation run `./test_eeg_conn.sh`.

### Data Collection

Start data collection with `./collect_data.py`. Keystrokes, mouse clicks, EEG signals, and gaze-point data are then logged to the paths denoted in `_config.yaml`.

### Training

Not Implemented

### Inference

Not Implemented

## Ideas

"Symbol" mode (e.g. 'if', 'else') versus "Key" mode (e.g. 'i', 'f', 'e', 'l', 's', 'e')

Speaking as you type, because it involves more neurons.

Use autoencoder to filter out when brain scanner giving poor reading -- i.e. not wearing earclips, not turned on, low-battery, etc.

## TODO

* Add caret location to key logger
* Add rawdata_to_sql
* Add anamoly detection
* Data filtering: Remove all key events w/no associated EEG and/or eye data
* Data filtering: Remove all eeg events outside of known good events
* Dashboard denoting status (tobii_user_position_guide_subscribe, etc)
* Log user position, etc., from eye-tracker and use to improve gaze point accuracy.