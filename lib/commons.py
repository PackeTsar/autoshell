#!/usr/bin/python

import time
import queue
import Queue
import logging
import threading


class autoqueue:
    def __init__(self, thread_count, worker_func, worker_args):
        self.log = logging.getLogger("modules")
        self.queue = queue.Queue(maxsize=0)
        self.thread_count = thread_count
        self.worker_func = worker_func
        self.worker_args = worker_args
        self.auto_threads = []
        self._start_threads()

    def _start_threads(self):
        self.log.debug("commons.autoqueue._start_threads:\
 Starting %s threads" % str(self.thread_count))
        for i in range(0, self.thread_count):
            auto_thread = autothread(self.worker_func,
                                     self.worker_args,
                                     self.queue)
            self.auto_threads.append(auto_thread)

    def put(self, item):
        self.queue.put(item)

    def get(self, item):
        self.queue.get(item)

    def kill_all(self):
        for athread in self.auto_threads:
            athread.terminate = True

            self.log.warning("autoqueue.block:\
 Threads being shut down. Press CTRL-C to force unblock")
            try:
                somelive = True
                while somelive:
                    somelive = False
                    for athread in self.auto_threads:
                        if athread.thread.isAlive():
                            somelive = True
            except KeyboardInterrupt:
                self.log.warning("autoqueue.block:\
 Forcing unblock")
                return None

    def block(self, kill=True):
        self.log.debug("autoqueue.block:\
 Blocking until queue emptied and threads idle")
        busy = True
        try:
            while busy:
                if self.queue.empty():
                    busy = False
                    for athread in self.auto_threads:
                        if not athread.idle:
                            busy = True
            if kill:
                self.log.info("autoqueue.block:\
 Blocking complete. Killing threads...")
                self.kill_all()
            else:
                self.log.info("autoqueue.block:\
 Blocking complete. Continuing")
        except KeyboardInterrupt:
            if kill:
                self.log.warning("autoqueue.block:\
 Interrupted. Killing threads...")
                self.kill_all()
            else:
                self.log.info("autoqueue.block:\
 Blocking complete. Continuing")


class autothread:
    def __init__(self, worker_func, worker_args, worker_queue):
        self.log = logging.getLogger("modules")
        self.idle = False
        self.alive = True
        self.terminate = False
        self.worker_func = worker_func
        self.worker_args = worker_args
        self.queue = worker_queue
        self.thread = threading.Thread(target=self._supervisor)
        self.thread.daemon = True
        self.thread.start()

    def _supervisor(self):
        while not self.terminate:
            self.idle = True
            try:
                item = self.queue.get_nowait()
                self.idle = False
                try:
                    self.worker_func(self, item)
                except Exception as e:
                    self.log.exception('Exception raised in %s:' %
                                       threading.current_thread().name)
                self.idle = True
            except Queue.Empty:
                time.sleep(0.1)
        self.log.debug('Thread terminating')
        self.idle = True
        self.alive = False
