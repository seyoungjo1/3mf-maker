"""Read the owner's recent posts for visual study. No publishing endpoints."""
import json, os, urllib.request
from pathlib import Path
config=json.loads(Path('instagram/config.json').read_text())
root=Path('instagram/references/account'); root.mkdir(parents=True,exist_ok=True)
token=os.environ.get('IG_ACCESS_TOKEN','')
req=urllib.request.Request('https://graph.instagram.com/'+config['api_version']+'/'+config['user_id']+'/media?fields=id,caption,media_type,media_url,thumbnail_url,permalink,children%7Bmedia_type,media_url,thumbnail_url%7D&limit=6',headers={'Authorization':'Bearer '+token})
try:
    with urllib.request.urlopen(req,timeout=30) as response: data=json.load(response)
except Exception:
    root.joinpath('status.json').write_text(json.dumps({'ok':False,'reason':'media_read_failed'})); raise SystemExit(0)
posts=[]
for i,post in enumerate(data.get('data',[])):
    entry={k:post.get(k,'') for k in ('id','caption','media_type','permalink')}; entry['images']=[]
    items=post.get('children',{}).get('data',[])[:2] or [post]
    for j,item in enumerate(items):
        url=item.get('thumbnail_url') if item.get('media_type')=='VIDEO' else item.get('media_url')
        if not url or not url.startswith('https://'): continue
        try:
            with urllib.request.urlopen(url,timeout=30) as response:
                raw=response.read(12000000)
            name=f'post_{i+1}_{j+1}.jpg'; root.joinpath(name).write_bytes(raw); entry['images'].append(name)
        except Exception: entry['download_failed']=True
    posts.append(entry)
root.joinpath('status.json').write_text(json.dumps({'ok':True,'posts':posts},ensure_ascii=False,indent=2)+'\n')
