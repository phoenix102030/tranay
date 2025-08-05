import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from functools import reduce
from pathlib import Path
from typing import Iterator, Optional


def root(file: Path) -> ET.Element:
    return ET.parse(file).getroot()


def iterparse_stream(file_path: str) -> Iterator[tuple[str, ET.Element]]:
    """
    Stream XML elements from a file incrementally.
    """
    context = ET.iterparse(file_path, events=("start", "end"))
    _, root = next(context)
    yield from context
    root.clear()


def iterparse_elements(file_path: str, tag: str) -> Iterator[ET.Element]:
    """
    Stream XML elements with a specific tag from a file.
    """
    for event, elem in iterparse_stream(file_path):
        if event == "end" and elem.tag == tag:
            yield elem
            elem.clear()


def create_elem(name: str, attrs: dict[str, str] = {}) -> ET.Element:
    return ET.Element(name, attrs)


def create_sub_elem(
    elem: ET.Element, sub_elem_name: str, attribs: dict[str, str] = {}
) -> ET.Element:
    ET.SubElement(elem, sub_elem_name, attribs)
    return elem


def extract_attribute(element: ET.Element, key: str, default: str = "") -> str:
    return element.get(key, default)


def update_sub_elem(
    elem: ET.Element, sub_elem_name: str, attribs: dict[str, str]
) -> Optional[ET.Element]:
    sub_element = elem.find(sub_elem_name)
    if sub_element is None:
        return None
    for key, value in attribs.items():
        sub_element.set(key, value)
    return elem


def append_elements_to_root(root: ET.Element, elements: list[ET.Element]) -> ET.Element:
    return reduce(
        lambda parent, elem: (parent.append(elem), parent)[1],  # type: ignore[func-returns-value]
        elements,
        root,
    )


def update_vtype_to_elem(
    elem: ET.Element, params: dict[str, str]
) -> Optional[ET.Element]:
    return update_sub_elem(elem, "vType", params)


def to_attrs(mandatory: dict[str, str], optional: dict[str, str]) -> dict[str, str]:
    attrs = mandatory.copy()
    attrs.update({k: v for k, v in optional.items() if v is not None})
    return attrs


def generate_empty_sumocfg() -> ET.Element:
    configuration = create_elem(
        "configuration",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/sumoConfiguration.xsd",
        },
    )

    return create_sub_elem(configuration, "input")


def generate_sumocfg(
    net_file: str, rou_file: Optional[str] = None, add_files: list[str] = []
) -> ET.Element:
    sumo_cfg = generate_empty_sumocfg()
    input_elem = sumo_cfg.find("input")

    if input_elem is None:
        raise RuntimeError("SUMO config is not well configured")

    input_elem = create_sub_elem(input_elem, "net-file", {"value": net_file})

    if rou_file:
        input_elem = create_sub_elem(input_elem, "route-files", {"value": rou_file})

    if add_files:
        input_elem = create_sub_elem(
            input_elem, "additional-files", {"value": ", ".join(add_files)}
        )

    return sumo_cfg


def generate_empty_add() -> ET.Element:
    return create_elem(
        "additional",
        {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/additional_file.xsd",
        },
    )


def print_elem(elem: ET.Element) -> None:
    print(ET.tostring(elem, encoding="unicode", method="xml"))


def write_xml_to_file(xml_element: ET.Element, filename: str) -> None:
    tree = ET.ElementTree(xml_element)
    tree.write(filename, encoding="utf-8", xml_declaration=True)


def write_formated_xml_to_file(xml_element: ET.Element, filename: str) -> None:
    rough_string = ET.tostring(xml_element, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="  "))
