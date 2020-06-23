# NSIDC-Data-Tutorials

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/nsidc/NSIDC-Data-Tutorial/master?urlpath=lab/tree/notebooks)

[![CircleCI](https://circleci.com/gh/nsidc/NSIDC-Data-Tutorials.svg?style=svg)](https://circleci.com/gh/nsidc/NSIDC-Data-Tutorials)

## Summary

This combined repository includes tutorials and code resources provided by the NASA National Snow and Ice Data Center Distributed Active Archive Center (NSIDC DAAC). These tutorials are provided as Python-based Jupyter notebooks that provide guidance on working with various data products, including how to access, subset, transform, and visualize data. Each tutorial can be accessed by navigating to the /notebooks folder of this repository. Please see the README files associated with each individual tutorial folder for more information on each tutorial and their learning objectives.

## Tutorials

### SnowEx_ASO_MODIS_Snow

Snow Depth and Snow Cover Data Exploration

Originally demonstrated through the NASA Earthdata Webinar "Let It Snow! Accessing and Analyzing Snow Data at the NSIDC DAAC" on May 6, 2020, this tutorial provides guidance on how to discover, access, and couple snow data across varying geospatial scales from NASA's SnowEx, Airborne Snow Observatory, and Moderate Resolution Imaging Spectroradiometer (MODIS) missions. The tutorial highlights the ability to search and access data by a defined region, and combine and compare snow data across different data formats and scales using a Python-based Jupyter Notebook.

### ICESat-2_MODIS_Arctic_Sea_Ice

Getting the most out of NSIDC DAAC data: Discovering, Accessing, and Harmonizing Arctic Remote Sensing Data

Originally presented during the 2019 AGU Fall Meeting, this tutorial demonstrates the NSIDC DAAC's data discovery, access, and subsetting services, along with basic open source resources used to harmonize and analyze data across multiple products. The tutorial is provided as a series of Python-based Jupyter Notebooks, focusing on sea ice height and ice surface temperature data from NASA’s ICESat-2 and MODIS missions, respectively, to characterize Arctic sea ice.

## Usage with Binder

The Binder button above allows you to explore and run the notebook in a shared cloud computing environment without the need to install dependencies on your local machine. Note that this option will not directly download data to your computer; instead the data will be downloaded to the cloud environment.

## Usage with Docker

### On Mac OSX or Linux


1. Install [Docker](https://docs.docker.com/install/). Use the left-hand navigation to select the appropriate install depending on operating system.

2. Download the [NSIDC-Data-Tutorials repository from Github](https://github.com/nsidc/NSIDC-Data-Tutorials/archive/master.zip).

3. Unzip the file, and open a terminal window in the `NSIDC-Data-Tutorials` folder's location.

4. From the terminal window, launch the docker container using the following command, replacing [path/notebook_folder] with your path and notebook folder name:

```bash
docker run --name tutorials -p 8888:8888 -v [path/notebook_folder]:/home/jovyan/work nsidc/tutorials
```

Example:

```bash
docker run --name tutorials -p 8888:8888 -v /Users/name/Desktop/NSIDC-Data-Tutorials:/home/jovyan/work nsidc/tutorials
```

Or, with docker-compose:

```bash
docker-compose up
```

Learn more about using the extra docker-compose files as overrides [here](https://docs.docker.com/compose/extends/).

If you want to mount a directory with write permissions, you need to grant the container the same permissions as the one on the directory to be mounted and tell it that has "root" access (within the container). This is important if you want to persist your work or download data to a local directory and not just the docker container. Run the example command below for this option:

```bash
docker run --name tutorials -e NB_UID=$(id -u) --user root -p 8888:8888 -v  /Users/name/Desktop/NSIDC-Data-Tutorials:/home/jovyan/work nsidc/tutorials
```

The initialization will take some time and will require 2.6 GB of space. Once the startup is complete you will see a line of output similar to this:

```
To access the notebook, open this file in a browser:
        file:///home/jovyan/.local/share/jupyter/runtime/nbserver-6-open.html
    Or copy and paste one of these URLs:
        http://4dc97ddd7a0d:8888/?token=f002a50e25b6f623aa775312737ba8a23ffccfd4458faa6f
     or http://127.0.0.1:8888/?token=f002a50e25b6f623aa775312737ba8a23ffccfd4458faa6f
```

If you started your container with the `-d`/`--detach` option, check `docker logs tutorials` for this output.

5. Open up a web browser and copy one of the URLs as instructed above.

6. You will be brought to a Jupyter Notebook interface running through the Docker container. The left side of the interface displays your local directory structure. Navigate to the **`work`** folder of the `NSIDC-Data-Tutorials` repository folder. You can now interact with the notebooks to explore and access data.


### On Windows

1. Install [Docker](https://docs.docker.com/docker-for-windows/install/).

2. Download the [NSIDC-Data-Tutorials repository from Github](https://github.com/nsidc/NSIDC-Data-Tutorials/archive/master.zip).

3. Unzip the file, and open a terminal window (use Command Prompt or PowerShell, not PowerShell ISE) in the `NSIDC-Data-Tutorials` folder's location.

5. From the terminal window, launch the docker container using the following command, replacing [path\notebook_folder] with your path and notebook folder name:

```bash
docker run --name tutorials -p 8888:8888 -v [path\notebook_folder]:/home/jovyan/work nsidc/tutorials
```

Example:

```bash
docker run --name tutorials -p 8888:8888 -v C:\notebook_folder:/home/jovyan/work nsidc/tutorials
```

Or, with docker-compose:

```bash
docker-compose up
```

Learn more about using the extra docker-compose files as overrides [here](https://docs.docker.com/compose/extends/).

If you want to mount a directory with write permissions you need to grant the container the same permissions as the one on the directory to be mounted and tell it that has "root" access (within the container)

```bash
docker run --name tutorials --user root -p 8888:8888 -v C:\notebook_folder:/home/jovyan/work nsidc/tutorials
```

The initialization will take some time and will require 2.6 GB of space. Once the startup is complete you will see a line of output similar to this:

```
To access the notebook, open this file in a browser:
        file:///home/jovyan/.local/share/jupyter/runtime/nbserver-6-open.html
    Or copy and paste one of these URLs:
        http://(6a8bfa6a8518 or 127.0.0.1):8888/?token=2d72e03269b59636d9e31937fcb324f5bdfd0c645a6eba3f
```

If you started your container with the `-d`/`--detach` option, check `docker logs tutorials` for this output.

6. Follow the instructions and copy one of the URLs into a web browser and hit return. The address should look something like this:

`http://127.0.0.1:8888/?token=2d72e03269b59636d9e31937fcb324f5bdfd0c645a6eba3f`

7. You will now see the NSIDC-Data-Tutorials repository within the Jupyter Notebook interface. Navigate to **/work** to open the notebooks.

8. You can now interact with the notebooks to explore and access data.

## Usage with Conda

Install miniconda3 (Python 3.7) for your platform from [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

Download the [NSIDC-Data-Tutorials](https://github.com/nsidc/NSIDC-Data-Tutorials) repository from Github by clicking the green 'Clone or Download' button located at the top right of the repository page.

Unzip the file, and open a command line or terminal window in the NSIDC-Data-Tutorials folder's location.

From a command line or terminal window, install the required environment with the following command:

```bash
conda env create -f binder/environment.yml
```

you should now see that the dependencies were installed and our environment is ready to be used.

Activate the environment with

```
conda activate tutorial
```

Launch the notebook locally with the following command:

```bash
jupyter lab
```

This should open a browser window with the JupyterLab IDE, showing your current working directory on the left-hand navigation. Navigate to the tutorial folder of choice and click on their associated *.ipynb files to get started.

> **NOTE:** Some times Conda environments change(break) even with pinned down dependencies, if you run into an issue with dependencies for the tutorials please open an issue and we'll try to fix it as soon as possible.


## Credit

This software is developed by the National Snow and Ice Data Center with funding from multiple sources.

## License

This repository is licensed under the MIT license. [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
