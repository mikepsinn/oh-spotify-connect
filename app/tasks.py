import ohapi
import json
import tempfile
import requests
from app.models import OpenHumansMember
from celery import shared_task
from .helpers import parse_timestamp

SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'


@shared_task
def update_play_history(oh_member_id):
    oh_member = OpenHumansMember.objects.get(oh_id=oh_member_id)
    print('updating data for {}'.format(oh_member_id))
    spotify_user = oh_member.user.spotify_user

    spotify_archive, old_file_id = get_spotify_archive(oh_member)
    spotify_archive = extend_archive(spotify_archive, spotify_user)
    if spotify_archive:
        with tempfile.TemporaryFile() as f:
            js = json.dumps(spotify_archive)
            js = str.encode(js)
            f.write(js)
            f.flush()
            f.seek(0)
            ohapi.api.upload_stream(
                f, "spotify-listening-archive.json", metadata={
                    "description": "Spotify Play History",
                    "tags": ["spotify"]
                    }, access_token=oh_member.get_access_token())
            if old_file_id:
                ohapi.api.delete_file(
                    file_id=old_file_id,
                    access_token=oh_member.get_access_token())
        print('updated data for {}'.format(oh_member_id))
        update_song_metadata.delay(oh_member.oh_id)


def get_spotify_archive(oh_member):
    files = ohapi.api.exchange_oauth2_member(
        access_token=oh_member.get_access_token()
    )['data']
    for f in files:
        if f['basename'] == 'spotify-listening-archive.json':
            return requests.get(f['download_url']).json(), f['id']
    return [], ''


def extend_archive(spotify_archive, spotify_user):
    response = requests.get(
        SPOTIFY_BASE_URL + '/me/player/recently-played?limit=50', headers={
          'Authorization': 'Bearer {}'.format(spotify_user.get_access_token())
          })
    if response.status_code == 429:
        update_play_history.apply_async(
                    args=[spotify_user.user.oh_member.oh_id],
                    countdown=int(response.headers['Retry-After'])+1)
        return None
    recently_played = response.json()
    if 'items' in recently_played.keys():
        recent_items = [i for i in reversed(recently_played['items'])]
        if spotify_archive:
            last_timestamp = parse_timestamp(
                                spotify_archive[-1]['played_at'])
            for entry in recent_items:
                played_at = parse_timestamp(entry['played_at'])
                if played_at > last_timestamp:
                    spotify_archive.append(entry)
            return spotify_archive
        else:
            return recent_items
    return None


@shared_task
def update_song_metadata(oh_member_id):
    oh_member = OpenHumansMember.objects.get(oh_id=oh_member_id)
    print('updating song metadata for {}'.format(oh_member_id))
    spotify_user = oh_member.user.spotify_user
    spotify_archive, _ = get_spotify_archive(oh_member)
    spotify_metadata, old_file_id = get_song_metadata(oh_member)
    spotify_metadata = fetch_song_metadata(
        spotify_user,
        spotify_archive,
        spotify_metadata)
    print('got all metadata')
    print(spotify_metadata)
    if spotify_metadata:
        with tempfile.TemporaryFile() as f:
            js = json.dumps(spotify_metadata)
            js = str.encode(js)
            f.write(js)
            f.flush()
            f.seek(0)
            ohapi.api.upload_stream(
                f, "spotify-track-metadata.json", metadata={
                    "description": "Spotify metadata on songs you listen to",
                    "tags": ["spotify", "metadata"]
                    }, access_token=oh_member.get_access_token())
            if old_file_id:
                ohapi.api.delete_file(
                    file_id=old_file_id,
                    access_token=oh_member.get_access_token())
        print('updated metadata for {}'.format(oh_member_id))


def get_song_metadata(oh_member):
    files = ohapi.api.exchange_oauth2_member(
        access_token=oh_member.get_access_token()
    )['data']
    for f in files:
        if f['basename'] == 'spotify-track-metadata.json':
            return requests.get(f['download_url']).json(), f['id']
    return {}, ''


def fetch_song_metadata(spotify_user, spotify_archive, spotify_metadata):
    # get all track IDs that don't have saved metadata yet
    ids_to_fetch = [i['track']['id'] for i in spotify_archive
                    if i['track']['id'] not in spotify_metadata.keys()]
    # remove duplicates
    ids_to_fetch = list(set(ids_to_fetch))
    # break into lists of 100 to honor spotify API limits
    chunked_ids_fetch = [
        ids_to_fetch[i:i + 100] for i in range(0, len(ids_to_fetch), 100)]
    for chunk in chunked_ids_fetch:
        print('start getting chunk')
        print(','.join(chunk))
        response = requests.get(
            SPOTIFY_BASE_URL + '/audio-features/?ids={}'.format(
                ','.join(chunk)),
            headers={
              'Authorization': 'Bearer {}'.format(
                spotify_user.get_access_token())
              })
        print(response.json())
        if response.status_code == 429:
            update_song_metadata.apply_async(
                        args=[spotify_user.user.oh_member.oh_id],
                        countdown=int(response.headers['Retry-After'])+1)
            return spotify_metadata
        for entry in response.json()['audio_features']:
            print(entry)
            if entry:
                spotify_metadata[entry['id']] = entry
        print('finished getting a chunk')
    return spotify_metadata
