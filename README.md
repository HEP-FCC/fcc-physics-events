# FCC Physics Events

Database of pre-generated samples for FCC-hh and FCC-ee physics performance
studies.

## Website hierarchy

The website has four possible hierarchy levels. From top to bottom they are:
* Accelerator --- FCC-hh or FCC-ee
* Event type --- Gen, Delphes, Full Sim
* Campaign
* Detector

## Local development

Install `php`:
```
dnf install php-cli
```

Run local server:
```
php -S localhost:8000
```


## Deployment

Changes to this repo will be reflected in the website within few hours. A cron
job is set up to pick up the latest changes in the master branch.


## Limiting which files are served

To limit the files served by the Apache server `.htaccess` file is employed in
several directories.
