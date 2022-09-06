
class Fast:
    def __int__(self, setting: str = None):
        self.container = None
        self.server = None
        self.log = None

        if setting is not None:
            self.__init_setting(setting)
            self.__init_container(setting)

    def start(self):
        pass

    def __init_setting(self, setting):
        pass

    def __init_container(self, setting):
        pass
