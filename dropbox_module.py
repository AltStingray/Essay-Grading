import dropbox
import requests

CLIENT_ID = "shc5rkn4hixve4j"
CLIENT_SECRET = "wejv8edxnhyelum"
redirect_link = f"https://www.dropbox.com/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri=https://benchmark-summary-report-eae227664887.herokuapp.com/start&response_type=code"

data = {}

def store(value, access_token_or_link):

    data[access_token_or_link] = value


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

    #access_token = data["access_token"]
    
    #url = data["link"]

    dbx = dropbox.Dropbox(access_token, app_key="shc5rkn4hixve4j" , app_secret="wejv8edxnhyelum")

    with open("video.mp3", 'wb') as file:

        try:
            metadata, res = dbx.sharing_get_shared_link_file(url)
            file.write(res.content)
            print("File downloaded successfully!")

        except dropbox.exceptions.ApiError as err:
            print(f"Error: {err}")

    return file