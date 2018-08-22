import ohapi
import json
import tempfile
import requests
# from celery import shared_task


SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'


def update_play_history(request):
    member = request.user.oh_member
    spotify_user = request.user.spotify_user

    params = {}
    final_json = {}

    files = ohapi.api.exchange_oauth2_member(
        access_token=member.get_access_token()
    )['data']

    if len(files) > 0:
        final_json = requests.get(files[0]['download_url']).json()
        params['after'] = final_json[-1]['played_at']

    recently_played = requests.get(SPOTIFY_BASE_URL + '/me/player/recently-played', headers={
        'Authorization': 'Bearer {}'.format(spotify_user.get_access_token())
    }, params=params).json()

    with open(tempfile.TemporaryFile()) as f:
        json.dump(recently_played, f)
        ohapi.api.upload_stream(f, "play_history.json", metadata={
            "description": "Spotify Play History",
            "tags": ["spotify"]
        }, access_token=spotify_user.get_access_token())
