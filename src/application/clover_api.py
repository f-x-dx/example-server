import requests
import urllib
import json
import re

class CloverResponseObject(dict):
    """Object to encapsulate response JSON."""
    def __init__(self, obj):
        for key, value in obj.items():
            self.__dict__[key] = value
        dict.__init__(self, obj)

class CloverAPI(object):
    """CloverAPI object for making API calls to Clover's server."""

    #base_url = "http://localhost:9000" # local
    # base_url = "https://stg1.dev.clover.com" #staging
    base_url = "https://www.clover.com" # production
    # TODO: change back to production before release

    path_match = re.compile("\{([a-zA-Z]*)\}")

    @classmethod
    def build_auth_url(cls, callback, app_id, permissions=None):
        """Builds an url to the Clover authentication server. Send the user to
        this url to authenticate, and Clover will send an auth-code to the
        callback.

        Available permissions:
            "CUSTOMERS_R"
            "CUSTOMERS_W"
            "PAYMENTS_R"
            "PAYMENTS_W"
            "INVENTORY_R"
            "INVENTORY_W"
            "ORDERS_R"
            "ORDERS_W"
            "EMPLOYEES_R"
            "EMPLOYEES_W"
            "MERCHANT_R"
            "MERCHANT_W"

        Args:
            callback: Callback URL
            app_id: Clover App ID from the developer page.
            permissions: A python list of extra permissions
        Returns:
            A string which is the url to send the user to for authentication.
        """
        params = {"redirect_uri": callback,
                  "client_id": app_id}

        if permissions is not None:
            params["scope"] = ",".join(permissions)

        return "{}/oauth/authorize?{}".format(cls.base_url,
                                              urllib.urlencode(params))

    def __init__(self, access_token=None, merchant_id=None):
        """Makes a CloverAPI object.

        Args:
            access_token: Token to access Clover's API, appended as a URL
                          parameter, if present
            merchant_id: Replaces "{mId}" in the endpoint URL, if present
        Returns:
            A CloverAPI object
        """
        self.merchant_id = merchant_id
        self.access_token = access_token

    def get(self, endpoint, **kwargs):
        """Send a get request using Clover's API

        Extra query parameters will be formatted in the URL. For example, if
        itemId is passed in as a keyword argument and "{itemId}" is in the
        endpoint url, "{itemId}" will be replaced with the value of that
        argument. If "{itemId}" is not present, the argument will be added as a
        query parameter in the URL.

        Args:
            endpoint: Clover endpoint's url
            **kwargs: Any other parameters.
        Returns:
            A CloverResponseObject converted from the response JSON, which
            allows access to values in the JSON object. For example, if the JSON
            object is: {name: "My Merchant Name"}, to get the name from the
            corresponding CloverResponseObject, use: `response.name`
        Raises:
            requests.exceptions.HTTPError: If Clover's server returns an error
                                           code between 400 and 599.
        """
        return self._send("GET", endpoint, **kwargs)

    def post(self, endpoint, data, **kwargs):
        """Send a post request using Clover's API.

        See documentation for `get`

        Args:
            endpoint: See documentation for `get`
            data: A python object to convert to a JSON object to send
            **kwargs: See documentation for `get`
        Returns:
            See documentation for `get`
        Raises:
            See documentation for `get`
        """
        return self._send("POST", endpoint, data, **kwargs)

    def _send(self, method, endpoint, data={}, **kwargs):
        # Set parameters
        parameters = kwargs
        if self.access_token:
            parameters["access_token"] = self.access_token
        if self.merchant_id:
            parameters["mId"] = self.merchant_id

        # Replace user-defined path parameters
        path_params = CloverAPI.path_match.findall(endpoint)
        for key in path_params:
            if key in parameters:
                endpoint = endpoint.replace('{%s}' % key, parameters[key])
                parameters.pop(key)
            else:
                raise KeyError("Missing path parameter: " + key)

        url = CloverAPI.base_url + endpoint

        # Send request
        if method == "POST":
            headers = {}
            headers["content-type"] = "application/json"
            response = requests.post(url, headers=headers, params=parameters,
                                 data=json.dumps(data))
        elif method == "GET":
            response =  requests.get(url, params=parameters)

        error_msg = None
        if 400 <= response.status_code < 500:
            error_msg = '%s Client Error: %s\n%s'
        elif 500 <= response.status_code < 600:
            error_msg = '%s Server Error: %s\n%s'

        if error_msg:
            raise requests.exceptions.HTTPError(
                error_msg % (response.status_code, response.reason, response.text),
                response=response
            )

        # Clover always returns JSON object in response

        return json.loads(response.content, object_hook=CloverResponseObject)


# Example! Increases the price of all items in the inventory by 1 cent
if __name__ == '__main__':
    # TODO: remove during production
    CloverAPI.base_url = "https://www.clover.com"

    # Create CloverAPI instance with Merchant ID and Access Token
    c = CloverAPI("9c655e20-d50b-df20-8c2d-d48f0ef7d8da", merchant_id="PTEXTPYDZ6K4C")

    # Get all items from merchant's inventory
    response = c.get("/v2/merchant/{mId}/inventory/items")

    for item in response.items:
        c.post("/v2/merchant/{mId}/inventory/items/{itemId}/price",
               {"price": item.price + 1}, itemId=item.id)
