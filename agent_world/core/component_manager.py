# Component Manager for ECS-style storage.
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type, TypeVar

T = TypeVar("T")


class ComponentManager:
    """Track components attached to entities and registered component classes."""

    def __init__(self) -> None:
        # Maps component class name to the class object
        self._registry: Dict[str, Type[Any]] = {}
        # Maps entity id to {component name: component instance}
        self._components: Dict[int, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------
    def register_component(self, component_cls: Type[Any]) -> None:
        """Register a component class for later lookup."""
        name = component_cls.__name__
        self._registry[name] = component_cls
        # Registration hooks would be triggered here in future.

    def unregister_component(self, component_cls: Type[Any] | str) -> None:
        """Remove a component class from the registry."""
        name = (
            component_cls if isinstance(component_cls, str) else component_cls.__name__
        )
        self._registry.pop(name, None)
        # Unregistration hooks would be triggered here in future.

    # ------------------------------------------------------------------
    # Component access API
    # ------------------------------------------------------------------
    def add_component(self, entity_id: int, component: Any) -> None:
        """Attach a component instance to an entity."""
        name = type(component).__name__
        if name not in self._registry:
            # Auto-register unknown component classes
            self.register_component(type(component))
        self._components.setdefault(entity_id, {})[name] = component
        # Future hook: on_component_added(entity_id, component)

    def get_component(self, entity_id: int, component_cls: Type[T]) -> Optional[T]:
        """Return a component of the given class for an entity, if present."""
        comps = self._components.get(entity_id)
        if not comps:
            return None
        return comps.get(component_cls.__name__)  # type: ignore[return-value]

    def remove_component(self, entity_id: int, component_cls: Type[T]) -> Optional[T]:
        """Remove and return the component of the given class from an entity."""
        comps = self._components.get(entity_id)
        if not comps:
            return None
        comp = comps.pop(component_cls.__name__, None)
        # Future hook: on_component_removed(entity_id, comp)
        return comp  # type: ignore[return-value]

    def components_for_entity(self, entity_id: int) -> Iterable[Any]:
        """Iterate over all components attached to an entity."""
        return self._components.get(entity_id, {}).values()
