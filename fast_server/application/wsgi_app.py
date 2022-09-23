from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import os
import urllib.parse
from wsgiref.handlers import SimpleHandler
from wsgiref.headers import Headers
from platform import python_implementation
import socketserver
# import threading
# from concurrent.futures import ThreadPoolExecutor
from .thread_pool import ThreadPoolExecutor
from .tools import pprint

__version__ = "0.2"
__all__ = ['WSGIServer', 'WSGIRequestHandler', 'ThreadingWSGIServer', 'make_server']


server_version = "WSGIServer/" + __version__
sys_version = python_implementation() + "/" + sys.version.split()[0]
software_version = server_version + ' ' + sys_version


class _Headers(Headers):
    def __bytes__(self):
        try:
            return str(self).encode('iso-8859-1')
        finally:
            return str(self).encode('utf-8')


class ServerHandler(SimpleHandler):

    server_software = software_version

    headers_class = _Headers

    def close(self):
        try:
            self.request_handler.log_request(
                self.status.split(' ', 1)[0], self.bytes_sent
            )
        finally:
            SimpleHandler.close(self)


class WSGIServer(HTTPServer):

    """BaseHTTPServer that implements the Python WSGI protocol"""

    application = None

    def server_bind(self):
        """Override server_bind to store the server name."""
        HTTPServer.server_bind(self)
        self.setup_environ()

    def setup_environ(self):
        # Set up base environment
        env = self.base_environ = {}
        env['SERVER_NAME'] = self.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PORT'] = str(self.server_port)
        env['REMOTE_HOST'] = ''
        env['CONTENT_LENGTH'] = ''
        env['SCRIPT_NAME'] = ''

    def get_app(self):
        return self.application

    def set_app(self, application):
        self.application = application


class _Threads(list):
    """
    Joinable list of all non-daemon threads.
    """
    def append(self, thread):
        self.reap()
        if thread.daemon:
            return
        super().append(thread)

    def pop_all(self):
        self[:], result = [], self[:]
        return result

    def join(self):
        for thread in self.pop_all():
            thread.join()

    def reap(self):
        self[:] = (thread for thread in self if thread.is_alive())


class _NoThreads:
    """
    Degenerate version of _Threads.
    """
    def append(self, thread):
        pass

    def join(self):
        pass


class ThreadingMixIn:
    """Mix-in class to handle each request in a new thread."""

    # Decides how threads will act upon termination of the
    # main process
    daemon_threads = False
    # If true, server_close() waits until all non-daemonic threads terminate.
    block_on_close = True
    # Threads object
    # used by server_close() to wait for all threads completion.
    _threads = _NoThreads()

    threading_pool = ThreadPoolExecutor(1)

    def set_pool(self, max_workers, max_waiters):
        self.threading_pool = ThreadPoolExecutor(max_workers, max_waiters)

    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        # if self.block_on_close:
        #     vars(self).setdefault('_threads', _Threads())
        # t = threading.Thread(target=self.process_request_thread,
        #                      args=(request, client_address))
        # print("创建了线程", self.pool.name)
        # t.daemon = self.daemon_threads
        # self._threads.append(t)
        # t.start()
        self.threading_pool.submit(self.process_request_thread, request, client_address)

    def server_close(self):
        super().server_close()
        self._threads.join()


class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    pass


if hasattr(os, "fork"):
    class ForkingWSGIServer(socketserver.ForkingMixIn, WSGIServer):
        pass


class WSGIRequestHandler(BaseHTTPRequestHandler):

    server_version = "WSGIServer/" + __version__

    def get_environ(self):
        env = self.server.base_environ.copy()
        env['SERVER_PROTOCOL'] = self.request_version
        env['SERVER_SOFTWARE'] = self.server_version
        env['REQUEST_METHOD'] = self.command
        if '?' in self.path:
            path, query = self.path.split('?', 1)
        else:
            path, query = self.path, ''

        env['PATH_INFO'] = urllib.parse.unquote(path, 'iso-8859-1')
        env['QUERY_STRING'] = query

        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]

        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']

        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        for k, v in self.headers.items():
            k = k.replace('-', '_').upper()
            v = v.strip()
            if k in env:
                continue                    # skip content length, type,etc.
            if 'HTTP_'+k in env:
                env['HTTP_'+k] += ','+v     # comma-separate multiple headers
            else:
                env['HTTP_'+k] = v
        return env

    def get_stderr(self):
        return sys.stderr

    def handle(self):
        """Handle a single HTTP request"""
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request():  # An error code has been sent, just exit
            return

        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ(),
            multithread=False,
        )
        handler.request_handler = self      # backpointer for logging
        handler.run(self.server.get_app())


def make_server(
    host, port, app, server_class=WSGIServer, handler_class=WSGIRequestHandler
):
    """Create a new WSGI server listening on `host` and `port` for `app`"""
    server = server_class((host, port), handler_class)
    server.set_app(app)
    return server


def make_multi_server(
        host, port, app, max_workers=1, max_waiters=None, process=False, handler_class=WSGIRequestHandler
):
    """创建多线程或者多进程的环境"""
    if max_workers == 1:
        server = make_server(host, port, app)
    else:
        if process and not hasattr(os, "fork"):
            pprint("Windows environment does not support multi process mode temporarily", color='yellow')
        if process and hasattr(os, "fork"):
            server = ForkingWSGIServer((host, port), handler_class)
        else:
            server = ThreadingWSGIServer((host, port), handler_class)
            if max_waiters == 0:
                max_waiters = None
            server.set_pool(max_workers, max_waiters)
        server.set_app(app)
    return server
