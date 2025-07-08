# SCOOTER Web App Documentation

## Project Overview

The SCOOTER Web App is a Flask-based application designed for user studies on image perception and adversarial examples. It guides participants through a structured workflow, including:

- Consent forms
- Colorblindness (Ishihara) testing
- Comprehension checks
- Main study with image classification tasks
- Feedback collection
- Leaderboard and performance tracking

This guide will help you quickly set up a local demo. For future improvements and a detailed roadmap, see [Roadmap and ToDos](#roadmap-and-todos).

---

## System Requirements

- **Python**: 3.8.19
- **PostgreSQL**: 16 or compatible
- **Flask** and dependencies (see `requirements.txt`)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd <repo-directory>
   ```

2. **Create a virtual environment:**
   We recommend using Conda for Python version management.
   ```bash
   conda create -n webapp python=3.8.19
   conda activate webapp
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Setup: SCOOTER Database

### Requirements
- **PostgreSQL 16** (with `psql` command-line access)
- A PostgreSQL user account (e.g., `postgres`)

### Phase 1: Create the Database
1. **Switch to your Postgres user:**
   ```bash
   sudo -i -u postgres
   ```
2. **Start the PostgreSQL shell:**
   ```bash
   psql
   ```
3. **Create the database:**
   ```sql
   CREATE DATABASE scooterdb;
   \c scooterdb
   ```

### Phase 2: Set Up Tables and Web Agent Account
1. **Activate your Conda environment:**
   ```bash
   conda activate webapp
   ```
2. **Run the setup script:**
   ```bash
   python setup.py
   ```
   > **Note:** This script assumes a PostgreSQL superuser named `postgres` with the default password `postgres`. Change these defaults for production use!

#### Option 1: Fresh Database Setup
- You will be prompted for mail service configuration. For testing, you can use a dummy mail setup.
- Enter your mail server details (or use dummy values for local testing).
- Select the attack type to load (e.g., enter `5` for AdvPP).
- Generate a Flask secret key (recommended: let the script generate one automatically).
- Enter your database connection details:
  - Host (e.g., `localhost`)
  - Username (e.g., `scooter_web` — this will be created by the script)
  - Password (choose a strong, unique password!)

> **Security Tip:** Never use trivial passwords in production. The authors are not responsible for security issues caused by weak credentials.

- The script will create all required tables and functions (see `schema.sql` for details).

#### Option 2: Import Existing Data
- Download the sample data from [Zenodo](https://doi.org/10.5281/zenodo.15771501) (`scooter_db_entries.zip`).
- Extract the files to a directory outside the codebase (e.g., `/home/youruser/data/scooter_samples`).
- When prompted, enter the absolute path to this directory.

#### Option 3: Upload New Images
- (Details coming soon.)

---

## Starting the Web App

Once setup is complete, start the development server:

```bash
python app.py
```

- Run this command from the `ui` directory.
- The app will be available at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

### Accessing the Study

By default, direct access to the root page shows an error (this is expected!). Participants must enter via a personalized link:

```
http://127.0.0.1:5000/consent-form?PROLIFIC_PID=<your_dummy_pid>
```

- `<your_dummy_pid>` should be a random, 24-character, lowercase alphanumeric string (e.g., `2xx5ezc6xdwbywi4oftg4716`).
- This simulates a participant's entry point and allows you to test the full workflow.

---

## Project Structure

### Core Files

- **app.py**: Main Flask application entry point
- **routes.py**: Defines primary application routes
- **config.py**: Handles configuration for database, mail, and storage
- **schema.sql**: Database schema definition
- **db_utils.py**: Database utility functions
- **wsgi.py**: WSGI entry point for production deployment

### Modules

- **consent_form/**: Participant consent form logic
- **colorblindness_test/**: Ishihara colorblindness screening
- **comprehension_check/**: Participant understanding verification
- **main_study/**: Core experiment logic
- **endpoints/**: API endpoints
- **mail/**: Email functionality
- **notices/**: User notifications and legal pages
- **leaderboard/**: Performance tracking and display
- **debug/**: Debugging tools and utilities

### Utilities

- **data_processing.py**: Study data processing functions
- **utils.py**: General utility functions
- **streamlit_automations.py**: Streamlit-based automation scripts
- **export_annotations.py**: Tools for exporting study annotations
- **setup.py**: Configuration and setup utilities

---

## Database Schema Overview

The database includes the following main tables:

- **participants**: Participant information and progress
- **attention_check_images**: Images for attention checks
- **modified_images**: Adversarially modified images
- **real_images**: Reference (unmodified) images
- **ishihara_test_cards**: Color vision test cards
- **comprehension_check_images**: Images for comprehension checks
- **feedback**: Participant feedback
- **site_logs**: User activity logs
- **image_logs**: Image interaction logs
- **leaderboard**: Performance and ranking data

---

## Application Flow

1. **Participant Entry**: User enters with a Prolific ID (PID)
2. **Consent Form**: Review and agree to study terms
3. **Colorblindness Test**: Screen for color vision deficiencies
4. **Study Introduction**: Instructions and context
5. **Comprehension Check**: Verify participant understanding
6. **Main Study**: Image classification tasks
7. **Feedback**: Collect participant feedback
8. **Completion**: Confirmation and compensation info

---

## Key Features & Safeguards

### Illegal Behavior Prevention
- Prevents skipping required steps
- Blocks retaking completed sections
- Enforces strict workflow order

### Leaderboard
- Tracks participant performance
- Displays overall accuracy and breakdowns (real vs. modified images)
- Allows comparison by model and attack type

### Data Processing
- Export and analyze participant data
- Tools for annotation export and result analysis

---

## Roadmap and To-Dos
- Refactor codebase for maintainability and readability
- Add tutorials on:
  - Workflow details
  - Personalizing the web page
  - Setting up a Prolific study and evaluating ratings
  - Common platform issues
  - Exporting reported metrics
- Expand documentation and user guides

---

## License and Credits

See `Copyright.md` for information on third-party code and licensing. 