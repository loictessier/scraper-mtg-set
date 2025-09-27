import os
import requests
import dropbox
from dropbox.files import WriteMode


def get_dropbox_client():
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not app_key or not app_secret or not refresh_token:
        raise RuntimeError("Dropbox OAuth variables missing (APP_KEY, APP_SECRET, REFRESH_TOKEN)")

    # Échanger le refresh_token contre un access_token
    resp = requests.post("https://api.dropbox.com/oauth2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
        "client_secret": app_secret,
    })

    resp.raise_for_status()
    access_token = resp.json()["access_token"]

    # Créer le client Dropbox
    return dropbox.Dropbox(oauth2_access_token=access_token)


def upload_and_share(file_path, folder="/MTG"):
    dbx = get_dropbox_client()
    dest_path = f"{folder}/{os.path.basename(file_path)}"

    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dest_path, mode=WriteMode("overwrite"))

    link = dbx.sharing_create_shared_link_with_settings(dest_path)
    return link.url
