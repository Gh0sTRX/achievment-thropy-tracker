"""Reported device metadata, kept separate from achievement-list identity."""
import re

LABELS={'xbox360':'Xbox 360','xboxone':'Xbox One','xboxseries':'Xbox Series X|S',
        'windows':'Windows / PC','gfwl':'Games for Windows Live','ios':'iOS','android':'Android',
        'windowsphone':'Windows Phone','ps3':'PS3','ps4':'PS4','ps5':'PS5','psvita':'PS Vita','pspc':'PlayStation PC'}


def xbox_devices(title, metadata=None, generation='2'):
    metadata=metadata or {}
    raw=metadata.get('devices') or title.get('devices') or []
    if isinstance(raw,str):raw=[raw]
    if title.get('platform'):raw=list(raw)+[title['platform']]
    aliases={'xbox360':'xbox360','xboxone':'xboxone','scarlett':'xboxseries','xboxseriesxs':'xboxseries',
             'xboxseries':'xboxseries','pc':'windows','win32':'windows','windows':'windows','windows10':'windows',
             'ios':'ios','iphone':'ios','ipad':'ios','android':'android','windowsphone':'windowsphone','gfwl':'gfwl'}
    devices=[]
    for value in raw:
        key=re.sub('[^a-z0-9]','',str(value).lower())
        if key in aliases and aliases[key] not in devices:devices.append(aliases[key])
    # Explicit edition markers refine generic metadata; never infer PC from a bare game name.
    name=str(title.get('name','')).lower()
    markers=[(r'\b(android)\b','android'),(r'\b(ios|iphone|ipad)\b','ios'),(r'\b(windows phone)\b','windowsphone'),
             (r'\b(windows|win 10|win10)\b','windows'),(r'\b(xbox 360)\b','xbox360'),(r'\b(gfwl)\b','gfwl')]
    for pattern,device in markers:
        if re.search(pattern,name) and device not in devices:devices.append(device)
    if not devices and generation=='1' and title.get('platforms')==[1]:devices=['xbox360']
    return devices


def describe(devices, fallback='Cihaz belirtilmemiş'):
    return ' / '.join(LABELS.get(d,d) for d in devices) or fallback


def apply(game, devices):
    game['devices']=list(dict.fromkeys(devices))
    game['device_label']=describe(game['devices'])
    game['shared_achievement_list']=len(game['devices'])>1
    return game
