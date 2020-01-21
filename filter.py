
import spotipy.util as util
from spotipy import *
import os



        
def main():
    username = os.getenv('SPOTIFY_USER_ID')

    scope = 'user-top-read user-library-read playlist-modify-public'
    spotify_token = util.prompt_for_user_token(username, scope)
    
    sp = Spotify(auth=spotify_token) if spotify_token else print('Cannot get Spotify token')

    old_playlist_uri = input('URI: ')
    d = sp.user_playlist_tracks(username, old_playlist_uri)
    old_playlist_name = sp.user_playlist(username, old_playlist_uri)['name']
    r = 22.5
    new_playlist_name = f'Filtered {old_playlist_name} {r}'
    results = sp.user_playlist_create(username, new_playlist_name)
    new_playlist_id = results['id']
    for item in d['items']:
        track_uri = item['track']['id']
        anal = sp.audio_analysis(track_uri)
        duration = sp.audio_features(track_uri)[0]['duration_ms'] / 1000
        num_sections = len(anal['sections'])
        ratio = duration / num_sections
        if ratio <= r:
            sp.user_playlist_add_tracks(username, new_playlist_id, [track_uri])


main()