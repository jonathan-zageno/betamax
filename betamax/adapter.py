import os
from requests.adapters import BaseAdapter, HTTPAdapter
from betamax.cassette import Cassette
from betamax.exceptions import BetamaxError


class BetamaxAdapter(BaseAdapter):

    """This object is an implementation detail of the library.

    It is not meant to be a public API and is not exported as such.

    """

    def __init__(self, **kwargs):
        super(BetamaxAdapter, self).__init__()
        self.cassette = None
        self.cassette_name = None
        self.http_adapter = HTTPAdapter(**kwargs)
        self.serialize = None
        self.options = {}

    def cassette_exists(self):
        if self.cassette_name and os.path.exists(self.cassette_name):
            return True
        return False

    def close(self):
        self.http_adapter.close()

    def eject_cassette(self):
        if self.cassette:
            self.cassette.eject()
        self.cassette = None  # Allow self.cassette to be garbage-collected

    def load_cassette(self, cassette_name, serialize, options):
        self.cassette_name = cassette_name
        self.serialize = serialize
        self.options.update(options)
        placeholders = self.options.get('placeholders')
        # load cassette into memory
        if self.cassette_exists():
            self.cassette = Cassette(cassette_name, serialize,
                                     placeholders=placeholders)
        elif os.path.exists(os.path.dirname(cassette_name)):
            self.cassette = Cassette(cassette_name, serialize, 'w+',
                                     placeholders=placeholders)
        else:
            raise RuntimeError('No cassette could be loaded.')

    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):
        match_on = self.options['match_requests_on']
        if self.cassette and not self.cassette.is_empty():
            self.cassette.match_options = set(match_on)
            interaction = self.cassette.find_match(request)
            if interaction is None:
                raise BetamaxError('A request was made that could not be'
                                   ' handled')
            response = interaction.as_response()
        else:
            response = self.http_adapter.send(
                request, stream=stream, timeout=timeout, verify=verify,
                cert=cert, proxies=proxies
                )
            self.cassette.save_interaction(response, request)
        return response
