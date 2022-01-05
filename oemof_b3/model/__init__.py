import os

from oemoflex.tools.helpers import load_yaml


here = os.path.dirname(os.path.abspath(__file__))

component_attrs_update = load_yaml(os.path.join(here, "component_attrs_update.yml"))

bus_attrs_update = load_yaml(os.path.join(here, "bus_attrs_update.yml"))

foreign_keys_update = load_yaml(os.path.join(here, "foreign_keys_update.yml"))

foreign_key_descriptors_update = load_yaml(
    os.path.join(here, "foreign_key_descriptors_update.yml")
)

facade_attsr_update = os.path.join(here, "facade_attrs")
