import json
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from classes.enum.ServiceType import ServiceType


def mock_service_url_side_effect(service_type):
    if service_type == ServiceType.AUTH_SERVICE:
        return "http://mockauthservice"
    elif service_type == ServiceType.DATABASE_SERVICE:
        return "http://mockdatabaseservice"
    elif service_type == ServiceType.FILE_SERVICE:
        return "http://mockfileservice"


class MockRedirectResponse:
    """
    Creates a new instance of the MockRedirectResponse class.

    :param str url: The URL of the redirect response.
    :param int status_code: The status code of the redirect response. Defaults to 303.
    """
    def __init__(self, url, status_code=303, content=None):
        self.url = url
        self.status_code = status_code
        self.cookies = {}
        self.content = content

    async def __call__(self, scope, receive, send):
        headers = [(b'content-type', b'application/json')]
        for key, value in self.cookies.items():
            set_cookie_header = f"{key}={value['value']}; Path=/; HttpOnly" if value[
                'httponly'] else f"{key}={value['value']}; Path=/"
            headers.append((b'set-cookie', set_cookie_header.encode('utf-8')))
        body_content = json.dumps({
            "url": self.url,
            "status_code": self.status_code,
            "cookies": self.cookies  # Reintroduce cookies in the body for testing
        }).encode('utf-8')

        await send({
            'type': 'http.response.start',
            'status': self.status_code,
            'headers': headers,
        })
        await send({
            'type': 'http.response.body',
            'body': body_content,
        })

    def set_cookie(self, key, value, httponly=True):
        self.cookies[key] = {'value': value, 'httponly': httponly}

    def delete_cookie(self, key):
        if key in self.cookies:
            del self.cookies[key]

    def json(self):
        # This method returns a dictionary representation of the object
        return {
            "url": self.url,
            "status_code": self.status_code,
            "cookies": self.cookies
        }

    def text(self):
        # This method returns a JSON-like string representation of the object
        return json.dumps(self.json())


class MockTemplateResponse:
    """
    Represents a mock template response.

    :param template_name: The name of the template.
    :type template_name: str
    :param detail: The context data for the template.
    :type detail: dict
    :param status_code: The status code of the response (default is 200).
    :type status_code: int

    """
    def __init__(self, template_name, detail, error=None, status_code=200):
        self.template_name = template_name
        self.detail = detail
        self.error = error
        self.status_code = status_code

    def json(self):
        # This method returns a dictionary representation of the object
        return {
            "template_name": self.template_name,
            "error": self.error,
            "context": self.detail,
            "status_code": self.status_code
        }

    def text(self):
        # This method returns a JSON-like string representation of the object
        return json.dumps(self.json())

@pytest.fixture
def mock_template_response_with_cookies():
    with patch('fastapi.templating.Jinja2Templates.TemplateResponse') as mock_template_response:
        def template_response_mock(*args, **kwargs):
            template_name = args[0]

            try:
                # remove request from the context
                del args[1]['request']
            except KeyError:
                pass

            try:
                error = args[1]['error']
                # remove error from the context
                del args[1]['error']
            except KeyError:
                error = None

            try:
                detail = args[1]
            except KeyError:
                detail = None
            return MockTemplateResponse(template_name, detail= detail, error=error, status_code=200)

        mock_template_response.side_effect = template_response_mock
        yield