from django.core.management.base import BaseCommand
from app.models import SpotifyUser
import requests
import ohapi
import tempfile
import json
import ijson
import tempfile


class Command(BaseCommand):
    help = 'Fix data files'

    def handle(self, *args, **options):
        spotify_users = SpotifyUser.objects.all()
        for sp in spotify_users:
            song_files = {}
            try:
                oh_member = sp.user.oh_member
                files = ohapi.api.exchange_oauth2_member(
                        access_token=oh_member.get_access_token()
                    )['data']
                for f in files:
                    if f['source'] == 'direct-sharing-176' and f['basename'] == 'spotify-listening-archive.json':
                        fid = f['id']
                        spotify_data = requests.get(f['download_url']).json()
                        spotify_data_sorted = []
                        for key in sorted(spotify_data.keys()):
                            spotify_data_sorted.append(spotify_data[key])
                        with tempfile.TemporaryFile() as f:
                            js = json.dumps(spotify_data_sorted)
                            js = str.encode(js)
                            f.write(js)
                            f.flush()
                            f.seek(0)
                            ohapi.api.upload_stream(
                                f, "spotify-listening-archive.json", metadata={
                                    "description": "Spotify Play History",
                                    "tags": ["spotify"]
                                    }, access_token=oh_member.get_access_token())
                            ohapi.api.delete_file(
                                file_id=fid,
                                access_token=oh_member.get_access_token())
            except:
                pass
