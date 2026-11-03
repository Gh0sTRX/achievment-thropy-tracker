from atlas.core import game_id

def make_sample() -> dict:
    names=['ORBITAL RANGER','PIXEL VALLEY','DEEP BLUE','NIGHT DRIVE']
    badges=[('First Steps',10,1.05),('Explorer',25,1.35),('Challenge Accepted',40,1.9),('Final Chapter',100,3.1),('Collector',50,2.2)]
    games=[];ach=[]
    for i,name in enumerate(names):
        gid=game_id('demo',name)
        games.append({'id':gid,'name':name,'platform':'demo','title_id':'',
            'platform_edition':'demo','cover_url':'','hero_url':'','image_source':'',
            'plan':'Demo game — not a real platform title','notes':'','ownership':'unknown'})
        for j,(t,pts,ratio) in enumerate(badges):
            ach.append({'id':f'demo:{i}:{j}','provider_id':f'demo:{i}:{j}',
                'game_id':gid,'game_name':name,'name':t,'points':pts,'ratio':ratio,
                'dlc':'','source_url':'','unlocked':j < (i+1)%4,'unlock_time':'',
                'flag':False,'description':'Demonstration only. Import your own data to replace this.',
                'icon_url':'','source':'demo'})
    return {'schema':1,'platform':'demo','gamertag':'','created_at':'',
            'complete_export':False,'games':games,'achievements':ach}

