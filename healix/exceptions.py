import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Returns all errors in a consistent envelope:
    {
        "success": false,
        "error": {
            "status_code": 400,
            "message": "Human-readable summary",
            "details": { ...field-level errors... }
        }
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'message': _extract_message(response.data),
                'details': response.data,
            },
        }
        response.data = error_data
    else:
        logger.exception('Unhandled exception in %s: %s', context.get('view'), exc)
        response = Response(
            {
                'success': False,
                'error': {
                    'status_code': 500,
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': {},
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _extract_message(data):
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            if isinstance(value, str):
                return f"{key}: {value}"
    if isinstance(data, list) and data:
        return str(data[0])
    return 'An error occurred.'
