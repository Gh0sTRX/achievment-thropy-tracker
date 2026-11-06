"""Local synthetic recovery fixture. No live credentials, external network or game art."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError
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
    # Exercise both a stale saved source and a newly discovered official 404.
    games[0]['cover_url']='https://cdn.akamai.steamstatic.com/steam/apps/1/stale.png'
    games[3]['artwork_match']=dict(provider='SteamGridDB',provider_id='123',confirmed=True,game_id='fixture:3',platform='pc',title_id='4',platform_edition='steam',devices=['pc'])
    store.library.update(gamertag='SENTETİK ARŞİV · GERÇEK OYUNCU DEĞİL',games=games,achievements=[])
    store.save()
    data=Path('assets/atlas-mark.png').read_bytes()
    def fetch(url,**kwargs):
        if url.endswith('/stale.png') or '/apps/4/library_600x900.jpg' in url:
            raise HTTPError(url,404,'Synthetic missing cover',{},None)
        if not (url.startswith('https://cdn.akamai.steamstatic.com/steam/apps/') or url=='https://cdn2.steamgriddb.com/synthetic-approved.png'):
            raise ValueError('Fixture blocks external network')
        return data,'image/png'
    with patch.object(artwork,'fetch',side_effect=fetch),patch.object(artwork,'search_game',return_value=[{'id':123,'name':'SENTETİK ADAY — EDİSYONU ONAYLA'}]),patch.object(artwork,'candidates',return_value=[{'kind':'cover','url':'https://cdn2.steamgriddb.com/synthetic-approved.png'}]):
        print(json.dumps({'url':app.url}),flush=True)
        app.serve_forever()
