"""Validated local presentation preferences; never changes provider identities."""
import math
DEFAULTS = {'theme_mode':'auto','platform_filter':'all','library_layout':'grid',
 'focus_game_id':None,'reduced_motion':False,'dense_mode':False,'high_contrast':False,
 'font_scale':1.0,'hero_contrast':0.68}
ENUMS = {'theme_mode':('auto','all','xbox','psn','pc'),
 'platform_filter':('all','xbox','psn','pc'),'library_layout':('grid','showcase','collection')}

def validate(values, games):
    if not isinstance(values,dict) or set(values)-set(DEFAULTS):raise ValueError('Geçersiz görünüm ayarı.')
    clean={}
    for key,value in values.items():
        if key in ENUMS:
            if value not in ENUMS[key]:raise ValueError('Görünüm seçeneği geçersiz.')
        elif key=='focus_game_id':
            if value is not None and value not in {g['id'] for g in games}:raise ValueError('Odak oyunu bulunamadı.')
        elif key in ('reduced_motion','dense_mode','high_contrast'):
            if type(value) is not bool:raise ValueError('Görünüm ayarı boolean olmalı.')
        else:
            bounds=(0.5,0.85) if key=='hero_contrast' else (1,1.3)
            if type(value) not in (float,int) or not math.isfinite(value) or not bounds[0]<=value<=bounds[1]:raise ValueError('Görünüm değeri sınır dışında.')
        clean[key]=value
    return clean
