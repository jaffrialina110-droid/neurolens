"""
NeuroLens Extension System

Advanced Stage modules are registered separately.
A failed optional extension must not stop the main app.
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Extension:
    name: str
    title: str
    description: str
    enabled: bool = False
    renderer: Optional[Callable] = None


class ExtensionRegistry:

    def __init__(self):
        self._extensions = {}

    def register(self, extension: Extension):
        if not isinstance(extension, Extension):
            raise TypeError("Invalid extension")

        self._extensions[extension.name] = extension

    def get(self, name):
        return self._extensions.get(name)

    def all(self):
        return list(self._extensions.values())

    def enabled(self):
        return [
            item for item in self._extensions.values()
            if item.enabled
        ]

    def render(self, name, st):
        extension = self.get(name)

        if not extension or not extension.enabled:
            return False

        if not extension.renderer:
            return False

        try:
            extension.renderer(st)
            return True
        except Exception:
            st.warning(
                f"{extension.title} is temporarily unavailable."
            )
            return False


registry = ExtensionRegistry()
