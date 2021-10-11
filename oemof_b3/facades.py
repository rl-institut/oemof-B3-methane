from oemof.solph import Bus, Flow, Sink, Transformer, sequence
from oemof.solph.components import GenericStorage
from oemoflex.facades import TYPEMAP, Facade


class MethanisationReactor(Transformer, Facade):
    r"""A methanisation reactor that transforms e.g. H2 and CO2 to CH4.

    Note that investment is currently not implemented for this facade.

    Parameters
    ----------



    The reactor is modelled as two storages connected by a transformer with a fixed flow:

    .. math::

    Examples
    --------
    Basic usage example of the MethanisationReactor class with arbitrary values for the parameters.

    >>> from oemof import solph
    >>> from oemof_b3 import facades
    >>> bus_h2 = solph.Bus('h2')
    >>> bus_co2 = solph.Bus('hco2')
    >>> bus_ch4 = solph.Bus('ch4')
    >>> m_reactor = MethanisationReactor(
    ...     name='m_reactor',
    ...     carrier='h2_co2',
    ...     tech='methanisation_reactor',
    ...     h2_bus=bus_h2,
    ...     c02_bus=bus_co2,
    ...     ch4_bus=bus_ch4,
    ...     capacity_charge=50,
    ...     capacity_discharge=50,
    ...     efficiency_charge=1,
    ...     efficiency_discharge=1,
    ...     availability=[0.8, 0.7, 0.6],
    ...     # ? storage_capacity_a=1000,
    ...     # ? storage_capacity_b=1000,
    ...     # ? initial_storage_level_a=0,
    ...     # ? initial_storage_level_b=0,
    ...     # ? min_storage_level_a=[0.1, 0.2, 0.15],
    ...     # ? max_storage_level_a=[0.9, 0.95, 0.92],
    ...     # ? min_storage_level_b=[0.1, 0.2, 0.15],
    ...     # ? max_storage_level_b=[0.9, 0.95, 0.92],
    ...     methanisation_rate=[0.3, 0.2, 0.5],
    ...     efficiency_methanisation=0.93
    ...     )
    """

    def __init__(self, *args, **kwargs):

        kwargs.update(
            {
                "_facade_requires_": [
                    "h2_bus",
                    "co2_bus",
                    "ch4_bus",
                    "carrier",
                    "tech",
                ]
            }
        )
        super().__init__(*args, **kwargs)

        self.capacity_charge = kwargs.get("capacity_charge")

        self.capacity_discharge = kwargs.get("capacity_discharge")

        self.efficiency_charging = kwargs.get("efficiency_charging", 1)

        self.efficiency_discharging = kwargs.get("efficiency_discharging", 1)

        self.methanisation_rate = kwargs.get("methanisation_rate")

        self.efficiency_methanisation = kwargs.get("efficiency_methanisation")

        self.marginal_cost = kwargs.get("marginal_cost", 0)

        self.input_parameters = kwargs.get("input_parameters", {})

        self.output_parameters = kwargs.get("output_parameters", {})

        self.expandable = bool(kwargs.get("expandable", False))

        self.build_solph_components()

    def build_solph_components(self):

        if self.expandable:
            raise NotImplementedError("Investment for bev class is not implemented.")

        storage_educts = GenericStorage(
            carrier=self.carrier,
            tech=self.tech,
            label=self.label + "-storage_educts",
            inflow_conversion_factor=self.efficiency_charging,
            nominal_storage_capacity=1000,
        )

        combine_educts = Transformer(
            carrier=self.carrier,
            tech=self.tech,
            label=self.label + "-combine-educts",
            inputs={
                self.h2_bus: Flow(),
                self.co2_bus: Flow(),
            },
            outputs={
                storage_educts: Flow(
                    nominal_value=self.capacity_charge, **self.input_parameters
                )
            },
            conversion_factors={self.co2_bus: 0.2, self.h2_bus: 0.8},
        )

        storage_products = GenericStorage(
            carrier=self.carrier,
            tech=self.tech,
            label=self.label + "-storage_products",
            outputs={
                self.ch4_bus: Flow(
                    nominal_value=self.capacity_discharge,
                    variable_cost=self.marginal_cost,
                    **self.output_parameters
                )
            },
            outflow_conversion_factor=self.efficiency_discharging,
            nominal_storage_capacity=1000,
        )

        self.inputs.update({storage_educts: Flow()})

        self.outputs.update(
            {storage_products: Flow(nominal_value=self.methanisation_rate)}
        )

        self.conversion_factors = {
            storage_educts: sequence(1),
            storage_products: sequence(self.efficiency_methanisation),
        }

        self.subnodes = (combine_educts, storage_educts, storage_products)


TYPEMAP.update(
    {
        "methanisation_reactor": MethanisationReactor,
    }
)
