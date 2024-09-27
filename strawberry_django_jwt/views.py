from typing import Optional, cast, Any, Union

from asgiref.sync import sync_to_async
from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseNotAllowed, HttpResponseBase
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView, BaseView, GraphQLView
from strawberry.http import GraphQLHTTPResponse, process_result
from strawberry.http.exceptions import HTTPException
from strawberry.types import ExecutionResult

from strawberry_django_jwt.exceptions import JSONWebTokenError


class StatusGraphQLHTTPResponse(GraphQLHTTPResponse):
    status: Optional[int]


def make_status_response(response: GraphQLHTTPResponse) -> StatusGraphQLHTTPResponse:
    res = cast(StatusGraphQLHTTPResponse, response)
    res["status"] = 200
    return res


class BaseStatusHandlingGraphQLView(BaseView):
    def _create_response(self, response_data: GraphQLHTTPResponse, sub_response: HttpResponse) -> JsonResponse:
        data = cast(StatusGraphQLHTTPResponse, response_data)
        response = JsonResponse(data, status=data.get("status", None))

        for name, value in sub_response.items():
            response[name] = value

        return response


class StatusHandlingGraphQLView(BaseStatusHandlingGraphQLView, GraphQLView):
    def process_result(self, request: HttpRequest, result: ExecutionResult) -> StatusGraphQLHTTPResponse:
        res = make_status_response(process_result(result))
        if result.errors and any(isinstance(err, JSONWebTokenError) for err in [e.original_error for e in result.errors]):
            res["status"] = 401
        return res


class AsyncStatusHandlingGraphQLView(BaseStatusHandlingGraphQLView, AsyncGraphQLView):
    async def process_result(self, request: HttpRequest, result: ExecutionResult) -> StatusGraphQLHTTPResponse:
        res = make_status_response(process_result(result))
        if result.errors and any(isinstance(err, JSONWebTokenError) for err in [e.original_error for e in result.errors]):
            res["status"] = 401
        return res


class ProtectedAsyncGraphQLView(AccessMixin, AsyncGraphQLView):
    @method_decorator(csrf_exempt)
    async def dispatch(  # pyright: ignore
        self, request: HttpRequest, *args: Any, **kwargs: Any
    ) -> Union[HttpResponseNotAllowed, TemplateResponse, HttpResponseBase]:
        is_authenticated = await sync_to_async(lambda: request.user.is_authenticated)()
        if request.method.upper() == 'GET' and not is_authenticated:
            return self.handle_no_permission()

        try:
            return await self.run(request=request)
        except HTTPException as e:
            return HttpResponse(
                content=e.reason,
                status=e.status_code,
            )
