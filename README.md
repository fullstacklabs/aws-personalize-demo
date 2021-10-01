# AWS Personalize Demo

This demo application is created for the intent to demostrate the AWS Personalize capabilities.

It uses a small version of the [Movie Len Dataset](https://grouplens.org/datasets/movielens) that holds recommendation records for Movies.

## Requirements

- [Python] https://www.python.org/downloads/

## Installation

- Create a virtual environment for avoid problems with Python version
  
```bash
python3 -m venv /path/to/new/virtual/environment
```

- Activate the virtual environment
  
```bash
source /path/to/new/virtual/environment/bin/activate
```

- Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all the dependencies.

```bash
pip install -r requirements.txt
```

- Configure the AWS Credentials to access the account

```bash
export AWS_ACCESS_KEY_ID=<AWS Access Key>
export AWS_SECRET_ACCESS_KEY=<AWS Secret Key>
export AWS_DEFAULT_REGION=<AWS Default region>
```

## Usage

- For creation of the AWS Personalize Solution Version to be used during the demo run 

```bash
python personalize_demo_creator.py
```

- For actually using the AWS Personalize Solution Version to find out recomendation for a random user

```bash
python3 personalize_demo_executor.py
```

- For clean up the resources used during the demo
  
```bash
python3 personalize_demo_cleanup.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)