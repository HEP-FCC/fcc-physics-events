# FCC Physics Events

Specific deployment of the [umb-template](https://github.com/HEP-FCC/umb-template) for the metadata of the FCC physics datasets.

## 📦 Repository

The canonical repository is on GitHub: [HEP-FCC/fcc-physics-events](https://github.com/HEP-FCC/fcc-physics-events). It is pull-mirrored to [CERN GitLab](https://gitlab.cern.ch/hep-fcc/fcc-physics-events), which runs CI/CD. Please open issues and merge requests on GitHub.

## 🚀 Deployment

This application is automatically deployed after any change to the master branch. Firstly the web application is packaged to 2 docker images called fcc-physics-events-backend and fcc-physics-events-frontend. They are pushed to the CERN's docker registry in the [fcc-physics-events repository](https://registry.cern.ch/harbor/projects/3847/repositories). Then it is deployed to the CERN's PAAS OpenShift cluster in the [fcc-physics-events namespace](https://paas.cern.ch/topology/ns/fcc-physics-events).

For this we need a [Docker Registry robot account](https://registry.cern.ch/harbor/projects/3847/robot-account) with appropriate permissions and [OpenShift service account](https://paas.docs.cern.ch/2._Deploy_Applications/Advanced_Topics/2-serviceaccount/) token which is called `github-actions-deployer` (don't worry about the name).

## 🙏 Acknowledgments

- Developed by [@lexi-k](https://github.com/lexi-k) during the CERN Summer Student Programme 2025
