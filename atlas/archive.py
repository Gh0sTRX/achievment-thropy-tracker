"""Offline, credential-free Atlas snapshot export and guarded restore.

Only the active library and non-secret state are portable. Cached artwork,
OAuth material, provider settings and historical profile files stay local.
The restore marker reverts an interrupted two-file restore on next startup.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

FORMAT = "achievement-atlas-local-v1"
MAX_BYTES = 48_000_000
MAX_GAMES = 20_000
MAX_ACHIEVEMENTS = 120_000
STATE_FIELDS = frozenset({
    "pins", "hidden", "custom_art", "xbox_titles", "linked_profile",
    "sync_at", "log", "ui", "demo_removed", "public_profiles", "sync_warnings",
})
_PENDING = ".atlas-restore-pending.json"
_BACKUP_NAME = re.compile(r"^pre-restore-[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}\.json$")


def _encoded(value: dict) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("Arşiv JSON içeriği geçersiz.") from exc


def _validate_data(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("Arşiv veri bölümü geçersiz.")
    library, state = data.get("library"), data.get("state")
    if not isinstance(library, dict) or not isinstance(state, dict):
        raise ValueError("Arşivde kütüphane veya yerel durum bulunamadı.")
    games, achievements = library.get("games"), library.get("achievements")
    if not isinstance(games, list) or not isinstance(achievements, list):
        raise ValueError("Arşivde oyun/başarım listeleri geçersiz.")
    if len(games) > MAX_GAMES or len(achievements) > MAX_ACHIEVEMENTS:
        raise ValueError("Arşivde izin verilen kayıt sayısı aşıldı.")
    ids = {}
    for g in games:
        if not isinstance(g, dict):
            raise ValueError("Oyun kaydı geçersiz.")
        ident, platform = g.get("id"), g.get("platform")
        if (not isinstance(ident, str) or not 1 <= len(ident) <= 256
                or platform not in ("xbox", "psn", "pc") or ident in ids):
            raise ValueError("Oyun kimliği, platformu veya tekrarı geçersiz.")
        ids[ident] = platform
    seen = set()
    for a in achievements:
        if not isinstance(a, dict):
            raise ValueError("Başarım kaydı geçersiz.")
        ident, gid = a.get("id"), a.get("game_id")
        if (not isinstance(ident, str) or not 1 <= len(ident) <= 256
                or ident in seen or not isinstance(gid, str) or gid not in ids):
            raise ValueError("Başarım kimliği veya oyun bağı geçersiz.")
        if a.get("platform") not in (None, "", ids[gid]):
            raise ValueError("Başarım başka bir platformdaki oyuna bağlanamaz.")
        seen.add(ident)
    if not isinstance(library.get("gamertag", ""), str):
        raise ValueError("Arşiv oyuncu adı geçersiz.")
    for key in ("pins", "hidden", "log", "sync_warnings"):
        if not isinstance(state.get(key, []), list):
            raise ValueError("Arşiv yerel listesi geçersiz: " + key)
    for key in ("custom_art", "xbox_titles", "ui", "public_profiles"):
        if not isinstance(state.get(key, {}), dict):
            raise ValueError("Arşiv yerel ayarları geçersiz: " + key)
    if state.get("linked_profile") is not None and not isinstance(
            state["linked_profile"], dict):
        raise ValueError("Arşiv bağlantı bilgisi geçersiz.")
    if any(not isinstance(x, str) for x in state.get("pins", [])):
        raise ValueError("Arşiv pin listesi geçersiz.")
    if any(not isinstance(x, dict) or not isinstance(x.get("game"), str)
           for x in state.get("sync_warnings", [])):
        raise ValueError("Arşiv eşitleme uyarıları geçersiz.")
    for key, profile in state.get("public_profiles", {}).items():
        if key not in ("xbox", "psn") or not isinstance(profile, dict):
            raise ValueError("Arşiv profil eşleştirmesi geçersiz.")
        if not isinstance(profile.get("username", ""), str):
            raise ValueError("Arşiv profil adı geçersiz.")
    return data


def make_archive(library: dict, state: dict, *, internal_recovery: bool = False) -> dict:
    """Portable exports exclude secrets; private on-disk rollback keeps all state."""
    safe_state = (deepcopy(state) if internal_recovery else
                  {k: deepcopy(state[k]) for k in STATE_FIELDS if k in state})
    data = _validate_data({"library": deepcopy(library), "state": safe_state})
    raw = _encoded(data)
    if len(raw) > MAX_BYTES:
        raise ValueError("Yerel arşiv 48 MB sınırını aşıyor.")
    return {
        "format": FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "data": data,
    }


def verify_archive(document: object) -> dict:
    if not isinstance(document, dict) or document.get("format") != FORMAT:
        raise ValueError("Desteklenmeyen Atlas arşivi.")
    digest = document.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Arşiv bütünlük bilgisi eksik.")
    data = _validate_data(document.get("data"))
    raw = _encoded(data)
    if len(raw) > MAX_BYTES or not hmac.compare_digest(
            hashlib.sha256(raw).hexdigest(), digest):
        raise ValueError("Arşiv değiştirilmiş, eksik veya çok büyük.")
    return deepcopy(data)


def _write_json(path: Path, document: dict) -> None:
    """A fully flushed temporary file is replaced in the same directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".atlas-write-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_encoded(document))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def recover_interrupted_restore(root: Path) -> bool:
    """A pending restore always reverts to the pre-restore snapshot."""
    root = Path(root)
    pending = root / _PENDING
    if not pending.exists():
        return False
    try:
        marker = json.loads(pending.read_text(encoding="utf-8"))
        name = marker.get("backup") if isinstance(marker, dict) else None
        if not isinstance(name, str) or not _BACKUP_NAME.fullmatch(name):
            raise ValueError("Kurtarma işaretçisi bozuk.")
        path = root / "recovery" / name
        previous = verify_archive(json.loads(path.read_text(encoding="utf-8")))
        _write_json(root / "library.json", previous["library"])
        _write_json(root / "state.json", previous["state"])
        pending.unlink()
        return True
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(
            "Önceki geri yükleme yarıda kalmış. Dosyalar korunuyor; "
            "recovery klasörünü yedekleyip kurtarma kaydını kontrol et."
        ) from exc


def restore_files(root: Path, document: dict, previous_library: dict,
                  previous_state: dict) -> dict:
    """Validate first, leave a recovery snapshot, then replace the two JSON files."""
    root = Path(root)
    data = verify_archive(document)
    recover_interrupted_restore(root)
    backup = make_archive(previous_library, previous_state, internal_recovery=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"pre-restore-{stamp}-{secrets.token_hex(6)}.json"
    _write_json(root / "recovery" / name, backup)
    pending = root / _PENDING
    _write_json(pending, {"backup": name})
    try:
        _write_json(root / "library.json", data["library"])
        _write_json(root / "state.json", data["state"])
        pending.unlink()
    except Exception:
        # If rollback itself fails, leave the marker for the next startup.
        recover_interrupted_restore(root)
        raise
    return data
