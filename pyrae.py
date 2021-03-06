#!/usr/bin/python3

import ctypes
import urllib.parse
import bs4
import requests

s = requests.Session()


class _Shared:
    PARSER = 'lxml'

    def __init__(self):
        pass

    @staticmethod
    def solve_challenge(c, slt, s1, s2, n, table):
        m = pow(ord(s2) - ord(s1) + 1, n)
        arr = [s1] * n
        chlg = None

        for _i in range(m-1):
            for j in range(n-1, -1, -1):
                arr[j] = chr(ord(arr[j]) + 1)

                if arr[j] <= s2:
                    break

                arr[j] = s1

            chlg = ''.join(arr)
            crc = -1

            for k in chlg + slt:
                index = ((crc ^ ord(k)) & 0x000000FF) * 9
                x = int(table[index:index+8], 16)
                crc = ctypes.c_int32(crc >> 8).value ^ ctypes.c_int32(x).value

            crc = abs(crc ^ -1)

            if crc == c:
                break

        return chlg

    @staticmethod
    def get_payload(r, rf):
        try:
            tmp = r.index('document.forms[0].elements[1].value=\"') + 37
            first = r[tmp:r.index(':', tmp)]

            tmp = r.index('var slt = \"') + 11
            slt = r[tmp:r.index('\"', tmp)]

            tmp = r.index('var c = ') + 8
            c = int(r[tmp:r.index('\r', tmp)])

            tmp = r.index('var s1 = \'') + 10
            s1 = r[tmp:r.index('\'', tmp)]

            tmp = r.index('var s2 = \'') + 10
            s2 = r[tmp:r.index('\'', tmp)]

            tmp = r.index('var n = ') + 8
            n = int(r[tmp:r.index('\n', tmp)])

            tmp = r.index('var table = \"') + 13
            table = r[tmp:r.index('\"', tmp)]
        except ValueError:
            return None

        chlg = _Shared.solve_challenge(c, slt, s1, s2, n, table)

        if chlg is None:
            return None

        cr = ':'.join([first, chlg, slt, str(c)])

        return [['TS017111a7_id', '3'],
                ['TS017111a7_cr', cr],
                ['TS017111a7_76', '0'],
                ['TS017111a7_86', '0'],
                ['TS017111a7_md', '1'],
                ['TS017111a7_rf', rf],
                ['TS017111a7_ct', '0'],
                ['TS017111a7_pd', '0']]

    @staticmethod
    def do_request(request_url, rf):
        r = s.get(request_url)

        if r.status_code != requests.codes.ok:
            return None

        payload = _Shared.get_payload(r.text, rf)

        if payload is None:
            return None

        r = s.post(request_url, data=payload)

        if r.status_code == requests.codes.ok:
            return r


class DLE:
    HOST = 'http://dle.rae.es'
    URL_RANDOM_WORD = HOST + '/srv/random'
    URL_TODAYS_WORD = HOST + '/srv/wotd'
    URL_FETCH = HOST + '/srv/fetch'
    URL_SEARCH = HOST + '/srv/search'

    def __init__(self):
        pass

    @staticmethod
    def _conjugate(name, data, col):
        result = [name]

        for i in data:
            result.append([i[0], i[col]])

        return result

    @staticmethod
    def conjugate_verb(verb):
        verb_id = DLE.search_word(verb)[1]

        return DLE.conjugate_id(verb_id)

    @staticmethod
    def conjugate_id(verb_id):
        payload = {'id': verb_id}
        r = s.get(DLE.URL_FETCH, data=payload)

        if r.status_code != requests.codes.ok:
            return None

        soup = bs4.BeautifulSoup(r.text, _Shared.PARSER)
        cnj = soup.find('table', class_='cnj')

        if cnj is None:
            return None

        data = []
        h = []

        for row in cnj.find_all('tr'):
            cells = [cell.text.strip() for cell in row.find_all('td')]
            data.append([cell for cell in cells if cell is not None])
            heads = [header.text.strip() for header in row.find_all('th')]
            h.append([header for header in heads if header is not None])

        data = [e for e in data if e is not None]

        vc = [h[0][0]]
        vc.append([h[1][0], data[0][0]])
        vc.append([h[1][1], data[0][1]])
        vc.append([h[3][0], data[1][0]])
        vc.append(DLE._conjugate(h[5][0] + ' ' + h[6][3], data[2:10], 1))
        vc.append(DLE._conjugate(h[5][0] + ' ' + h[6][4], data[2:10], 2))
        vc.append(DLE._conjugate(h[5][0] + ' ' + h[15][0], data[10:18], 1))
        vc.append(DLE._conjugate(h[5][0] + ' ' + h[15][1], data[10:18], 2))
        vc.append(DLE._conjugate(h[5][0] + ' ' + h[24][0], data[18:26], 1))
        vc.append(DLE._conjugate(h[33][0] + ' ' + h[34][3], data[26:34], 1))
        vc.append(DLE._conjugate(h[33][0] + ' ' + h[34][4], data[26:34], 2))
        vc.append(DLE._conjugate(h[33][0] + ' ' + h[43][0], data[34:42], 1))
        vc.append(h[52][0])
        vc.append([data[42][0], data[42][1]])
        vc.append([data[43][0], data[43][1]])
        vc.append([data[44][0], data[44][1]])
        vc.append([data[45][0], data[45][1]])

        return vc

    @staticmethod
    def random_word():
        s.cookies.clear()

        r = _Shared.do_request(DLE.URL_RANDOM_WORD, DLE.URL_RANDOM_WORD)

        if r is None:
            return None

        soup = bs4.BeautifulSoup(r.text, _Shared.PARSER)
        article = soup.article

        if article is not None:
            return article.text

    @staticmethod
    def _request_word(word, after_host, m=None):
        url = DLE.HOST + '/?w=' + word
        url2 = DLE.HOST + after_host + word

        if m is not None:
            url += m
            url2 += m

        if _Shared.do_request(url, 'http://www.rae.es/') is None:
            return None

        r = _Shared.do_request(url2, url2)

        if r is None:
            return None

        return bs4.BeautifulSoup(r.text, _Shared.PARSER)

    @staticmethod
    def _options(soup):
        results = []

        for op in soup.find_all('a'):
            results.append([op.text, op.get('href').replace('fetch?id=', '')])

        return results

    @staticmethod
    def search_id(word_id):
        payload = {'id': word_id}
        r = s.get(DLE.URL_FETCH, data=payload)

        if r.status_code != requests.codes.ok:
            return None

        soup = bs4.BeautifulSoup(r.text, _Shared.PARSER)
        article = soup.article

        if article is not None:
            return article.text

    @staticmethod
    def search_word(word, m=None):
        s.cookies.clear()

        soup = DLE._request_word(word, '/srv/search?w=', m)

        if soup is None:
            return None

        f0 = soup.find('div', id_='f0')

        verb_id = None

        if f0 is not None:
            result = f0.span.text
        else:
            article = soup.article
            result = article.text if article is not None else DLE._options(soup)

            if result is None:
                return None

            e2 = soup.find('a', class_='e2')

            if e2 is not None:
                verb_id = e2['href'].replace('fetch?id=', '')

        return result if isinstance(result, list) else [result, verb_id]

    @staticmethod
    def exact(word):
        return DLE.search_word(word, '&m=30')

    @staticmethod
    def starts_with(prefix):
        return DLE.search_word(prefix, '&m=31')

    @staticmethod
    def ends_with(suffix):
        return DLE.search_word(suffix, '&m=32')

    @staticmethod
    def contains(substring):
        return DLE.search_word(substring, '&m=33')

    @staticmethod
    def anagrams(word):
        s.cookies.clear()

        soup = DLE._request_word(word, '/srv/anagram?w=')

        if soup is not None:
            return DLE._options(soup)

    @staticmethod
    def todays_word():
        s.cookies.clear()

        if _Shared.do_request(DLE.HOST + '/?w=', 'http://www.rae.es/') is None:
            return None

        payload = {'': 'diccionario'}
        r = s.get(DLE.URL_SEARCH, data=payload)

        if r.status_code != requests.codes.ok:
            return None

        r = s.get(DLE.URL_TODAYS_WORD)

        if r.status_code != requests.codes.ok:
            return None

        soup = bs4.BeautifulSoup(r.text, _Shared.PARSER)
        word = soup.a
        word_id = word['href'].replace('id=', '')

        return [word.text, word_id]

    @staticmethod
    def get_lemmas():
        letters = 'aábcdeéfghiíjklmnñoópqrstuúvwxyz'

        prefix = letters[0]
        result = []

        while prefix:
            tmp = DLE.starts_with(prefix)
            nxt = True

            if tmp is not None and tmp:
                current = [i[0] for i in tmp if i is not None]

                if len(current) < 200:
                    result.extend(list(set(current) - set(result)))
                else:
                    prefix += letters[0]
                    nxt = False

            if nxt:
                if prefix[-1] == letters[-1]:
                    prefix = prefix[:-1]

                if prefix != letters[-1]:
                    i = letters.find(prefix[-1])
                    prefix = prefix[:-1] + letters[i + 1]

            if prefix == letters[-1]:
                    prefix = ''

        result.sort()

        return result


class DPD:
    URL_SEARCH = 'http://lema.rae.es/dpd/?key='

    def __init__(self):
        pass

    @staticmethod
    def search(word):
        s.cookies.clear()

        w = urllib.parse.quote_plus(word)
        r = _Shared.do_request(DPD.URL_SEARCH + w, DPD.URL_SEARCH + w)

        if r is None:
            return None

        soup = bs4.BeautifulSoup(r.text, _Shared.PARSER)
        article = soup.article

        if article is not None:
            return article.text


class DEJ:
    def __init__(self):
        pass


def main():
    pass

if __name__ == '__main__':
    main()
