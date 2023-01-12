.. _model_pem_electrolyser:

~~~~~~~~~~~~~~~~
PEM Electrolyser
~~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top
	
Scope
=====

This model was developed to implement a simplified model of a PEM electrolyser for energy system optimization with oemof.solph. 

Concept
=======

- scheme
- process description
- table with symbols

.. figure:: _pics/PEMEL.png
	:align: center
	:width: 50%

	Fig. 1: Simple diagram of an proton exchange membrane electrolyser.

PEM electrolysis uses a proton-conducting membrane that is usually firmly connected to the electrodes on both sides. 
Bipolar plates guide the water to the anode and enable the separation of the product gases. At the anode, the water is 
split into oxygen and protons. The protons diffuse through the membrane to the cathode, where they react with two 
electrons to form hydrogen. :cite:`Sterner2017`

Assumptions
-----------

Formulas
--------
For a simple calculation of the energy consumption and the amount of water needed as well as hydrogen and oxygen produced,
the following approach is applied.

.. math::
	\begin{align}
		\eta & = \frac{m_{H_2} \cdot HHV_{H_2}}{E}
	\end{align}

with :math:`E = P \cdot t`



