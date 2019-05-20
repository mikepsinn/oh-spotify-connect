from django.core.management.base import BaseCommand
from app.models import SpotifyUser
import requests
import ohapi
import tempfile
import json


class Command(BaseCommand):
    help = 'Fix data files'

    def handle(self, *args, **options):
        spotify_users = SpotifyUser.objects.all()
        for sp in spotify_users:
            print('process {}'.format(sp.user.oh_member))
            # get all files for user
            oh_member = sp.user.oh_member
            files = ohapi.api.exchange_oauth2_member(
                    access_token=oh_member.get_access_token()
                )['data']
            print(files)
            parsed_files = {}
            # read all files, key=fileid, value=json content
            for f in files:
                if f['basename'] == 'spotify-listening-archive.json':
                    try:
                        json_data = requests.get(f['download_url']).json()
                        parsed_files[f['id']] = json_data
                    except Exception:
                        continue
            print('got all data')
            # merge entries into single dict, key=timestamp, value=full record
            joined_data = {}
            for fid, json_data in parsed_files.items():
                for entry in json_data:
                    joined_data[entry['played_at']] = entry
            # order entries for user
            entries = list(joined_data.keys())
            entries.sort()
            spotify_archive = []
            for i in entries:
                spotify_archive.append(joined_data[i])

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
            for fid in list(parsed_files.keys()):
                ohapi.api.delete_file(
                    file_id=fid,
                    access_token=oh_member.get_access_token())
