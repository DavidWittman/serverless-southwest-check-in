# Serverless Southwest Check In

[![Build Status](https://travis-ci.org/DavidWittman/serverless-southwest-check-in.svg?branch=master)](https://travis-ci.org/DavidWittman/serverless-southwest-check-in)

Automatically check in to your Southwest flight using the AWS Serverless Platform.

This project was inspired by similar projects from [Aaron Ortbals](https://github.com/aortbals/southwest-checkin) and [Joe Beda](https://github.com/jbeda/southwest-checkin).

## Quickstart

## Installation

Skip to the [Deploy](#deploy) section if you already have Terraform installed and configured with your AWS credentials.

### Requirements

 - [Terraform](https://www.terraform.io/intro/getting-started/install.html). Install this first.
 - AWS IAM user credentials with Administrator access (for Terraform)

### Configure your AWS Credentials

Add your credentials to your environment, with `aws configure`, or directly with Terraform.

Here's an example of setting your credentials via environment variables. For more detailed explanations, see the [Terraform AWS Provider documentation](https://www.terraform.io/docs/providers/aws/).

``` bash
$ export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
$ export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
$ export AWS_DEFAULT_REGION=us-east-1
```

## Usage

### Deploy

To package, build, and deploy to AWS, run:

``` bash
$ make deploy
```

Or, if you don't have make installed:

```
$ pip install -r lambda/requirements.txt -t lambda/vendor && terraform apply
```

### Add a flight

New flights can be added by executing the AWS Step Function or by Email trigger.

#### Manually execute Step Function

Invoke the `sw-schedule-check-in` Lambda function via the AWS cli, and pass in your check-in details in JSON as parameters for the event. Here's an example:

```
STEP_FN_INPUT='{
  "first_name": "George",
  "last_name": "Bush",
  "confirmation_number": "ABC123",
  "email": "gwb@example.com"
}'
STEP_FN_ARN=$(aws --output text stepfunctions list-state-machines --query 'stateMachines[*].stateMachineArn' | grep -E ':sw-check-in$')
aws stepfunctions start-execution \
  --state-machine-arn "$STEP_FN_ARN" \
  --input "$STEP_FN_INPUT"
```

The `email` parameter is optional and sets the email address to which your boarding passes will be sent.

#### Add via Email

Alternatively, check-ins can be submitted via e-mail using the AWS SES Lambda Receiver Action.

TODO

## Contributing

### Testing

To run tests, you must first have the requirements provided in `lambda/requirements-dev.txt` installed:

``` bash
$ pip install -r lambda/requirements-dev.txt
```

After you have installed the test dependencies, you can run the test suite with:

``` bash
# unit tests
$ make test
# flake8 style check
$ make lint
```
