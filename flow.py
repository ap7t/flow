import spotipy.util as util
import argparse
import spotipy
import os
from pifx import PIFX
import json
from random import shuffle, choice
import time


def convert_ms(t):
    """ Convert milliseconds to mm:ss notation"""
    return f'{int((t // 1000) // 60)}:{int((t // 1000) % 60):0>2}'

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

def main(breathe: bool = False, bpm=False, strobe=False):
    username = os.getenv('SPOTIFY_USER_ID')

    lifx_key = os.getenv('LIFX_KEY')
    scope = 'user-read-currently-playing user-read-playback-state user-modify-playback-state'
    spotify_token = util.prompt_for_user_token(username, scope)
    
    sp = spotipy.Spotify(auth=spotify_token) if spotify_token else print('Cannot get Spotify token')
    light = PIFX(lifx_key)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s',  '--strobe', action='store_true', help='Strobe to the BPM of a song (changes based on tempo changes)')
    parser.add_argument('-b',  '--breathe', action='store_true', help='With breathe effect')

    args = parser.parse_args()

    with open('colours.json', 'r') as fp:
        colours = json.load(fp)

    try:
        details = get_details(sp)
        uri = details['uri']
        device = sp.devices()['devices'][0]['id']
        if not details['is_playing']:
            sp.start_playback(device_id=device, position_ms=details['progress_ms'])

        sections = sp.audio_analysis(uri)['sections']
        sect_ends = [(sections[i]['start'] + sections[i]['duration'])*1000 for i in range(len(sections))]

        i = 0
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

        steps = [0.1, 1.0]
        iterations = 0
        prev_tempo = 0
        prev_loudness = 0
        prev_colour_type = ''

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

            speed = 2 if tempo_change in ["", "-"] else 1 
            p = time_interval_per_beat*speed
            cyc = totalbeats / speed


            type_col = colour_types[ind]
            while type_col is prev_colour_type:
                type_col = choice(colour_types)

            colour_keys = list(colours[type_col].keys())

            rand_col = choice(colour_keys)
            
            to_colour = colours[type_col][rand_col]

            t0 = 0

            if args.strobe:
                t0 = time.time()
                light.set_state(color=to_colour, brightness=1.0)
                light.pulse_lights(color='#000000', period=p, cycles=cyc)
                        
            else:
                t0 = time.time()
                light.set_state(color=to_colour, brightness=1.0)


            t1 = time.time()
            delay = (t1 - t0) * 1000

            cur_time = sp.current_playback()['progress_ms']
            
            while cur_time < sect_end - delay: 
                start_time = time.time()
                details = get_details(sp)
                iterations +=1
                check_song = details['uri']
                if uri != check_song:
                    os.system('clear')
                    print('Changing song')
                    main()
                
                brightness = steps[i]
                os.system('clear')

                print(f"Song: {details['song']}") 
                print(f"Artist: {details['artist']}")
                print(f"Album: {details['album']}")
                print(f'Duration: {convert_ms(sect_ends[-1])}\n')
                print(f'Section: {ind + 1}/{len(sect_ends)}')
                print(f'Current position: {convert_ms(cur_time)}')
                print(f'When it\'ll change: {convert_ms(sect_end)}\n')
                print(f'Colours: {rand_col} to {to_colour}') if bpm and not strobe else print(f'Type: {type_col}\nColour: {rand_col}\n')
                print(f'Change in tempo: {tempo_change}')
                print(f'Change in loudness: {loudness_change}')
            

                if args.breathe:
                    print(f'Brightness {brightness:0<4}')
                    light.set_state(color=to_colour, brightness=brightness)
                    i += 1
                    if i >= len(steps):
                        i = 0

                end_time = time.time()
                taken = end_time - start_time
                time.sleep(1 - taken)
                cur_time = get_details(sp)['progress_ms'] 


            os.system('clear')
            if ind != len(sections) - 1:
                print('Changing colour')
            prev_tempo = tempo
            prev_loudness = loudness
            
        main()


    except TypeError:
        os.system('clear')
        print('No currently playing song')
        main()
    except ZeroDivisionError:
        main()
    
    except KeyboardInterrupt:
        light.set_state(color='hue:240 kelvin:9000', power='on', brightness=1.0) # my usual colour
        quit()


if __name__ == "__main__":
    main()