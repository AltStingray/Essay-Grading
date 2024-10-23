import dropbox
import requests
import os

CLIENT_ID = os.environ.get("DROPBOX_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DROPBOX_CLIENT_SECRET")
redirect_link = f"https://www.dropbox.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https://benchmark-summary-report-eae227664887.herokuapp.com/start&response_type=code"

def authorization(auth_code):
    token_url = "https://api.dropboxapi.com/oauth2/token"

    response = requests.post(
        token_url,
        data={
            "code": auth_code,
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": "https://benchmark-summary-report-eae227664887.herokuapp.com/start"
        }
    )

    if response.status_code==200:
        token_data = response.json()
        access_token = token_data["access_token"]
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

    return access_token


def download_file(url, access_token):

    dbx = dropbox.Dropbox(access_token, app_key=CLIENT_ID, app_secret=CLIENT_SECRET)

    with open("video.mp3", 'wb') as file:

        try:
            metadata, res = dbx.sharing_get_shared_link_file(url)
            print(f"Name of the video: {metadata["name"]}")
            file.write(res.content)
            print("File downloaded successfully!")

        except dropbox.exceptions.ApiError as err:
            print(f"Error: {err}")

    return file