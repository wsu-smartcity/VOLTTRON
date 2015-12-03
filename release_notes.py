import argparse
from getpass import getpass
import json
import os
import requests
import sys
from pprint import pprint

requests.packages.urllib3.disable_warnings()
#AUTH_URI = 'https://api.github.com/user'
BASE_URI = "https://api.github.com/repos/VOLTTRON/volttron"


#auth = requests.get(AUTH_URI, auth=AUTH_TUPLE)

def main(user, password, base_uri=BASE_URI):
    ISSUES = base_uri+"/issues"
    RELEASE = base_uri+"/releases/latest"
    SINCE = ISSUES + "?since={}"
    AUTH_TUPLE = (user, password)

    r = requests.get(RELEASE, auth=AUTH_TUPLE, verify=False)

    latest_release = r.json()

    print('Retrieving data since: {} ...'.format(latest_release['published_at']))
    r = requests.get(SINCE.format(latest_release['published_at']),
                     auth=AUTH_TUPLE, verify=False)

    print('Parsing issues ...')
    for issue in r.json():
        req = requests.get(issue['comments_url'], auth=AUTH_TUPLE, verify=False)
        for comment in req.json():
            if '$$RELEASE_NOTE' in comment['body']:
                pprint(comment)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]), add_help=True,
        description='VOLTTRON release notes generator',
        usage='%(prog)s [OPTION]...',
        argument_default=argparse.SUPPRESS
    )

    parser.add_argument('username',
                        help='Github acccount to use for the api.')

    vals = parser.parse_args()

    passkey = getpass('Github password/key: ', sys.stdout)
    main(user=vals.username, password=passkey)
