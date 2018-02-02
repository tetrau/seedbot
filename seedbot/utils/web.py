import requests
import lxml.html
import time
import logging

logger = logging.getLogger('seedbot')
logger.addHandler(logging.NullHandler())


class WebPage:
    def __init__(self, headers, cookies, proxies, interval=3):
        self.session = requests.session()
        self.session.headers.update(headers)
        self.session.cookies.update(cookies)
        self.session.proxies.update(proxies)
        self.interval = interval

    def get(self, url):
        logger.debug('GET {}'.format(url))
        time.sleep(self.interval)
        return self.session.get(url).text

    def get_bin(self, url):
        logger.debug('GET {}'.format(url))
        time.sleep(self.interval)
        return self.session.get(url).content

    def lazy_get(self, url):
        if isinstance(url, str):
            return lambda: self.get(url)
        else:
            return lambda: self.get(url())

    def lazy_get_bin(self, url):
        if isinstance(url, str):
            return lambda: self.get_bin(url)
        else:
            return lambda: self.get_bin(url())


class Xpath:
    class XpathResultPlaceholder:
        def __init__(self, html, xpath, index=None):
            self.html = html
            self.xpath = xpath
            self.index = index

        def __getitem__(self, item):
            return self.__class__(self.html, self.xpath, item)

        def __call__(self):
            if callable(self.html):
                html = self.html()
            else:
                html = self.html
            if self.index is None:
                return lxml.html.fromstring(html).xpath(self.xpath)[0]
            else:
                return lxml.html.fromstring(html).xpath(self.xpath)[self.index]

    def xpath(self, html, xpath):
        return lxml.html.fromstring(html).xpath(xpath)

    def lazy_xpath(self, html, xpath):
        return self.XpathResultPlaceholder(html, xpath)
