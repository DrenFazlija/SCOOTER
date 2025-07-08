Scooter UI Documentation
=======================

Project Overview
--------------

Scooter UI is a Flask-based web application designed for conducting user studies related to image perception and adversarial examples. The application implements a complete participant workflow including:

* Participant consent forms
* Colorblindness testing (Ishihara test) 
* Comprehension checks
* Main study with image classification tasks
* Feedback collection
* Leaderboard functionality

The application appears to focus on studies involving participants' ability to distinguish between real and modified images, likely in the context of adversarial machine learning research.

System Requirements
-----------------

* Python 3.x
* PostgreSQL 16 or compatible version
* Flask and associated dependencies

Installation
-----------

1. Clone the repository
2. Install required dependencies::

    pip install -r requirements.txt

3. Set up PostgreSQL database:

   * Install PostgreSQL 16
   * Configure the utility file for importing/exporting databases
   * Create a database for the application
   * Run the schema.sql file to create necessary tables

4. Configure the application:

   * Create database.ini file with PostgreSQL credentials::

       [postgresql]
       host=<host>
       dbname=<database name>
       user=<username>
       password=<password>

   * Create mail.ini file for email configuration
   * Create secret.key file for Flask application security

5. Start the application::

    python app.py

Project Structure
---------------

Core Files
~~~~~~~~~

* **app.py**: Main Flask application entry point
* **routes.py**: Primary routes for the application
* **config.py**: Configuration handling for database, mail, and data storage
* **schema.sql**: Database schema definition
* **db_utils.py**: Database utility functions
* **wsgi.py**: WSGI entry point for production deployment

Modules
~~~~~~~

* **consent_form/**: Participant consent form handling
* **colorblindness_test/**: Ishihara test for colorblindness screening
* **comprehension_check/**: Verification of participant understanding
* **main_study/**: Core experiment functionality
* **endpoints/**: API endpoints
* **mail/**: Email functionality
* **notices/**: User notifications
* **leaderboard/**: Performance tracking and comparison
* **debug/**: Debug tools and utilities

Utility Files
~~~~~~~~~~~~

* **data_processing.py**: Functions for processing study data
* **utils.py**: General utility functions
* **automations.py**: Automation scripts
* **export_annotations.py**: Tools for exporting study annotations
* **setup_configs.py**: Configuration setup utilities

Database Schema
-------------

The database is structured around these main tables:

* **participants**: Stores participant information and progress
* **attention_check_images**: Images used to verify participant attention
* **modified_images**: Adversarially modified images for the study
* **real_images**: Unmodified reference images
* **ishihara_test_cards**: Color vision test cards
* **comprehension_check_images**: Images used to verify participant understanding
* **feedback**: Participant feedback data
* **site_logs**: User activity logging
* **image_logs**: Image interaction tracking
* **leaderboard**: Performance tracking and ranking

Application Flow
--------------

1. **Participant Entry**: Users enter with a Prolific ID (PID)
2. **Consent Form**: Participants review and agree to study terms
3. **Colorblindness Test**: Screening for color vision deficiencies
4. **Study Introduction**: Instructions and context for the experiment
5. **Comprehension Check**: Verification of participant understanding
6. **Main Study**: Image classification tasks
7. **Feedback**: Collection of participant feedback
8. **Study Completion**: Confirmation and compensation information

Key Components
------------

Illegal Behavior Check
~~~~~~~~~~~~~~~~~~~~

The application includes mechanisms to prevent participants from:

* Skipping required steps
* Retaking completed portions
* Manipulating the study flow

Leaderboard
~~~~~~~~~~

Tracks and displays participant performance with:

* Overall accuracy metrics
* Separate tracking for real vs. modified image detection
* Comparison by model and attack type

Data Processing
~~~~~~~~~~~~~

Includes tools for:

* Exporting annotations
* Processing participant data
* Analyzing results

Development
----------

The project is actively under development with ongoing tasks including:

* Restructuring code for improved maintainability
* Implementing additional security features
* Adding Docker support
* Creating automated setup scripts

License and Credits
-----------------

See Copyright.md for information on third-party code used in the UI.