import os, dropbox
from dropbox.files import WriteMode
from dropbox.sharing import CreateSharedLinkWithSettingsError

def upload_and_share(local_path: str, token: str, folder="/MTG") -> str:
    dbx = dropbox.Dropbox(token)
    dest_path = f"{folder.rstrip('/')}/{os.path.basename(local_path)}"

    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dest_path, mode=WriteMode("overwrite"))

    try:
        link = dbx.sharing_create_shared_link_with_settings(dest_path)
        url = link.url
    except CreateSharedLinkWithSettingsError:
        links = dbx.sharing_list_shared_links(path=dest_path).links
        url = links[0].url if links else None

    return url.replace("?dl=0", "?dl=1") if url else None
