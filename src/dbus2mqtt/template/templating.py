import asyncio
import urllib.parse

from datetime import datetime, tzinfo
from importlib.metadata import version
from typing import Any, TypeVar

from jinja2 import (
    BaseLoader,
    StrictUndefined,
    TemplateError,
    TemplateRuntimeError,
    UndefinedError,
)
from jinja2.nativetypes import NativeEnvironment, NativeTemplate
from jinja2_ansible_filters import AnsibleCoreFiltersExtension

R = TypeVar("R")


def now(tz: tzinfo | None = None) -> datetime:
    """Returns new datetime object representing current time.

    Args:
        tz: If no tz is specified, uses local timezone.

    Returns:
        Current datetime object.
    """
    return datetime.now(tz)


def urldecode(string: str) -> str:
    """Decode a url-encoded URL string by replacing %xx escapes with their single-character equivalent.

    Args:
        string: The string to decode.

    Returns:
        A decoded URL string.

    Example:
        ```python
        >>> urldecode('abc%20def')
        'abc def'
        >>> urldecode('El%20Ni%C3%B1o')
        'El Niño'
        ```
    """
    return urllib.parse.unquote(string)


def _compile_template(environment: NativeEnvironment, templatable: str) -> NativeTemplate:
    try:
        template: NativeTemplate = environment.from_string(templatable)  # type: ignore
        return template
    except TemplateError as e:
        raise TemplateError(f"Error compiling template, template={templatable}: {e}") from e


class TemplateEngine:
    def __init__(self):

        engine_globals = {}
        engine_globals["now"] = now
        engine_globals["urldecode"] = urldecode
        engine_globals["dbus2mqtt"] = {"version": version("dbus2mqtt")}

        engine_filters = {}
        engine_filters["urldecode"] = urldecode

        self.jinja2_env = NativeEnvironment(
            loader=BaseLoader(),
            extensions=[AnsibleCoreFiltersExtension],
            undefined=StrictUndefined,
            keep_trailing_newline=False,
        )

        self.jinja2_async_env = NativeEnvironment(
            loader=BaseLoader(),
            extensions=[AnsibleCoreFiltersExtension],
            undefined=StrictUndefined,
            enable_async=True,
        )

        self.app_context: dict[str, Any] = {}

        self.jinja2_env.globals.update(engine_globals)
        self.jinja2_async_env.globals.update(engine_globals)

        self.jinja2_env.filters.update(engine_filters)
        self.jinja2_async_env.filters.update(engine_filters)

    def add_functions(self, custom_functions: dict[str, Any]):

        # Filter out coroutine functions/objects for the sync environment
        custom_sync_only_functions: dict[str, Any] = {
            name: obj
            for name, obj in custom_functions.items()
            if not (asyncio.iscoroutinefunction(obj) or asyncio.iscoroutine(obj))
        }

        self.jinja2_env.globals.update(custom_sync_only_functions)
        self.jinja2_async_env.globals.update(custom_functions)

    def update_app_context(self, context: dict[str, Any]):
        self.app_context.update(context)

    def _convert_value(self, res: object | None, res_type: type[R]) -> R | None:

        if res is None:
            return res

        if isinstance(res, res_type):
            return res

        try:
            return res_type(res)  # type: ignore

        except Exception as e:
            raise ValueError(
                f"Error converting rendered template result from '{type(res).__name__}' to '{res_type.__name__}'"
            ) from e

    def _render_template_nested(
        self, templatable: str | dict[str, Any], context: dict[str, Any]
    ) -> object | None:

        if isinstance(templatable, str):
            template = _compile_template(self.jinja2_env, templatable)
            try:
                res = template.render(**context)
                str(res)  # access value to trigger jinja UndefinedError
                return res
            except UndefinedError as e:
                raise TemplateRuntimeError(
                    f"Error rendering template, template={templatable}: {e}"
                ) from e

        elif isinstance(templatable, dict):
            res = {}
            for k, v in templatable.items():
                if isinstance(v, (dict, str)):
                    res[k] = self._render_template_nested(v, context)
                else:
                    res[k] = v
            return res

    async def _async_render_template_nested(
        self, templatable: str | dict[str, Any], context: dict[str, Any]
    ) -> object | None:

        if isinstance(templatable, str):
            template = _compile_template(self.jinja2_async_env, templatable)
            try:
                res = await template.render_async(**context)
                str(res)  # access value to trigger jinja UndefinedError
                return res
            except UndefinedError as e:
                raise TemplateRuntimeError(
                    f"Error rendering template, template={templatable}: {e}"
                ) from e

        elif isinstance(templatable, dict):
            res = {}
            for k, v in templatable.items():
                if isinstance(v, (dict, str)):
                    res[k] = await self._async_render_template_nested(v, context)
                else:
                    res[k] = v
            return res

    def _assert_template_res_type(
        self,
        templatable: str | dict[str, Any],
        res_type: type[R],
    ):
        if isinstance(templatable, dict) and res_type is not dict:
            raise ValueError(
                f"res_type should be dict for dictionary templates, templatable={templatable}"
            )

    def render_template_optional(
        self,
        templatable: str | dict[str, Any],
        res_type: type[R],
        context: dict[str, Any] | None = None,
    ) -> R | None:

        self._assert_template_res_type(templatable, res_type)
        res = self._render_template_nested(templatable, context or {})
        res = self._convert_value(res, res_type)
        return res

    def render_template(
        self,
        templatable: str | dict[str, Any],
        res_type: type[R],
        context: dict[str, Any] | None = None,
    ) -> R:
        res = self.render_template_optional(templatable, res_type, context)
        assert res is not None
        return res

    async def async_render_template_optional(
        self,
        templatable: str | dict[str, Any],
        res_type: type[R],
        context: dict[str, Any] | None = None,
    ) -> R | None:

        self._assert_template_res_type(templatable, res_type)
        res = await self._async_render_template_nested(templatable, context or {})
        res = self._convert_value(res, res_type)

        return res

    async def async_render_template(
        self,
        templatable: str | dict[str, Any],
        res_type: type[R],
        context: dict[str, Any] | None = None,
    ) -> R:
        res = await self.async_render_template_optional(templatable, res_type, context)
        assert res is not None
        return res
