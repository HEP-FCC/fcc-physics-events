# FCC Physics Events

> [!IMPORTANT]  
> This is archived version of the website, currently the website source code is based on
> [Universal Metadata Browser Template](https://github.com/HEP-FCC/umb-template) which is adapted
> [here](https://gitlab.cern.ch/hep-fcc/fcc-physics-events).

Database of pre-generated samples for FCC-hh and FCC-ee physics performance
studies.

## Website hierarchy

The website has four possible hierarchy levels. Depending on the type of the
events it is either:

* Accelerator --- FCC-hh or FCC-ee
* Event type --- Gen, Delphes, Full Sim
* Campaign --- spring2021, winter2023, ...
* Detector --- CLD, IDEA, ...
or:
* Accelerator --- FCC-hh or FCC-ee
* Event type --- Gen, Delphes, Full Sim
* Generator type --- STDHEP, LesHouches, ...
* Campaign --- spring2021, winter2023, ...

## Local development

Install `php`, for RedHat based distros it is simply:

```sh
dnf install php-cli
```

Run local server:

```sh
php -S localhost:8000
```

## Deployment

Changes to this repo will be reflected in the website within few hours. A cron
job is set up to pick up the latest changes in the master branch.

## Limiting which files are served

To limit the files served by the Apache server `.htaccess` files are employed
across several directories.

## Publishing Dirac samples

To publish a Dirac sample one needs to create an entry for it in "augments" json
file stored in `data` directory.
ATM one can specify following fields:

```txt
name: Name for the sample
cross-section: Cross-section in pb
cross-section-error: Error on cross-section in pb
efficiency: Used to adjust sample cross-section
efficiency-info: Info about the adjustment
```

To update the sample database use `bin/generate_samples_db`. The database is
also updated every hour using cron.
