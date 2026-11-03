"""Deterministic, auditable recommendations. Rarity != difficulty or time.

No fake user-progress measurements: true 'nearest achievement' requires an API progress
fraction, otherwise a candidate is labelled a heuristic suggestion.
"""
from collections import defaultdict


def rank(library, pins=(), limit=12):
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