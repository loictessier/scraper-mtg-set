import os
import requests
import dropbox
import logging
from dropbox.files import WriteMode


def get_dropbox_client():
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not app_key or not app_secret or not refresh_token:
        logging.error("Dropbox OAuth variables missing (APP_KEY, APP_SECRET, REFRESH_TOKEN)")
        raise RuntimeError("Dropbox OAuth variables missing (APP_KEY, APP_SECRET, REFRESH_TOKEN)")

    logging.info("Requesting new Dropbox access token using refresh token...")

    # Échanger le refresh_token contre un access_token
    resp = requests.post("https://api.dropbox.com/oauth2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
        "client_secret": app_secret,
    })

    if resp.status_code != 200:
        logging.error(f"Failed to refresh access token: {resp.status_code} {resp.text}")
    resp.raise_for_status()

    access_token = resp.json().get("access_token")
    logging.info("Successfully obtained Dropbox access token")

    return dropbox.Dropbox(oauth2_access_token=access_token)


def upload_and_share(file_path, folder="/MTG"):
    dbx = get_dropbox_client()
    dest_path = f"{folder}/{os.path.basename(file_path)}"

    logging.info(f"Uploading file to Dropbox: {file_path} → {dest_path}")
    try:
        with open(file_path, "rb") as f:
            dbx.files_upload(f.read(), dest_path, mode=WriteMode("overwrite"))
        logging.info(f"File uploaded successfully to {dest_path}")
    except Exception as e:
        logging.error(f"Dropbox upload failed for {file_path}: {e}", exc_info=True)
        raise

    try:
        # Essaye de créer un nouveau lien
        link = dbx.sharing_create_shared_link_with_settings(dest_path)
        logging.info(f"Shared link created: {link.url}")
        return link.url
    except dropbox.exceptions.ApiError as e:
        if (isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError) 
                and e.error.is_shared_link_already_exists()):
            # Récupère le lien existant
            logging.warning(f"Shared link already exists for {dest_path}, reusing it")
            links = dbx.sharing_list_shared_links(path=dest_path, direct_only=True).links
            if links:
                logging.info(f"Reused shared link: {links[0].url}")
                return links[0].url
            else:
                logging.error(f"No existing link found for {dest_path} despite error")
                raise
        else:
            logging.error(f"Failed to create shared link for {dest_path}: {e}", exc_info=True)
            raise


def list_files(folder="/MTG"):
    dbx = get_dropbox_client()

    logging.info(f"Listing content of folder: {folder}")
    try:
        list = dbx.files_list_folder(folder)
    except Exception as e:
        logging.error(f"Dropbox listing failed for {folder}: {e}", exc_info=True)
        raise

    return list