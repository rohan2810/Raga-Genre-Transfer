import json
import shutil

from helper_functions import *
from utils import *

ROOT_PATH = 'datasets'
MUSIC_STYLE = "bhairavi"
TEST_PATH = 'MIDI/' + MUSIC_STYLE + '/' + MUSIC_STYLE + '_test/'
CONVERTER_PATH = os.path.join(ROOT_PATH, TEST_PATH + 'converter')
CLEANER_PATH = os.path.join(ROOT_PATH, TEST_PATH + 'cleaner')
TEST_PER = 0.5
LAST_BAR_MODE = 'remove'


def divide_test_and_train():
    if not os.path.exists(os.path.join(ROOT_PATH, TEST_PATH + 'origin_midi')):
        os.makedirs(os.path.join(ROOT_PATH, TEST_PATH + 'origin_midi'))
    l = [f for f in os.listdir(os.path.join(ROOT_PATH, 'MIDI/' + MUSIC_STYLE + '/' + MUSIC_STYLE + '_midi'))]
    print(l)
    idx = np.random.choice(len(l), int(TEST_PER * len(l)), replace=False)
    print(len(idx))
    for i in idx:
        shutil.move(os.path.join(ROOT_PATH, 'MIDI/' + MUSIC_STYLE + '/' + MUSIC_STYLE + '_midi', l[i]),
                    os.path.join(ROOT_PATH, TEST_PATH + 'origin_midi', l[i]))


def convert_clean():
    midi_paths = get_midi_path(os.path.join(ROOT_PATH, 'MIDI/' + MUSIC_STYLE + '/' + MUSIC_STYLE + '_test/origin_midi'))
    midi_dict = {}
    kv_pairs = [convert_midi_to_pianoroll(midi_path) for midi_path in midi_paths]
    for kv_pair in kv_pairs:
        if kv_pair is not None:
            midi_dict[kv_pair[0]] = kv_pair[1]
    print(kv_pairs)
    with open(os.path.join(ROOT_PATH, TEST_PATH + 'midis.json'), 'w') as outfile:
        json.dump(midi_dict, outfile)

    print("[Done] {} files out of {} have been successfully converted".format(len(midi_dict), len(midi_paths)))

    with open(os.path.join(ROOT_PATH, TEST_PATH + 'midis.json')) as infile:
        midi_dict = json.load(infile)
    count = 0
    path_exists(CLEANER_PATH)
    midi_dict_clean = {}
    for key in midi_dict:
        if midi_filter(midi_dict[key]):
            midi_dict_clean[key] = midi_dict[key]
            count += 1
            shutil.copyfile(os.path.join(CONVERTER_PATH, key + '.npz'),
                            os.path.join(CLEANER_PATH, key + '.npz'))
    print(midi_dict_clean)
    with open(os.path.join(ROOT_PATH, TEST_PATH + 'midis_clean.json'), 'w') as outfile:
        json.dump(midi_dict_clean, outfile)

    print("[Done] {} files out of {} have been successfully cleaned".format(count, len(midi_dict)))


def select_clean_midi():
    if not os.path.exists(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi')):
        os.makedirs(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi'))
    l = [f for f in os.listdir(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner'))]
    print(l)
    print(len(l))
    for i in l:
        shutil.copy(os.path.join(ROOT_PATH, TEST_PATH + 'origin_midi', os.path.splitext(i)[0] + '.mid'),
                    os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi', os.path.splitext(i)[0] + '.mid'))


def merge_and_crop():
    if not os.path.exists(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi_gen')):
        os.makedirs(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi_gen'))
    if not os.path.exists(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy')):
        os.makedirs(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy'))
    l = [f for f in os.listdir(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi'))]
    print(l)
    count = 0
    for i in range(len(l)):
        try:
            # multitrack = Multitrack(resolution=4, name=os.path.splitext(l[i])[0])
            x = pretty_midi.PrettyMIDI(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi', l[i]))
            multitrack = pypianoroll.from_pretty_midi(x)

            category_list = {'Piano': [], 'Drums': []}
            program_dict = {'Piano': 0, 'Drums': 0}

            for idx, track in enumerate(multitrack.tracks):
                if track.is_drum:
                    category_list['Drums'].append(idx)
                else:
                    category_list['Piano'].append(idx)
            tracks = []
            # merged = multitrack[category_list['Piano']].get_merged_pianoroll()
            merged = multitrack.blend()
            print(merged.shape)

            pr = get_bar_piano_roll(merged)
            print(pr.shape)
            pr_clip = pr[:, :, 24:108]
            print(pr_clip.shape)
            if int(pr_clip.shape[0] % 4) != 0:
                pr_clip = np.delete(pr_clip, np.s_[-int(pr_clip.shape[0] % 4):], axis=0)
            pr_re = pr_clip.reshape(-1, 64, 84, 1)
            print(pr_re.shape)
            save_midis(pr_re, os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_midi_gen', os.path.splitext(l[i])[0] +
                                           '.mid'))
            np.save(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy', os.path.splitext(l[i])[0] + '.npy'), pr_re)
        except:
            count += 1
            print('Wrong', l[i])
            continue
    print(count)


def concat_numpy_array():
    l = [f for f in os.listdir(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy'))]
    print(l)
    train = np.load(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy', l[0]))
    print(train.shape, np.max(train))
    for i in range(1, len(l)):
        print(i, l[i])
        t = np.load(os.path.join(ROOT_PATH, TEST_PATH + 'cleaner_npy', l[i]))
        train = np.concatenate((train, t), axis=0)
    print(train.shape)
    np.save(os.path.join(ROOT_PATH, TEST_PATH + MUSIC_STYLE + '_test_piano.npy'), (train > 0.0))


def separate_phrases():
    if not os.path.exists(os.path.join(ROOT_PATH, TEST_PATH + 'phrase_test')):
        os.makedirs(os.path.join(ROOT_PATH, TEST_PATH + 'phrase_test'))
    x = np.load(os.path.join(ROOT_PATH, TEST_PATH + MUSIC_STYLE + '_test_piano.npy'))
    print(x.shape)
    count = 0
    for i in range(x.shape[0]):
        if np.max(x[i]):
            count += 1
            np.save(
                os.path.join(ROOT_PATH, TEST_PATH + 'phrase_test/' + MUSIC_STYLE + '_piano_test_{}.npy'.format(i + 1)),
                x[i])
            print(x[i].shape)
            # if count == 11216:
            #     break
    print(count)


def main():
    divide_test_and_train()
    convert_clean()
    select_clean_midi()
    merge_and_crop()
    concat_numpy_array()
    separate_phrases()


if __name__ == '__main__':
    main()
