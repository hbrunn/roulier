# -*- coding: utf-8 -*-
"""Implement dpdWS."""
import requests
from lxml import objectify, etree
from jinja2 import Environment, PackageLoader
from roulier.transport import Transport
from roulier.ws_tools import remove_empty_tags
from roulier.exception import CarrierError

import logging

log = logging.getLogger(__name__)


class ChronopostTransport(Transport):
    """Implement Dpd WS communication."""

    CHRONOPOST_WS = "https://ws.chronopost.fr/shipping-cxf/ShippingServiceWS"

    def send(self, payload):
        """Call this function.

        Args:
            payload.body: XML in a string
            payload.header : auth
        Return:
            {
                response: (Requests.response)
                body: XML response (without soap)
            }
        """
        soap_message = self.soap_wrap(payload["body"])
        log.debug(soap_message)
        response = self.send_request(soap_message)
        log.info("WS response time %s" % response.elapsed.total_seconds())
        return self.handle_response(response)

    def soap_wrap(self, body):
        """Wrap body in a soap:Enveloppe."""
        env = Environment(
            loader=PackageLoader("roulier", "/carriers/chronopost/templates"),
            extensions=["jinja2.ext.with_"],
        )

        template = env.get_template("chronopost_soap.xml")
        data = template.render(body=body)
        return data.encode("utf8")

    def send_request(self, body):
        """Send body to Chronopost WS."""
        return requests.post(
            self.CHRONOPOST_WS, headers={"content-type": "text/xml"}, data=body
        )

    def handle_500(self, response):
        """Handle reponse in case of ERROR 500 type."""
        log.warning("Chronopost error 500")
        obj = objectify.fromstring(response.content)
        errors = [
            {
                "id": obj.xpath("//faultcode")[0],
                "message": obj.xpath("//faultstring")[0],
            }
        ]
        raise CarrierError(response, errors)

    def handle_200(self, response):
        """Handle response type 200 (success)."""

        def extract_soap(response_xml):
            obj = objectify.fromstring(response_xml)
            return obj.Body.getchildren()[0]

        body = extract_soap(response.content)
        result = body.getchildren()[0]
        if result.errorCode != 0:
            raise CarrierError(response, result.errorMessage)
        body_xml = etree.tostring(body)
        return {"body": body_xml, "response": response}

    def handle_response(self, response):
        """Handle response of webservice."""
        if response.status_code == 200:
            return self.handle_200(response)
        elif response.status_code == 500:
            return self.handle_500(response)
        else:
            raise CarrierError(
                response,
                [
                    {
                        "id": None,
                        "message": "Unexpected status code from server",
                    }
                ],
            )
