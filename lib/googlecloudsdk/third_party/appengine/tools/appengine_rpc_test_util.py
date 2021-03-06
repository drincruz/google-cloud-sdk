"""Utilities for testing code that uses appengine_rpc's *RpcServer."""



import logging
import StringIO
import urllib2

from googlecloudsdk.third_party.appengine.tools.appengine_rpc import AbstractRpcServer
from googlecloudsdk.third_party.appengine.tools.appengine_rpc import HttpRpcServer


class TestRpcServerMixin(object):
  """Provides a mocked-out version of HttpRpcServer for testing purposes."""

  def set_strict(self, strict=True):
    """Enables strict mode."""
    self.opener.set_strict(strict)

  def _GetOpener(self):
    """Returns a MockOpener.

    Returns:
      A MockOpener object.
    """
    return TestRpcServerMixin.MockOpener()

  class MockResponse(object):
    """A mocked out response object for testing purposes."""

    def __init__(self, body, code=200, headers=None):
      """Creates a new MockResponse.

      Args:
        body: The text of the body to return.
        code: The response code (default 200).
        headers: An optional header dictionary.
      """
      self.fp = StringIO.StringIO(body)
      self.code = code
      self.headers = headers
      self.msg = ""

      if self.headers is None:
        self.headers = {}

    def info(self):
      return self.headers

    def read(self, length=-1):
      """Reads from the response body.

      Args:
        length: The number of bytes to read.

      Returns:
        The body of the response.
      """
      return self.fp.read(length)

    def readline(self):
      """Reads a line from the response body.

      Returns:
        A line of text from the response body.
      """
      return self.fp.readline()

    def close(self):
      """Closes the response stream."""
      self.fp.close()

  class MockOpener(object):
    """A mocked-out OpenerDirector for testing purposes."""

    def __init__(self):
      """Creates a new MockOpener."""
      self.requests = []
      self.responses = {}
      self.ordered_responses = {}
      self.cookie = None
      self.strict = False

    def set_strict(self, strict=True):
      """Enables strict mode."""
      self.strict = strict

    def open(self, request):
      """Logs the request and returns a MockResponse object."""
      full_url = request.get_full_url()
      if "?" in full_url:
        url = full_url[:full_url.find("?")]
      else:
        url = full_url
      if (url != "https://www.google.com/accounts/ClientLogin"
          and not url.endswith("_ah/login")):
        assert "X-appcfg-api-version" in request.headers
        assert "User-agent" in request.headers
      request_data = (full_url, bool(request.data))
      self.requests.append(request_data)
      if self.cookie:
        request.headers["Cookie"] = self.cookie
        response = self.responses[url](request)

      # Use ordered responses in preference to specific response to generic 200.
      if url in self.ordered_responses:
        logging.debug("Using ordered pre-canned response for: %s" % full_url)
        response = self.ordered_responses[url].pop(0)(request)
        if not self.ordered_responses[url]:
          self.ordered_responses.pop(url)
      elif url in self.responses:
        logging.debug("Using pre-canned response for: %s" % full_url)
        response = self.responses[url](request)
      elif self.strict:
        raise Exception('No response found for url: %s (%s)' % (url, full_url))
      else:
        logging.debug("Using generic blank response for: %s" % full_url)
        response = TestRpcServerMixin.MockResponse("")
      if "Set-Cookie" in response.headers:
        self.cookie = response.headers["Set-Cookie"]

      # Handle error status codes in the same way as the appengine_rpc openers.
      # urllib2 will raise HTTPError for non-2XX status codes, per RFC 2616.
      if not (200 <= response.code < 300):
        code, msg, hdrs = response.code, response.msg, response.info()
        fp = StringIO.StringIO(response.read())
        raise urllib2.HTTPError(url=url, code=code, msg=None, hdrs=hdrs, fp=fp)
      return response

    def AddResponse(self, url, response_func):
      """Calls the provided function when the provided URL is requested.

      The provided function should accept a request object and return a
      response object.

      Args:
        url: The URL to trigger on.
        response_func: The function to call when the url is requested.
      """
      self.responses[url] = response_func

    def AddOrderedResponse(self, url, response_func):
      """Calls the provided function when the provided URL is requested.

      The provided functions should accept a request object and return a
      response object.  This response will be added after previously given
      responses if they exist.

      Args:
        url: The URL to trigger on.
        response_func: The function to call when the url is requested.
      """
      if url not in self.ordered_responses:
        self.ordered_responses[url] = []
      self.ordered_responses[url].append(response_func)

    def AddOrderedResponses(self, url, response_funcs):
      """Calls the provided function when the provided URL is requested.

      The provided functions should accept a request object and return a
      response object. Each response will be called once.

      Args:
        url: The URL to trigger on.
        response_funcs: A list of response functions.
      """
      self.ordered_responses[url] = response_funcs


class TestRpcServer(TestRpcServerMixin, AbstractRpcServer):
  pass


class TestHttpRpcServer(TestRpcServerMixin, HttpRpcServer):
  pass


class UrlLibRequestResponseStub(object):
  def __init__(self, headers=None):
    self.headers = {}
    if headers:
      self.headers = headers

  def add_header(self, header, value):
    # Note that this does not preserve header order.
    # If that's a problem for your tests, add some functionality :)
    self.headers[header] = value


class UrlLibRequestStub(UrlLibRequestResponseStub):
  pass


class UrlLibResponseStub(UrlLibRequestResponseStub, StringIO.StringIO):
  def __init__(self, body, headers, url, code, msg):
    UrlLibRequestResponseStub.__init__(self, headers)
    if body:
      StringIO.StringIO.__init__(self, body)
    else:
      StringIO.StringIO.__init__(self, "")
    self.url = url
    self.code = code
    self.msg = msg
