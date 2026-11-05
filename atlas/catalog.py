"""Conservative catalogue classification; never removes legacy user records."""
APPS={'internet explorer','netflix','youtube','hulu','amazon instant video','amazon video','twitch','xbox video','xbox music','microsoft edge','skype'}
def record_type(game):
    explicit=str(game.get('catalogue_type') or game.get('title_type') or '').casefold()
    if explicit in ('app','application'):return 'app'
    return 'app' if game.get('platform')=='xbox' and str(game.get('name','')).strip().casefold() in APPS else 'game'
def is_app(game):return record_type(game)=='app'
def only_games(library):
    games=[g for g in library.get('games',[]) if not is_app(g)];ids={g['id'] for g in games}
    return {**library,'games':games,'achievements':[a for a in library.get('achievements',[]) if a.get('game_id') in ids]}
