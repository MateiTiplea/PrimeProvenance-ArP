<div align="center">

  <h1>ArP - Artwork Provenance</h1>
  
  <p>
    A semantic web platform for modeling and managing the provenance of artistic works
  </p>

<!-- Badges -->
<p>
  <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/MateiTiplea/PrimeProvenance-ArP" alt="contributors" />
  </a>
  <a href="">
    <img src="https://img.shields.io/github/last-commit/MateiTiplea/PrimeProvenance-ArP" alt="last update" />
  </a>
  <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/network/members">
    <img src="https://img.shields.io/github/forks/MateiTiplea/PrimeProvenance-ArP" alt="forks" />
  </a>
  <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/stargazers">
    <img src="https://img.shields.io/github/stars/MateiTiplea/PrimeProvenance-ArP" alt="stars" />
  </a>
  <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/issues/">
    <img src="https://img.shields.io/github/issues/MateiTiplea/PrimeProvenance-ArP" alt="open issues" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/github/license/MateiTiplea/PrimeProvenance-ArP.svg" alt="license" />
  </a>
  
</p>

   
<h4>
    <a href="#">View Demo</a>
  <span> · </span>
    <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/wiki">Documentation</a>
  <span> · </span>
    <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/issues/">Report Bug</a>
  <span> · </span>
    <a href="https://github.com/MateiTiplea/PrimeProvenance-ArP/issues/">Request Feature</a>
  </h4>
</div>

<br />

<!-- Table of Contents -->
# :notebook_with_decorative_cover: Table of Contents

- [About the Project](#star2-about-the-project)
  * [Tech Stack](#space_invader-tech-stack)
  * [Features](#dart-features)
- [Getting Started](#toolbox-getting-started)
  * [Prerequisites](#bangbang-prerequisites)
  * [Installation](#gear-installation)
  * [Running Locally](#running-running-locally)
- [Usage](#eyes-usage)
- [Deployment](#rocket-deployment)
- [Roadmap](#compass-roadmap)
- [Contributing](#wave-contributing)
- [License](#warning-license)
- [Contact](#handshake-contact)
- [Acknowledgements](#gem-acknowledgements)

<!-- About the Project -->
## :star2: About the Project

ArP (Artwork Provenance) is a microservice-based web application designed to model and manage the provenance of artistic works. The platform leverages semantic web technologies to query, visualize, and recommend artworks using linked data from DBpedia, Wikidata, and Romanian cultural heritage datasets.

The system exposes statistical information via a SPARQL endpoint and integrates with Getty vocabularies for standardized art terminology.

<!-- Tech Stack -->
### :space_invader: Tech Stack

<details>
  <summary>Backend</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li><a href="https://fastapi.tiangolo.com/">FastAPI</a> - Modern, fast web framework for building APIs</li>
    <li><a href="https://rdflib.readthedocs.io/">RDFLib</a> - Python library for working with RDF</li>
    <li><a href="https://github.com/RDFLib/sparqlwrapper">SPARQLWrapper</a> - SPARQL endpoint interface</li>
  </ul>
</details>

<details>
  <summary>Frontend</summary>
  <ul>
    <li><a href="https://reactjs.org/">React</a> - JavaScript library for building user interfaces</li>
    <li><a href="https://vitejs.dev/">Vite</a> - Next generation frontend tooling</li>
    <li><a href="https://tailwindcss.com/">Tailwind CSS</a> - Utility-first CSS framework</li>
  </ul>
</details>

<details>
  <summary>Database</summary>
  <ul>
    <li><a href="https://jena.apache.org/documentation/fuseki2/">Apache Jena Fuseki</a> - SPARQL server and RDF triplestore</li>
  </ul>
</details>

<details>
  <summary>DevOps</summary>
  <ul>
    <li><a href="https://www.docker.com/">Docker</a> - Containerization platform</li>
    <li><a href="https://docs.docker.com/compose/">Docker Compose</a> - Multi-container orchestration</li>
    <li><a href="https://railway.app/">Railway</a> - Cloud deployment platform</li>
  </ul>
</details>

<!-- Features -->
### :dart: Features

- Query artwork provenance data using SPARQL
- Integration with DBpedia, Wikidata, and Getty vocabularies
- RDF-based knowledge modeling
- Valid HTML5 with schema.org and RDFa markup
- Shareable resource URLs and QR codes
- RESTful API with OpenAPI documentation

<!-- Getting Started -->
## :toolbox: Getting Started

<!-- Prerequisites -->
### :bangbang: Prerequisites

This project uses Docker and Docker Compose for containerization. Make sure you have them installed:

- [Docker](https://docs.docker.com/get-docker/) (version 20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (version 2.0+)

For local development without Docker:

- [Python](https://www.python.org/downloads/) (version 3.11+)
- [Node.js](https://nodejs.org/) (version 18+)
- [npm](https://www.npmjs.com/) or [yarn](https://yarnpkg.com/)

<!-- Installation -->
### :gear: Installation

Clone the repository

```bash
git clone https://github.com/MateiTiplea/PrimeProvenance-ArP.git
cd PrimeProvenance-ArP
```

<!-- Running Locally -->
### :running: Running Locally

Start all services using Docker Compose

```bash
docker-compose up --build
```

The services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **SPARQL Endpoint**: http://localhost:3030

<!-- Usage -->
## :eyes: Usage

_Usage examples and code snippets will be added as the project develops._

<!-- Deployment -->
## :rocket: Deployment

This project is configured for deployment on [Railway](https://railway.app/).

To deploy:

1. Connect your GitHub repository to Railway
2. Configure environment variables in Railway dashboard
3. Deploy the application

_Detailed deployment instructions will be added._

<!-- Roadmap -->
## :compass: Roadmap

- [ ] Project setup and architecture design
- [ ] Core RDF data model and ontology
- [ ] SPARQL endpoint integration
- [ ] REST API implementation
- [ ] Web client with RDFa markup
- [ ] Integration with DBpedia/Wikidata
- [ ] Getty Vocabularies integration
- [ ] Romanian Heritage data import
- [ ] Recommendation engine
- [ ] QR code generation
- [ ] Cloud deployment
- [ ] Documentation and technical report

<!-- Contributing -->
## :wave: Contributing

Contributions are always welcome!

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

<!-- License -->
## :warning: License

Distributed under the MIT License. See `LICENSE` for more information.

Content and data are distributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `LICENSE-DATA` for more information.

<!-- Contact -->
## :handshake: Contact

Project Link: [https://github.com/MateiTiplea/PrimeProvenance-ArP](https://github.com/MateiTiplea/PrimeProvenance-ArP)

<!-- Acknowledgements -->
## :gem: Acknowledgements

- [WADe Course](https://profs.info.uaic.ro/sabin.buraga/teach/courses/wade/) - Web Application Development
- [DBpedia](https://www.dbpedia.org/)
- [Wikidata](https://www.wikidata.org/)
- [Getty Vocabularies](https://vocab.getty.edu/)
- [Europeana](https://www.europeana.eu/)
- [Awesome README Template](https://github.com/Louis3797/awesome-readme-template)

---

<div align="center">
  <p>Tags: <code>project</code> <code>infoiasi</code> <code>wade</code> <code>web</code></p>
</div>
