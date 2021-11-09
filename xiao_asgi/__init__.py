"""xiao asgi is a small ASGI framework for creating ASGI applications.

Contained in the package are modules that handle receiving requests, routing
requests to an endpoint and sending responses.

Modules:
    applications: receives the initial request and passing it
        to the appropriate route.
    connections: handles receiving requests and sending responses.
    requests: object representation of received requests.
    responses: object represenstations of responses that can be rendered for
        sending as a response.
    routing: representations of a route and holds the endpoints for processing
        a request.
"""
__version__ = "0.1.0"
