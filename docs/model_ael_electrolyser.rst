.. _model_ael_electrolyser:

~~~~~~~~~~~~~~~~~~~~~
Alkaline Electrolyser
~~~~~~~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top
	
Scope
=====

This model was developed to implement a simplified model of an AEL electrolyser for energy system optimization with oemof.solph. 

Concept
=======

- scheme
- process description
- table with symbols

.. figure:: _pics/AEL.png
	:align: center
	:width: 50%

	Fig. 1: Simple diagram of an alkaline electrolyser.

The alkaline elektrolysis is the most mature technology among electrolysers. A liquid electrolyt (potassium hydroxide solution) as well as a ion-conducting membrane.
The addition of potassium hydroxide increases the conductivity of water. At the cathode, water is split into hydrogen and hydroxide ions. 
The hydrogen rises and can be separated. The ions diffuse through the membrane and react at the anode, releasing electrons to form water 
and oxygen. At high loads, active circulation of the electrolyte is necessary to ensure sufficient circulation of the electrolyte. :cite:`Sterner2017`

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

