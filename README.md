## Setup environment
### You have pipenv
Create a virtual environment and Install requirements
```bash
mkdir .venv
```
```bash
pipenv install
```
Into virtual environment
```bash
pipenv shell
```
### You don't have pipenv
```bash
pip install requirement/requirements.txt
```
---
### Setup environmental variables
```bash
cp .env.sample .env
```
Note: Please update the values for environmental variables.

---
## Run Code
Get Radar Data
```bash 
python main.py
```
Read Radar Data
```bash
python read_npy.py
```