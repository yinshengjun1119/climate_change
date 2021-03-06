# -*- coding: utf-8 -*-
'''
爬取给定列表版本，用的是scrapy
'''
import scrapy
from wosspider.items import WosspiderItem
from lxml import etree
import requests
import json
import re
import time
from wosspider.seleniumimpactid import Selenium_impact_id
from wosspider.seleniumrefer import Selenium_refer
from wosspider.seleniumurl import Selenium_article_url


from scrapy.http.response.html import HtmlResponse
from scrapy.selector.unified import SelectorList

class WosSpiderSpider(scrapy.Spider):
    name = 'wos_spider'
    allowed_domains = ['apps.webofknowledge.com']
    start_urls = ['http://apps.webofknowledge.com/full_record.do?product=UA&search_mode=GeneralSearch&qid=1&SID=7BsMLYBgOqQMbkfrqtC&page=1&doc=1']
    # base_domain = "http://apps.webofknowledge.com/"
    art_list = ["Forced waves and their asymptotics in a Lotka-Volterra cooperative model under climate change", "Environmental impacts of a reduced flow stretch on hydropower plants", "Characterizing the regional contribution to PM10 pollution over northern France using two complementary approaches: Chemistry transport and trajectory-based receptor models"]

    def parse(self, response):
        if response.url == 'http://apps.webofknowledge.com/':
            art = self.art_list.pop(0)
            url, response = Selenium_article_url(art)
        url = response.url
        start = time.perf_counter()
        impact, authorid = Selenium_impact_id(url)
        if authorid.startswith('Funding Agency'):
            authorid = ''
        else:
            if 'Funding Agency' in authorid:
                indexauthor = authorid.index('Funding Agency')
                authorid = authorid[:indexauthor]
        # 其实这里可以封装成function
        if authorid != '':
            lauthoridindex = []
            authorid = authorid.split('\n')
            for index, lis in enumerate(authorid):
                reg1 = re.search(r'[A-Za-z]*, [A-Za-z]*', lis)
                if reg1:
                    lauthoridindex.append(index)
                # print(reg1)
            # print(lauthoridindex)
            authorid_refine = [['Author,Web of Science ResearcherID,ORCID Number']]
            for index, i in enumerate(lauthoridindex):
                if index + 1 < len(lauthoridindex):
                    authorid_refine.append(authorid[i:lauthoridindex[index + 1]])
                else:
                    authorid_refine.append(authorid[i:])
            authorid = authorid_refine
        if impact != '':
            impact_refine = ['JCR® Category;Quartile in Category']
            impact = impact.split('\n')
            for i in impact:
                # print(i)
                r1 = re.search(r'[A-Za-z]\d', i[-2:])
                # r1 = re.compile(r'[A-Za-z]\d')
                if r1:
                    jcr = ' '.join(i.split()[:-1])
                    quartile = i.split()[-1]
                    impact_refine.append(jcr + ';' + quartile)
            impact_refine.append(impact[-1])
            impact = impact_refine
        if authorid == '':
            authorid = []
        if impact == '':
            impact = []
        end = time.perf_counter()
        print('=' * 30)
        print('获取impact, authorid外接selenium用时：{}'.format(end - start))
        print("主程序中的authorid:")
        print(authorid)
        print("主程序中的impact:")
        print(impact)
        htmlElement = etree.HTML(response.text)

        # next = htmlElement.xpath(
        #     "//a[@class='view-all-link snowplow-view-all-in-cited-references-page-top']/@href")[0]
        # print(next)
        '''
        以下包括:
        1. 主表：article中字段：
        title, author, author2(作者清洗版),reprintauthor(通讯作者), journal, volume, issue, page, doi, pubdate(发表日期), documenttype, publisher, researchdomain(期刊的研究领域), abstract, authorkeywords, keywordsplus, reprintaddress, address, emailaddress, fund, researchareas, woscategories, lang, wosnum(wos自己对文章的编码), issn, eissn, idsnum, refer(次数）, cited(次数), url, self.referarticles(引用文献列表), self.authorrefer(引用文献对应的作者), self.journalrefer(引用文献对应的期刊), self.othersrefer(引用文献的其他信息)

        2. 作者副表author
        特有字段：
        authorlistkey (= author + wosnum, 为该表主键), coauthors
        与主表相同字段：
        title, wosnum, doi, address, emailaddress, pubdate, researchareas, woscategories, lang 

        3. 文献副表referlist
        特殊字段:
            每篇文章所引用的文章的所有title, author, journal, other（包括volume issue page date等信息）信息
            referarticles = []
            authorrefer = []
            journalrefer = []
            othersrefer = []

        citedtitles(被引用文章)，citedauthors，citedjournals，citedothers
        (这些字段在pipeline里面实现，这里只有集合list)

        与主表相同字段：
        wosnum, doi, title, author, refer

        '''
        start = time.perf_counter()
        title = ''.join(
            htmlElement.xpath("//div[@aria-label='Main content']//div[@class='title']//text()")).strip().replace("\n",
                                                                                                                 "")
        # print(title)
        journal = ''.join(htmlElement.xpath(
            "//div[@class='block-record-info block-record-info-source']//span[@class='sourceTitle']//text()")).strip().replace(
            "\n", "").lower()
        # print(journal)

        '''
        alls2里面包含了以下字段：
        volume, issue, page, doi, date, documenttype, publisher, researchdomain 
        '''

        alls2 = htmlElement.xpath(
            "//div[@class='block-record-info block-record-info-source']//p[@class='FR_field']")

        data2 = []
        for a in alls2:
            # print(''.join(a.xpath(".//text()")))
            data2.append(''.join(a.xpath(".//text()")))
        # print(data2)
        volume = ''.join([s for s in data2 if "Volume" in s]).strip().replace("\n", "")
        if volume != '':
            volume = volume.split(':')[-1]
        # print(volume)
        issue = ''.join([s for s in data2 if "Issue" in s]).strip().replace("\n", "")
        if issue != '':
            issue = issue.split(':')[-1]
        page = ''.join([s for s in data2 if "Pages" in s]).strip().replace("\n", "")
        if page != '':
            page = page.split(':')[-1]
        doi = ''.join([s for s in data2 if "DOI" in s]).strip().replace("\n", "")
        if doi != '':
            doi = doi.replace('DOI:', '', 1)
        date = ''.join([s for s in data2 if "Published" in s]).strip().replace("\n", "")
        if date != '':
            date = date.split(':')[-1]
        # print(date)
        documenttype = ''.join([s for s in data2 if "Document Type" in s]).strip().replace("\n", "")
        if documenttype != '':
            documenttype = documenttype.split(':')[-1]
        publisher = ''.join([s for s in data2 if "Publisher" in s]).strip().replace("\n", "")
        if publisher != '':
            publisher = ' '.join(publisher.split(' ')[1:])
        # 这里有个爬虫过程得到的意外惊喜：期刊的领域
        researchdomain = ''.join([s for s in data2 if "Research Domain" in s]).strip().replace("\n", "")
        if researchdomain != '':
            researchdomain = researchdomain.replace('Research Domain ', '', 1)

        # print(data)
        print(response.url)
        '''
        alls里面包含了以下字段：
        author, author2, coauthors, abstract, authorkeywords, keywordplus, reprintaddress, reprintauthor, address, emailaddress, researchareas, woscategories, lang, wosnum, issn, eissn, idsnum, refer, cited
        '''

        alls = htmlElement.xpath("//div[@class='block-record-info']//p[@class='FR_field']")

        data = []
        for a in alls:
            # print(''.join(a.xpath(".//text()")))
            data.append(''.join(a.xpath(".//text()")))
            # print('*' * 30)
        author = ''.join([s for s in data if "By" in s]).strip().replace("\n", "")
        author = author.replace(r' ', '')

        # print(author)

        # 对作者进行数据清洗,去除[1,2]等方括号之内的
        author2 = author.split(':')[1:]
        author2 = ''.join(author2)
        a1 = re.compile(r'\[.*?\]')
        author2 = a1.sub('', author2).split(';')
        # print(author2)
        if author != '':
            author = author.replace('By:', '', 1)
        # 合作者处理（其实就是遍历时，取到除了遍历到的元素之外的元素的操作）

        coauthors = []
        for index, i in enumerate(author2):
            coauthors.append(author2[:index] + author2[index + 1:])
            # print(coauthors)
        # wos太坑爹了，一周前按照顺序索引爬没问题，现在基本abstract没规律了
        # abstract = ''.join(data[1]).strip().replace("\n", "")
        # if abstract == '' or ' ':
        all_abstract = htmlElement.xpath("//div[@class='block-record-info']//text()")
        all_abstract = ''.join(all_abstract).strip().replace('\n', ' ')
        # print(all_abstract)
        try:
            index1 = all_abstract.index('Abstract')
            # print(index1)
            try:
                index2 = all_abstract.index('Keywords')
            except:
                index2 = all_abstract.index('Author')
            # print(index2)
            abstract = all_abstract[index1 + 9:index2]
        except:
            abstract = ''
            # print('='*30)
            # print(abstract)
            # a3 = re.compile(r'(Abstract)(.*?)(Keywords)')
            # abstract = re.findall(a3, all_abstract)
            # for i in all_abstract:
            #     if i == '\n':
            #         all_abstract.remove(i)
            # print(all_abstract)
            # for index, i in enumerate(all_abstract):
            #     if i == 'Abstract':
            #         abstract = all_abstract[index+1]
            #         break
            # abstract = ''.join(all_abstract).strip().replace("\n", "")

        # if "Author Keywords" or "KeyWords Plus" in abstract:
        #     abstract = ''
        authorkeywords = ''.join([s for s in data if "Author Keywords" in s]).strip().replace("\n", "")

        keywordsplus = ''.join([s for s in data if "KeyWords Plus" in s]).strip().replace("\n", "")
        if keywordsplus != '':
            keywordsplus = keywordsplus.split(':')[1:]
        if authorkeywords == '' and keywordsplus == '':
            authorkeywords = ''.join([s for s in data if "Keyword List" in s]).strip().replace("\n", "")
        if authorkeywords != '':
            authorkeywords = authorkeywords.split(':')[1:]
        # 这里reprintaddress仅仅为了找到reprint author
        reprintauthor = ''.join([s for s in data if "Reprint Address" in s]).strip().replace("\n", "")
        # s = 'Reprint Address:        Dirksen, R (reprint author)'

        a2 = re.compile(r'[:](.*?)[\(]')
        reprintauthor = re.findall(a2, reprintauthor)
        reprintauthor = ''.join(reprintauthor).strip()
        # print('reprintauthor:',reprintauthor)
        # 所有地址一起分割：
        reprintaddress = ''.join(
            htmlElement.xpath("//div[@class='block-record-info']//td[@class='fr_address_row2']/text()"))
        address = htmlElement.xpath("//div[@class='block-record-info']//td[@class='fr_address_row2']/a/text()")

        # address = ''.join([s for s in data if "Addresses" in s]).strip().replace("\n", "")
        emailaddress = ''.join([s for s in data if "E-mail Addresses" in s]).strip().replace("\n", "")
        if emailaddress != '':
            emailaddress = emailaddress.split(':')[1:]
        fundingagency = htmlElement.xpath("//table[@class='FR_table_borders']//tr[@class='fr_data_row']/td/text()")
        grantnumber = htmlElement.xpath("//table[@class='FR_table_borders']//tr[@class='fr_data_row']/td/div/text()")
        while '\n' in fundingagency:
            fundingagency.remove('\n')
        for index, i in enumerate(fundingagency):
            if "\xa0" in i:
                fundingagency[index] = i.replace("\xa0", '')
        while '\n' in grantnumber:
            grantnumber.remove('\n')
        for index, i in enumerate(grantnumber):
            if "\xa0" in i:
                grantnumber[index] = i.replace("\xa0", '')
        fund = list(zip(fundingagency, grantnumber))
        # fund = ''.join(htmlElement.xpath("//table[@class='FR_table_borders']//text()")).strip().replace("\n", " ")
        # print(fund)

        researchareas = ''.join([s for s in data if "Research Areas" in s]).strip().replace("\n", "")
        if researchareas != '':
            researchareas = researchareas.split(':')[-1]
        # 这里找到publisher有点困难
        if publisher == '':
            if researchareas:
                researchareas_1 = "\n" + researchareas
                try:
                    publisher = data[data.index(researchareas_1) - 1]
                except:
                    pass
                if 'Publisher ' in publisher:
                    publisher = ' '.join(publisher.split(' ')[1:])
                if "E-mail Addresses:" or "Addresses:" in publisher:
                    publisher = ''
            else:
                publisher = ''

        woscategories = ''.join([s for s in data if "Web of Science Categories" in s]).strip().replace("\n", "")
        if woscategories != '':
            woscategories = woscategories.split(':')[-1]
        lang = ''.join([s for s in data if "Language" in s]).strip().replace("\n", "")
        if lang != '':
            lang = lang.split(':')[-1]
        wosnum = ''.join([s for s in data if "Accession Number:" in s]).strip().replace("\n", "")
        if wosnum != '':
            wosnum = wosnum.split(':')[-1]
        issn = ''.join([s for s in data if "ISSN" in s]).strip().replace("\n", "")
        if 'eISSN' in issn:
            issn = issn.split('eISSN')[0]
        if issn != '':
            issn = issn.split(':')[-1]
        eissn = ''.join([s for s in data if "eISSN" in s]).strip().replace("\n", "")
        if eissn != '':
            eissn = eissn.split(':')[-1]
        idsnum = ''.join([s for s in data if "IDS Number" in s]).strip().replace("\n", "")
        if idsnum != '':
            idsnum = idsnum.split(':')[-1]
        refer = ''.join([s for s in data if "Cited References in Web of Science Core Collection" in s]).strip().replace(
            "\n", "")
        if refer != '':
            refer = refer.split(':')[-1].strip()
        cited = ''.join([s for s in data if "Times Cited in Web of Science Core Collection" in s]).strip().replace("\n",
                                                                                                                   "")
        if cited != '':
            cited = cited.split(':')[-1].strip()

        authorlistkey = author + wosnum

        url = response.url
        end = time.perf_counter()
        print('=' * 30)
        print('其他字段用时：{}'.format(end - start))

        # 所有参考文献：这个爬虫最麻烦的地方，为了速度尽量不用selenium
        # 这里也是这个爬虫最耗时的地方, 因为这里面引用文献下一页有递归思想
        start = time.perf_counter()
        referarticles = []
        authorrefer = []
        journalrefer = []
        others = []
        next = htmlElement.xpath("//a[@class='view-all-link snowplow-view-all-in-cited-references-page-top']/@href")
        if next != []:
            next_url = 'http://apps.webofknowledge.com/' + next[0]
            referarticles, authorrefer, journalrefer, others = Selenium_refer(next_url)
        end = time.perf_counter()
        print('=' * 30)
        print('引用文献全部用时：{}'.format(end - start))

        # l = [self.referarticles, self.authorrefer, self.journalrefer, self.othersrefer]
        # next = htmlElement.xpath("//a[@class='view-all-link snowplow-view-all-in-cited-references-page-top']/@href")
        # q = Queue()
        # thread1 = threading.Thread(target=self.thread_job, args=(l, next, q))
        # thread1.start()
        #
        # self.referarticles, self.authorrefer, self.journalrefer, self.othersrefer = q.get()
        # thread1.join()

        '''
        以下使用json.dumps的都是列表，mysql数据库存入list数据得转str，以后在数据库中要使用这些数据先在python中用eval()去除引号即为list
        '''
        start = time.perf_counter()
        item = WosspiderItem(
            title=title,
            author=author,
            author2=json.dumps(author2),
            reprintauthor=reprintauthor,
            journal=journal,
            volume=volume,
            issue=issue,
            page=page,
            doi=doi,
            pubdate=date,
            documenttype=documenttype,
            publisher=publisher,
            researchdomain=researchdomain,
            abstract=abstract,
            authorkeywords=authorkeywords,
            keywordsplus=keywordsplus,
            reprintaddress=reprintaddress,
            address=json.dumps(address),
            emailaddress=emailaddress,
            fund=json.dumps(fund),
            researchareas=researchareas,
            woscategories=woscategories,
            lang=lang,
            wosnum=wosnum,
            issn=issn,
            eissn=eissn,
            idsnum=idsnum,
            refer=refer,
            cited=cited,
            url=url,
            referarticles=json.dumps(referarticles),
            authorrefer=json.dumps(authorrefer),
            journalrefer=json.dumps(journalrefer),
            othersrefer=json.dumps(others),
            coauthors=json.dumps(coauthors),
            authorlistkey=authorlistkey,
            impact=json.dumps(impact),
            authorid=json.dumps(authorid)
        )
        end = time.perf_counter()
        print('=' * 30)
        print('写入item用时：{}'.format(end - start))
        yield item

        while self.art_list != []:
            art = self.art_list.pop(0)
            next_url, next_response = Selenium_article_url(art)
            if next_url != '':
                yield scrapy.Request(next_url, callback=self.parse)


