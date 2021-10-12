# Automatic Davinci Resolve Editor
The project aims to automatically prepare jumpcuts based on silence detection and embedded timecodes in the videos

## Assumptions
- You are editing on Davinci Resolve
- You have already setup the pre-requisites for Davinci Resolve scripting
- All the videos have timecode built-in. Or else, you would have to burn the timecode yourself.
- You have already created the Resolve project and imported the media in the media pool
- You have already installed ffmpeg and have the bin in your path

## Requirements
- ffmpeg-python
- timecode
- numpy

## Parameters you can change
- file_extension = ".MOV"
- frame_rate = 59.94
- timeline_name = "sample"

## How to use
- Copy paste the two python files and requirements.txt in the folder containing the videos. Flat structure is required
- Open CMD, cd to the folder and run "pip install -r requirements.txt" and then "python jumpcut.py"
- Check the resolve media pool and Voila! Your timeline should be there

## Tested On
- Windows 10
- Python 3.6.0 (Wierd dependency issues with Davinci Resolve APIs)

## Common Problems
- Don't use conda. The APIs doesn't seem to work with conda
- If you are using VSCode with tabnine. Uninstall tabnine extension! (Resolve and tabnine both share the same port, I believe)

## Todo
- Automatically apply a LUT
- Apply audio denoiser
- Apply some presets I have configured in Resolve

## Reference
- Unofficial DaVinci Resolve Scripting Documentation - https://deric.github.io/DaVinciResolve-API-Docs/
- SMPTE Timecode Python library - https://github.com/eoyilmaz/timecode
- Frames to SMPTE timecode code - https://gist.github.com/manneohrstrom/8033e178cd38589b0226b45cef1dfe30