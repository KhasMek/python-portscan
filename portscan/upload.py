from portscan import log

import datetime
import dropbox
import os
import requests
import time

__all__ = [
    'UploadToDropbox',
    'GetShareableLink',
]


def UploadToDropbox(files, folder_dest):
    """ Uploads each file denoted in 'files' to the DropBox folder denoted by folder_dest """

    try:
        DROP_BOX_API = os.environ['dropbox_key']
    except:
        log.send_log("ENV Var dropbox_key DNE")
        raise EnvironmentError

    try:
        GOOGLE_API = os.environ['google_key']
    except:
        log.send_log("ENV Var google_key DNE")
        raise EnvironmentError

    # Dropbox module init
    dbx = dropbox.Dropbox(DROP_BOX_API)
    dbx.users_get_current_account()

    isinstance(files, list)
    isinstance(folder_dest, str)

    log.send_log("Uploading " + ','.join(str(x) for x in files) + " to Dropbox folder: " + folder_dest)

    returnLinks = []
    CHUNKSIZE = 2 * 1024 * 1024

    for file in files:

        fileSize = os.path.getsize(file)
        full_db_path = folder_dest + datetime.datetime.fromtimestamp(time.time()).strftime(
            '%Y-%m-%d %H:%M:%S') + "_" + os.path.basename(file)

        if fileSize <= CHUNKSIZE:
            with open(file, "rb") as f:
                dbx.files_upload(f.read(), full_db_path, mute=True)

                result = GetShareableLink(full_db_path, DROP_BOX_API)

                if result.status_code == 200:
                    returnLinks.append(result.json()['url'])
                else:
                    log.send_log("Error using the Dropbox Share API " + str(result))
        else:
            with open(file, "rb") as f:

                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNKSIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())

                commit = dropbox.files.CommitInfo(path=full_db_path)

                while f.tell() < fileSize:

                    if (fileSize - f.tell()) <= CHUNKSIZE:
                        print(dbx.files_upload_session_finish(f.read(CHUNKSIZE), cursor, commit))
                    else:
                        dbx.files_upload_session_append(f.read(CHUNKSIZE), cursor.session_id, cursor.offset)
                        cursor.offset = f.tell()

            result = GetShareableLink(full_db_path)
            if result.status_code == 200:
                returnLinks.append(result.json()['url'])
            else:
                log.send_log("Error using the Dropbox Share API " + str(result))

    log.send_log("Finished uploading " + ','.join(str(x) for x in files) + " to Dropbox folder: " + folder_dest)

    for i in range(0, len(returnLinks)):
        headers = {'Content-Type': 'application/json', }
        params = (('key', GOOGLE_API),)
        data = '{"longUrl": "%s"}' % returnLinks[i]

        r = requests.post('https://www.googleapis.com/urlshortener/v1/url', headers=headers, params=params, data=data)
        if r.status_code == 200:
            returnLinks[i] = r.json()["id"]
        else:
            log.send_log("Error using the Google UrlShortener API " + str(r))
    return returnLinks


def GetShareableLink(path, DROP_BOX_API):
    """ Private Helper Function that returns a shareable link to the file denoted by 'path'"""
    isinstance(path, str)

    auth = 'Bearer ' + DROP_BOX_API
    headers = {
        'Authorization': auth,
        'Content-Type': 'application/json',
    }
    data = '{"path": "%s","settings": {"requested_visibility": "public"}}' % path

    result = requests.post('https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings', headers=headers,
                           data=data)
    return result
