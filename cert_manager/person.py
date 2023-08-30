# -*- coding: utf-8 -*-
"""Define the cert_manager.person.Person class."""

import logging

from requests.exceptions import HTTPError

from ._endpoint import Endpoint
from ._helpers import paginate

LOGGER = logging.getLogger(__name__)


class Person(Endpoint):
    """Query the Sectigo Cert Manager REST API for Person data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(
            client=client, endpoint="/person", api_version=api_version
        )

    @paginate
    def list(self, **kwargs):
        """Return a list of people from the Sectigo API."""
        url = self._url("")
        result = self._client.get(url, params=kwargs)
        return result.json()

    def find(self, email) -> int | None:
        """Return person with the given email from the Sectigo API.

        :param str email: The email address for which we are searching
        :return int|None: Id of person if found
        """
        url = self._url(f"/id/byEmail/{email}")
        try:
            result = self._client.get(url)
        except HTTPError as err:
            if err.response.status_code == 404:
                return None
            raise err
        return result.json()["personId"]

    def get(self, person_id: int) -> dict:
        """Return person details

        :param int perso_id: Person ID
        :return dict: dictionary representing a person"""
        url = self._url(f"/{person_id}")
        response = self._client.get(url)
        return response.json()

    def create(
        self,
        firstName,
        email,
        validationType,
        organizationId,
        middleName=None,
        lastName=None,
        phone=None,
        commonName=None,
        secondaryEmails=None,
        eppn=None,
        upn=None,
    ) -> int | None:
        """Create a person through Sectigos API.

        :param str firstName: Person’s first name (not blank, length 1-64)
        :param str middleName: Person’s middle name (0-64)
        :param str lastName: Person’s last name (not blank, length 0-64)
        :param str email: Person’s email (length 0-128)
        :param str validationType: STANDARD or HIGH
        :param int organizationId: Organization or department ID
        :param str phone: phone number, (regex: (#|0-9|\(|\)|\-|\+| x)*, length 0-32)
        :param str commonName: Person commonName (0-64)
        :param list[str] secondaryEmails: Person's Secondary Emails
            :param str eppn: Person EPPN (like email)
        :param str upn: Person UPN (0-256)
        :return int: ID of created person
        """

        url = self._url("")
        response = self._client.post(
            url,
            data={
                "firstName": firstName,
                "email": email,
                "validationType": validationType,
                "organizationId": organizationId,
                "middleName": middleName,
                "lastName": lastName,
                "phone": phone,
                "commonName": commonName,
                "secondaryEmails": secondaryEmails,
                "eppn": eppn,
                "upn": upn,
            },
        )
        try:
            _id = int(
                response.headers.get("Location", "").split("/")[-1]
            )
            return _id
        except Exception as err:
            return None

    def update(
        self,
        person_id,
        firstName=None,
        email=None,
        validationType=None,
        organizationId=None,
        middleName=None,
        lastName=None,
        phone=None,
        commonName=None,
        secondaryEmails=None,
        eppn=None,
        upn=None,
    ) -> bool:
        """update a person through Sectigos API.

        :param int person_id: Person ID
        :param str firstName: Person’s first name (not blank, length 1-64)
        :param str middleName: Person’s middle name (0-64)
        :param str lastName: Person’s last name (not blank, length 0-64)
        :param str email: Person’s email (length 0-128)
        :param str validationType: STANDARD or HIGH
        :param int organizationId: Organization or department ID
        :param str phone: phone number, (regex: (#|0-9|\(|\)|\-|\+| x)*, length 0-32)
        :param str commonName: Person commonName (0-64)
        :param list[str] secondaryEmails: Person's Secondary Emails
            :param str eppn: Person EPPN (like email)
        :param str upn: Person UPN (0-256)
        :return bool: success
        """

        url = self._url(f"/{person_id}")
        result = self._client.put(
            url,
            data={
                "firstName": firstName,
                "email": email,
                "validationType": validationType,
                "organizationId": organizationId,
                "middleName": middleName,
                "lastName": lastName,
                "phone": phone,
                "commonName": commonName,
                "secondaryEmails": secondaryEmails,
                "eppn": eppn,
                "upn": upn,
            },
        )
        return True

    def delete(self, person_id):
        """Delete a person through the Sectigo API.

        :param int person_id: Person ID
        :return bool: success
        """
        url = self._url(f"/{person_id}")
        self._client.delete(url)
        return True
