"""Cooperative cancellation and conservative target-scoped incremental reuse."""
import asyncio
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import time

class Cancelled(Exception):pass
context=ContextVar('atlas_sync',default=None)
def check():
    value=context.get()
    if value and value['stop']():raise Cancelled()
async def request(awaitable):
    task=asyncio.ensure_future(awaitable)
    try:
        while not task.done():
            check()
            await asyncio.wait({task},timeout=.1)
        check()
        return task.result()
    except BaseException:
        task.cancel()
        await asyncio.gather(task,return_exceptions=True)
        raise

def signature(title):
    # Reuse only when the provider supplied explicit progress and an update time.
    stamp=title.get('lastUnlock') or title.get('lastUpdated')
    earned=title.get('currentAchievements');total=title.get('totalAchievements')
    if not stamp or type(earned) is not int or type(total) is not int or total<=0 or not 0<=earned<=total:return ''
    return hashlib.sha256(json.dumps([stamp,earned,total,title.get('currentGamerscore'),title.get('maxGamerscore')],sort_keys=True).encode()).hexdigest()

def reuse(g,title,identity):
    value=context.get();sig=signature(title)
    if not value or value['force'] or not sig:return None
    old=value.get('cache') or {}
    if old.get('id')!=identity:return None
    if 'game_index' not in value:
        value['game_index']={x['id']:x for x in old.get('games',[])}
        value['item_index']={}
        for a in old.get('achievements',[]):value['item_index'].setdefault(a['game_id'],[]).append(a)
    prior=value['game_index'].get(g['id'])
    if not prior or prior.get('sync_signature')!=sig or prior.get('api_generation')!=g.get('api_generation'):return None
    age=time.time()-prior.get('sync_checked_at',0)
    rows=value['item_index'].get(g['id'],[])
    if not 0<=age<600 or not rows or len(rows)!=title['totalAchievements']:return None
    g['sync_signature']=prior['sync_signature'];g['sync_checked_at']=prior['sync_checked_at']
    return deepcopy(rows)

def mark(g,title):
    g['sync_signature']=signature(title);g['sync_checked_at']=time.time()
