import errno
import os

import numpy as np
import pretty_midi
import pypianoroll

ROOT_PATH = 'datasets'
CONVERTER_PATH = os.path.join(ROOT_PATH, 'bhairavi_test/converter')
CLEANER_PATH = os.path.join(ROOT_PATH, 'bhairavi_test/cleaner')
LAST_BAR_MODE = 'remove'


# helper functions

# return a list of path of midi files in the given path
def get_midi_path(path):
    paths = []
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.mid') or filename.endswith('.midi'):
                paths.append(os.path.join(dirpath, filename))
    return paths


# extract information from the given midi file
def get_midi_info(pm):
    if pm.time_signature_changes:
        pm.time_signature_changes.sort(key=lambda x: x.time)
        first_beat_time = pm.time_signature_changes[0].time
    else:
        first_beat_time = pm.estimate_beat_start()

    tc_times, tempi = pm.get_tempo_changes()

    if len(pm.time_signature_changes) == 1:
        time_sign = '{}/{}'.format(pm.time_signature_changes[0].numerator,
                                   pm.time_signature_changes[0].denominator)
    else:
        time_sign = None

    midi_info = {
        'first_beat_time': first_beat_time,
        'num_time_signature_change': len(pm.time_signature_changes),
        'time_signature': time_sign,
        'tempo': tempi[0] if len(tc_times) == 1 else None
    }

    return midi_info


# return multitrack instance with the piano roll merged to Bass, Drums, Guitar, Piano and Strings.
def merge_pianoroll(multitrack):
    """Return a `pypianoroll.Multitrack` instance with piano-rolls merged to
    five tracks (Bass, Drums, Guitar, Piano and Strings)"""
    category_list = {'Bass': [], 'Drums': [], 'Guitar': [], 'Piano': [], 'Strings': []}
    program_dict = {'Piano': 0, 'Drums': 0, 'Guitar': 24, 'Bass': 32, 'Strings': 48}

    for idx, track in enumerate(multitrack.tracks):
        if track.is_drum:
            category_list['Drums'].append(idx)
        elif track.program // 8 == 0:
            category_list['Piano'].append(idx)
        elif track.program // 8 == 3:
            category_list['Guitar'].append(idx)
        elif track.program // 8 == 4:
            category_list['Bass'].append(idx)
        else:
            category_list['Strings'].append(idx)

    tracks = []
    for key in category_list:
        if category_list[key]:
            merged = multitrack.blend()
            tracks.append(pypianoroll.Track(key, program_dict[key], key == 'Drums', merged))
        else:
            tracks.append(pypianoroll.Track(key, program_dict[key], key == 'Drums', None))
    return pypianoroll.Multitrack(multitrack.name, multitrack.resolution, multitrack.tempo, multitrack.downbeat, tracks)


def path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


# convert midi file to multi-track piano-roll and save to a particular dataset directory
def convert_midi_to_pianoroll(path):
    try:
        midi_name = os.path.splitext(os.path.basename(path))[0]
        print(midi_name)
        pm = pretty_midi.PrettyMIDI(path)
        midi_info = get_midi_info(pm)
        print(midi_info)
        multitrack = pypianoroll.from_pretty_midi(pm)
        merged = merge_pianoroll(multitrack)
        print(merged)
        path_exists(CONVERTER_PATH)
        merged.save(os.path.join(CONVERTER_PATH, midi_name + '.npz'))
        return [midi_name, midi_info]

    except:
        return None


def midi_filter(midi_info):
    if midi_info['first_beat_time'] > 0.0:
        return False
    elif midi_info['num_time_signature_change'] > 1:
        return False
    # elif midi_info['time_signature'] not in ['4/4']:
    #     return False
    return True


def get_bar_piano_roll(piano_roll):
    if int(piano_roll.shape[0] % 64) != 0:
        if LAST_BAR_MODE == 'fill':
            piano_roll = np.concatenate((piano_roll, np.zeros((64 - piano_roll.shape[0] % 64, 128))), axis=0)
        elif LAST_BAR_MODE == 'remove':
            piano_roll = np.delete(piano_roll, np.s_[-int(piano_roll.shape[0] % 64):], axis=0)
    piano_roll = piano_roll.reshape(-1, 64, 128)
    return piano_roll
