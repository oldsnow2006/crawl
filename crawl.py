import threading
import time
from queue import Queue
import requests
from lxml import etree
import json


#用来存放采集线程
g_crawl_list=[]

#用来存放解析线程
g_parser_list=[]

class CrawlThread(threading.Thread):
    """爬取线程类"""
    def __init__(self,name,page_queue,data_queue):
        super(CrawlThread,self).__init__()
        self.name=name
        self.page_queue=page_queue
        self.data_queue=data_queue
        self.url='https://www.qiushibaike.com/hot/page/{}/'
        self.headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'}
    def run(self):
        print('%s----线程启动' %self.name)
        while 1:
            if self.page_queue.empty():
                break
            #从队列中取出页码
            page=self.page_queue.get()
            #拼接URL，发送请求
            url=self.url.format(page)
            r=requests.get(url,headers=self.headers )
            self.data_queue.put(r.text)
            #把采集结果放到data_queue
        print('%s----线程结束' %self.name)
class ParserThread(threading.Thread):
    """解析线程类"""
    def __init__(self,name,data_queue,fp,lock):
        super(ParserThread,self).__init__()
        self.name=name
        self.data_queue=data_queue
        self.fp=fp
        self.lock=lock
    def run(self):
        while 1:
            time.sleep(1)
            if self.data_queue.empty():
                break
            #从data_queue中取出一页数据
            data=self.data_queue.get()
            #解析内容函数
            self.parse_content(data)
    def parse_content(self,data):
        tree=etree.HTML(data)
        article_list=tree.xpath('//div[contains(@class,"article block")]')
        items=[]
        for article in article_list:

            author=article.xpath('string(.//div[@class="author clearfix"]//h2)').strip()

            span=article.xpath('string(.//div[@class="content"]/span)').strip()

            item={'作者':author,
            '内容':span}

            items.append(item)


        # for author in author_list:


        #写到文件中
        self.lock.acquire()

        self.fp.write(json.dumps(items,ensure_ascii=False)
                     + '\n')
        self.lock.release()


def create_queue():
    #创建页码队列
    page_queue=Queue()
    for page in range(1,5):
        page_queue.put(page)

    #创建内容队列
    data_queue=Queue()
    return page_queue,data_queue

def create_crawl_thread(page_queue,data_queue):
   #创建采集线程
    crawl_name=['采集线程1','采集线程2','采集线程3']
    for name in crawl_name:
        tcrawl=CrawlThread(name,page_queue,data_queue)
        g_crawl_list.append(tcrawl)

def create_parser_thread(data_queue,fp,lock):
   #创建解析线程
    parser_name=['解析线程1','解析线程2','解析线程3']
    for name in parser_name:
        tparser=ParserThread(name,data_queue,fp,lock)
        g_parser_list.append(tparser)
def main():
    #创建队列函数
    page_queue,data_queue=create_queue()

    #打开文件
    fp=open('package.json','a',encoding="utf-8")

    #创建锁
    lock=threading.Lock()



    #创建采集线程
    create_crawl_thread(page_queue,data_queue)

    #创建解析线程
    create_parser_thread(data_queue,fp,lock)

    #启动所有采集线程
    for tcrawl in g_crawl_list:
        tcrawl.start()

    #启动所有解析线程
    for tparser in g_parser_list:
        tparser.start()

    #主线程等待子线程结束

    for tcrawl in g_crawl_list:
        tcrawl.join()

    for tparser in g_parser_list:
        tparser.join()
    print("主线程子线程全部结束")
if __name__=='__main__':
    main()