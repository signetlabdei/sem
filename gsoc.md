---
title: "A Simulation Execution Manager for ns-3"
---

A Google Summer of Code 2018 project.

Developed by Davide Magrin under the mentorship of Dizhi Zhou for the
[ns-3](https://www.nsnam.org) project.

------------------------------------------------------------------------

### Objective ###

The aim of this project is to provide a way for users of the ns-3 Network
Simulator to easily manage simulation campaigns, going from running simulation
scripts to visualizing results in as few steps as possible.

While it's very easy to run ns-3 simulations, up to now there was no
ready-to-use solution for running multiple simulations to extract statistically
meaningful results. ns-3 users had to rely on custom-written scripts, leading to
duplicated effort and solutions that were difficult to share with others due to
their customization.

With this GSoC project, I hope to have laid down the foundation for a more
collaborative effort on part of the ns-3 community, and to have made some steps
of ns-3 use easier for newcomers.

Further details on the scope and motivation of the project can be found
in the original [GSoC proposal](resources/GSoC_proposal.pdf).

### Code and documentation ###

A [Github repo](https://github.com/DvdMgr/sem) was used to host all the work
that was completed during the GSoC period. The state of the repository at the
end GSoC can be accessed at the
[gsoc-final](https://github.com/DvdMgr/sem/tree/gsoc-final) git tag. Similarly,
tags named gsoc-week2 through gsoc-week13 track the progress for each week.
Aside from a [pull request](https://github.com/DvdMgr/sem/pull/15) merged in
week 12, all code in the repository was written by Davide Magrin.

Documentation for the project is hosted at
[ReadTheDocs](https://simulationexecutionmanager.readthedocs.io).

Build status can be checked through [Travis CI](https://travis-ci.org/DvdMgr/sem).

#### Quick install ####

The developed program can be installed through pip:

```
pip install https://github.com/DvdMgr/sem/archive/gsoc-final.zip
```

To get started using the command line interface, just run:

```
sem --help
```

### State of the project ###

All features of the original proposal were fully developed. Additionally, a
command line interface for the library was also added. A detailed history of the
progress was kept at [the project's ns-3 wiki
page](https://www.nsnam.org/wiki/GSoC2018:_A_Simulation_Execution_Manager_for_ns-3).

Additional items that came up (and are not essential to the core functionality
of the library) were converted to [Github
Issues](https://github.com/DvdMgr/sem/issues) and tagged with the enhancement
label. I plan to keep working on these items in my spare time.

Finally, I want to note that, since the developed code has already become part
of my workflow when using ns-3, I plan to keep developing the library as main
contributor as long as I will work with ns-3 (at least a couple more years,
until completion of my PhD, and maybe beyond that point).

### Things I've learned ###

Technologies and workflows I got to learn more about during the GSoC period
include:

- Tools for Python project management and development;
- Open source project maintenance:
  - Working with pull requests;
  - Managing issues;
  - Coordinating contributors.
- Thorough testing practices;
- Usage of continuous integration tools;
- The DRMAA API;
- Usage of various Python libraries.
