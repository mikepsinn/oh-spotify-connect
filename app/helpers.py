from ohapi import api
import datetime


def get_download_url(oh_member):
    files = api.exchange_oauth2_member(
        access_token=oh_member.get_access_token())['data']
    for f in files:
        if f['basename'] == 'spotify-listening-archive.json':
            return {'url': f['download_url'], 'created': f['created']}
    return None


def parse_timestamp(time_string):
    try:
        timestamp = datetime.datetime.strptime(
                            time_string,
                            '%Y-%m-%dT%H:%M:%S.%fZ')
        return timestamp
    except:
        timestamp = datetime.datetime.strptime(
                            time_string,
                            '%Y-%m-%dT%H:%M:%SZ')
        return timestamp
