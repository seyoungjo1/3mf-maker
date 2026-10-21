"""Publish one explicitly approved carousel; persistent checkpoints prevent blind retries."""
import hashlib,json,os,re,subprocess,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path

class PublishError(Exception): pass

def api(path, token, version, params=None, write=False):
    query=urllib.parse.urlencode(params or {})
    url=f'https://graph.instagram.com/{version}/{path}'
    data=query.encode() if write else None
    if query and not write: url+='?'+query
    req=urllib.request.Request(url,data=data,headers={'Authorization':'Bearer '+token},method='POST' if write else 'GET')
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as exc:
        code=subcode=None
        try:
            error=json.loads(exc.read(65536)).get('error',{});code=error.get('code');subcode=error.get('error_subcode')
        except Exception: pass
        raise PublishError(f'Meta HTTP {exc.code}; code={code if isinstance(code,int) else "unknown"}; subcode={subcode if isinstance(subcode,int) else "unknown"}') from None
    except Exception: raise PublishError('Network or response failure; no automatic write retry') from None

def save(path,state):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    subprocess.run(['git','add',str(path)],check=True)
    diff=subprocess.run(['git','diff','--cached','--quiet'])
    if diff.returncode:
        subprocess.run(['git','commit','-m','docs: checkpoint Instagram publication'],check=True)
        subprocess.run(['git','push'],check=True)

def ready(container,token,version):
    for _ in range(60):
        status=api(container,token,version,{'fields':'status_code'}).get('status_code')
        if status=='FINISHED': return
        if status in ('ERROR','EXPIRED','PUBLISHED'): raise PublishError('Unexpected container status: '+status)
        time.sleep(10)
    raise PublishError('Container processing timed out')

def validate(manifest):
    if not re.fullmatch(r'[a-z0-9-]{1,70}',manifest['post_id']): raise PublishError('Invalid post ID')
    if not re.fullmatch(r'[a-f0-9]{40}',manifest['asset_commit']): raise PublishError('Assets must use immutable commit')
    if not 2<=len(manifest['assets'])<=10: raise PublishError('Invalid carousel size')
    if len(manifest['caption'])>2200: raise PublishError('Caption too long')
    if manifest.get('approved_by_user') is not True: raise PublishError('No publication authorization')
    for item in manifest['assets']:
        path=Path(item['path'])
        if not str(path).startswith('docs/social/previews/shuttle-r9/') or '..' in path.parts: raise PublishError('Invalid asset path')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']: raise PublishError('Asset hash mismatch')
        data=path.read_bytes()
        if item['type']=='IMAGE' and data[:3]!=b'\xff\xd8\xff': raise PublishError('Image must be JPEG')
        if item['type']=='VIDEO' and data[4:8]!=b'ftyp': raise PublishError('Video must be MP4')
        if item['type'] not in ('IMAGE','VIDEO'): raise PublishError('Invalid media type')

def run():
    manifest=json.loads(Path('posts/shuttle-r9/approved.json').read_text())
    validate(manifest)
    path=Path('docs/social/publish-state')/(manifest['post_id']+'.json')
    if path.exists():
        previous=json.loads(path.read_text())
        if previous.get('status')=='published': print('Already published:',previous.get('permalink'));return
        raise PublishError('Existing publication checkpoint. Inspect it; do not retry blindly.')
    config=json.loads(Path('config/instagram.json').read_text());token=os.environ.get('IG_ACCESS_TOKEN','').strip()
    if not token: raise PublishError('Missing IG_ACCESS_TOKEN')
    version=config['api_version'];account=config['user_id']
    me=api('me',token,version,{'fields':'user_id,username'})
    if str(me.get('user_id'))!=account or me.get('username')!=config['expected_username']: raise PublishError('Account mismatch')
    # Detect a previously published matching caption before any write.
    feed=api(account+'/media',token,version,{'fields':'id,caption,permalink','limit':25})
    for post in feed.get('data',[]):
        if post.get('caption')==manifest['caption']: raise PublishError('Matching caption already exists; inspect existing post')
    for item in manifest['assets']:
        url='https://raw.githubusercontent.com/seyoungjo1/3mf-maker/'+manifest['asset_commit']+'/'+urllib.parse.quote(item['path'])
        with urllib.request.urlopen(url,timeout=60) as response:
            if hashlib.sha256(response.read(20000000)).hexdigest()!=item['sha256']: raise PublishError('Public media mismatch')
    state={'post_id':manifest['post_id'],'status':'creating','user_id':account,'children':[],'asset_commit':manifest['asset_commit']}
    save(path,state)
    try:
        for item in manifest['assets']:
            url='https://raw.githubusercontent.com/seyoungjo1/3mf-maker/'+manifest['asset_commit']+'/'+urllib.parse.quote(item['path'])
            params={'is_carousel_item':'true'}
            if item['type']=='VIDEO':params.update(media_type='VIDEO',video_url=url)
            else:params['image_url']=url
            child=api(account+'/media',token,version,params,True)['id']
            state['children'].append(child);save(path,state);ready(child,token,version)
        parent=api(account+'/media',token,version,{'media_type':'CAROUSEL','children':','.join(state['children']),'caption':manifest['caption']},True)['id']
        state.update(status='container_created',container_id=parent);save(path,state);ready(parent,token,version)
        state['status']='publishing';save(path,state)
        published=api(account+'/media_publish',token,version,{'creation_id':parent},True)['id']
        state.update(status='published',media_id=published);save(path,state)
        result=api(published,token,version,{'fields':'id,permalink,media_type,children{id}'})
        state.update(permalink=result.get('permalink'),media_type=result.get('media_type'),item_count=len(result.get('children',{}).get('data',[])))
        save(path,state);print('Published:',state.get('permalink'))
    except Exception as exc:
        if state.get('status')!='published':
            state['status']='unknown' if state.get('status')=='publishing' else 'failed'
        state['error']=str(exc) if isinstance(exc,PublishError) else 'Operation interrupted; inspect checkpoint'
        save(path,state)
        raise PublishError(state['error']) from None

if __name__=='__main__':
    try: run()
    except PublishError as exc: print(str(exc));raise SystemExit(1)
