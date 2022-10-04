import threading
import datetime
import sched
import time
from .setting import Setting


INFO_LOG = 'info'
WARN_LOG = 'warn'
ERROR_LOG = 'error'
SPLIT_LINE = "==============================>"
TYPE_MAP = {INFO_LOG: 'info', WARN_LOG: 'warning', ERROR_LOG: 'error'}


class Cache:
    interval = 1

    def _start(self):
        threading.Thread(target=self._loop_monitor).start()

    def _task(self):
        pass

    def _loop_monitor(self):
        scheduler = sched.scheduler(time.time, time.sleep)  # 生成调度器
        while True:
            scheduler.enter(self.interval, 1, self._task, ())
            scheduler.run()
            if not threading.main_thread().is_alive():
                break


class Log(Cache):
    __instance = None
    __init_flag = False
    __init_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__init_lock:
                cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self, setting: Setting = None):
        if Log.__init_flag:
            return
        Log.__init_flag = True
        self._storage = setting.log_path
        self.max_len = setting.log_max
        self._log_list = []
        self.__alt_lock = threading.RLock()

        with open(self._storage, mode='w', encoding='utf-8') as file_obj:
            pass

        self._start()

    def log(self, info, _type=INFO_LOG):
        now = datetime.datetime.now()
        t = now.strftime("%Y-%m-%d %H:%M:%S")
        tt = "\n" + SPLIT_LINE + "\n"
        log_info = tt + t + "  " + TYPE_MAP.get(_type, TYPE_MAP[INFO_LOG]) + "\n" + info + tt
        with self.__alt_lock:
            self._log_list.append(log_info)

    def ilog(self, info):
        self.log(info, INFO_LOG)

    def elog(self, info):
        self.log(info, ERROR_LOG)

    def wlog(self, info):
        self.log(info, WARN_LOG)

    def _task(self):
        if len(self) > self.max_len:
            with self.__alt_lock:
                len_ = len(self) - self.max_len
                self.storage("".join(self._log_list[:len_]))
                self._log_list = self._log_list[len_:]
        if not threading.main_thread().is_alive():
            self.storage("".join(self))

    def storage(self, data):
        try:
            # 尝试打开日志文件
            with open(self._storage, mode='a', encoding='utf-8') as file_obj:
                file_obj.write(data + "\n")
        except FileExistsError:
            # 打开失败，文件已损坏或丢失，则创建一个新的文件，在将数据写进去
            with open(self._storage, mode='w', encoding='utf-8') as file_obj:
                pass

    def __iter__(self):
        for i in self._log_list:
            yield i

    def __len__(self):
        return len(self._log_list)

