from oemof.solph import Bus, Flow, Sink, Transformer, sequence
from oemoflex.facades import TYPEMAP, Facade


class MethanisationReactor(Facade):
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
    >>> bus_h2_co2 = solph.Bus('h2_co2')
    >>> bus_ch4 = solph.Bus('ch4')
    >>> m_reactor = MethanisationReactor(
    ...     name='m_reactor',
    ...     carrier='h2_co2',
    ...     tech='methanisation_reactor',
    ...     from_bus=bus_h2_co2,
    ...     to_bus=bus_ch4,
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
                    "bus",
                    "carrier",
                    "tech",
                ]
            }
        )
        super().__init__(*args, **kwargs)

        self.build_solph_components()

    def build_solph_components(self):

        if self.expandable:
            raise NotImplementedError("Investment for bev class is not implemented.")


TYPEMAP.update(
    {
        "methanisation_reactor": MethanisationReactor,
    }
)
