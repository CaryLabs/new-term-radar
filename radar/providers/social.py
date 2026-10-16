import base64
import html
import urllib.parse

from . import transport
from .errors import ProviderError


def reddit(query, time='week', sort='top', limit=25):
    client = transport.credential('reddit_client_id')
    secret = transport.credential('reddit_client_secret')
    basic = base64.b64encode((client+':'+secret).encode()).decode()
    token, ticket = transport.request('reddit','token','https://www.reddit.com/api/v1/access_token',
        form={'grant_type':'client_credentials'},headers={'Authorization':'Basic '+basic})
    access = token.get('access_token')
    if not isinstance(access,str) or not access:raise ProviderError('Reddit OAuth token missing')
    transport.record(ticket,'ok')
    params = urllib.parse.urlencode({'q':query,'t':time,'sort':sort,'limit':limit,'raw_json':1})
    data,ticket = transport.request('reddit','search','https://oauth.reddit.com/search?'+params,
                                    headers={'Authorization':'Bearer '+access})
    listing = data.get('data')
    if not isinstance(listing,dict) or not isinstance(listing.get('children'),list):
        raise ProviderError('Reddit response missing listing')
    posts=[]
    for item in listing['children']:
        p=item.get('data',{})
        if p.get('over_18'):continue
        if not all(k in p for k in ('id','title','selftext','score','subreddit','permalink','created_utc')):
            raise ProviderError('Reddit post missing required fields')
        posts.append({'id':p['id'],'title':' '.join(p['title'].split()),'text':' '.join(p['selftext'].split())[:600],
                      'score':int(p['score']),'comments':int(p.get('num_comments',0)),'subreddit':p['subreddit'],
                      'url':'https://www.reddit.com'+p['permalink'],'created':float(p['created_utc'])})
    transport.record(ticket,'ok',usage={'items':len(posts),'sampled':bool(listing.get('after'))})
    return posts,0


def youtube_comments(video_id):
    key=transport.credential('youtube_api_key')
    params=urllib.parse.urlencode({'key':key,'part':'snippet','videoId':video_id,'maxResults':20,
                                  'order':'relevance','textFormat':'plainText'})
    data,ticket=transport.request('youtube','comments','https://www.googleapis.com/youtube/v3/commentThreads?'+params)
    if not isinstance(data.get('items'),list):raise ProviderError('YouTube response missing items')
    out=[]
    try:
        for row in data['items']:
            snippet=row['snippet']['topLevelComment']['snippet']
            out.append({'id':row['snippet']['topLevelComment']['id'],
                        'text':html.unescape(snippet['textDisplay']), 'likes':int(snippet['likeCount'])})
    except (KeyError,TypeError,ValueError):raise ProviderError('YouTube comment missing fields') from None
    transport.record(ticket,'ok',usage={'items':len(out),'quota_units':1,'sampled':bool(data.get('nextPageToken'))})
    return out,0


def youtube_videos(query, limit=3):
    key=transport.credential('youtube_api_key')
    params=urllib.parse.urlencode({'key':key,'part':'snippet','q':query,'type':'video','maxResults':min(limit,50)})
    data,ticket=transport.request('youtube','video_search','https://www.googleapis.com/youtube/v3/search?'+params)
    if not isinstance(data.get('items'),list):raise ProviderError('YouTube response missing search items')
    try:ids=[row['id']['videoId'] for row in data['items']]
    except (KeyError,TypeError):raise ProviderError('YouTube video search has missing identifiers') from None
    transport.record(ticket,'ok',usage={'items':len(ids),'quota_units':100})
    return ids,0
