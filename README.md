## Installation

### Requirements

 - [Serverless](https://serverless.com/framework/docs/providers/aws/guide/installation/)
 - IAM user credentials with Administrator access (for Serverless)

## Usage

### Configure your AWS Credentials

Add your credentials to your environment, with `aws configure`, or directly with Serverless.

Here's an example of setting your credentials via environment variables. For more detailed explanations, see the [Serverless documentation](https://serverless.com/framework/docs/providers/aws/guide/credentials/).

``` bash
$ export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
$ export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
```

### Deploy

To package, build, and deploy to AWS, run:

``` bash
$ make deploy
```
Or, if you don't have make installed:

```
$ pip install -r requirements.txt -t vendor && serverless deploy
```

### Add a flight

Invoke the `add` lambda function via serverless, and pass in your first name, last name, and confirmation number in JSON as parameters for the event. Here's an example:

```
$ serverless invoke -f add -d '{ "first_name": "George", "last_name": "Bush", "confirmation_number": "ABC123" }'
```

I'll likely add some helper scripts (or an API gateway) around this invocation in the future.

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
