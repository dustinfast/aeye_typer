# Fast AEye TypeR

An accessibility tool (WIP) attempting to allow hands free mouse and keyboard use via an eye-tracker and wearable bran-scanner.

This tool differs from existing solutions in that

* It is inteded for use in a linux environment
* The rate of typing is intended to be on par with a proficient typist's WPM rate.
*  Use is based on eye movement and thought alone - i.e. a completely paralyzed but fully conscious person may use it.

Author: Dustin Fast <dustin.fast@hotmail.com>

## Usage

### Setup

First, clone the applications repo and build the docker image with

```bash
cd docker
./build.sh
```

Then run/enter the docker container with

```bash
cd ../
./open_container.sh LOCAL_APP_DATA_DIRECTORY_PATH
```  

Once inside the container, get the device ID's of your mouse and keyboard with `xinput'. E.g.  

``` bash
$ xinput
⎡ Virtual core pointer              id=2    [master pointer  (3)]
⎜   ↳ Virtual core XTEST pointer    id=4    [slave  pointer  (2)]
⎜   ↳ DELL Laser Mouse              id=11   [slave  pointer  (2)] # Mouse
⎜   ↳ SynPS/2 Synaptics TouchPad    id=15   [slave  pointer  (2)]
⎣ Virtual core keyboard             id=3    [master keyboard (2)]
    ↳ Virtual core XTEST keyboard   id=5    [slave  keyboard (3)]
    ↳ Power Button                  id=6    [slave  keyboard (3)]
    ↳ Video Bus                     id=7    [slave  keyboard (3)]
    ↳ Video Bus                     id=8    [slave  keyboard (3)]
    ↳ Power Button                  id=9    [slave  keyboard (3)]
    ↳ Sleep Button                  id=10   [slave  keyboard (3)]
    ↳ Dell Keyboard                 id=12   [slave  keyboard (3)] # Keyboard
```

Then update `_config.yaml` with those IDs. For example:  

```yaml
DEVICE_ID_MOUSE: "11"
DEVICE_ID_KEYBOARD: "12"
```

Next, run `./setup.sh`, and calibrate the eye-tracker with ...  

With these steps complete, you may wish to commit your changes to the docker container with ``docker commit ...`.

### Data Collection

Start data collection with `./log_event_data.out`. Keystrokes, mouse clicks, etc., are then logged to the SQLite databse given in `_config.yaml`.

### Training

Not Implemented

### Inference

Not Implemented

## Ideas

"Symbol" mode (e.g. 'if', 'else') versus "Key" mode (e.g. 'i', 'f', 'e', 'l', 's', 'e')

Speaking as you type, because it involves more neurons.



## TODO

* Add gaze logging on key AND mouse click
* Fix: Mouse clicks not registered by vscode
* Rename LogKeys to EventLogger
