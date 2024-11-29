# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from facebook_business.exceptions import (
    FacebookBadObjectError,
)
from facebook_business.adobjects.abstractobject import AbstractObject


class ObjectParser:
    """
    Parser for API response
    """

    def __init__(
        self,
        api=None,
        target_class=None,
        reuse_object=None,
        custom_parse_method=None,
    ):
        """ Initialize an ObjectParser.
        To Initialize, you need to provide either a reuse_object, target_class,
        or an custom_parse_method.
        Args:
            api: FacebookAdsApi object.
            target_class (optional): The expected return object type.
            reuse_object (optional): Reuse existing object to populate response.
            custom_parse_method (optional): Custom parsing method.
        """
        if not any([target_class, reuse_object is not None, custom_parse_method]):
            raise FacebookBadObjectError(
                'Must specify either target class calling object' +
                'or custom parse method for parser')
        self._reuse_object = reuse_object
        self._target_class = target_class
        self._custom_parse_method = custom_parse_method
        self._api = api

    def parse_single(self, response, override_target_class=None):
        if self._custom_parse_method is not None:
            return self._custom_parse_method(response, self._api)

        from .ad import Ad
        from .adpreview import AdPreview
        from .adset import AdSet
        from .campaign import Campaign

        data = response.get('data', response)
        if 'images' in response and not isinstance(data.get('images', []), list):
            _, data = data['images'].popitem()

        subfields = {
            'campaigns': Campaign,
            'adsets': AdSet,
            'ads': Ad,
            'previews': AdPreview
        }

        for subfield, _class in subfields.items():
            if subfield in data:
                data[subfield] = [
                    self.parse_single(item, override_target_class=_class)
                    for item in data[subfield]['data']
                ]

        data.pop('success', None)

        target_class = override_target_class or self._target_class
        if self._reuse_object is not None:
            self._reuse_object._set_data(data)
            return self._reuse_object
        elif self._target_class is not None:
            return AbstractObject.create_object(self._api, data, target_class)
        else:
            raise FacebookBadObjectError(
                'Specify either target class, reuse_object, or custom_parse_method')

    def parse_multiple(self, response):
        data_list = response.get('data', [response])
        return [self.parse_single(json_obj) for json_obj in data_list]
