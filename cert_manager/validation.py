# -*- coding: utf-8 -*-
"""Define the cert_manager.validation.Validation class."""

import logging

from ._endpoint import Endpoint
from ._helpers import paginate

LOGGER = logging.getLogger(__name__)

class InvalidValidationMethodError(ValueError):
    pass

class Validation(Endpoint):
    """Query DCV data and start/abort DCV requests"""

    _find_params_to_api = {
        'position': 'position',
        'size': 'size',
        'domain': 'domain',
        'org': 'org_id',
        'department': 'department',
        'dcv_status': 'dcvStatus',
        'order_status': 'orderStatus',
        'expires_in': 'expiresIn'
    }
    _validation_methods = ['cname', 'email', 'http', 'https']

    def __init__(self, client, api_version="v2"):
        super().__init__(client=client, endpoint="/dcv", api_version=api_version)
        self._api_url = self._url("/validation")
        self.__dcv = None

    def status(self, domain):
        result = self._client.post(self._url('status'), data = {'domain':domain})

        return result.json()

    @paginate
    def find(self, **kwargs):
        params = {
            self._find_params_to_api[param]: kwargs.get(param)
            for param in self._find_params_to_api  # pylint:disable=consider-using-dict-items
        }

        result = self._client.get(self._api_url, params=params)

        return result.json()

    def start(self, domain, method):
        if not( method in  self._validation_methods):
            raise InvalidValidationMethodError(method)

        result = self._client.post(self._url(f'start/domain/{method}'), data={'domain':domain})
        return result.json()

    def clear(self, domain):
        result = self._client.post(self._url('clear'), data={'domain':domain})
        return result.json()

    def submit(self, domain, method):
        if not( method in  self._validation_methods):
            raise InvalidValidationMethodError(method)

        result = self._client.post(self._url(f'submit/domain/{method}'), data={'domain':domain})
        return result.json()
