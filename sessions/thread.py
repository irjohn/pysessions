import asyncio
import threading
from time import sleep

# The `AsyncLoopThread` class is a subclass of `threading.Thread` that runs an asynchronous event loop until it
# is stopped.
class AsyncLoopThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = threading.Event()


    def run(self):
        self._loop = self._target()
        asyncio.set_event_loop(self._loop)
        self._stop_task = self._loop.create_task(self.check_stop())
        if not self._loop.is_running():
            self._loop.run_forever()
        return


    async def check_stop(self):
        while not self.stopped:
            await asyncio.sleep(0)
        self.shutdown()

    def shutdown(self):
        tasks = asyncio.all_tasks(loop=self._loop)
        for task in tasks:
            task.cancel()
        self._loop.stop()

    def stop(self):
        self._stop_event.set()
        while self._loop.is_running():
            sleep(0.01)

    @property
    def stopped(self):
        return self._stop_event.is_set()