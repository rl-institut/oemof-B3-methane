from oemof.solph import Flow, Transformer, sequence, NonConvex
from oemof.solph.components import GenericStorage
from oemoflex.facades import TYPEMAP, Facade


class GenericStorage(GenericStorage):
    r"""
    Supplement GenericStorage with carrier and tech properties to work with labeling in
    postprocessing.

    Needed for GenericStorage subnodes in MethanationReactor
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.carrier = kwargs.get("carrier", None)
        self.tech = kwargs.get("tech", None)


class Transformer(Transformer):
    r"""
    Supplement Transformer with carrier and tech properties to work with labeling in postprocessing.

    Needed for Transformer subnodes in MethanationReactor
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.carrier = kwargs.get("carrier", None)
        self.tech = kwargs.get("tech", None)


class MethanationReactor(Transformer, Facade):
    r"""A methanation reactor that transforms e.g. H2 and CO2 to CH4.

    Note that investment is currently not implemented for this facade.

    Parameters
    ----------
    h2_bus : oemof.solph.Bus
    co2_bus : oemof.solph.Bus
    ch4_bus : oemof.solph.Bus
    carrier : str
    tech : str
    capacity_charge : numeric
    capacity_discharge : numeric
    storage_capacity_educts : numeric
    storage_capacity_products : numeric
    efficiency_charge : numeric
    efficiency_discharge : numeric
    methanation_rate : numeric
    efficiency_methanation : numeric
    marginal_cost : numeric
    input_parameters : numeric
    output_parameters : numeric
    expandable : boolean
    methanation_option : str

    The reactor is modelled as two storages connected by a transformer with a fixed flow:

    .. math::

    Examples
    --------
    Basic usage example of the MethanationReactor class with arbitrary values for the parameters.

    >>> from oemof import solph
    >>> from oemof_b3 import facades
    >>> bus_h2 = solph.Bus('h2')
    >>> bus_co2 = solph.Bus('hco2')
    >>> bus_ch4 = solph.Bus('ch4')
    >>> m_reactor = MethanationReactor(
    ...     name='m_reactor',
    ...     carrier='h2_co2',
    ...     tech='methanation_reactor',
    ...     h2_bus=bus_h2,
    ...     co2_bus=bus_co2,
    ...     ch4_bus=bus_ch4,
    ...     capacity_charge=50,
    ...     capacity_discharge=50,
    ...     storage_capacity_educts=100,
    ...     storage_capacity_products=1000,
    ...     efficiency_charge=1,
    ...     efficiency_discharge=1,
    ...     availability=[0.8, 0.7, 0.6],
    ...     methanation_rate=[0.3, 0.2, 0.5],
    ...     efficiency_methanation=0.93
    ...     )
    """
    MIX_RATIO_CO2 = 0.139  # tCO2/MWh_H2
    MIX_RATIO_H2 = 1
    MIN_FLOW = 0.2

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

        self.storage_capacity_educts = kwargs.get("storage_capacity_educts")

        self.storage_capacity_products = kwargs.get("storage_capacity_products")

        self.efficiency_charge = kwargs.get("efficiency_charge", 1)

        self.efficiency_discharge = kwargs.get("efficiency_discharge", 1)

        self.methanation_rate = kwargs.get("methanation_rate")

        self.efficiency_methanation = kwargs.get("efficiency_methanation")

        self.marginal_cost = kwargs.get("marginal_cost", 0)

        self.input_parameters = kwargs.get("input_parameters", {})

        self.output_parameters = kwargs.get("output_parameters", {})

        self.expandable = bool(kwargs.get("expandable", False))

        self.methanation_option = kwargs.get("methanation_option", 0)

        self.nonconvex = kwargs.get("nonconvex", False)

        self.build_solph_components()

    def build_solph_components(self):

        if self.expandable:
            raise NotImplementedError(
                "Investment for methanation class is not implemented."
            )

        storage_educts = GenericStorage(
            carrier=self.carrier,
            tech=self.tech,
            label=self.label + "-storage_educts",
            inflow_conversion_factor=self.efficiency_charge,
            nominal_storage_capacity=self.storage_capacity_educts,
            loss_rate=0,
        )

        if self.nonconvex:
            self.input_parameters.update(
                {
                    "min": self.MIN_FLOW,
                    "nonconvex": NonConvex(),
                }
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
            conversion_factors={
                self.co2_bus: self.MIX_RATIO_CO2,
                self.h2_bus: self.MIX_RATIO_H2,
            },
        )

        if self.nonconvex:
            self.output_parameters.update(
                {
                    "min": self.MIN_FLOW,
                    "nonconvex": NonConvex(),
                }
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
            outflow_conversion_factor=self.efficiency_discharge,
            nominal_storage_capacity=self.storage_capacity_products,
        )

        self.inputs.update({storage_educts: Flow()})

        methanation_implementation = {}
        # 0. No constraints on methanation
        methanation_implementation["no_constraints"] = {storage_products: Flow()}
        # 1. Fixed methanation rate
        methanation_implementation["fixed_rate"] = {
            storage_products: Flow(
                fixed=True,
                fix=sequence(1),
                nominal_value=self.methanation_rate,
            )
        }
        # 2. Methanation rate can be optimized
        methanation_implementation["variable_rate"] = {
            storage_products: Flow(nominal_value=self.methanation_rate)
        }
        # 3. Methanation rate can be optimized and has a "minimum load".
        methanation_implementation["variable_rate_with_min"] = {
            storage_products: Flow(
                nominal_value=self.methanation_rate,
                min=0.5,
                nonconvex=NonConvex(),
            )
        }
        # 4. Methanation rate can be optimized,
        # has a "minimum load" and constraints on ramping up and down
        methanation_implementation["variable_rate_with_min_and_ramping"] = {
            storage_products: Flow(
                nominal_value=self.methanation_rate,
                min=0.1,
                positive_gradient={"ub": 0.01},
                negative_gradient={"ub": 0.01},
            )
        }
        # 5. Methanation rate can be optimized
        # and has constraints on ramping up and down
        methanation_implementation["variable_rate_with_ramping"] = {
            storage_products: Flow(
                nominal_value=self.methanation_rate,
                positive_gradient={"ub": 0.01},
                negative_gradient={"ub": 0.05},
            )
        }
        # 6. Methanation rate depends on available educts but is constrained by active
        # reactor volume.
        # TODO: Linear dependency on storage level (via extra constraint?)

        self.outputs.update(methanation_implementation[self.methanation_option])

        self.conversion_factors = {
            storage_educts: sequence(1),
            storage_products: sequence(self.efficiency_methanation),
        }

        self.subnodes = (combine_educts, storage_educts, storage_products)


TYPEMAP.update(
    {
        "methanation_reactor": MethanationReactor,
    }
)
