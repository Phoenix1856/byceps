"""
byceps.util.templating
~~~~~~~~~~~~~~~~~~~~~~

Templating utilities.

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import render_template
from jinja2 import BaseLoader, Environment, FunctionLoader, Template
from jinja2.sandbox import ImmutableSandboxedEnvironment


TEMPLATE_FILENAME_EXTENSION = '.html'


def templated(arg) -> Callable:
    """Decorate a callable to wrap its return value in a template and that in
    a response object.

    This decorator expects the decorated callable to return a dictionary of
    objects that should be added to the template context, or ``None``.

    The name of the template to render can be either specified as argument or,
    if not present, will be determined by concatenating the callable's module
    and function object name (format: 'module_callable').

    The rendered template string will be wrapped in a ``Response`` object and
    returned.
    """
    def decorator(f: Callable, template_name: Optional[str]=None):
        @wraps(f)
        def decorated(*args, **kwargs):
            name = _get_template_name(f, template_name)

            context = f(*args, **kwargs)

            if context is None:
                context = {}
            elif not isinstance(context, dict):
                return context

            return render_template(name, **context)
        return decorated

    if hasattr(arg, '__call__'):
        return decorator(arg)

    def wrapper(f: Callable):
        return decorator(f, arg)

    return wrapper


def _get_template_name(view_function: Callable, template_name: Optional[str]) \
                      -> str:
    if template_name is None:
        name = _derive_template_name(view_function)
    else:
        name = template_name

    return name + TEMPLATE_FILENAME_EXTENSION


def _derive_template_name(view_function: Callable) -> str:
    """Derive the template name from the view function's module and name."""
    # Select segments between `byceps.blueprints.` and `.views`.
    module_package_name_segments = view_function.__module__.split('.')
    blueprint_path_segments = module_package_name_segments[2:-1]

    action_name = view_function.__name__

    return '/'.join(blueprint_path_segments + [action_name])


def load_template(source: str, *, template_globals: Dict[str, Any]=None):
    """Load a template from source, using the sandboxed environment."""
    env = create_sandboxed_environment()

    if template_globals is not None:
        env.globals.update(template_globals)

    return env.from_string(source)


def create_sandboxed_environment(*, loader: Optional[BaseLoader]=None) \
                                -> Environment:
    """Create a sandboxed environment."""
    if loader is None:
        # A loader that never finds a template.
        loader = FunctionLoader(lambda name: None)

    return ImmutableSandboxedEnvironment(
        loader=loader,
        autoescape=True)


def get_variable_value(template: Template, name: str) -> Optional[Any]:
    """Return the named variable's value from the template, or `None` if
    the variable is not defined.
    """
    try:
        return getattr(template.module, name)
    except AttributeError:
        return None
