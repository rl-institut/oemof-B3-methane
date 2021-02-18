.. _model_methanisation_storage_electrolyzer:

~~~~~~~~~~~~~~~~~~~~~
Methanisation Storage
~~~~~~~~~~~~~~~~~~~~~

.. contents:: `Contents`
    :depth: 1
    :local:
    :backlinks: top
	
Scope
=====

This model was developed to implement a simplified model of a methanisation storage for energy system optimization with oemof.solph. 

Concept
=======

- scheme
- process description
- table with symbols

.. figure:: _pics/Speichermodell_2.png
	:align: center
	
	Fig. 1: Model of the underground storage.
	
The underground storage (UGS) serves as a reactor for biological methanation and as a storage facility for the methane produced. 
In a first step, the reactants hydrogen and carbon dioxide are fed into the UGS. In the process of biological methanisation, 
archaea process the reactants into the products methane and water during their anaerobic metabolisation.
The methane is stored in the UGS and can be extracted as needed.

Assumptions
-----------

Formulas
--------
