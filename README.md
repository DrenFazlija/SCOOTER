# SCOOTER: A Human Evaluation Framework for Unrestricted Adversarial Examples

## Table of Contents

1. **[Setting up the Environment](#setting-up-the-environment)**
2. **[R for Equivalence Testing](#r-for-equivalence-testing)**
3. **[Project Structure](#project-structure)**
4. **[More Data!](#more-data)**
5. **[License](#license)**

## Setting up the Environment

To reproduce and repurpose our existing software pipeline, users/researchers need the following software components:
1. **Python 3:** To calculate the SCOOTER metrics and other statistics, Python must be pre-installed. Python for your operating system (if not already pre-installed) can be downloaded from the following link: https://www.python.org/downloads/
2. **Miniconda:** Within this codebase, virtual Python environments are set up using Conda. Such environments allow us to manage project-relevant packages within a separate Python instance. For more information on Conda, see: https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html
3. **C++ Build Tools (Windows only):** If this is your first time working with Python packages such as `numpy`, you may also need to setup Microsoft C++ build tools. Below, you can find (ChatGPT generated!) setup instructions:

    - Go to https://visualstudio.microsoft.com/visual-cpp-build-tools/
    - Download and install.
    - During installation, select "C++ build tools" and include the Windows 10/11 SDK.
    - Restart your terminal or IDE after installation.

Assuming that everything went smoothly, you should now be able to create virtual environments via conda. However, you first need to download the repository via `git clone`:
```bash
git clone https://github.com/DrenFazlija/SCOOTER.git
```

> [!NOTE]
> Please go to the `ui` directory to setup the web app demo – the below steps only cover data processing!

Next, a virtual Python environment must be set up using `conda` and configured with the appropriate Python packages. The Python version used for this project is `3.10.0`.

**1. Create Conda Environment**
```bash 
conda create -n scooter python=3.10.0
```

**2. Activate Conda Environment and Install Packages**
```bash
cd SCOOTER # Change to the Repository Directory
conda activate scooter
conda install pip # necessary for some conda versions
pip install -r requirements.txt
```

## R for Equivalence Testing
To run our introduced TOST-based equivalence test, you will also neeed to install R (see: https://cran.rstudio.com/). Our corresponding script ran successfully with `R version 4.2.2`.

We also highly recommend that you download the RStudio IDE as it simplifies the workflow: https://posit.co/download/rstudio-desktop/

## Project Structure

The repository is organized into the following main directories:

- `4o_ratings/`: All ratings provided by GPT-4o + Python scripts covering the rating summary process and the system prompt used.
  - `ratings_summary.py`: Allows researchers to process the 4o ratings of all six attacks
  - `gpt_4o_assessment.py`: Allows one to assess their own images using our defined system prompt
- `manual_processing/`: Contains information about how we created the altered ImageNet subsample **ImageNet S-R50-N**
- `scooter_metrics/`: Contains all relevant data and scripts to calculate the core SCOOTER metrics
  - `anonymized_*.csv`: Anonymized collection of ratings of all participants of the specified attack
  - `mixed_effect_TOST.R`: Performes the equivalence test based on anonymized ratings collection
  - `scooter_metrics.py`: Handle automated grading
- `ui/`: The codebase behind the SCOOTER web app (documentation will be expanded upon throughout Q3 2025)

## More Data
You can find the generated images and some more data at our Zenodo repository!
https://doi.org/10.5281/zenodo.15771501

## License
This project is made available under the MIT License. You are free to:
- Use the code for any purpose
- Modify the code to suit your needs
- Distribute your modified versions
- Use the code for commercial purposes
