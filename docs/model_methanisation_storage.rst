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
	
Der Untergrundspeicher (UGS) dient als Reaktor für die biologische Methanisierung sowie als Speicher des produzierten Methans.
In einem ersten Schritt werden die Edukte Wasserstoff und Kohlenstoffdioxid in den UGS geleitet. Im Prozess der biologischen Methanisierung 
verwerten Archaeen während ihrer anaeroben Metabolisierung die Edukte in die Produkte Methan und Wasser.
Das Methan wird im UGS gespeichert und kann bei Bedarf entnommen werden.

Assumptions
-----------

Formulas
--------
