# make it compatible to django 1.10
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
import logging
import re
from django.utils.termcolors import colorize

MAX_BODY_LENGTH = 50000  # log no more than 3k bytes of content
request_logger = logging.getLogger('django.request')


class LoggingMiddleware(MiddlewareMixin):

    def process_request(self, request):
        headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_') or k.startswith('REMOTE')}
        user = getattr(request, 'user', None)
        if user and user.is_authenticated():
            headers.update({'user': user.username})
        request_logger.info(colorize("{} {} {}".format(request.method, request.get_full_path(), headers), fg="cyan"))
        if headers:
            self._log(headers)
        if request.body:
            self._log(self._chunked_to_max(request.body))

    def process_response(self, request, response):
        resp_log = "{} {} - {}".format(request.method, request.get_full_path(), response.status_code)
        if (response.status_code in range(400, 600)):
            request_logger.info(colorize(resp_log, fg="magenta"))
            self._log_resp(response, level=logging.ERROR)
        else:
            request_logger.info(colorize(resp_log, fg="cyan"))
            self._log_resp(response)

        return response

    def _log_resp(self, response, level=logging.DEBUG):
        if not re.match('^application/json', response.get('Content-Type', ''), re.I):  # only log content type: 'application/xxx'
            return

        self._log(response._headers, level)
        self._log(response._headers, level)
        self._log(self._chunked_to_max(response.content), level)

    def _log(self, msg, level=logging.DEBUG):
        for line in str(msg).split('\n'):
            line = colorize(line, fg="magenta") if (level >= logging.ERROR) else colorize(line, fg="cyan")
            request_logger.log(level, line)

    def _chunked_to_max(self, msg):
        if len(msg) > MAX_BODY_LENGTH:
            return "{0}\n...\n".format(msg[0:MAX_BODY_LENGTH])
        else:
            return msg
