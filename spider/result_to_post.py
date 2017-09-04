#!/usr/bin/env python

import re
import requests
import json
import time

from pyspider.result import ResultWorker

#import logging
#logging.basicConfig(level=logging.DEBUG)
#
#import httplib
#
#httplib.HTTPConnection.debuglevel = 1
#
#logging.basicConfig()
#logging.getLogger().setLevel(logging.DEBUG)
#requests_log = logging.getLogger("requests.packages.urllib3")
#requests_log.setLevel(logging.DEBUG)
#requests_log.propagate = True

host = 'http://$HOST/ghost/api/v0.1'

auth = {}
auth['grant_type']='password'
auth['username']=''
auth['password']=''
auth['client_id']=''
auth['client_secret']=''



class PostResultWorker(ResultWorker):
    headers = {}
    headers['Authorization']=''
    headers['Content-Type']='application/json'
    headers['Accept']='application/json'

    post = {}
    post['author']='1'
    post['featured']=False
    post['language']='en_US'
    post['markdown']=''
    post['page']=False
    post['slug']=''
    post['status']='draft'
    post['tags']=[]
    post['title']=''

    token=''
    tokenTime=0
    tokenExp=3000
    tokenType=''


    slugs={}

    def on_result(self, task, result):
        self.do_post(result)

    def get_token(self):
        r = requests.post(self.host+"/authentication/token", data=self.auth)
        res = json.loads(r.text)
        self.token=res['access_token']
        self.tokenType=res['token_type']
        self.tokenTime=time.time()

    def get_header(self):
        now=time.time()
        if (now-self.tokenTime > self.tokenExp):
            self.get_token()
            self.headers['Authorization']=self.tokenType + " " + self.token

        return self.headers

    def get_slug(self, result):
        url=result['url']
        if (-1 != url.find('?')):
            url=url[:url.find('?')]
        slugt=url.split('/')[-1]
        if (len(slugt) == 0):
            slugt=result['url'].split('/')[-2]

        if slugt in self.slugs:
            return self.slugs[slugt]

        r=requests.get(self.host+"/slugs/post/"+slugt+'/', headers=self.get_header());
        slug=json.loads(r.text)['slugs'][0]['slug']
        self.slugs[slugt]=slug

        return slug


    def get_post_payload(self, result):
        self.post['title']=result['title']
        self.post['slug']=self.get_slug(result)
        post_payload = {}
        post_payload['posts'] = [self.post]

        return post_payload


    def do_post(self, result):
        r = requests.post(self.host+"/posts/?include=tags", headers=self.get_header(), data=json.dumps(self.get_post_payload(result)))

        res = json.loads(r.text)
        newp=res['posts'][0]

        url=self.host+"/posts/"+str(newp['id'])+"/?include=tags";
        newp['markdown']=result['desc'] + '<br><br>[Readmore]('+result['url']+')'
        if (len(result['images']) > 0):
            newp['markdown'] = newp['markdown'] + '<br><br>![](' + result['images'][0] + ')'
        newp['status']='published'

        tags=[]
        orgtags=result['tags']
        for orgtag in orgtags:
            slug=str(orgtag).strip().lower().replace('/','').replace(' ', '-')
            r = requests.get(self.host+'/tags/slug/'+slug, headers=self.get_header())
            if (r.status_code != 200):
                tag = {}
                tag['name']=orgtag
                tag['hidden']=False
                payload={}
                payload['tags']=[tag]
                r = requests.post(self.host+"/tags", headers=self.get_header(), data=json.dumps(payload))
                
            newtag=json.loads(r.text)['tags'][0]
            tags.append(newtag)

        newp['tags']=tags
        payload = {}
        payload['posts'] = [newp]

        r = requests.put(url, headers=self.get_header(), data=json.dumps(payload))
        print(r.text)


if __name__ == '__main__':
    result={}
    result["url"]= 'https://blog.twitter.com/2016/open-sourcing-twitter-heron'
    result["title"]= 'Open Sourcing Twitter Heron'
    result["desc"]= 'Last year we announced the introduction of our new distributed stream computation system, Heron. Today we are excited to announce that we are open sourcing Heron under the permissive Apache v2.0 license'
    result["data"]= 'Last year we announced the introduction of our new distributed stream computation system, Heron. Today we are excited to announce that we are open sourcing Heron under the permissive Apache v2.0 license'
    result["tags"]= ['Twitter', 'open source']
    result["images"]= ['https://g.twimg.com/blog/blog/image/manhattan_1.png']

    worker = PostResultWorker(None, None)
    worker.do_post(result)
