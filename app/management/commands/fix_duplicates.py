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
            metadata_files = {}
            try:
                print('process {}'.format(sp.user.oh_member))
                # get all files for user
                oh_member = sp.user.oh_member
                files = ohapi.api.exchange_oauth2_member(
                        access_token=oh_member.get_access_token()
                    )['data']
                if len(files) == 1:
                    continue
                # read all files, key=fileid, value=json content
                for f in files:
                    if f['source'] == 'direct-sharing-176' and f['basename'] == 'spotify-listening-archive.json':
                        song_files[f['id']] = f['download_url']
                    if f['source'] == 'direct-sharing-176' and f['basename'] == 'spotify-track-metadata.json':
                        metadata_files[f['id']] = f['download_url']

                print('got all data')
                # merge entries into single dict,
                # key=timestamp, value=full record
                all_songs = {}
                for i, u in song_files.items():
                    data = requests.get(u).text
                    for_ijson = tempfile.NamedTemporaryFile(mode='w')
                    for_ijson.write(data)
                    for_ijson.flush()
                    json_data = ijson.items(open(for_ijson.name, 'r'), 'item')
                for element in json_data:
                    all_songs[element['played_at']] = element
                all_songs_list = []
                for key in sorted(all_songs.keys()):
                    all_songs_list.append(all_songs[key])

                all_metadata = {}
                for i, u in metadata_files.items():
                    single_metadata = requests.get(u).json()
                    all_metadata = {**all_metadata, **single_metadata}
                print('merged files')

                with tempfile.TemporaryFile() as f:
                    js = json.dumps(all_songs)
                    js = str.encode(js)
                    f.write(js)
                    f.flush()
                    f.seek(0)
                    ohapi.api.upload_stream(
                        f, "spotify-listening-archive.json", metadata={
                            "description": "Spotify Play History",
                            "tags": ["spotify"]
                            }, access_token=oh_member.get_access_token())
                with tempfile.TemporaryFile() as f:
                    js = json.dumps(all_metadata)
                    js = str.encode(js)
                    f.write(js)
                    f.flush()
                    f.seek(0)
                    ohapi.api.upload_stream(
                        f, "spotify-track-metadata.json", metadata={
                            "description": "Spotify metadata on songs you listen to",
                            "tags": ["spotify", "metadata"]
                            }, access_token=oh_member.get_access_token())
                for fid in list(song_files.keys()):
                    ohapi.api.delete_file(
                        file_id=fid,
                        access_token=oh_member.get_access_token())
                for fid in list(metadata_files.keys()):
                    ohapi.api.delete_file(
                        file_id=fid,
                        access_token=oh_member.get_access_token())
            except Exception:
                continue
