"""Crash-recoverable two-file library/state persistence.

The commit marker is written only after both old files have safe copies. On
startup a pending marker restores the exact prior bytes, including unknown
legacy fields. This protects normal saves, not separate profile/media caches.
"""
from __future__ import annotations
import json
import os
import tempfile
from pathlib import Path

_MARKER = '.atlas-save-pending.json'
_FILES = ('library.json', 'state.json')
_SAVED = ('.atlas-save-library.previous', '.atlas-save-state.previous')


def _atomic_bytes(path: Path, content: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.atlas-stage-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _payload(document: dict) -> bytes:
    try:
        return json.dumps(document, ensure_ascii=False, indent=2,
                          allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('Yerel kayıt JSON biçimi geçersiz; kayıt yapılmadı.') from exc


def recover_pending(root) -> bool:
    root = Path(root)
    marker = root / _MARKER
    if not marker.exists():
        return False
    try:
        value = json.loads(marker.read_text(encoding='utf-8'))
        existed = value.get('existed') if isinstance(value, dict) else None
        if value.get('format') != 'atlas-save-v1' or not (
                isinstance(existed, list) and len(existed) == 2 and
                all(type(flag) is bool for flag in existed)):
            raise ValueError('Geçersiz veri kurtarma işaretçisi.')
        # Verify every backup before modifying either live file.
        copies = []
        for filename, backup, present in zip(_FILES, _SAVED, existed):
            source = root / backup
            if present and not source.is_file():
                raise ValueError('Gerekli kayıt yedeği bulunamadı: ' + filename)
            copies.append(source.read_bytes() if present else None)
        for filename, previous in zip(_FILES, copies):
            path = root / filename
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_bytes(path, previous)
        marker.unlink()
        for filename in _SAVED:
            (root / filename).unlink(missing_ok=True)
        return True
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Yerel kaydetme yarıda kalmış; önceki dosyalar korunamadı. '
                         'Veri klasöründeki .atlas-save-* dosyalarını silme.') from exc


def save_pair(root, library: dict, state: dict):
    """Journal one pair write, reverting if the second replace fails."""
    root = Path(root)
    # Validate before creating backups or modifying the current data.
    contents = (_payload(library), _payload(state))
    recover_pending(root)
    root.mkdir(parents=True, exist_ok=True)
    previous = [(root / filename).read_bytes() if (root / filename).exists()
                else None for filename in _FILES]
    # Backups are fully flushed before the transaction marker becomes visible.
    for backup, data in zip(_SAVED, previous):
        if data is not None:
            _atomic_bytes(root / backup, data)
        else:
            (root / backup).unlink(missing_ok=True)
    _atomic_bytes(root / _MARKER, _payload({
        'format': 'atlas-save-v1',
        'existed': [item is not None for item in previous],
    }))
    try:
        for filename, data in zip(_FILES, contents):
            _atomic_bytes(root / filename, data)
        (root / _MARKER).unlink()
    except Exception:
        # Keep the marker if rollback itself is interrupted.
        recover_pending(root)
        raise
    finally:
        if not (root / _MARKER).exists():
            for backup in _SAVED:
                (root / backup).unlink(missing_ok=True)
