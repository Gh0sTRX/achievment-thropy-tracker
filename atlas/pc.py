"""PC is an ecosystem; providers keep their own account, game and achievement IDs."""
from . import steam
PROVIDERS={'steam':steam}
def provider(name='steam'):
    if name not in PROVIDERS:raise ValueError('Bu PC sağlayıcısı henüz desteklenmiyor.')
    return PROVIDERS[name]


def fetch(username,progress=lambda *args:None,name='steam'):
    try:return provider(name).fetch(username,progress)
    except steam.SteamError as error:
        fault=ValueError(str(error));fault.code=error.code
        raise fault from None
