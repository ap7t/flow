import spotipy.util as util
import argparse
from spotipy import *
import os
from pifx import PIFX
import json
from random import shuffle, choice, randint
import time
from math import floor
from screen import Screen

class extSpotify(Spotify):
    def __init__(self, auth):
        Spotify.__init__(self, auth)

    def start_playback(self, device_id = 'efa79d094f50b14182691a57622a5c6f72a99b52', context_uri = None, uris = None, offset = None, position_ms = None):
        ''' Start or resume user's playback.
            Provide a `context_uri` to start playback or a album,
            artist, or playlist.
            Provide a `uris` list to start playback of one or more
            tracks.
            Provide `offset` as {"position": <int>} or {"uri": "<track uri>"}
            to start playback at a particular offset.
            Parameters:
                - device_id - device target for playback
                - context_uri - spotify context uri to play
                - uris - spotify track uris
                - offset - offset into context by index or track
                - position_ms - position to start playback
        '''
        if context_uri is not None and uris is not None:
            self._warn('specify either context uri or uris, not both')
            return
        if uris is not None and not isinstance(uris, list):
            self._warn('uris must be a list')
            return
        data = {}
        if context_uri is not None:
            data['context_uri'] = context_uri
        if uris is not None:
            data['uris'] = uris
        if offset is not None:
            data['offset'] = offset
        if position_ms is not None:
            data['position_ms'] = position_ms
        return self._put(self._append_device_id("me/player/play", device_id), payload=data)

def convert_ms(t):
    """ Convert milliseconds to mm:ss notation"""
    return f'{floor(int((t / 1000))) // 60}:{floor(int(t // 1000)) % 60:0>2}'

def get_details(sp):
    """ Return a dictionary with the keys song, artist, uri and progress_ms, is_playing for currently playing song"""
    results = sp.current_playback()
    song = results['item']['name']
    uri = results['item']['uri']
    artist = results['item']['artists'][0]['name']
    album = results['item']['album']['name']
    progress_ms = results['progress_ms']
    is_playing = results['is_playing']

    return {'song':song, 'artist':artist, 'album': album, 'uri':uri, 'progress_ms':progress_ms, 'is_playing':is_playing}

def generate_random_colour():
    num = randint(0, 16777215) 
    hex_num = '#' + f'{hex(num)[2:]}'.zfill(6)
    return hex_num

def main():
    username = os.getenv('SPOTIFY_USER_ID')

    lifx_key = os.getenv('LIFX_KEY')
    scope = 'user-read-currently-playing user-read-playback-state user-modify-playback-state'
    spotify_token = util.prompt_for_user_token(username, scope)
    
    sp = extSpotify(auth=spotify_token) if spotify_token else print('Cannot get Spotify token')
    light = PIFX(lifx_key)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s',  '--strobe', action='store_true', help='Strobe to the BPM of a song (changes based on tempo changes)')
    parser.add_argument('-b',  '--breathe', action='store_true', help='Breathe to the BPM of a song (changes based on tempo changes)')
    parser.add_argument('-m', '--mixed', action='store_true', help='Changes between stobing and breathing to BPM of a song (changes based on loudness changes)')
    parser.add_argument('-t',  '--tempo', action='store_true', help='Relative changes in tempo between sections will not change the period of light effect')

    args = parser.parse_args()

    with open('colours.json', 'r') as fp:
        colours = json.load(fp)

    all_colours = [h for t, c in colours.items() for n, h in c.items()]
    shuffle(all_colours)
    try:
        details = get_details(sp)
        uri = details['uri']
        # device = sp.devices()['devices'][0]['id']
        if not details['is_playing']:
            sp.start_playback(uris=[uri], position_ms=details['progress_ms'])

        sections = sp.audio_analysis(uri)['sections']
        sect_ends = [(sections[i]['start'] + sections[i]['duration'])*1000 for i in range(len(sections))]

        i = 0
        j = 0
        redish = ['red', 'orange', 'pink', 'brown']
        not_reddish = ['blue', 'cyan', 'green', 'purple']
        shuffle(redish)
        shuffle(not_reddish)
        colour_types = []

        for ind, not_red in enumerate(not_reddish):
            colour_types.append(not_red)
            colour_types.append(redish[ind])
        while len(sect_ends) > len(colour_types):
            colour_types *= 2

        cur_time = sp.current_playback()['progress_ms']

        iterations = 0
        prev_tempo = 0
        # prev_tempo_change = ''
        prev_loudness = 0
        prev_colour_type = ''
        prev_colour_name = 'Normal colour'
        prev_colour = 'hue:240 kelvin:9000'
        delays = []

        for ind, sect_end in enumerate(sect_ends):
            if cur_time > sect_end:
                continue 

            loudness = sections[ind]['loudness']
            tempo = sections[ind]['tempo']
            duration = sections[ind]["duration"]
            totalbeats = (duration / 60) * tempo
            time_interval_per_beat = ((duration/ totalbeats) / 1)
            tempo_change = "" if ind == 0 else '+' if tempo - prev_tempo > 0 else '-'
            loudness_change = "" if ind == 0 else '+' if loudness - prev_loudness > 0 else '-' # if 

            if not args.tempo:
                speed = 2 if tempo_change in ['', '-'] else 1
            else:
                speed = 2

            p = time_interval_per_beat*speed
            cyc = totalbeats / speed

            if args.mixed:
                if loudness_change == '+':
                    args.strobe = True
                    args.breathe = False
                elif loudness_change in ['', '-']:
                    args.strobe = False 
                    args.breathe = True
                    
            type_col = colour_types[ind]
            while type_col is prev_colour_type:
                type_col = choice(colour_types)
            
            
            colour_keys = list(colours[type_col].keys())
            # midpoint = len(colour_keys) // 2
            # colour_keys = colour_keys[:midpoint] if loudness_change == '+' else colour_keys[midpoint:]
            rand_col = choice(colour_keys)
            colour = colours[type_col][rand_col]

            t0 = 0
            light.set_state(color=colour, brightness=1.0)
            to_colour = '#000000'


            if args.strobe:
                t0 = time.time()
                light.pulse_lights(color=to_colour, period=p, cycles=cyc)
            elif args.breathe:
                t0 = time.time()
                light.breathe_lights(color=to_colour, period=p, cycles=cyc)
            else:
                t0 = time.time()
                light.set_state(color=colour, brightness=1.0)

            t1 = time.time()
            delay = (t1 - t0) * 1000
            delays.append(delay)
            avg_delay = sum(delays)/len(delays)
            cur_time = sp.current_playback()['progress_ms']
            
            while cur_time < sect_end - avg_delay: 
                details = get_details(sp)
                iterations +=1
                check_song = details['uri']

                if not details['is_playing']:           # pause effect until playback starts again
                    light.set_state(color=colour, brightness=1.0)
                    duration = (sections[ind]["duration"] + sections[ind]['start']) * 1000 - details['progress_ms']
                    totalbeats = (duration / 60) * tempo
                    cyc = totalbeats / speed
                    details = get_details(sp)
                    while not details['is_playing']:
                        details = get_details(sp)
                    if args.strobe:
                        light.pulse_lights(color=to_colour, period=p, cycles=cyc)   
                    elif args.breathe:
                        light.breathe_lights(color=to_colour, period=p, cycles=cyc)
                    else:
                        light.set_state(color=colour, brightness=1.0)



                if uri != check_song:
                    os.system('clear')
                    print('Changing song')
                    main()
                
                os.system('clear')

                print(f"Song: {details['song']}") 
                print(f"Artist: {details['artist']}")
                print(f"Album: {details['album']}")
                print(f'Duration: {convert_ms(sect_ends[-1])}\n')
                print(f'Section: {ind + 1}/{len(sect_ends)}')
                print(f'Current position: {convert_ms(cur_time)}')
                print(f'When it\'ll change: {convert_ms(sect_end)}\n')
                print(f'Colour: {type_col.title()}\nShade: {rand_col.title()}\n')
                print(f'Change in tempo: {tempo_change}')
                print(f'Change in loudness: {loudness_change}')
            
                cur_time = get_details(sp)['progress_ms']


            os.system('clear')

            prev_tempo = tempo
            prev_loudness = loudness
            prev_colour_name = rand_col
            prev_colour = colour


        
        sp.next_track()
        main()


    except TypeError:
        os.system('clear')
        print('No currently playing song')
        main()

    except ZeroDivisionError:
        main()
    
    except KeyboardInterrupt:
        os.system('clear')
        light.set_state(color='hue:240 kelvin:9000', power='on', brightness=1.0) # my usual colour
        sp.pause_playback()
        quit()
    
    except SpotifyException:
        os.system('clear')
        print('Access token expired')
        time.sleep(5)
        main()


if __name__ == "__main__":
    main()
    
