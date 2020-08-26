import logging
from logging import handlers
from logging.handlers import RotatingFileHandler

from proj_manga import mod_settings
from proj_manga.mod_imports import *
from proj_manga.mod_settings import get_value


# class Logger(object):
#     level_relations = {
#         'debug': logging.DEBUG,
#         'info': logging.INFO,
#         'warning': logging.WARNING,
#         'error': logging.ERROR,
#         'crit': logging.CRITICAL
#     }  # 日志级别关系映射
#
#     def __init__(self, filename, level='info', when='D', backCount=3,
#                  fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
#         self.logger = logging.getLogger(filename)
#         format_str = logging.Formatter(fmt)  # 设置日志格式
#         self.logger.setLevel(self.level_relations.get(level))  # 设置日志级别
#         sh = logging.StreamHandler()  # 往屏幕上输出
#         sh.setFormatter(format_str)  # 设置屏幕上显示的格式
#         th = None
#         if get_value("PrintLog"):
#             th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount,
#                                                    encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
#         if mod_settings.get_value("PrintLog"):
#             th.setFormatter(format_str)  # 设置文件里写入的格式
#             self.logger.addHandler(th)
#         self.logger.addHandler(sh)  # 把对象加到logger里
#
#
def logger_init():
    logdir = get_value("Log_Dir")
    try:
        if not os.path.exists(logdir):
            os.mkdir(logdir)
    except Exception as e:
        print(e)
    # fmt = "%(asctime)s %(levelname)s %(filename)s %(funcName)s [line:%(lineno)d] %(message)s"
    # datafmt = '%Y-%m-%d %H:%M:%S'
    # handler_1 = logging.StreamHandler()
    # curTime = time.strftime("%Y-%m-%d", time.localtime())  # 获取当前日期
    # handler_2 = RotatingFileHandler(logdir + "/Runtime{0}.log".format(curTime), backupCount=20,
    #                                 encoding='utf-8')
    # # 设置rootlogger 的输出内容形式，输出渠道
    # logging.basicConfig(format=fmt, datefmt=datafmt, level=logging.INFO, handlers=[handler_1, handler_2])


def delfile(path):
    try:
        os.remove(path)
        return 0
    except Exception as e:
        return str(e)


def delfolder(path):
    ret = 0
    try:
        os.rmdir(os.path.abspath(path))
    except FileNotFoundError as e:
        ret = e
    except OSError as e:
        for i in os.listdir(os.path.abspath(path)):
            if os.path.isfile("%s/%s" % (os.path.abspath(path), i)):
                os.remove("%s/%s" % (os.path.abspath(path), i))
            else:
                delfolder("%s/%s" % (os.path.abspath(path), i))
    except Exception as e:
        return e
    finally:
        if ret == 0:
            os.rmdir(os.path.abspath(path))
        return ret
