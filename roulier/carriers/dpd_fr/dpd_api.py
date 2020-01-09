# -*- coding: utf-8 -*-
"""Implementation of Dpd Fr Api."""
from roulier.api import Api

DPD_LABEL_FORMAT = (
    'PDF',
    'ZPL',
)

DPD_PRODUCTS = {
    'DPD CLASSIC': 1,
    'DPD CLASSIC INTERCONTINENTAL': 40033,
    'DPD PREDICT': 40275,
    'DPD RELAIS': 40276,
    'DPD RETOUR': 40278,
    # 'DPD Retour en Relais',  # Not implemented yet
}

class DpdApi(Api):
    def _service(self):
        schema = super(DpdApi, self)._service()
        schema['labelFormat'].update({
            'allowed': DPD_LABEL_FORMAT,
            'default': 'ZPL',
            'required': True, 'empty': False})
        schema['agencyId'].update({
            'required': True, 'empty': False,
            # 'description': 'Agency code int(3)'
            })
        # departureUnitId 
        schema['customerCountry'] = {
            'required': True, 'empty': False,
            'default': '',
            'type': 'string',
            # 'description': 'Customer country code (France = FR) int(2)'
            # senderCountryCode
            }
        schema['customerId'].update({
            'required': True, 'empty': False,
            'type': 'integer',
            'coerce': int,
            'default': 0,
            # 'description': 'Customer number int(6)'
            }) #payerId
        schema['customerAddressId'] = {
            'required': True, 'empty': False,
            'default': 0,
            'type': 'integer',
            'coerce': int,
            # 'description': payerAddressId
        }
        schema['senderId'] = {
            'default': 0,
            'empty': False,
            'required': True,
            'coerce': int,
            'type': 'integer',
        }

        schema['senderZipCode'] = {
            'default': '',
            'empty': False,
            'required': True,
        }
        schema['senderAddressId'] = { 
            'default': 0, 
            'coerce': int,
            'type': 'integer',
            'required': True, 
            'empty': False
        }
        schema['replaceSender'] = {
            'default': False,
        }
        schema['shippingDate'].update({
            'required': False, 'empty': True
            # 'description': forma: YYYYMMDD
        })

        def dpd_product_coerce(value):
            if value in DPD_PRODUCTS.values():
                return value
            return DPD_PRODUCTS.get(value, 1)

        schema['product'].update({
            'empty': False,
            'required': True,
            'default': DPD_PRODUCTS["DPD CLASSIC"],
            # 'description': 'Type de produit',
            'allowed': DPD_PRODUCTS.values() + DPD_PRODUCTS.keys(),
            'coerce': dpd_product_coerce
        })

        schema['parcelShopId'] = {
            'default': '',
            'empty': True,
            'required': False,
            # 'description': 'Drop-off Location id (Relais Colis)'
        }

        return schema

    def _address(self):
        schema = super(DpdApi, self)._address()
        schema['country'].update({'required': True, 'empty': False})
        schema['zip'].update({'required': True, 'empty': False})
        schema['city'].update({'required': True, 'empty': False})
        return schema

    def _to_address(self):
        schema = super(DpdApi, self)._to_address()
        schema['name'] = { 'empty': True}
        schema['firstName'] = {'default': '', 'coerce': 'accents'}
        schema['door1'] = {'default': ''}  # 'description': """Door code 1"""
        schema['door2'] = {'default': ''}  # 'description': """Door code 2"""}
        schema['intercom'] = {'default': ''}  # 'description': """Intercom"""}
        for field in ['city', 'company', 'name', 'street1', 'street2']:
            schema[field].update({'coerce': 'accents'})
        return schema

    def _auth(self):
        schema = super(DpdApi, self)._auth()
        schema['login'].update({'required': True, 'empty': False})
        schema['password']['required'] = False
        return schema

    def normalize(self, data):
        externalApi = super(DpdApi, self)
        internalApi = self._interal_api()
        step1 = externalApi.normalize(data)
        step2 = internalApi.normalize(step1)
        return step2

    def api_values(self):
        """Return a dict containing expected keys.

        It's a normalized version of the schema.
        only internal api
        """
        return self._validator().normalized({}, self.api_schema())

    def _interal_api(self):
        # for the moment we have only one api
        return DpdApiGetLabelMappingIn()

class DpdApiGetLabelMappingIn():
    """Convert internal schema to external
    internal: what comes from the user
    external: the remote endpoint
    in: internal -> external
    """

    def _clean_empty(self, input_data):
        """Remove empty keys recursively from dict.
        
        We don't want to send empty values to WS"""
        if type(input_data) is dict:
            return {
                key: self._clean_empty(val) for key, val in input_data.items()
                if val
            }
        if type(input_data) is list:
            return [self._clean_empty(val)
                for val in input_data
                if val]
        return input_data

    def normalize(self, input_data):
        val = {}
        val.update(self._manifest(input_data))
        val.update(self._parcels(input_data))
        val.update(self._to_address(input_data))
        val.update(self._from_address(input_data))
        val.update(self._service(input_data))
        val.update(self._products(input_data))
        return {
            "body": self._clean_empty(val),
            "auth": input_data['auth'],
        }

    def _service(self, data):
        return {
           "shipmentDate": data["service"]["shippingDate"],
           "payerId": data["service"]["customerId"],
           "payerAddressId": data["service"]["customerAddressId"],
           "senderId": data["service"]["senderId"],
           "senderAddressId": data["service"]["senderAddressId"],
           "senderZipCode": data["service"]["senderZipCode"],
           "senderCountryCode": data["service"]["customerCountry"],  
           "departureUnitId": data["service"]["agencyId"],
           "parcelShopId": data["service"]["parcelShopId"],
           "receiverAdditionalAdrInfo": data["service"]["instructions"],
        }

    def _products(self, data):
        return {
            "products": {
                "productId": data['service']['product']
            }
        }

    def _to_address(self, data):

        def harmonize_address(to_address):
            """If firstName then lastName should be send

            Otherwise we put stuff in company."""
            company = to_address["company"]
            firstName = to_address["firstName"]
            lastName = to_address["name"]

            if not firstName:
                if company == lastName:
                    return {
                        "receiverFirmName": company,
                    }
                else:
                    return {
                        "receiverFirmName": "%s %s" % (lastName, company)
                    }
            else:
                return {
                    "receiverFirmName": company,
                    "receiverFirstName": firstName,
                    "receiverLastName": lastName,
                }

        add = harmonize_address(data['to_address'])
        add.update({
           "receiverStreet": data["to_address"]["street1"],
           "receiverStreetInfo": data["to_address"]["street2"],
           "receiverCountryCode": data["to_address"]["country"],
           "receiverCity": data["to_address"]["city"],
           "receiverZipCode": data["to_address"]["zip"],
           "receiverMobileNumber": data["to_address"]["phone"],
           "receiverEmailAddress": data["to_address"]["email"],
        })
        return add


    def _from_address(self, data):
        if not data['service']['replaceSender']:
            return {'replaceSender': False }
        return { 
            "replaceSender": True,
            "replaceSenderAddress": 
            {
            "name": data["from_address"]["company"] or data["from_address"]["name"],
            "street": data["from_address"]["street1"],
            "streetInfo": data["from_address"]["street2"],
            "countryCode": data["from_address"]["country"],
            "city": data["from_address"]["city"],
            "zipCode": data["from_address"]["zip"],
            "telNo": data["from_address"]["phone"],
            }
        }

    def _parcels(self, data):
        output = []
        for parcel in data['parcels']:
            output.append(self._parcel(data, parcel))
        return { "parcels": output }

    def _parcel(self, data, parcel):
        return { 
           "cref1": data["service"]["reference1"],
           "cref2": data["service"]["reference2"],
           "cref3": data["service"]["reference3"],
            #"3": { "rename": "hinsAmount"},
            "weight": parcel['weight'],
        }
    
    def _manifest(self, data):
        return { "manifest": {
            "language": "fr",
            "labelFormat": "A4",
            "referenceAsBarcode": False,
            "fileType": data["service"]["labelFormat"], 
            "dpi": "300",
        }}