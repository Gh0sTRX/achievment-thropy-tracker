# Build on Windows: python -m PyInstaller --noconfirm packaging/windows.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
extra_data, extra_binaries, hidden = [], [], []
for package in ('xbox', 'psnawp_api', 'pycountry', 'certifi', 'webview'):
    data, binaries, imports = collect_all(package)
    extra_data += data
    extra_binaries += binaries
    hidden += imports

a = Analysis([str(root / 'run.py')], pathex=[str(root)],
    binaries=extra_binaries,
    datas=[(str(root / 'atlas' / 'web'), 'atlas/web')] + extra_data,
    hiddenimports=hidden, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='AchievementAtlas',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='AchievementAtlas')
