# from __future__ import print_function
# from gevent.pywsgi import WSGIServer
#
#
# def application(env, start_response):
#     if env['PATH_INFO'] == '/':
#         start_response('200 OK', [('Content-Type', 'text/html')])
#         return [b"<b>hello world</b>"]
#     elif env['PATH_INFO'] == '/discovery':
#         start_response('200 OK', [('Content-Type', 'application/json')])
#         return [b'{"public-key": "zM4YNmYah0qfjHqG7lt0fk5Z8u5jEKTB_KeHFCgbNgw"}']
#     else:
#         start_response('404 Not Found', [('Content-Type', 'text/html')])
#         return [b'<h1>Not Found</h1>']
#
#
# if __name__ == '__main__':
#     print('Serving on 8088...')
#     WSGIServer(('', 8088), application).serve_forever()
# #
# # def handle(socket, address):
# #     print('new socket ', self.g)
# #
# # pool = Pool(10000) # do not accept more than 10000 connections
# # server = StreamServer(('127.0.0.1', 1234), handle, spawn=pool)
# # server.serve_forever()
