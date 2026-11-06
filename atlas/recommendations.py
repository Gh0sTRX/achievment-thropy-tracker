"""Deterministic, auditable recommendations. Rarity != difficulty or time.

No fake user-progress measurements: true 'nearest achievement' requires an API progress
fraction, otherwise a candidate is labelled a heuristic suggestion.
"""
from collections import defaultdict
from .catalog import only_games


def next_moves(library, pins=(), today=None):
    """At most three archive-backed choices; never infer ease from rarity/points."""
    from datetime import datetime, timezone, timedelta
    from .dates import normalize_unlock_date
    today=today or datetime.now(timezone.utc).date()
    library=only_games(library);pinset=set(pins)
    groups=defaultdict(list)
    for item in library.get('achievements',[]):groups[item['game_id']].append(item)
    choices=[]
    for game in library.get('games',[]):
        items=groups[game['id']]
        pending=[a for a in items if not a.get('unlocked') and not a.get('flag')]
        if not pending:continue
        earned=sum(bool(a.get('unlocked')) for a in items);total=len(items)
        dates=[]
        for a in items:
            value=normalize_unlock_date(a.get('unlock_time')) if a.get('unlocked') else ''
            if value:
                day=datetime.fromisoformat(value).date()
                if today-timedelta(days=30)<=day<=today:dates.append(day)
        selected=sorted(pending,key=lambda a:(a['id'] not in pinset,str(a['id'])))[0]
        pinned=selected['id'] in pinset;near=earned/total>=.75
        if not (pinned or near or dates):continue
        reasons=[]
        if pinned:reasons.append('Kendi sabitlediğin hedef')
        if near:reasons.append(f'Eldeki kayıtlarda {earned}/{total} kazanılmış; {total-earned} kayıt kaldı')
        if dates:reasons.append('Bu oyunda son 30 günde tarihli kazanım kaydın var: '+max(dates).isoformat())
        sources=sorted({str(a.get('metadata_source') or a.get('source') or 'Kaynak belirtilmemiş') for a in items})
        reasons.append('Kaynak: '+', '.join(sources))
        reasons.append('Süre, zorluk, sahiplik ve çevrimiçi erişilebilirlik doğrulanmadı')
        if not library.get('complete_export'):reasons.append('Arşiv kapsamı kısmi/bilinmiyor; kalan kayıt sayısı tüm oyun veya DLC kapsamı değildir')
        choices.append((not pinned,not near,-earned/total,-max(dates).toordinal() if dates else 0,str(game['id']),
            {'achievement_id':selected['id'],'game_id':game['id'],'game':game.get('name',''),
             'achievement':selected.get('name',''),'points':selected.get('points',0),'reasons':reasons,
             'progress':None,'is_measured':False,'signals':{'pinned':pinned,'recorded_completion':near,'recent_unlock':bool(dates)}}))
    choices.sort(key=lambda x:x[:-1])
    return [x[-1] for x in choices[:3]]


def rank(library, pins=(), limit=12):
    library=only_games(library)
    games={g['id']:g for g in library.get('games',[])}
    by_game=defaultdict(list)
    for a in library.get('achievements',[]):by_game[a['game_id']].append(a)
    candidates=[]
    for gid,items in by_game.items():
        game=games.get(gid,{})
        pending=[a for a in items if not a.get('unlocked') and not a.get('flag')]
        if not pending:continue
        earned=sum(bool(a.get('unlocked')) for a in items)
        total=len(items)
        blocked=sum(bool(a.get('flag')) and not bool(a.get('unlocked')) for a in items)
        p=earned/total if total else 0
        for a in pending:
            # Heuristic, no time estimates. TA ratio is a population rarity indicator only.
            ratio=float(a.get('ratio') or 0)
            rarity_bonus=max(0,14-4*(ratio-1)) if ratio else 2
            points=min(int(a.get('points') or 0),100)/10
            game_completion=round(36*p,2)
            method_bonus=8 if a.get('description') or a.get('method') else 0
            pinned_bonus=24 if a['id'] in pins else 0
            progress=None
            cur=a.get('progress_current');target=a.get('progress_target')
            try:
                if cur is not None and target and float(target)>0:
                    progress=max(0,min(1,float(cur)/float(target)))
            except (TypeError,ValueError,ZeroDivisionError):pass
            actual_progress_bonus=40*progress if progress is not None else 0
            score=round(game_completion+rarity_bonus+points+method_bonus+pinned_bonus+actual_progress_bonus,2)
            reasons=[]
            if progress is not None:reasons.append(f'API ilerlemesi %{progress*100:.0f} olarak bildiriyor')
            if a['id'] in pins:reasons.append('kendi hedef listende')
            if p>=.5:reasons.append(f'oyunda {earned}/{total} başarım kazanılmış')
            if ratio and ratio<1.8:reasons.append('TA topluluğunda görece yaygın')
            if int(a.get('points') or 0)>=50:reasons.append(f"{a['points']} G kazandırıyor")
            if a.get('description'):reasons.append('kazanma koşulu açıklaması mevcut')
            if not reasons:reasons.append('kalan başarımlar arasında puanlandı')
            candidates.append({'achievement_id':a['id'],'game_id':gid,'game':game.get('name',''),
                 'achievement':a['name'],'points':a.get('points',0), 'ratio':ratio,
                 'score':score,'reasons':reasons,'progress':progress,'is_measured':progress is not None,
                 'blocked_in_game':blocked, 'game_progress':round(100*p,1)})
    candidates.sort(key=lambda x:(-x['score'],x['game'].casefold(),x['achievement'].casefold()))
    results=[];per_game=defaultdict(int)
    # Diversify; no one title dominates next actions.
    for a in candidates:
        if per_game[a['game_id']]>=2:continue
        per_game[a['game_id']]+=1
        results.append(a)
        if len(results)>=limit:break
    return results


def insights(library):
    library=only_games(library)
    games={g['id']:g for g in library.get('games',[])}
    groups=defaultdict(list)
    for a in library.get('achievements',[]):groups[a['game_id']].append(a)
    near=[];high_value=[];at_risk=[]
    for gid,items in groups.items():
        g=games.get(gid,{})
        earned=sum(bool(a.get('unlocked')) for a in items)
        unearned=[a for a in items if not a.get('unlocked')]
        blocked=[a for a in unearned if a.get('flag')]
        remaining=sum(int(a.get('points') or 0) for a in unearned)
        item={'game_id':gid,'game':g.get('name',''),'earned':earned,'total':len(items),
              'remaining':len(unearned),'remainingG':remaining,'blocked':len(blocked)}
        if unearned and earned and not blocked:near.append(item)
        high_value.append(item)
        if blocked:at_risk.append(item)
    near.sort(key=lambda x:(x['remaining'],-x['earned']/x['total']))
    high_value.sort(key=lambda x:-x['remainingG'])
    at_risk.sort(key=lambda x:-x['blocked'])
    return {'almost_done':near[:8],'most_score':high_value[:8], 'at_risk':at_risk[:8]}
