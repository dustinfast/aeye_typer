# Fast AEye TypeR

An accessibility tool (WIP) attempting to allow hands free mouse and keyboard use via an eye-tracker and wearable bran-scanner.

This tool differs from existing solutions in that

* It is inteded for use in a linux environment
* The rate of typing is intended to be on par with a proficient typist's WPM rate.
*  Use is based on eye movement and thought alone - i.e. a completely paralyzed but fully conscious person may use it.

Author: Dustin Fast <dustin.fast@hotmail.com>

## What's in a name?

Fast AEye TypeR is named after it's creator and with the word "typer" having the last letter capitalized as a nod to his adventurous spirit embodied by his car -- a Honda Civic Type R.

## Usage

First, build the docker image with

```bash
cd docker
./build.sh
```

Then run the docker container with `./run.sh LOCAL_CODEBASE`, where LOCAL_CODE_BASE is the path to the application's codebase on your local machine.  

Once inside the container, get the device ID's of your mouse and keyboard using `xinput'. E.g.  

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

Then update `DEVICE_ID_MOUSE` and `DEVICE_ID_KEYBOARD` in _config.yaml with the appropriate IDs. E.g.

```yaml
DEVICE_ID_MOUSE: 11
DEVICE_ID_KEYBOARD: 12
```

Next, run `./setup.sh`, then start the application with `./fast_aeye_typer.py`

## Ideas

"Symbol" mode (e.g. 'if', 'else') versus "Key" mode (e.g. 'i', 'f', 'e', 'l', 's', 'e')

## TODO

Mouse clicks not registered by vscode