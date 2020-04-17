# Fast AEye TypeR

An accessibility tool (WIP) attempting to allow hands free mouse and keyboard use via an eye-tracker and wearable bran-scanner.

This tool differs from existing solutions in that

* It is inteded for use in a linux environment
* The rate of typing is intended to be on par with a proficient typist's WPM rate.
*  Use is based on eye movement and thought alone - i.e. a completely paralyzed but fully conscious person may use it.

Author: Dustin Fast <dustin.fast@hotmail.com>

## Usage

### Setup

First, clone the applications repo and build the docker image with --

```bash
cd docker
./build.sh
```

Then run/enter the docker container with --  

```bash
cd ../
./run_docker_cont.sh LOCAL_APP_DATA_DIRECTORY_PATH
```  

#### Eye Tracker Installation

1. Install the eye-tracker and compile binaries with `./setup.sh`.

2. From a local terminal (outside the container) commit the install to the container with ``docker commit fast_aeye_typer fast_aeye_typer:latest`.  

3. Restart the container (this time from inside the container) with an `exit` followed by `./open_container.sh`.  

4. Verify your eye-tracker is correctly installed with `./tobii_cam_test.out`.

#### OpenBCI EEG Installation

...

### Data Collection

Start data collection with `./log_event_data.py`. Keystrokes, mouse clicks, EEG data, etc., are then logged to the paths given by `_config.yaml`.


### Training

Data collected must first be converted for use by the ML algorithms with `rawdata_to_sql.py`.

### Inference

Not Implemented

## Ideas

"Symbol" mode (e.g. 'if', 'else') versus "Key" mode (e.g. 'i', 'f', 'e', 'l', 's', 'e')

Speaking as you type, because it involves more neurons.

Use autoencoder to filter out when brain scanner giving poor reading -- i.e. not wearing earclips, not turned on, low-battery, etc.

## TODO

* Add gaze logging on key AND mouse click
* Add rawdata_to_sql
* Add anamoly detection
