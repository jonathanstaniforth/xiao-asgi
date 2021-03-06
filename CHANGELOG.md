# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Support for the WebSocket Denial Response ASGI extensions by making ``WebSocketConnection`` inherit from ``HttpConnection``.

### Changed
- The routes parameter for the Xiao class is now a keyword parameter with a default value of an empty list allowing it to be optional.

## [0.2.1] - 2021-11-10
### Changed
- The project version to 0.2.1.

## [0.2.0] - 2021-11-10
### Changed
- Refactored project to simplify and reduce dependencies.

## [0.1.0] - 2021-06-23
### Added
- CHANGELOG file to record changes to the project.
- Xiao class for establishing an ASGI application.
- Route and Router classes for routing a request to an endpoint.
- PlainTextResponse for sending text/plain responses.
- JsonResponse class for sending application/json responses.
- HtmlResponse class for sending text/html responses.
- Response class for sending responses to a client.
- Request class for representing received HTTP requests.

### Changed
- Moved unit tests to tests/unit folder.
