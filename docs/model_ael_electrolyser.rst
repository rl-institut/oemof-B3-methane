.. _model_ael_electrolyser:

~~~~~~~~~~~~~~~~
AEL Electrolyser
~~~~~~~~~~~~~~~~

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
	:width: 20%

	Fig. 1: Simple diagram of an alkaline electrolyser.

Die alkalische Elektrolyse ist die ausgereifteste Technologie der drei Arten. Es wird ein flüssiger Elektrolyt (Kaliumhydroxidlösung) 
sowie eine ionenleitende Membran verwendet. Durch die Zugabe von Kaliumhydroxid wird die Leitfähigkeit von Wasser erhöht. An der Kathode 
wird Wasser in Wasserstoff und Hydroxid-Ionen aufgespalten. Der Wasserstoff steigt auf und kann abgeschieden werden. Die Ionen diffundieren 
durch die Membran und reagieren an der Anode unter Abgabe von Elektronen zu Wasser und Sauerstoff. Bei hohen Lasten ist eine aktive Umwälzung 
des Elektrolyten erforderlich, damit eine ausreichende Zirkulation des Elektrolyten gewährleistet wird. :cite:`Sterner2017`

Assumptions
-----------

Formulas
--------
