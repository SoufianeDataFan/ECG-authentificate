Autentificate_ECG
---
Using neural networks on ECG data to see if it is a valid candidate for biometric authentication.

### Pre-Requisites

Make sure you have the following items installed:
1. python2.7
2. [wfdb package](https://pypi.python.org/pypi/wfdb) using `pip install wfdb`
3. [keras](https://keras.io/#installation/)
4. [pandas](https://pandas.pydata.org/pandas-docs/stable/install.html)
5. [numpy](https://docs.scipy.org/doc/numpy/user/install.html)

### Usage

1. `python data_processing.py`: Converts all .dat files in `data/` to .csv. Extract labels and features from individual .csv
files. Outputs the following files in the `processed_data/` folder:
    * `labels.csv`: labels [person_id, recording_label, signal_id, age, gender, date record was collected]
    * `rec_##.csv`: filtered ecg signals & unfiltered ecg signals [noisy]


2. `python model_personid.py`: Train and evaluate model for person
identification. See line 370 in `data_processing.py` on specific instructions
for data setup.

### Database

This project uses the [ECG-ID Database from
Physionet](https://physionet.org/physiobank/database/ecgiddb). It can be found
in the `data/` folder. [Note: the original database does not include .csv files.
See `class Generate_csv` in `data_processing.py` to learn more about how the .dat files were converted to
csv using [rdsamp](https://pypi.python.org/pypi/wfdb)]
