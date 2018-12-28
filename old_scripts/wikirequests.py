import requests

loginurl = "https://wiki.ka-raceing.de/start?do=login"
payload = {
    'u': 'testuser',
    'p': 'dog1412'
}

with requests.Session() as s:
    p = s.post(loginurl, data=payload)

    print(p.text)

    req = s.get('https://wiki.ka-raceing.de/{}?do=backlink'.format(
        ":motor:kupplung:kit17:design_c:simulation_kupplung"))

    print(req.text)