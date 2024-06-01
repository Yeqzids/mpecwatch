# MPEC Watch

[MPEC Watch](https://sbnmpc.astro.umd.edu/mpecwatch/index.html) provides various statistical metrics and plots derived from the Minor Planet Center's Minor Planet Electronic Circular service. The project is inspired by [MPEC statistics](http://mpec.jostjahn.de) by Jost Jahn.

## Individual_OMF
This script is used to generate the figures (OMF: Obersers, Measurers, and Facilities) for individual observatories. 

## Overall_OMF
This script is used to generate the figures (OMF: Obersers, Measurers, and Facilities) for the congergation of ALL observatories.

## StationMPECGraph
This is the main script used to generate the webpages for each of the stations. This depends on Individual_OMF having been run first since it pulls the figures from the output of that script.

## Acknowledgment

This project makes use of [Bootstrap](https://getbootstrap.com/), [Bootstrap Table](https://bootstrap-table.com/), data provided by the [International Astronomical Union's Minor Planet Center](https://minorplanetcenter.net/).

## Author

* [Quanzhi Ye](https://www.astro.umd.edu/~qye/)
* Taegon Hibbitts
