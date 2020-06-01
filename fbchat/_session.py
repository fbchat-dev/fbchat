import requests
import brotli


class Session(requests.Session):
    def request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
        resp = requests.Session.request(self, method, url, params, data, headers, cookies, files,
                                 auth, timeout, allow_redirects, proxies, hooks, stream, verify,
                                 cert, json)
        return Response(resp)


class Response:
    def __init__(self, base_response):
        self.base_response = base_response

    @property
    def content(self):
        if 'content-encoding' in self.base_response.headers and self.base_response.headers["content-encoding"] == 'br':
            return brotli.decompress(self.base_response.content)
        return self.base_response.content

    def __getattr__(self, attr):
        return getattr(self.base_response, attr)
