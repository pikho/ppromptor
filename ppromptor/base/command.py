from abc import abstractmethod


class CommandExecutor:
    @abstractmethod
    def run_cmd(self, **kwargs):
        pass
