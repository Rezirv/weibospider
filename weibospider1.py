import json
import requests
from pymongo import MongoClient
import time
import random
import re
import redis
from selenium import webdriver
rechina = re.compile("[\u4e00-\u9fa5]+")
headers = {
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
    'Cookie': 'ALF=1550929682;MLOGIN=1;M_WEIBOCN_PARAMS=oid%3D3761323192%26luicode%3D20000174%26lfid%3D2304131900022001_-_WEIBO_SECOND_PROFILE_WEIBO%26uicode%3D10000011%26fid%3D231051_-_followers_-_1900022001;SCF=AhEZGdL30CoH49T2ivZgTEgB5e30m_rnNt_pR4YN6CdajyY4qMwXCoC51ko2cUK5vhGVDTphAh0jTb1Az7B_rok.;SSOLoginState=1548338733;SUB=_2A25xTbZ9DeRhGeVM61QS9S_OyTuIHXVSsdo1rDV6PUJbktANLXP2kW1NTTcT7oAYJS0vVhkyRd-2rx6fBLHqnLRF;SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWP_WfHTwe4FHnvGalqH9wN5JpX5K-hUgL.FoeEehq0SK2EeoM2dJLoI79C9PDDMrqt;SUHB=0cSnD_1pyvvVWr;WEIBOCN_FROM=1110006030;XSRF-TOKEN=556ffa;_T_WM=a6e8ed6ad6c10496f8a9ec1cc9134cd2',
    'Accept':'application/json, text/plain, */*',
    'Referer':'https://m.weibo.cn/profile/1900022001',
    'Connection':'close',
    'MWeibo-Pwa':'1',
    '-Requested-With':'XMLHttpRequest'
}
proxies=[{'http':'http://proxy.asec.buptnsrc.com:8001'},
         {'http':'http://proxy3.asec.buptnsrc.com:8001'},
         {'http':'http://proxy4.asec.buptnsrc.com:8001'},
         {'http':'http://proxy5.asec.buptnsrc.com:8001'}]

class weibo():

    def __init__(self):
        pass

    def user_detail(self, uid):
        """
        获取相关用户的详细信息
        :return:
        """
        url = "https://m.weibo.cn/profile/info?uid=%s"%(uid)
        time.sleep(random.randint(2,7))
        p = random.choice(proxies)
        user_info = requests.post(url, headers=headers, proxies=p)
        data = json.loads(user_info.text)
        user = data['data']['user']
        users_info = {
            'uid':user['id'],
            'name': user['screen_name'],
            'verified': user['verified_reason'],
            'profile_url':user['profile_url'],
            'description':user['description']
        }
        weibos =[]
        for page in range(1,5):
            weibo_url ="https://m.weibo.cn/api/container/getIndex?containerid=230413{}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={}".format(uid, page)
            try:
                p2 = random.choice(proxies)
                weibo_info = requests.get(weibo_url, headers=headers, proxies=p2 )
                time.sleep(random.randint(2,5))
                weibo_infos = json.loads(weibo_info.text)
            except BaseException as e:
                print(e)
            cards = weibo_infos['data']['cards']
            for card in cards:
                if card['card_type'] == 9:
                    every_weibo = {
                        'id':card['mblog']['id'],
                        'text':''.join(rechina.findall(card['mblog']['text'])),
                        'time':card['mblog']['created_at'],
                        'attitudes_count':card['mblog']['attitudes_count'],
                        'comments_count':card['mblog']['comments_count'],
                        'reposts_count':card['mblog']['reposts_count']
                    }
                    weibos.append(every_weibo)
        users_info['weibo']=weibos
        self.user.insert(dict(users_info))

    def weibo_fans(self, uid):
        """
        获取每个用户的fans,并将fans的uid存入redis
        :param uid:
        :return:
        """
        fans_group = {
            'owner':uid
        }
        myfans = []
        for page in range(1,20):
            try:
                url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{}&since_id={}'.format(uid, page)
                p = random.choice(proxies)
                fans_page = requests.get(url, headers=headers, proxies=p)
                fans_lists = json.loads(fans_page.text)
                group = fans_lists['data']['cards'][0]['card_group']
            except Exception as e:
                print(e)
            else:
                for fan in group:
                    if fan['card_type'] == 10:
                        pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
                        r = redis.Redis(connection_pool=pool)
                        r.sadd('weivoUid',fan['user']['id'])
                        everyfan ={
                            'id':fan['user']['id'],
                            'name':fan['user']['screen_name'],
                            'follow_count':fan['user']['follow_count'],
                            'fans_count':fan['user']['followers_count'],
                            'desc1':fan['desc1'],
                            'desc2':fan['desc2'],
                            'profile_url':fan['user']['profile_url']
                        }
                        myfans.append(everyfan)
        fans_group['fans']=myfans
        self.fans.insert(dict(fans_group))
        print("写fans入mongodb成功")

    def weibo_follow(self, uid):
        """
        获取关注的用户的信息并存入mongodb
        :param uid:
        :return:
        """
        follows = {
            'ownerid':uid
        }
        myfollows = []
        for page in range(1,40):
            try:
                url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{}&page={}'.format(uid, page)
                p = random.choice(proxies)
                follows_page = requests.get(url, headers=headers, proxies=p)
            except Exception as e:
                print(e)
            else:
                follows_lists = json.loads(follows_page.text)
                try:
                    list = follows_lists['data']['cards'][0]['card_group']
                except:
                    pass
                else:
                    for follow in list:
                        if follow['card_type'] == 10:
                            self.r.sadd('weivoUid',follow['user']['id'])
                            every_follow = {
                                'id':follow['user']['id'],
                                'name':follow['user']['screen_name'],
                                'followers_count':follow['user']['followers_count'],
                                'fans':follow['user']['follow_count'],
                                'profile_url':follow['user']['profile_url'],
                                'desc1':follow['desc1'],
                                'desc2':follow['desc2']
                            }
                            myfollows.append(every_follow)
        follows['follows'] = myfollows
        self.follow.insert(dict(follows))
        print("写follows入mongodb成功")

    def get_uid(self):
        return self.r.spop('weivoUid')

    def open_redis(self):
        """
        连接redis
        :return:
        """
        self.pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
        self.r = redis.Redis(connection_pool=self.pool)


    def open_db(self):
        """
        连接mongodb
        :return:
        """
        self.client = MongoClient('localhost')
        self.db = self.client.weibodata
        self.follow = self.db.follow
        self.fans = self.db.fans
        self.user = self.db.user

    def close_db(self):
        """
        断开mongodb连接
        :return:
        """
        self.client.close()

if __name__ == '__main__':
    weibo =weibo()
    weibo.open_db()
    weibo.open_redis()
    flag = True
    while flag:
        uid =weibo.get_uid()
        weibo.weibo_fans(uid)
    weibo.close_db()
