import json
import os


def load_fixture(resource):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    fixture_filename = '{0}.json'.format(resource)
    fixture_path = os.path.join(fixtures_path, fixture_filename)
    return json.load(open(fixture_path))
