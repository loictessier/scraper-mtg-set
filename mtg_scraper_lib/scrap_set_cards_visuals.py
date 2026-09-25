import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional

MV_PICS_BASE = "https://www.magic-ville.com/pics/big"
MV_CARD_PAGE = "https://www.magic-ville.com/fr/carte.php"
SCRYFALL_API = "https://api.scryfall.com"
USER_AGENT = (
    "Mozilla/5.0 (compatible; mtg-scraper/1.0; +https://github.com/loictessier/scrapper-mtg-set)"
)
DFC_LAYOUTS = {
    "transform",
    "modal_dfc",
    "double_faced_token",
    "reversible_card",
    "art_series",
}


def create_output_folder(set_prefix):
    folder = f"./output/{set_prefix.upper()}/visuals"
    os.makedirs(folder, exist_ok=True)
    return folder


def _http_request(url, method="GET", timeout=30):
    req = urllib.request.Request(
        url,
        method=method,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    return urllib.request.urlopen(req, timeout=timeout)


def image_url(folder: str, number: int) -> str:
    return f"{MV_PICS_BASE}/{folder}/{number:03d}.jpg"


def image_exists(folder: str, number: int) -> bool:
    url = image_url(folder, number)
    try:
        with _http_request(url, method="HEAD") as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            return 200 <= resp.status < 300 and "image" in content_type
    except urllib.error.HTTPError as e:
        if e.code == 405:
            # Some hosts reject HEAD; fall back to a tiny GET check via full download attempt later
            try:
                with _http_request(url, method="GET") as resp:
                    content_type = (resp.headers.get("Content-Type") or "").lower()
                    return 200 <= resp.status < 300 and "image" in content_type
            except Exception:
                return False
        return False
    except Exception:
        return False


def download_image(url: str, path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read()
        if "image" not in content_type and not data.startswith(b"\xff\xd8"):
            print(f"[WARN] Pas une image JPEG pour {url} (content-type={content_type})")
            return False
        with open(path, "wb") as f:
            f.write(data)
        print(f"Téléchargé : {path}")
        return True
    except Exception as e:
        print(f"Erreur téléchargement {url} : {e}")
        return False


def resolve_pics_folder(set_code: str) -> str:
    """Prefer French folder ({set}FR) when available, else {set}."""
    set_code = set_code.lower()
    for folder in (f"{set_code}FR", set_code):
        if image_exists(folder, 1):
            print(f"[INFO] Dossier images Magic-Ville : pics/big/{folder}/")
            return folder
    raise RuntimeError(
        f"Aucune image trouvée pour {set_code} "
        f"(testé pics/big/{set_code}FR/001.jpg et pics/big/{set_code}/001.jpg)"
    )


def alternate_pics_folder(set_code: str, primary: str) -> Optional[str]:
    """Other language folder to try when primary is missing a card (e.g. fraFR vs fra)."""
    set_code = set_code.lower()
    fr = f"{set_code}FR"
    alt = set_code if primary == fr else fr
    return alt if alt != primary else None


def download_card_image(folders: List[str], number: int, path: str) -> bool:
    """Try each Magic-Ville pics folder until one yields a JPEG."""
    for i, folder in enumerate(folders):
        url = image_url(folder, number)
        if not image_exists(folder, number):
            continue
        if download_image(url, path):
            if i > 0:
                print(f"[INFO] {number:03d} pris depuis le dossier de repli pics/big/{folder}/")
            return True
    return False


def _scryfall_get(url: str) -> dict:
    time.sleep(0.1)  # polite rate limit
    with _http_request(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _scryfall_get_or_none(url: str) -> Optional[dict]:
    try:
        return _scryfall_get(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def fetch_scryfall_search(query: str) -> List[Dict]:
    """Paginated Scryfall card search."""
    url = f"{SCRYFALL_API}/cards/search?q={urllib.parse.quote(query)}"
    cards = []  # type: List[Dict]
    while url:
        try:
            payload = _scryfall_get(url)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(body)
            except Exception:
                if e.code == 404:
                    return cards
                raise
            if payload.get("object") == "error":
                if e.code == 404 or payload.get("code") == "not_found":
                    return cards
                raise RuntimeError(f"Scryfall error: {payload.get('details') or payload}")
        if payload.get("object") == "error":
            if payload.get("code") == "not_found":
                return cards
            raise RuntimeError(f"Scryfall error: {payload.get('details') or payload}")
        cards.extend(payload.get("data") or [])
        url = payload.get("next_page")
    return cards


def fetch_scryfall_cards(set_code: str) -> List[Dict]:
    """All paper prints in the set (paginated). Tokens live in a separate set code."""
    return fetch_scryfall_search(f"e:{set_code.lower()} unique:prints")


def resolve_token_set_code(set_code: str) -> Optional[str]:
    """
    Related token set for an expansion, e.g. rix -> trix, dsk -> tdsk.
    Tokens are NOT returned by e:{set} or e:{set} include:extras.
    """
    set_code = set_code.lower()
    info = _scryfall_get_or_none(f"{SCRYFALL_API}/sets/{set_code}")
    if not info:
        return None
    if info.get("set_type") == "token":
        return None

    candidate = f"t{set_code}"
    tinfo = _scryfall_get_or_none(f"{SCRYFALL_API}/sets/{candidate}")
    if (
        tinfo
        and tinfo.get("set_type") == "token"
        and (tinfo.get("parent_set_code") or "").lower() == set_code
    ):
        return candidate

    payload = _scryfall_get(f"{SCRYFALL_API}/sets")
    for entry in payload.get("data") or []:
        if (
            entry.get("set_type") == "token"
            and (entry.get("parent_set_code") or "").lower() == set_code
        ):
            return entry.get("code")
    return None


def fetch_related_token_cards(set_code: str) -> List[Dict]:
    """Token/emblem cards from the related t{set} (numeric collector numbers only)."""
    token_code = resolve_token_set_code(set_code)
    if not token_code:
        return []
    print(f"[INFO] Jetons Scryfall : set {token_code}")
    cards = fetch_scryfall_search(f"e:{token_code} unique:prints")
    tokens = []
    for card in cards:
        cn = str(card.get("collector_number") or "")
        if cn.isdigit():
            tokens.append(card)
    tokens.sort(key=lambda c: int(c.get("collector_number") or 0))
    return tokens


def numeric_collector_numbers(cards: List[Dict]) -> List[int]:
    numbers = []
    for card in cards:
        cn = str(card.get("collector_number") or "")
        if cn.isdigit():
            numbers.append(int(cn))
    return sorted(set(numbers))


def dfc_collector_numbers(cards: List[Dict]) -> List[int]:
    numbers = []
    for card in cards:
        layout = card.get("layout") or ""
        faces = card.get("card_faces") or []
        is_dfc = layout in DFC_LAYOUTS or len(faces) >= 2
        cn = str(card.get("collector_number") or "")
        if is_dfc and cn.isdigit():
            numbers.append(int(cn))
    return sorted(set(numbers))


def contiguous_mv_numbers_after(folders: List[str], start: int, limit: int = 80) -> List[int]:
    """Magic-Ville ids from start inclusive, while files exist contiguously."""
    found = []  # type: List[int]
    n = start
    while len(found) < limit:
        if any(image_exists(folder, n) for folder in folders):
            found.append(n)
            n += 1
            time.sleep(0.05)
        else:
            break
    return found


def map_token_mv_numbers(block: List[int], n_dfc: int, n_tokens: int) -> List[int]:
    """
    On older sets (e.g. RIX), MV appends DFC backs then tokens after the main max.
    On modern sets, DFC backs often sit in a high range (+1000) so the post-main
    block is tokens only — or empty (then caller looks for a high token range).
    """
    if not block or n_tokens <= 0:
        return []
    if n_dfc > 0 and len(block) >= n_dfc + n_tokens:
        return block[n_dfc : n_dfc + n_tokens]
    if n_dfc > 0 and len(block) <= n_dfc:
        # Looks like DFC backs only — do not mis-download them as tokens
        return []
    if len(block) >= n_tokens:
        return block[:n_tokens]
    return list(block)


def discover_token_mv_numbers(
    folders: List[str],
    main_max: int,
    n_tokens: int,
    n_dfc: int,
) -> List[int]:
    """
    Resolve Magic-Ville image ids for tokens.

    1) Contiguous block right after the main set (RIX-style: DFC backs then tokens).
    2) High id ranges with a gap (FRA-style: tokens start at 601 while main ends ~461).
    """
    if n_tokens <= 0:
        return []

    post_main = contiguous_mv_numbers_after(
        folders, main_max + 1, limit=n_dfc + n_tokens + 20
    )
    mapped = map_token_mv_numbers(post_main, n_dfc, n_tokens)
    if len(mapped) >= n_tokens:
        return mapped[:n_tokens]

    # High-range search: FRA tokens live at 601+, other sets may use 600/700/1000…
    starts = [600, 601] + list(range(650, 2001, 50))
    for start in starts:
        if start <= main_max:
            continue
        if not any(image_exists(folder, start) for folder in folders):
            continue
        block = contiguous_mv_numbers_after(folders, start, limit=n_tokens + 5)
        if len(block) >= n_tokens:
            print(
                f"[INFO] Jetons Magic-Ville trouvés en plage haute : "
                f"{block[0]}–{block[n_tokens - 1]}"
            )
            return block[:n_tokens]
        time.sleep(0.05)

    return mapped


def scryfall_image_url(card: Dict) -> Optional[str]:
    uris = card.get("image_uris")
    if not uris:
        faces = card.get("card_faces") or []
        if faces:
            uris = faces[0].get("image_uris")
    if not uris:
        return None
    return uris.get("large") or uris.get("normal") or uris.get("small")


def discover_back_image_number(set_code: str, front_number: int) -> Optional[int]:
    """
    DFC backs live in a much higher Magic-Ville id range (same pics folder).
    Pairing is only exposed on the HTML card page (#CardScanBack), e.g. mom 088 -> 943.
    May return None if Cloudflare blocks the HTML page.
    """
    ref = f"{set_code.lower()}{front_number:03d}"
    url = f"{MV_CARD_PAGE}?ref={ref}"
    try:
        with _http_request(url) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[WARN] Impossible de lire la page carte pour le verso {ref}: {e}")
        return None

    if re.search(r"just a moment|cf-challenge|cloudflare", html, re.I):
        print(f"[WARN] Cloudflare sur carte.php pour {ref} — verso non résolu")
        return None

    pics = re.findall(r"pics/big/[^/\"']+/(\d+)\.jpg", html, flags=re.I)
    # Preserve order, unique
    seen = []
    for p in pics:
        if p not in seen:
            seen.append(p)
    if len(seen) < 2:
        return None

    back = int(seen[1])
    front = int(seen[0])
    if back == front_number or back == front:
        # Prefer a number clearly in the high range if present
        for p in seen[1:]:
            n = int(p)
            if n != front_number and n > front_number:
                return n
        return None
    return back


def fetch_all_cards(set_code, on_progress: Optional[Callable] = None):
    set_code = set_code.lower()
    output_folder = create_output_folder(set_code)
    prefix = set_code.upper()

    folder = resolve_pics_folder(set_code)
    alt = alternate_pics_folder(set_code, folder)
    folders = [folder] + ([alt] if alt else [])
    if alt:
        print(f"[INFO] Repli dossier alternatif si besoin : pics/big/{alt}/")

    cards = fetch_scryfall_cards(set_code)
    main_numbers = numeric_collector_numbers(cards)
    if not main_numbers:
        raise RuntimeError(f"Aucun numéro de collection numérique trouvé sur Scryfall pour {set_code}")

    print(f"[INFO] {len(main_numbers)} cartes (numéros numériques) via Scryfall pour {set_code}")

    downloaded = 0

    for num in main_numbers:
        local_name = f"{prefix}{num:04d}.jpg"
        path = os.path.join(output_folder, local_name)
        print(f"→ Téléchargement {set_code}{num:03d} (essaie {' / '.join(folders)})")
        if download_card_image(folders, num, path):
            downloaded += 1
            if on_progress:
                on_progress(set_code, f"{set_code}{num:03d}")
        else:
            print(f"[WARN] Échec image recto pour {num}")
        time.sleep(0.15)

    dfc_numbers = dfc_collector_numbers(cards)
    if dfc_numbers:
        print(f"[INFO] {len(dfc_numbers)} cartes double face détectées — résolution des versos")
        for num in dfc_numbers:
            back_num = discover_back_image_number(set_code, num)
            if not back_num:
                print(f"[WARN] Verso introuvable pour {set_code}{num:03d}")
                continue
            local_name = f"{prefix}{num:04d}bis.jpg"
            path = os.path.join(output_folder, local_name)
            print(f"→ Verso DFC {set_code}{num:03d} ← pics …/{back_num:03d}.jpg")
            if download_card_image(folders, back_num, path):
                downloaded += 1
                if on_progress:
                    on_progress(set_code, f"{set_code}{num:03d}bis")
            time.sleep(0.15)

    token_cards = fetch_related_token_cards(set_code)
    if token_cards:
        main_max = max(main_numbers)
        mv_token_nums = discover_token_mv_numbers(
            folders,
            main_max=main_max,
            n_tokens=len(token_cards),
            n_dfc=len(dfc_numbers),
        )
        # Local names continue after the last main card (FRA0601 → FRA0462, …).
        if mv_token_nums and len(mv_token_nums) >= len(token_cards):
            print(
                f"[INFO] {len(token_cards)} jeton(s) ← Magic-Ville "
                f"{mv_token_nums[0]}–{mv_token_nums[len(token_cards) - 1]} "
                f"renommés localement {prefix}{main_max + 1:04d}–"
                f"{prefix}{main_max + len(token_cards):04d}"
            )
        elif mv_token_nums:
            print(
                f"[INFO] {len(mv_token_nums)}/{len(token_cards)} jeton(s) Magic-Ville ; "
                "repli Scryfall uniquement pour les manquants"
            )
        else:
            print(
                f"[INFO] {len(token_cards)} jeton(s) ; "
                "aucune plage Magic-Ville — repli Scryfall"
            )

        for i, card in enumerate(token_cards):
            cn = int(card["collector_number"])
            name = card.get("name") or f"token-{cn}"
            local_num = main_max + 1 + i
            local_name = f"{prefix}{local_num:04d}.jpg"
            path = os.path.join(output_folder, local_name)
            got = False

            if i < len(mv_token_nums):
                mv_num = mv_token_nums[i]
                print(
                    f"→ Jeton {name} (#{cn}) ← Magic-Ville …/{mv_num:03d}.jpg "
                    f"→ {local_name}"
                )
                if download_card_image(folders, mv_num, path):
                    downloaded += 1
                    got = True
                    if on_progress:
                        on_progress(set_code, f"{set_code}{local_num:03d}")
                time.sleep(0.15)

            if not got:
                url = scryfall_image_url(card)
                if url:
                    print(f"→ Jeton {name} (#{cn}) ← Scryfall (repli) → {local_name}")
                    if download_image(url, path):
                        downloaded += 1
                        if on_progress:
                            on_progress(set_code, f"{set_code}{local_num:03d}")
                else:
                    print(f"[WARN] Jeton sans image : {name} (#{cn})")
                time.sleep(0.15)

    if downloaded == 0:
        raise RuntimeError(
            f"Aucune image téléchargée pour {set_code}. "
            "Vérifiez le code d'édition et l'accès à magic-ville.com/pics/."
        )

    print(f"[INFO] Terminé : {downloaded} fichier(s) pour {set_code}")
    return downloaded


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Télécharge les visuels d'une édition Magic depuis Magic-Ville (URLs directes)."
    )
    parser.add_argument("set_code", help="Code de l'édition (ex: fic, j25, fdn, fca)")
    args = parser.parse_args()

    fetch_all_cards(args.set_code)
