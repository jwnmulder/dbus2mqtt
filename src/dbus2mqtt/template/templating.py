
from datetime import datetime
from typing import Any, TypeVar

from jinja2 import BaseLoader, StrictUndefined, TemplateError
from jinja2.nativetypes import NativeEnvironment

TemplateResultType = TypeVar('TemplateResultType')

class TemplateEngine:
    def __init__(self):

        engine_globals = {}
        engine_globals['now'] = datetime.now

        self.jinja2_env = NativeEnvironment(
            loader=BaseLoader(),
            extensions=['jinja2_ansible_filters.AnsibleCoreFiltersExtension'],
            undefined=StrictUndefined,
            keep_trailing_newline=False
        )

        self.jinja2_async_env = NativeEnvironment(
            loader=BaseLoader(),
            extensions=['jinja2_ansible_filters.AnsibleCoreFiltersExtension'],
            undefined=StrictUndefined,
            enable_async=True
        )

        self.app_context: dict[str, Any] = {}

        self.jinja2_env.globals.update(engine_globals)
        self.jinja2_async_env.globals.update(engine_globals)

    def add_functions(self, custom_functions: dict[str, Any]):
        self.jinja2_env.globals.update(custom_functions)
        self.jinja2_async_env.globals.update(custom_functions)

    def update_app_context(self, context: dict[str, Any]):
        self.app_context.update(context)

    def _convert_value(self, res: Any, res_type: type[TemplateResultType]) -> TemplateResultType:

        if res is None:
            return res

        if isinstance(res, res_type):
            return res

        try:
            return res_type(res) # type: ignore

        except Exception as e:
            raise ValueError(f"Error converting rendered template result from '{type(res).__name__}' to '{res_type.__name__}'") from e

    def _render_template_nested(self, templatable: str | dict[str, Any], context: dict[str, Any] = {}) -> Any:

        if isinstance(templatable, str):
            try:
                return self.jinja2_env.from_string(templatable).render(**context)
            except TemplateError as e:
                raise TemplateError(f"Error compiling template, template={templatable}: {e}") from e

        elif isinstance(templatable, dict):
            res = {}
            for k, v in templatable.items():
                if isinstance(v, dict) or isinstance(v, str):
                    res[k] = self._render_template_nested(v, context)
                else:
                    res[k] = v
            return res

    def render_template(self, templatable: str | dict[str, Any], res_type: type[TemplateResultType], context: dict[str, Any] = {}) -> TemplateResultType:

        if isinstance(templatable, dict) and res_type is not dict:
            raise ValueError(f"res_type should dict for dictionary templates, templatable={templatable}")

        res = self._render_template_nested(templatable, context)
        res = self._convert_value(res, res_type)
        return res

    async def _async_render_template_nested(self, templatable: str | dict[str, Any], context: dict[str, Any] = {}) -> Any:

        if isinstance(templatable, str):
            try:
                return await self.jinja2_async_env.from_string(templatable).render_async(**context)
            except TemplateError as e:
                raise TemplateError(f"Error compiling template, template={templatable}: {e}") from e

        elif isinstance(templatable, dict):
            res = {}
            for k, v in templatable.items():
                if isinstance(v, dict) or isinstance(v, str):
                    res[k] = await self._async_render_template_nested(v, context)
                else:
                    res[k] = v
            return res

    async def async_render_template(self, templatable: str | dict[str, Any], res_type: type[TemplateResultType], context: dict[str, Any] = {}) -> TemplateResultType:

        if isinstance(templatable, dict) and res_type is not dict:
            raise ValueError(f"res_type should be dict for dictionary templates, templatable={templatable}")

        res = await self._async_render_template_nested(templatable, context)
        res = self._convert_value(res, res_type)
        return res
