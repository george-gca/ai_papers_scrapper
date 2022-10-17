# AI Papers Scrapper

Download papers pdfs and other information from main AI conferences (when public available) and store it on `./data/`, creating one directory per conference, and one per year. More specifically, it creates the following structure:

    .
    └── data
        └── conf
            └── year
                ├── abstracts.csv       # format `title|abstract`
                ├── authors.csv         # format `title;authors`
                ├── paper_info.csv      # format `title;abstract_url;pdf_url`
                └── papers
                    ├── paper01.pdf     # pdf file from a paper
                    ├── paper02.pdf
                    ├── ...
                    └── paperN.pdf

Currently supports the following conferences, from 2017 and on:

| Source | Conferences |
| --- | --- |
| [AAAI Library](https://www.aaai.org/Library/AAAI/aaai-library.php) | AAAI |
| [ACL Anthology](https://aclanthology.org/) | ACL, COLING (even years), EACL (odd years, except 2019), EMNLP, Findings (2020 and on), IJCNLP (odd years), NAACL (except 2017 and 2020), SIGDIAL, TACL |
| [European Computer Vision Association](https://www.ecva.net/papers.php) | ECCV (even years) |
| [International Joint Conferences on Artificial Intelligence Organization](www.ijcai.org/) | IJCAI |
| [KDD](https://kdd.org/) | SIGKDD (abstracts only) |
| [Proceedings of Machine Learning Research](http://proceedings.mlr.press/) | ICML |
| [NeurIPS Proceedings](https://proceedings.neurips.cc/) | NeurIPS |
| [NeurIPS Datasets and Benchmarks Proceedings](https://datasets-benchmarks-proceedings.neurips.cc/) | NeurIPS Track on Datasets and Benchmarks (2021) |
| [OpenReview](https://openreview-py.readthedocs.io/en/latest/) | ICLR |
| [SIGCHI](https://st.sigchi.org/) | SIGCHI (2018 and on, abstracts only) |
| [ The Computer Vision Foundation open access](https://openaccess.thecvf.com/) | CVPR, ICCV (odd years), WACV (2020 and on) |

## Requirements

[Docker](https://www.docker.com/) or, for local installation:

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/)

## Usage

To make it easier to run the code, with or without Docker, I created a few helpers. Both ways use `start_here.sh` as an entry point. Since there are a few quirks when calling the scrappers, I created this file with all the necessary commands to run the code. All you need to do is to uncomment the relevant lines inside the `conferences` array and run the script.

### Running without Docker

You first need to install [Python Poetry](https://python-poetry.org/docs/). Then, you can install the dependencies and run the code:

```bash
poetry install
bash start_here.sh
```

### Running with Docker

To help with the Docker setup, I created a `Dockerfile` and a `Makefile`. The `Dockerfile` contains all the instructions to create the Docker image. The `Makefile` contains the commands to build the image, run the container, and run the code inside the container. To build the image, simply run:

```bash
make
```

To call `start_here.sh` inside the container, run:

```bash
make run
```
