import threading
import multiprocessing

from proj_manga import mod_email
from proj_manga.mod_imports import *
from proj_manga.mod_pic2pdf import folder2pdf, Downpic, mergefiles, GetPic_Base64
from proj_manga.mod_settings import get_value, set_value
from proj_manga.mod_mysql import SetLogStatus, GetUser, GetUsername


ua = UserAgent()
errorlist = list()

class thread_download(threading.Thread):
    def __init__(self, ua, referer, oripath, targetpath, logmini, logid):
        threading.Thread.__init__(self)
        self.ua = ua
        self.referer = referer
        self.oripath = oripath
        self.targetpath = targetpath
        self.logmini = logmini
        self.logid = logid

    def run(self):
        Downpic(self.ua, self.referer, self.oripath, self.targetpath, self.logmini, self.logid)


class thread_watch(threading.Thread):
    def __init__(self, title, chapter, url, ext, logmini, logid):
        threading.Thread.__init__(self)
        self.title = title
        self.chapter = chapter
        self.url = url
        self.ext = ext
        self.logmini = logmini
        self.logid = logid

    def run(self):
        Watch_dmzj(self.title, self.chapter, self.url, self.ext, self.logmini, self.logid)


log_lock = threading.Lock()


class html_logclass():
    def __init__(self, filename):
        self.logpath = filename

    def info(self, message):
        log_lock.acquire()
        datetime = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
        level = 'INFO'
        printdata = "<div id='log'>[%s] %s %s</div>" % (level, datetime, message)
        with open(self.logpath, 'a') as file_obj:
            file_obj.write(printdata)
        log_lock.release()

    def warning(self, message):
        log_lock.acquire()
        datetime = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
        level = 'WARN'
        printdata = "<div id='log'>[%s] %s %s</div>" % (level, datetime, message)
        with open(self.logpath, 'a') as file_obj:
            file_obj.write(printdata)
        log_lock.release()

    def critical(self, message):
        log_lock.acquire()
        datetime = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
        level = 'CRITICAL'
        printdata = "<div id='log'>[%s] %s %s</div>" % (level, datetime, message)
        with open(self.logpath, 'a') as file_obj:
            file_obj.write(printdata)
        log_lock.release()

    def error(self, message):
        log_lock.acquire()
        datetime = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))
        level = 'ERROR'
        printdata = "<div id='log'>[%s] %s %s</div>" % (level, datetime, message)
        with open(self.logpath, 'a') as file_obj:
            file_obj.write(printdata)
        log_lock.release()


def Search_dmzj(text, page):
    try:
        output = ""
        url = "https://manhua.dmzj.com/tags/search.shtml?" + "s=" + text + "&p=" + page
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(30)
        driver.get(url)
        time.sleep(1)
        html = driver.execute_script('return document.documentElement.outerHTML')
        driver.close()  # 记得关闭，否则占用内存资源
        soup = BeautifulSoup(html, "html.parser")
        category = soup.find("div", class_="tcaricature_new").find("div", class_="tcaricature_block tcaricature_block2")
        list = category.find_all("ul")
        for item in list:
            subitem = item.find_all("li")
            title = subitem[0]
            detail = subitem[1]
            output += "<tr>"
            referer = "https:%s" % title.find("a").__getitem__("href")
            picdata = GetPic_Base64(referer, title.find("img").__getitem__("src"))
            output += "<td><img class=\"r_image\" src=\"%s\"/></td>" % picdata
            output += "<td>%s</td>" % (title.find("a").getText())
            author = detail.find_all("div")[0].getText()
            latest = detail.find_all("div")[1].getText()
            output += "<td>%s</td>" % author
            output += "<td>%s</td>" % latest
            output += "<td style=\"width:50px\"><a href='%s'>%s</td></tr>" % (referer, referer)
        page = str(page)
        next_page = str(int(page) + 1)
        search = text
        table = output
        return {'search': search, 'page': page, 'next_page': next_page, 'table': table}
    except Exception as e:
        return -1


def Analyze_dmzj(url, ext, downloadlist, downloadall, logid, sendmail, merge, token):
    while get_value("Task_Running") == True:
        time.sleep(1)
    set_value("Task_Running", True, local=True)
    SetLogStatus(logid, "running")
    max_threads = multiprocessing.cpu_count()
    logmini = html_logclass(get_value("Log_Dir") + logid + ".log")
    try:
        tempdir = get_value("Temp_Dir")
        outdir = get_value("Output_Dir")
        logmini.info("正在下载地址" + url)
        headers = {"User-Agent": ua.random}
        logmini.info("尝试获取网页数据")
        response = requests.get(url=url, headers=headers, timeout=20)
        if response.status_code != 200:
            logmini.error("您输入的URL地址不合法！")
            logmini.error("响应状态" + str(response.status_code))
            SetLogStatus(logid, "failed")
            return
        html = response.text
        response.close()
        rooturl = url.split('/')[2]
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("span", class_="anim_title_text")
        logmini.info("作品名称：" + title.getText())
        category = soup.find_all("div", class_="cartoon_online_border")
        id = 0
        threads = []
        for subcategory in category:
            id += 1
            logmini.info("第" + str(id) + "页")
            list = subcategory.find_all("li")
            sid = 0
            for item in list:
                sid += 1
                logmini.info("Sid:" + str(sid) + "  " + item.find("a").getText())
                referlink = "https://" + rooturl + item.a['href']
                logmini.info("链接：" + referlink)
                if (sid in downloadlist) or (downloadall):
                    # 此处的多线程决定废弃
                    # n_thread = thread_watch(title.getText(), item.find("a").getText(), referlink, ext, logmini, logid)
                    # while True:
                    #     if (len(threading.enumerate()) < int(max_threads / 2)):
                    #         #这里除以2的原因是为了保证下载能够正常运行，避免死锁
                    #         break
                    # n_thread.start()
                    # threads.append(n_thread)
                    Watch_dmzj(title.getText(), item.find("a").getText(), referlink, ext, logmini, logid)
        # for t in threads:
        #     t.join()
        if merge == True:
            logmini.info("自动合并被设置为开，正在合并文件（注意：合并后单独文件将会被删除）。")
            path = get_value("Output_Dir") + logid + "/"
            if not downloadall:
                result = mergefiles(path,
                                    title.getText() + "_第%s到第%s话.pdf" % (str(downloadlist[0]), str(downloadlist[-1])),
                                    logmini)
            else:
                result = mergefiles(path, title.getText() + "_全部下载.pdf", logmini)
            if result == 0:
                logmini.info("合并成功。")
            else:
                logmini.info("合并失败。")
                SetLogStatus(logid, "failed")
                raise Exception
        if sendmail == True:
            logmini.info("自动发送kindle被设置为开，正在发送信件。")
            user = GetUser(GetUsername(token))
            s_host = user['s_host']
            s_port = user['s_port']
            s_pass = user['s_pass']
            s_email = user['email']
            kindle_email = user['kindle_email']
            valid = (s_host != "") and (s_port != "") and (s_pass != "") and (s_email != "") and (
                    kindle_email != "")
            try:
                if not valid:
                    raise Exception
                path = get_value("Output_Dir") + logid
                filelist = os.listdir(path)
                from proj_manga.mod_email import SendEmail_File
                for file in filelist:
                    logmini.info("正在发送文件 %s" % file)
                    path = os.path.join(os.getcwd(), get_value("Output_Dir")) + logid + "/" + file
                    mail_result = SendEmail_File(s_email, kindle_email, s_host, s_port, s_pass, path, file)
                    if mail_result == 0:
                        logmini.info("发送文件 %s 成功" % file)
                    else:
                        logmini.error("发送文件 %s 失败" % file)
            except Exception as e:
                logmini.error("发送文件失败")
        logmini.info("任务完成。")
        SetLogStatus(logid, "complete")
    except Exception as e:
        logmini.error("任务失败。%s" % e)
        SetLogStatus(logid, "failed")
    finally:
        set_value("Task_Running", False, local=True)


def Watch_dmzj(title, chapter, url, ext, logmini, logid):
    try:
        max_threads = multiprocessing.cpu_count()
        tempdir = get_value("Temp_Dir")
        outdir = get_value("Output_Dir")
        folderpath = ""
        oriurl = url
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        logmini.info("尝试获取网页数据,这可能需要较长的时间")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        html = driver.execute_script('return document.documentElement.outerHTML')
        soup = BeautifulSoup(html, "html.parser")
        urls = soup.find_all("option")
        page = 0
        driver.close()  # 记得关闭，否则占用内存资源
        threads = []
        for url in urls:
            page += 1
            logmini.info(url.getText())
            imgurl = "https:" + url.__getitem__('value')
            logmini.info(imgurl)
            folderpath = title + "_" + chapter
            try:
                if not os.path.exists(tempdir):
                    os.mkdir(tempdir)
                if not os.path.exists(outdir):
                    os.mkdir(outdir)
                if not os.path.exists(tempdir + folderpath):
                    os.mkdir(tempdir + folderpath)
            except Exception as e:
                logmini.warning(e)
            filepath = str(page).zfill(3)
            # 此处多线程决定废弃
            # newthread = thread_download(ua.random, oriurl, imgurl, tempdir + folderpath + "/" + filepath, logmini, logid)
            # while True:
            #     if (len(threading.enumerate()) < max_threads):
            #         break
            # threads.append(newthread)
            # newthread.start()
            Downpic(ua.random, oriurl, imgurl, tempdir + folderpath + "/" + filepath, logmini, logid)
        if ext == "pdf":
            folder2pdf(folderpath, logmini, logid)
    except Exception as e:
        logmini.error("%s_%s 下载失败:%s" % (title, chapter, e))
        SetLogStatus(logid, "uncompleted")
        driver.close()
    # for t in threads:
    #     t.join()


def printerrorlist():
    if len(errorlist) == 0:
        return 0
    logdir = get_value("Log_Dir")
    file = open(logdir + "ErrorList " + time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time())) + ".txt", "w+")
    for item in errorlist:
        print(item, file=file)
    file.close()
    return 0
