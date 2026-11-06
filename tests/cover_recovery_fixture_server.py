"""Local synthetic recovery fixture. No live credentials, external network or game art."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from atlas.server import LocalApp
from atlas import artwork

with TemporaryDirectory(prefix='atlas-cover-fixture-') as root:
    app=LocalApp(root);store=app.controller.store
    store.steamgriddb_key='SYNTHETIC-KEY-NOT-A-CREDENTIAL'
    games=[]
    for i in range(20):
        steam=i%3==0
        games.append(dict(id=f'fixture:{i}',name=f'SENTETİK TEST OYUNU {i:02}',platform='pc' if steam else 'xbox',
                          provider='steam' if steam else 'xbox',title_id=str(i+1) if steam else '',
                          devices=['pc'] if steam else ['xbox360'],platform_edition='steam' if steam else '360',notes='KEEP'))
    store.library.update(gamertag='SENTETİK ARŞİV · GERÇEK OYUNCU DEĞİL',games=games,achievements=[])
    store.save()
    data=Path('assets/atlas-mark.png').read_bytes()
    def fetch(url,**kwargs):
        if not url.startswith('https://cdn.akamai.steamstatic.com/steam/apps/'):
            raise ValueError('Fixture blocks external network')
        return data,'image/png'
    with patch.object(artwork,'fetch',side_effect=fetch),patch.object(artwork,'search_game',return_value=[{'id':123,'name':'SENTETİK ADAY — EDİSYONU ONAYLA'}]):
        print(json.dumps({'url':app.url}),flush=True)
        app.serve_forever()
