import os
from pathlib import Path
import ffmpeg
import sys
import logging
import os
import re
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

silence_start_re = re.compile(' silence_start: (?P<start>[0-9]+(\.?[0-9]*))$')
silence_end_re = re.compile(' silence_end: (?P<end>[0-9]+(\.?[0-9]*)) ')
total_duration_re = re.compile(
    'size=[^ ]+ time=(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9\.]{5}) bitrate=')

def _logged_popen(cmd_line, *args, **kwargs):
    logger.debug('Running command: {}'.format(subprocess.list2cmdline(cmd_line)))
    return subprocess.Popen(cmd_line, *args, **kwargs)

def get_chunk_times(in_filename, silence_threshold, silence_duration, start_time=None, end_time=None):
    input_kwargs = {}
    if start_time is not None:
        input_kwargs['ss'] = start_time
    else:
        start_time = 0.
    if end_time is not None:
        input_kwargs['t'] = end_time - start_time

    p = _logged_popen(
        (ffmpeg
            .input(in_filename, **input_kwargs)
            .filter('silencedetect', n='{}dB'.format(silence_threshold), d=silence_duration)
            # .filter('silencedetect', noise=0.0001)
            .output('-', format='null')
            .compile()
        ) + ['-nostats'],  # FIXME: use .nostats() once it's implemented in ffmpeg-python.
        stderr=subprocess.PIPE
    )
    output = p.communicate()[1].decode('utf-8')
    if p.returncode != 0:
        sys.stderr.write(output)
        sys.exit(1)
    logger.debug(output)
    lines = output.splitlines()

    # Chunks start when silence ends, and chunks end when silence starts.
    chunk_starts = []
    chunk_ends = []
    for line in lines:
        silence_start_match = silence_start_re.search(line)
        silence_end_match = silence_end_re.search(line)
        total_duration_match = total_duration_re.search(line)
        if silence_start_match:
            chunk_ends.append(float(silence_start_match.group('start')))
            if len(chunk_starts) == 0:
                # Started with non-silence.
                chunk_starts.append(start_time or 0.)
        elif silence_end_match:
            chunk_starts.append(float(silence_end_match.group('end')))
        elif total_duration_match:
            hours = int(total_duration_match.group('hours'))
            minutes = int(total_duration_match.group('minutes'))
            seconds = float(total_duration_match.group('seconds'))
            end_time = hours * 3600 + minutes * 60 + seconds

    if len(chunk_starts) == 0:
        # No silence found.
        chunk_starts.append(start_time)

    if len(chunk_starts) > len(chunk_ends):
        # Finished with non-silence.
        chunk_ends.append(end_time or 10000000.)

    return list(zip(chunk_starts, chunk_ends))

def frames_to_timecode(total_frames, frame_rate, drop):
    """
    Method that converts frames to SMPTE timecode.
    
    :param total_frames: Number of frames
    :param frame_rate: frames per second
    :param drop: true if time code should drop frames, false if not
    :returns: SMPTE timecode as string, e.g. '01:02:12:32' or '01:02:12;32'
    """
    if drop and frame_rate not in [29.97, 59.94]:
        raise NotImplementedError("Time code calculation logic only supports drop frame "
                                  "calculations for 29.97 and 59.94 fps.")

    fps_int = int(round(frame_rate))

    if drop:
        FRAMES_IN_ONE_MINUTE = 1800 - 2

        FRAMES_IN_TEN_MINUTES = (FRAMES_IN_ONE_MINUTE * 10) - 2

        ten_minute_chunks = total_frames / FRAMES_IN_TEN_MINUTES
        one_minute_chunks = total_frames % FRAMES_IN_TEN_MINUTES

        ten_minute_part = 18 * ten_minute_chunks
        one_minute_part = 2 * ((one_minute_chunks - 2) / FRAMES_IN_ONE_MINUTE)

        if one_minute_part < 0:
            one_minute_part = 0

        # add extra frames
        total_frames += ten_minute_part + one_minute_part

        # for 60 fps drop frame calculations, we add twice the number of frames
        if fps_int == 60:
            total_frames = total_frames * 2

        # time codes are on the form 12:12:12;12
        smpte_token = ";"

    else:
        # time codes are on the form 12:12:12:12
        smpte_token = ":"

    # now split our frames into time code
    hours = int(total_frames / (3600 * fps_int))
    minutes = int(total_frames / (60 * fps_int) % 60)
    seconds = int(total_frames / fps_int % 60)
    frames = int(total_frames % fps_int)
    return "%02d:%02d:%02d%s%02d" % (hours, minutes, seconds, smpte_token, frames)