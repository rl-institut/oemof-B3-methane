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

This model was developed to implement a simplified model of a PEM electrolszer for energy system optimization with oemof.solph. 

Concept
=======

- scheme
- process description
- table with symbols

.. figure:: _pics/PEMEL.png
	:align: center
	:width: 30%

	Fig. 1: Simple diagram of an proton exchange membrane electrolyser.

Die PEM-Elektrolyse nutzt eine protonenleitende Membran, die beidseitig meist fest mit den Elektroden verbunden ist. 
Bipolare Platten leiten das Wasser zur Anode und ermöglichen den Abtransport der Produktgase. An der Anode wird das 
Wasser in Sauerstoff und Protonen aufgespalten. Die Protonen diffundieren durch die Membran zu Kathode und regieren 
dort mit zwei Elektronen zu Wasserstoff. :cite:`Sterner2017`

Assumptions
-----------

Formulas
--------
For a simple calculation of the energy consumption and the amount of water needed as well as hydrogen and oxygen produced,
the following approach is applied.

.. math::
	\begin{align}
		E & = \frac{m_{H_2} \cdot HHV_{H_2}}{\eta} \\
		m_{H_2} & = \frac{\eta \cdot E}{HHV_{H_2}}
	\end{align}

with :math:`E = P \cdot t`



