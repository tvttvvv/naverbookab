Starting Container
[2026-02-16 03:27:27 +0000] [1] [INFO] Starting gunicorn 25.1.0
[2026-02-16 03:27:27 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2026-02-16 03:27:27 +0000] [1] [INFO] Using worker: sync
[2026-02-16 03:27:27 +0000] [1] [INFO] Control socket listening at /app/gunicorn.ctl
[2026-02-16 03:27:28 +0000] [3] [INFO] Booting worker with pid: 3
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/sync.py", line 142, in handle
    self.handle_request(listener, req, client, addr)
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/sync.py", line 185, in handle_request
    respiter = self.wsgi(environ, resp.start_response)
[2026-02-16 03:28:39 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:3)
[2026-02-16 03:28:39 +0000] [3] [ERROR] Error handling request /search
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 1536, in __call__
    return self.wsgi_app(environ, start_response)
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 1511, in wsgi_app
    response = self.full_dispatch_request()
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
  File "/app/app.py", line 44, in search
    response = requests.get(url, headers=headers, params=params, timeout=5)
  File "/usr/local/lib/python3.10/dist-packages/requests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/adapters.py", line 644, in send
    resp = conn.urlopen(
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connectionpool.py", line 787, in urlopen
    response = self._make_request(
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
  File "/usr/lib/python3.10/http/client.py", line 1395, in getresponse
    response.begin()
  File "/usr/lib/python3.10/http/client.py", line 323, in begin
    version, status, reason = self._read_status()
  File "/usr/lib/python3.10/http/client.py", line 284, in _read_status
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
  File "/usr/lib/python3.10/socket.py", line 705, in readinto
    return self._sock.recv_into(b)
  File "/usr/lib/python3.10/ssl.py", line 1303, in recv_into
    return self.read(nbytes, buffer)
  File "/usr/lib/python3.10/ssl.py", line 1159, in read
    return self._sslobj.read(len, buffer)
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/base.py", line 198, in handle_abort
    sys.exit(1)
SystemExit: 1
[2026-02-16 03:28:39 +0000] [3] [INFO] Worker exiting (pid: 3)
[2026-02-16 03:28:39 +0000] [4] [INFO] Booting worker with pid: 4
    response = self.full_dispatch_request()
    respiter = self.wsgi(environ, resp.start_response)
[2026-02-16 03:29:21 +0000] [1] [CRITICAL] WORKER TIMEOUT (pid:4)
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 1536, in __call__
[2026-02-16 03:29:21 +0000] [4] [ERROR] Error handling request /search
    return self.wsgi_app(environ, start_response)
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 1511, in wsgi_app
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/sync.py", line 142, in handle
    self.handle_request(listener, req, client, addr)
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/sync.py", line 185, in handle_request
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 917, in full_dispatch_request
    rv = self.dispatch_request()
  File "/usr/local/lib/python3.10/dist-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
  File "/app/app.py", line 44, in search
    response = requests.get(url, headers=headers, params=params, timeout=5)
  File "/usr/local/lib/python3.10/dist-packages/requests/api.py", line 73, in get
    return request("get", url, params=params, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/api.py", line 59, in request
    return session.request(method=method, url=url, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/sessions.py", line 589, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/sessions.py", line 703, in send
    r = adapter.send(request, **kwargs)
  File "/usr/local/lib/python3.10/dist-packages/requests/adapters.py", line 644, in send
    resp = conn.urlopen(
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connectionpool.py", line 787, in urlopen
    response = self._make_request(
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connectionpool.py", line 534, in _make_request
    response = conn.getresponse()
  File "/usr/local/lib/python3.10/dist-packages/urllib3/connection.py", line 571, in getresponse
    httplib_response = super().getresponse()
  File "/usr/lib/python3.10/http/client.py", line 1395, in getresponse
    response.begin()
  File "/usr/lib/python3.10/http/client.py", line 323, in begin
    version, status, reason = self._read_status()
  File "/usr/lib/python3.10/http/client.py", line 284, in _read_status
[2026-02-16 03:29:21 +0000] [4] [INFO] Worker exiting (pid: 4)
[2026-02-16 03:29:21 +0000] [5] [INFO] Booting worker with pid: 5
    return self._sock.recv_into(b)
  File "/usr/lib/python3.10/ssl.py", line 1303, in recv_into
    return self.read(nbytes, buffer)
  File "/usr/lib/python3.10/ssl.py", line 1159, in read
    return self._sslobj.read(len, buffer)
  File "/usr/local/lib/python3.10/dist-packages/gunicorn/workers/base.py", line 198, in handle_abort
    sys.exit(1)
SystemExit: 1
    line = str(self.fp.readline(_MAXLINE + 1), "iso-8859-1")
  File "/usr/lib/python3.10/socket.py", line 705, in readinto
