from getpass import getuser, getpass
import re
import math
import requests
import argparse


def do(args):
    """
    Link up with Kibana, pull index patterns and create individual datasources
    within Grafana for each index pattern.
    """

    # Setup client info
    for_real = args.for_real
    username = args.username
    password = args.password or getpass()
    kibana_auth = (username, password)
    kibana_host = args.kibana
    excludes = args.ignore or []
    excludes = [re.compile(p) for p in excludes]
    es_host = args.elasticsearch
    token = {'Authorization': f'Bearer {args.token}'}
    grafana_host = args.grafana

    print(f'Using exclusion rules: {", ".join(p.pattern for p in excludes)}')

    # Check both paths, determine if 5.x/6.x, check if Grafana API is reachable
    rv_v5 = requests.get(f'{kibana_host}/api/saved_objects', auth=kibana_auth)
    rv_v6 = requests.get(f'{kibana_host}/api/saved_objects/_find', params={'per_page': 1})
    if rv_v5.status_code != requests.codes.ok and rv_v6.status_code != requests.codes.ok:
        raise SystemExit('Error verifying Kibana API')
    kibana_v6 = rv_v5.status_code != requests.codes.ok

    rv = requests.get(f'{grafana_host}/api/datasources', headers=token)
    if rv.status_code != requests.codes.ok:
        raise SystemExit('Error verifying Grafana API')

    def kibana_api(page=1):
        """
        Because Elastic likes to change shit.
        """

        # New way
        if kibana_v6:
            # Because the comma delimited form is not accepted, but doubling the key
            # is, thanks Elastic
            return requests.get(
                f'{kibana_host}/api/saved_objects/_find?fields=title&fields=timeFieldName',
                params={
                    'type': 'index-pattern',
                    'page': page,
                },
                auth=kibana_auth
            )

        # Old way
        return requests.get(
            f'{kibana_host}/api/saved_objects/index-pattern',
            params={'page': page},
            auth=kibana_auth
        )

    # Get all the pages of the Kibana API index-pattern
    total_items = kibana_api().json()['total']
    total_pages = math.ceil(total_items / 20)

    print(f'Found {total_items} patterns, {total_pages} pages')

    index_patterns = []
    for page in range(1, total_pages + 1):
        saved_objects = kibana_api(page=page).json()['saved_objects']

        for o in saved_objects:
            name = o['attributes'].get('title', o['id'])
            timefield = o['attributes'].get('timeFieldName')

            # Skip if kibana
            if '.kibana' in name:
                print(f'Skipping "{o["id"]}", is likely kibana related')
                continue

            # Skip if it matches any exclusion patterns
            if any([p.search(name) for p in excludes]):
                print(f'"{name}" matches one of the exclusion rules, skipping')
                continue

            index_patterns.append([name, timefield])

    # Create source for each pattern
    failed = 0
    for i, item in enumerate(index_patterns, 1):
        pattern, timefield = item
        payload = {
            'access': 'proxy',
            'basicAuth': True,
            'database': pattern,
            'isDefault': False,
            'jsonData': {},
            'basicAuthUser': username,
            'basicAuthPassword': password,
            'user': '',
            'password': '',
            'type': 'elasticsearch',
            'url': es_host,
            'name': f'ES - {pattern}'
        }

        if timefield:
            payload['jsonData']['timeField'] = timefield

        print(f'{i}/{len(index_patterns)} Creating source for "{pattern}"', end='\n' if for_real else '')

        if not for_real:
            print(' (dry run, nothing done)')
            continue

        # This will only create new datasources, not overwrite existing ones
        rv = requests.post(
            f'{grafana_host}/api/datasources',
            headers=token,
            json=payload
        )

        if rv.status_code == requests.codes.ok:
            print(f'Created {pattern}!')
        else:
            failed += 1
            print(f'Failed to created {pattern}, response: status={rv.status_code}, response={rv.content}')

    print(f'Finished, created {len(index_patterns) - failed}, {failed} failed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', help='Grafana Bearer token (already base64\'d)', required=True)
    parser.add_argument('-u', '--username', default=getuser(), help='basic auth username for Kibana')
    parser.add_argument('-p', '--password', help='basic auth password for Kibana')
    parser.add_argument('-e', '--elasticsearch', help='Elasticsearch API', required=True)
    parser.add_argument('-k', '--kibana', help='Kibana host', required=True)
    parser.add_argument('-g', '--grafana', help='Grafana host', required=True)
    parser.add_argument('-i', '--ignore', nargs='*', help='regex(es) to exclude patterns')
    parser.add_argument('--for-real', action='store_true', default=False, help='dry run (do not create datasources)')
    args = parser.parse_args()
    do(args)


if __name__ == '__main__':
    main()
