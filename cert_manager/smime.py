# -*- coding: utf-8 -*-
"""Define the cert_manager.certificates.smime.SMIME class."""
import logging

from requests.exceptions import HTTPError

from ._certificates import Certificates
from ._helpers import Pending, Revoked, paginate, version_hack

LOGGER = logging.getLogger(__name__)


class SMIME(Certificates):
    """Query the Sectigo Cert Manager REST API for S/MIME data."""

    def __init__(self, client, api_version="v1"):
        """Initialize the class.

        :param object client: An instantiated cert_manager.Client object
        :param string api_version: The API version to use; the default is "v1"
        """
        super().__init__(client=client, endpoint="/smime", api_version=api_version)

    @paginate
    @version_hack(service="smime", version="v2")
    def list(self, **kwargs):
        """Return a list of all clients certificates from Sectigo.

        The 'size' and 'position' parameters passed as arguments to this function will be used
        by the pagination wrapper to page through results.  All other filtering parameters can be
        referenced at:
        https://sectigo.com/knowledge-base/detail/SCM-Sectigo-Certificate-Manager-REST-API/kA01N000000XDkE

        :param dict kwargs: A dictionary of arguments to pass to the API

        :return iter: An iterator object is returned to cycle through the certificates
        """
        result = self._client.get(self._api_url, params=kwargs)
        return result.json()

    @version_hack(service="smime", version="v2")
    def list_by_email(self, **kwargs):
        """Return a list of all client certificates for a person with given email

        :param str email: Person email
        :return iter: An iterator object is returned to cycle through the certificates
        """
        email = kwargs["email"]

        result = self._client.get(self._url(f"/byPersonEmail/{email}"))
        return result.json()

    def enroll(self, **kwargs):
        """Enroll a client certificate request with Sectigo to generate a certificate.

        :param string cert_type_name: The full cert type name
            Note: the name must match names returned from the get_types() method
        :param string csr: The Certificate Signing Request (CSR)
        :param string email: The person's e-mail
        :param string phone: The person's phone number
        :param list secondary_emails: The person's secondary e-mail(s)
        :param string first_name: The person's first name
        :param string middleName: The person's middle name
        :param string last_name: The person's last name
        :param string common_name: The person's common name.
            If ommited, constructed from person's full name
        :param string eppn: The person's EPPN
        :param string upn: The person's UPN (User Principal Name)
        :param int term: The length, in days, for the certificate to be issued
        :param int org_id: The ID of the organization in which to enroll the certificate
        :param list custom_fields: zero or more objects representing custom fields and their values
            Note: each object must have a 'name' key and a 'value' key
        :param int timeout: request timeout
        :return dict: The orderNumber (Obsolete, backendCertId should be used instead) and backendCertId
        """
        # Retrieve all the arguments
        cert_type_name = kwargs.get("cert_type_name")
        csr = kwargs.get("csr")
        email = kwargs.get("email")
        phone = kwargs.get("phone")
        secondary_emails = kwargs.get("secondary_emails", None)
        first_name = kwargs.get("first_name")
        middle_name = kwargs.get("middle_name")
        last_name = kwargs.get("last_name")
        common_name = kwargs.get("common_name")
        term = kwargs.get("term")
        org_id = kwargs.get("org_id")
        custom_fields = kwargs.get("custom_fields", [])
        eppn = kwargs.get("eppn")
        upn = kwargs.get("upn")

        # Make sure a valid certificate type name was provided
        if cert_type_name not in self.types:
            raise Exception(f"Incorrect certificate type specified: '{cert_type_name}'")

        type_id = self.types[cert_type_name]["id"]
        terms = self.types[cert_type_name]["terms"]

        # Make sure a valid term is specified
        if term not in terms:
            # You have to do the list/map/str thing because join can only operate on
            # a list of strings, and this will be a list of numbers
            trm = ", ".join(list(map(str, terms)))
            raise Exception(
                f"Incorrect term specified: {term}.  Valid terms are {trm}."
            )

        self._validate_custom_fields(custom_fields)

        url = self._url("/enroll")
        data = {
            "orgId": org_id,
            "csr": csr.rstrip(),
            "certType": type_id,
            "term": term,
            "email": email,
            "phone": phone,
            "secondaryEmails": secondary_emails,
            "firstName": first_name,
            "middleName": middle_name,
            "lastName": last_name,
            "commonName": common_name,
            "eppn": eppn,
            "upn": upn,
        }
        if custom_fields:
            data["customFields"] = custom_fields
        timeout = kwargs.pop("timeout", None)
        result = self._client.post(url, data=data, timeout=timeout)

        return result.json()

    def collect(self, cert_id, output_format=None, timeout=None):
        """Retrieve an existing client certificate from the API.

        This method will raise a Pending exception if the certificate is still in a pending state.

        :param int cert_id: The Certificate ID given on enroll success
        :param str output_format: Format for returned certificate
        :return str: the string representing the certificate in the requested format
        """
        if not cert_id:
            raise ValueError("Argument 'cert_id' can't be None")
        url = self._url(f"/collect/{cert_id}")

        params = {}
        if output_format:
            params["format"] = output_format
        try:
            result = self._client.get(url, params=params, timeout=timeout)
        except HTTPError as exc:
            jsondata = exc.response.json()
            err_code = jsondata.get("code")
            if err_code in Revoked.CODE:
                raise Revoked(f"certificate {cert_id} in 'revoked' state") from exc
            if err_code in Pending.CODE:
                raise Pending(
                    f"certificate {cert_id} still in 'pending' state"
                ) from exc
            raise exc

        # The certificate is ready for collection
        return result.content.decode(result.encoding)

    @version_hack(service="smime", version="v2")
    def replace(self, **kwargs):
        """Replace a pre-existing client certificate.

        :param int cert_id: The certificate ID
        :param string csr: The Certificate Signing Request (CSR)
        :param str reason: Reason for replacement (up to 512 characters), can be blank: "", but must exist.
        :param bool revoke: Revoke previous certificate if true. Default is True
        """
        # Retrieve all the arguments
        cert_id = kwargs["cert_id"]
        csr = kwargs["csr"]
        reason = kwargs.get("reason")
        revoke = kwargs.get("revoke", True)

        url = self._url(f"/replace/order/{cert_id}")
        data = {"csr": csr, "reason": reason, "revoke": revoke}
        self._client.post(url, data=data)

    @version_hack(service="smime", version="v2")
    def renew(self, order_num="", serial_num=""):
        """Renew a client certificate with the specified order or serial number.

        :param int order_num: The certificate order number
        :param str serial_num: The certificate serial number
            You can provide either the order or serial number, not both.

        :return dict: A dictionary containing the new order number and cert ID
        """
        if order_num and serial_num:
            raise ValueError("Cannot provide both order number and serial number")

        if order_num:
            url = self._url(f"/renew/order/{order_num}")
        else:
            url = self._url(f"/renew/serial/{serial_num}")
        ret = self._client.post(url)

        return ret.json()

    def revoke(
        self,
        cert_id: int = None,
        serial: str = None,
        reason_code: int = None,
        reason: str = None,
    ):
        """Revoke a client certificate specified by the certificate ID or serial.

        :param int cert_id: The certificate ID
        :param int serial: The certificate serial number
        :param int reason_code: Reason for revocation (0,1,3,4,5)
        :param str reason: The Reason for revocation.
            Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        """
        if not (cert_id or serial):
            raise ValueError("Argument `cert_id` or `serial` must be given")

        if cert_id:
            url = self._url(f"/revoke/order/{cert_id}")
        else:
            url = self._url(f"/revoke/serial/{serial}")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if (not reason) or (len(reason) > 511):
            raise ValueError(
                "Sectigo limit: reason must be > 0 character and < 512 characters"
            )

        if reason_code and not reason_code in (0, 1, 3, 4, 5):
            raise ValueError("reason code must be one of: 0, 1, 3, 4, 5")
        data = {}
        if reason:
            data["reason"] = reason
        if reason_code:
            data["reasonCode"] = reason_code
        return self._client.post(url, data=data)

    def revoke_by_email(self, email, reason=""):
        """Revoke all client certificate related to an email

        :param str email: The person email address
        :param str reason: The Reason for revocation.
            Reason can be up to 512 characters and cannot be blank (i.e. empty string)
        """
        url = self._url("/revoke")

        if not email:
            raise ValueError("Argument 'email' can't be empty or None")

        # Sectigo has a 512 character limit on the "reason" message, so catch that here.
        if (not reason) or (len(reason) > 511):
            raise ValueError(
                "Sectigo limit: reason must be > 0 character and < 512 characters"
            )

        data = {"email": email, "reason": reason}
        self._client.post(url, data=data)
