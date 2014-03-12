import threading
import Queue


Empty = Queue.Empty


class Pool(object):
    def __init__(self, num_processes, callback):
        self.num_processes = num_processes
        self.callback = callback
        self.requests = Queue.Queue()
        self.responses = Queue.Queue()
        self.workers = []
        for worker_num in range(num_processes):
            w = threading.Thread(target=_loop,
                                 args=(worker_num, callback, self.requests,
                                       self.responses))
            w.start()
            self.workers.append(w)

    def send(self, msg):
        self.requests.put(msg)

    def get(self, block=True, timeout=None):
        return self.responses.get(block, timeout)

    def close(self):
        for w in self.workers:
            self.requests.put(None)

    def join(self):
        for w in self.workers:
            w.join()


def _loop(worker_num, callback, requests, responses):
    while True:
        args = requests.get(block=True)
        if not args:
            break
        resp = callback(args)
        responses.put(resp)
