import requests
import os
import re
import json
from contextlib import closing
import urllib3
import pandas as pd
from lxml import etree
# import argparse

# arg = argparse.ArgumentParser("This is a Bilibili's vedio Downloader!\n")

def status_judge(code):
    print('状态码:' + str(code))


class BLVSpider:
    regex_cid = re.compile("\"cid\":(.{10})")
    regex_cid2 = re.compile("\d+")

    def __init__(self, avid):
        self.avid = avid
        self.oriUrl = 'https://www.bilibili.com/video/av{}'.format(avid)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        self.url = 'https://api.bilibili.com/x/player/playurl?avid={}&cid={}&qn=0&type=&otype=json'
        self.barUrl = 'https://comment.bilibili.com/{}.xml'

    def Check_Dir(self, videoname):
        self.parentpath = os.getcwd() + '/BLSpider/' + videoname + '/'
        print("输出地址：" + self.parentpath)
        if not os.path.exists(path=self.parentpath):
            os.makedirs(self.parentpath)
        self.videopath = self.parentpath + '/' + videoname + '.flv'

    def Parse_Url(self, info):
        self.headers['Referer'] = self.oriUrl
        response = requests.get(self.url.format(self.avid, info['cid']))
        if response.status_code == requests.codes.ok:
            result = json.loads(response.content.decode())
            durl = result['data']['durl'][0]
            video_url = durl['url']
            size = durl['size']
            print("视频大小：{:.3f}MB".format(size / 1024 / 1024))
            video_response = requests.get(video_url, headers=self.headers, stream=True)
            if video_response.status_code == requests.codes.ok:
                print("正在下载： {:3d}%".format(0), end='')
                with open(self.videopath, 'wb') as f:
                    buffer = 1024
                    count = 0
                    while True:
                        if count + buffer <= size:
                            f.write(video_response.raw.read(buffer))
                            count += buffer
                        else:
                            f.write(video_response.raw.read(buffer))
                            count += (size % buffer)
                        file_size = os.path.getsize(self.videopath)
                        print("\b\b\b\b{:3d}%".format((int)(file_size / size * 100)), end='')
                        if count == size:
                            print("\b\b\b\b{:3d}%    下载完成！".format(100), end='')
                            break;
                print()

    def Get_Barrage(self, cid):
        response = requests.get(self.barUrl.format(cid))
        if response.status_code == requests.codes.ok:
            print("开始下载弹幕")
            data = response.content.decode()
            regex_bar = re.compile(r'">(.*?)</d>')
            regex_time = re.compile(r'p="(\d+\.\d+),')
            barrage_list = re.findall(regex_bar, data)
            time_stamp = re.findall(regex_time, data)
            table = pd.DataFrame({"内容":barrage_list, "时间戳":time_stamp})
            table.to_csv(self.parentpath + '弹幕.csv', index=True, header=True)
            print("下载完毕！")

    def Get_Video_Info(self):
        response = requests.get(self.oriUrl, headers=self.headers)
        info = dict()
        if response.status_code == requests.codes.ok:
            html_element = etree.HTML(response.content.decode())
            author = dict()
            author['name'] = html_element.xpath("/html/body/div[@id='app']/div[@class='v-wrap']/div[@class='r-con']"
                                                "/div[@id='v_upinfo']//a[@report-id='name']/text()")[0]
            info['author'] = author
            cid1 = self.regex_cid.findall(response.content.decode())[0]
            cid = self.regex_cid2.match(cid1)[0]
            info['cid'] = cid
            info_url = "https://api.bilibili.com/x/web-interface/view?aid={}&cid={}".format(self.avid, cid)
            info_response = requests.get(info_url, headers=self.headers)
            if info_response.status_code == requests.codes.ok:
                data = json.loads(info_response.content.decode())["data"]

                #视频简介
                info['desc'] = data['desc']

                #标题
                info['title'] = data['title'].replace('/',' ')

                #详细信息
                stat = data['stat']

                #播放量
                info['view'] = stat['view']

                #弹幕
                info['danmaku'] = stat['danmaku']

                #评论
                info['reply'] = stat['reply']

                #硬币
                info['coin'] = stat['coin']

                #点赞
                info['like'] = stat['like']

                #收藏
                info['favorite'] = stat['favorite']

                #分享
                info['share'] = stat['share']

        self.Check_Dir(info['title'])

        with open(self.parentpath + '详细信息.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(info, ensure_ascii=False, indent=2))
        return info

    def run(self):
        info = self.Get_Video_Info()
        self.Parse_Url(info=info)
        self.Get_Barrage(info['cid'])


if __name__ == '__main__':
    # arg.add_argument("--avid","-a",default="",type=str,help="the avid of the vedio you want to download on Bilibili website")
    # args = arg.parse_args()
    # spider = BLVSpider(args.avid)
    aid = input("请输入av号：")
    spider = BLVSpider(aid)
    spider.run()