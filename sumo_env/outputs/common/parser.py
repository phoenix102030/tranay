import xml.etree.ElementTree as ET
from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")


def parse_attributes(
    element: ET.Element, attribute_map: dict[str, Type[Any]]
) -> dict[str, Any]:
    """Parse XML element attributes using a provided mapping."""
    return {key: caster(element.get(key, "0")) for key, caster in attribute_map.items()}


def parse_elements(
    parent: ET.Element, tag: str, parse_fn: Callable[[ET.Element], T]
) -> list[T]:
    """Parse child elements with a given tag using a custom parser."""
    return [parse_fn(child) for child in parent.findall(tag)]
