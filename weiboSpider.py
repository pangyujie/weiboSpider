import datetime
import re
import string
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
import traceback
import concurrent.futures

import requests
from bs4 import BeautifulSoup
from lxml import etree


cookie = {"Cookie": "SCF=AlJx51nACyZ00vHFohBskzxzWj_LEsM88RMtnf9y9O6akfrEhv5YxlHAjaTVS_gOzpFOW659rrkpTA_BCVsmQVk.; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFM3GjG724o4ORoFz4qdL5n5JpX5o2p5NHD95Qf1hBfSo-fSK.cWs4DqcjiMspaqPib9g8E; SUB=_2A250jC8kDeRhGeNG71cX9SvJwjqIHXVXjrFsrDV6PUJbkdBeLVShkW0dwqjmnfvoF0iBXjMJyKKQhdvoPg..; SUHB=0k1CbhMepbb59p; SSOLoginState=1502109556"}  # 将your cookie替换成自己的cookie
filter_val = 1  # 取值范围为0、1，程序默认值为0，代表要爬取用户的全部微博，1代表只爬取用户的原创微博
limit = 300
pool_size = 5

class Weibo:
    # weibo类初始化

    def __init__(self, user_id):
        self.user_id = user_id  # 用户id，即需要我们输入的数字，如昵称为“Dear-迪丽热巴”的id为1669879400
        self.userName = ''  # 用户名，如“Dear-迪丽热巴”
        self.weiboNum = 0  # 用户全部微博数
        self.weiboNum2 = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibos = []  # 微博内容
        self.num_zan = []  # 微博对应的点赞数
        self.num_forwarding = []  # 微博对应的转发数
        self.num_comment = []  # 微博对应的评论数
        self.transtable = str.maketrans({
            '\r': '',
            '\n': '',
            '\t': ''
        })

    # 获取用户昵称
    def getUserName(self):
        try:
            url = 'http://weibo.cn/%d/info' % (self.user_id)
            html = requests.get(url, cookies=cookie).content
            selector = etree.HTML(html)
            userName = selector.xpath("//title/text()")[0]
            self.userName = userName[:-3]
            # print '用户昵称：' + self.userName
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    # 获取用户微博数、关注数、粉丝数
    def getUserInfo(self):
        try:
            url = 'http://weibo.cn/u/%d?filter=%d&page=1' % (
                self.user_id, filter_val)
            html = requests.get(url, cookies=cookie).content
            selector = etree.HTML(html)
            pattern = r"\d+\.?\d*"

            # 微博数
            str_wb = selector.xpath(
                "//div[@class='tip2']/span[@class='tc']/text()")[0]
            guid = re.findall(pattern, str_wb, re.S | re.M)
            for value in guid:
                num_wb = int(value)
                break
            self.weiboNum = num_wb
            # print '微博数: ' + str(self.weiboNum)

            # 关注数
            str_gz = selector.xpath("//div[@class='tip2']/a/text()")[0]
            guid = re.findall(pattern, str_gz, re.M)
            self.following = int(guid[0])
            # print '关注数: ' + str(self.following)

            # 粉丝数
            str_fs = selector.xpath("//div[@class='tip2']/a/text()")[1]
            guid = re.findall(pattern, str_fs, re.M)
            self.followers = int(guid[0])
            # print '粉丝数: ' + str(self.followers)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    # 获取用户微博内容及对应的点赞数、转发数、评论数
    def getWeiboInfo(self):
        try:
            url = 'http://weibo.cn/u/%d?filter=%d&page=1' % (
                self.user_id, filter_val)
            html = requests.get(url, cookies=cookie).content
            try:
                selector = etree.HTML(html)
            except Exception:
                return
            if selector.xpath('//input[@name="mp"]') == []:
                pageNum = 1
            else:
                pageNum = (int)(selector.xpath(
                    '//input[@name="mp"]')[0].attrib['value'])
            pattern = r"\d+\.?\d*"
            weibo_cnt = 0
            for page in range(1, pageNum + 1):
                url2 = 'http://weibo.cn/u/%d?filter=%d&page=%d' % (
                    self.user_id, filter_val, page)
                html2 = requests.get(url2, cookies=cookie).content
                try:
                    selector2 = etree.HTML(html2)
                except Exception:
                    continue
                info = selector2.xpath("//div[@class='c']")
                # print len(info)
                if len(info) > 3:
                    for i in range(0, len(info) - 2):
                        self.weiboNum2 = self.weiboNum2 + 1
                        # 微博内容
                        str_t = info[i].xpath("div/span[@class='ctt']")
                        weibos = str_t[0].xpath('string(.)').translate(self.transtable)
                        self.weibos.append(weibos)
                        # print '微博内容：'+ weibos
                        # 点赞数
                        str_zan = info[i].xpath("div/a/text()")[-4]
                        guid = re.findall(pattern, str_zan, re.M)
                        num_zan = int(guid[0])
                        self.num_zan.append(num_zan)
                        # print '点赞数: ' + str(num_zan)
                        # 转发数
                        forwarding = info[i].xpath("div/a/text()")[-3]
                        guid = re.findall(pattern, forwarding, re.M)
                        num_forwarding = int(guid[0])
                        self.num_forwarding.append(num_forwarding)
                        # print '转发数: ' + str(num_forwarding)
                        # 评论数
                        comment = info[i].xpath("div/a/text()")[-2]
                        guid = re.findall(pattern, comment, re.M)
                        num_comment = int(guid[0])
                        self.num_comment.append(num_comment)
                        # print '评论数: ' + str(num_comment)

                        print('%d - %d' % (self.user_id, self.weiboNum2))
                        if self.weiboNum2 > limit:
                            if filter_val == 0:
                                print('共' + str(self.weiboNum2) + '条微博')
                            else:
                                print('共' + str(self.weiboNum2) + '条为原创微博')
                            return
        except Exception as e:
          print("Error: ", e)
          traceback.print_exc()

    # 主程序
    def start(self):
        try:
            self.getUserName()
            self.getUserInfo()
            self.getWeiboInfo()
            print('信息抓取完毕, %s' % self.userName)
            print('===========================================================================')
        except Exception as e:
            print("Error: ", e)

def read_ids(ids_file_path):
    ids = []
    with open(ids_file_path, 'r', encoding='utf-8') as file_in:
        for line in file_in:
            if line.strip():
                ids.append(line.strip())
    return ids

def create_anf_run(user_id):
    out_file_path = os.path.join(current_dir, 'weibo', 'weibos.' + user_id + '.txt')
    wb = Weibo(int(user_id))  # 调用weibo类，创建微博实例wb
    wb.start()
    with open(out_file_path, 'w', encoding='utf-8') as file_out:
        for idx, user_weibo in enumerate(wb.weibos):
            file_out.write(user_id + '#&#' + \
                            wb.userName + '#&#' + \
                            str(wb.following) + '#&#' + \
                            str(wb.followers) + '#&#' + \
                            str(wb.num_zan[idx]) + '#&#' + \
                            str(wb.num_forwarding[idx]) + '#&#' + \
                            str(wb.num_comment[idx]) + '#&#' + \
                            str(user_weibo) + '\n')

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    ids_file_path = os.path.join(current_dir, 'ids.txt')
    ids = read_ids(ids_file_path)
    os.makedirs(os.path.join(current_dir, 'weibo'), exist_ok=True)

    with concurrent.futures.ProcessPoolExecutor(max_workers=pool_size) as executor:
        executor.map(create_anf_run, ids)
