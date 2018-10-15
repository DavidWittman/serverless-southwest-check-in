import json
import os


def load_fixture(resource):
    """
    Load a fixture file from the fixtures path

    This function is a little surprising in that it automatically appends `.json` and tries
    to parse the result if possible. Otherwise it just loads the resource specified.
    """
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    fixture_filename = '{0}.json'.format(resource)
    fixture_path = os.path.join(fixtures_path, fixture_filename)

    try:
        fh = open(fixture_path, 'r')
        data = json.load(fh)
    except Exception:
        fh = open(os.path.join(fixtures_path, resource))
        data = fh.read()
    finally:
        fh.close()

    return data
