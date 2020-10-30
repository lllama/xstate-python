import xml.etree.ElementTree as ET
from typing import Optional
import json

from xstate.machine import Machine

ns = {"scxml": "http://www.w3.org/2005/07/scxml"}


def convert_scxml(element: ET.Element, parent):
    states = element.findall("scxml:state", namespaces=ns)
    state_els = element.findall("scxml:state", namespaces=ns)

    initial_state_key = element.attrib.get(
        "initial", convert_state(state_els[0], parent=element).get("key")
    )

    return {
        "id": "machine",
        "initial": initial_state_key,
        "states": accumulate_states(element, parent),
    }


def accumulate_states(element: ET.Element, parent: ET.Element):
    state_els = element.findall("scxml:state", namespaces=ns)
    states = [convert_state(state_el, element) for state_el in state_els]

    states_dict = {}

    for state in states:
        states_dict[state.get("key")] = state

    return states_dict


def convert_state(element: ET.Element, parent: ET.Element):
    parent_id = parent.attrib.get("id", "") if parent else None
    id = element.attrib.get("id")
    transition_els = element.findall("scxml:transition", namespaces=ns)
    transitions = [convert_transition(el, element) for el in transition_els]

    state_els = element.findall("scxml:state", namespaces=ns)
    states = {el.attrib.get("id"): convert_state(el, element) for el in state_els}

    onexit_el = element.find("scxml:onexit", namespaces=ns)
    onexit = convert_onexit(onexit_el, parent=element) if onexit_el else None
    onentry_el = element.find("scxml:onentry", namespaces=ns)
    onentry = convert_onentry(onentry_el, parent=element) if onentry_el else None

    result = {
        "id": f"{id}",
        "key": id,
        "exit": onexit,
        "entry": onentry,
        "states": states,
        "initial": state_els[0].attrib.get("id") if state_els else None,
    }

    if len(transitions) > 0:
        transitions_dict = {}

        for t in transitions:
            transitions_dict[t.get("event")] = t

        result["on"] = transitions_dict

    return result


def convert_transition(element: ET.Element, parent: ET.Element):
    event_type = element.attrib.get("event")
    event_target = element.attrib.get("target")

    raise_els = element.findall("scxml:raise", namespaces=ns)

    actions = [convert_raise(raise_el, element) for raise_el in raise_els]

    return {"event": event_type, "target": ["#%s" % event_target], "actions": actions}


def convert_raise(element: ET.Element, parent: ET.Element):
    return {"type": "xstate:raise", "event": element.attrib.get("event")}


def convert_onexit(element: ET.Element, parent: ET.Element):
    raise_els = element.findall("scxml:raise", namespaces=ns)
    actions = [convert_raise(raise_el, element) for raise_el in raise_els]

    return actions


def convert_onentry(element: ET.Element, parent: ET.Element):
    raise_els = element.findall("scxml:raise", namespaces=ns)
    actions = [convert_raise(raise_el, element) for raise_el in raise_els]

    return actions


def convert(element: ET.Element, parent: Optional[ET.Element] = None):
    _, _, element_tag = element.tag.rpartition("}")  # strip namespace
    result = elements.get(element_tag, lambda _: f"Invalid tag: {element_tag}")

    return result(element, parent)


elements = {"scxml": convert_scxml, "state": convert_state}


def scxml_to_machine(source: str) -> Machine:
    tree = ET.parse(source)
    root = tree.getroot()
    result = convert(root)
    machine = Machine(result)

    return machine
