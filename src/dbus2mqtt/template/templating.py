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

from dbus2mqtt.util import dt as dt_util

R = TypeVar("R")


def now(tz: tzinfo | str | None = None) -> datetime:
    """Return the current date and time as a timezone-aware datetime.

    Args:
        tz: Timezone to use. If omitted, the local timezone is used.
            A timezone name may be specified as an IANA timezone string,
            for example ``"Europe/Amsterdam"``.

    Returns:
        The current date and time in the requested timezone.

    Example:
        ```jinja
        {{ now() }}
        {{ now("UTC") }}
        {{ now("Europe/Amsterdam") }}
        ```
    """
    return dt_util.now(tz)


def utcnow() -> datetime:
    """Return the current date and time in UTC.

    Returns:
        The current date and time as a timezone-aware datetime in UTC.

    Example:
        ```jinja
        {{ utcnow() }}
        ```
    """
    return dt_util.utcnow()


def as_local(value: datetime) -> datetime:
    """Convert any datetime object to local time zone.

    Args:
        value: datetime object

    Returns:
        datetime object in local timezone

    Example:
        ```jinja
        {{ utcnow() | as_local }}
        ```
    """
    return dt_util.as_local(value)


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
        engine_globals["utcnow"] = utcnow
        engine_globals["as_local"] = as_local
        engine_globals["urldecode"] = urldecode
        engine_globals["dbus2mqtt"] = {"version": version("dbus2mqtt")}

        engine_filters = {}
        engine_filters["urldecode"] = urldecode
        engine_filters["as_local"] = as_local

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
        self.jinja2_env.globals.update(custom_functions)
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
