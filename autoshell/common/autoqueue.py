#!/usr/bin/python

"""
The common.autoqueue library contains classes and functions used for creating
thread pools and queues with automatic supervision, blocking, graceful
termination, and user interruption of activity.
"""


import time
import logging
import threading
from builtins import input

try:
    import Queue as queue  # For Python2
except ImportError:
    import queue  # For Python3.5-
except ModuleNotFoundError:
    import queue  # For Python3.6+


# log (shared) is used for shared logging of autoshell core components
log = logging.getLogger("shared")


class autoqueue:
    """
    common.autoqueue is a wrapper for the queue library; adding in a
    thread-pool functionaliy (using the autothread class). It provides
    functionality to track all the running threads and block the main thread
    until workers are finished and the queue is empty. It also includes
    options to user-interrupt thread activity; gracefully killing the threads
    upon interruption.
    """
    def __init__(self, thread_count, worker_func, worker_args):
        self._thread_count = thread_count
        self._worker_func = worker_func  # Worker function passed in
        self._worker_args = worker_args  # Args for worker function
        self._queue = queue.Queue(maxsize=0)  # Underlying queue
        self._auto_threads = []  # List of thread instances
        self._start_threads()

    def _start_threads(self):
        """
        common.autoqueue._start_threads starts a set of autothreads using
        the worker function and args handed to autoqueue. The autothreads
        will remain idle until items are added to the queue.
        """
        log.debug("common.autoqueue._start_threads:\
 Starting %s threads" % str(self._thread_count))
        for i in range(0, self._thread_count):
            auto_thread = autothread(self._worker_func,
                                     self._worker_args,
                                     self._queue)
            self._auto_threads.append(auto_thread)

    def put(self, item):
        # Mimic feel of a Queue instance
        self._queue.put(item)

    def get(self, item):
        # Mimic feel of a Queue instance
        self._queue.get(item)

    def _kill_all(self):
        """
        common.autoqueue._kill_all is used to gracefully terminate all
        running autothreads before returning control of the calling thread.
        It allows a interruption of the process to force the unblocking of
        the calling thread.
        """
        for athread in self._auto_threads:
            # Tell all supervisors to terminate their thread
            athread.terminate = True  # Set terminate flag
        log.info("common.autoqueue._kill_all:\
 Threads being shut down. Press CTRL-C to force unblock")
        # Loop through checking queue and threads before unblock
        try:
            still_running = True  # Threads are still running
            while still_running:
                # Initially set to false
                still_running = False
                for athread in self._auto_threads:
                    if athread.alive:
                        # Trip to true if a running thread is found
                        still_running = True
        # CTRL-C was pressed to force unblocking of main thread
        except KeyboardInterrupt:
            log.warning("common.autoqueue._kill_all:\
 Forcing unblock")
            return None
        # Proper graceful shutdown occured. Unblocking main thread
        log.debug("common.autoqueue._kill_all:\
 All threads shut down gracefully. Continuing ")

    def block(self, kill=True):
        """
        common.autoqueue.block is called externally and is used to block the
        calling thread until all the queue is empty and all threads are idle.
        """
        log.debug("common.autoqueue.block:\
 Blocking until queue emptied and threads idle")
        busy = True  # Initially set to true to start blocking
        try:
            while busy:
                if self._queue.empty():
                    busy = False  # Initially set to False
                    for athread in self._auto_threads:
                        if not athread.idle:
                            # Trip to True if a thread is still working
                            busy = True
            # If we are to kill the threads instead of leaving them running
            if kill:
                log.debug("common.autoqueue.block:\
 Blocking complete. Killing threads...")
                self._kill_all()
            else:
                log.debug("common.autoqueue.block:\
 Blocking complete. Leaving threads running...")
        except KeyboardInterrupt:
            log.debug("common.autoqueue.block:\
 User-Interrupt Detected: Clearing Block.")
            for athread in self._auto_threads:
                log.debug("common.autoqueue.block:\
 Thread (%s) Idle: %s" % (athread.thread.name, athread.idle))
            if kill:
                log.warning("common.autoqueue.block:\
 Killing threads...")
                self._kill_all()
            else:
                log.debug("common.autoqueue.block:\
 Not killing threads. Continuing...")


class autothread:
    """
    common.autothread is a wrapper class for the threading library. It adds
    in functionality of supervising running tasks, feeding tasks items
    from a queue, and terminating the thread when instructed. common.autothread
    is used by the common.autoqueue class for threading
    """
    def __init__(self, worker_func, worker_args, worker_queue):
        self.idle = False
        self.alive = True
        self.terminate = False
        self._worker_func = worker_func  # Worker function passed in
        if not worker_args:
            self._worker_args = ()  # Args for worker function
        else:
            self._worker_args = worker_args  # Args for worker function
        self._queue = worker_queue  # Queue containing items for worker
        self.thread = threading.Thread(target=self._supervisor)
        self.thread.daemon = True
        self.thread.start()

    def _supervisor(self):
        """
        common.autothread._supervisor is a supervisory function which feeds a
        worker function items from a managed queue. It detects and exceptions
        thrown by the worker function and logs them. It also allows for
        graceful termination by the caller.
        """
        while not self.terminate:
            self.idle = True  # Assume we are idle, trip if not
            try:
                # Will throw a Queue.Empty exception if queue is empty
                item = self._queue.get_nowait()
                # If no exception, then we are not idle
                self.idle = False
                # Protect supervisor from exception
                try:
                    self._worker_func(self, item, *self._worker_args)
                except Exception as e:
                    # Log exception to logging facility
                    log.exception('common.autoqueue.autothread._supervisor:\
 Exception raised in %s:' % threading.current_thread().name)
                # Give a second before setting idle in case _worker_func
                #  put something back in the queue and we need to
                #  detect it in autoqueue.block
                time.sleep(1)
                # Now we are idle again
                self.idle = True
            except queue.Empty:
                # Kill time to keep CPU from going to 100%
                time.sleep(1)
        # self.terminate was marked true. Shut down gracefully now
        log.debug('common.autoqueue.autothread._supervisor:\
 Thread terminating')
        self.idle = True
        self.alive = False
