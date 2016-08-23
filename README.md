## Installation

### Requirements

 - Serverless
 - IAM user credentials with Administrator access (for Serverless)
 - Python 2.7.x

## Usage

### Configure your AWS Credentials

``` bash
$ export AWS_ACCESS_KEY_ID=
$ export AWS_SECRET_ACCESS_KEY=
```

## Contributing

### Testing

To run tests, you must first have the requirements provided in `requirements-dev.txt` installed:

``` bash
$ pip install -r requirements-dev.txt
```

After you have installed the test dependencies, you can run the test suite with:

``` bash
# unit tests
$ make test
# flake8 style check
$ make lint
```

### Deploy

To package, build, and deploy to AWS, run:

``` bash
$ make deploy
```
