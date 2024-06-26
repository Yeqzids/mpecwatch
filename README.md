# MPEC Watch

[MPEC Watch](https://sbnmpc.astro.umd.edu/mpecwatch/index.html) provides various statistical metrics and plots derived from the Minor Planet Center's Minor Planet Electronic Circular service. The project is inspired by [MPEC statistics](http://mpec.jostjahn.de) by Jost Jahn.

## Change log

* 2024 Jun 11: observatory table has expanded columns.
* 2024 Jun 1: survey summary page now available; adding recovery stats; adding term definitions.
* 2024 May 30: export options added to individual station yearly breakdown of MPEC types.
* 2024 Apr 5: switching to MPC code list from Bill Gray's digested list to fix update hangs between code additions and Bill's updates.
* 2024 Feb 22: fixed NEA counts.
* 2023 Dec 1: adding time frequency plots (of observations).
* 2023 Oct 20: tables are now searchable; fixed menu count selector.
* 2023 Aug 11: bug fixes -- empty pages, plots and buggy CATCH links.
* 2023 Jul 27: monthly breakdown and CSV tables available.
* 2023 Jul 18: adding CATCH URLs if applicable.
* 2023 Jul 13: tables are now sortable; blank figures are shown if there is no data.
* 2023 Jul 2: added tally numbers to data tables.
* 2023 Jun 25: CSV table available on site pages; also adding tables of observers, measurers and facilities on site pages.
* 2023 Apr 16: fixed broken MPEC URLs.
* 2023 Feb 12: data table now available on site pages.
* 2022 Nov 15: 1st follow-up and follow-up info now available on site pages.
* 2022 Sep 2: adding statistics and graphs for individual sites.
* 2022 Feb 24: adding MPC Stuff page.
* 2022 Jan 25: first release!

## Description of (some) scripts under ./makepages

### Individual_OMF
This script is used to generate the figures (OMF: Obersers, Measurers, and Facilities) for individual observatories. 

### Overall_OMF
This script is used to generate the figures (OMF: Obersers, Measurers, and Facilities) for the congergation of ALL observatories.

### StationMPECGraph
This is the main script used to generate the webpages for each of the stations. This depends on Individual_OMF having been run first since it pulls the figures from the output of that script.

### Acknowledgment

This project makes use of [Bootstrap](https://getbootstrap.com/), [Bootstrap Table](https://bootstrap-table.com/), data provided by the [International Astronomical Union's Minor Planet Center](https://minorplanetcenter.net/).

## Author

* [Quanzhi Ye](https://www.astro.umd.edu/~qye/)
* Taegon Hibbitts
