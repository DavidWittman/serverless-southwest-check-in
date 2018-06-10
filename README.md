# Serverless Southwest Check In

[![Build Status](https://travis-ci.org/DavidWittman/serverless-southwest-check-in.svg?branch=master)](https://travis-ci.org/DavidWittman/serverless-southwest-check-in)

Serverless Southwest Check In is an email bot which will automatically check you into your Southwest flights. Never sit in a middle seat again!

This project is powered by the AWS Serverless Platform (Lambda, Step Functions, and SES) and was inspired by similar projects from Aaron Ortbals and [Joe Beda](https://github.com/jbeda/southwest-checkin).

## Quickstart

## Installation

Skip to the [Deploy](#deploy) section if you already have Terraform installed and configured with your AWS credentials.

### Requirements

 - [Terraform](https://www.terraform.io/intro/getting-started/install.html). Install this first.
 - AWS IAM user credentials with Administrator access (for Terraform)
 - A Route53 hosted zone for receiving emails via SES

### Configure your AWS Credentials

Add your credentials to your environment, with `aws configure`, or directly with Terraform.

Here's an example of setting your credentials via environment variables. For more detailed explanations, see the [Terraform AWS Provider documentation](https://www.terraform.io/docs/providers/aws/).

``` bash
$ export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
$ export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
$ export AWS_DEFAULT_REGION=us-east-1
```

### Initialize Terraform state

Run the following command to configure Terraform's [Remote State](https://www.terraform.io/docs/state/remote.html) in S3.

```
$ terraform init terraform/
```

You will be prompted for an S3 location to store the remote statefile in. If you wish to use a local state, just remove `terraform/backend.tf` and rerun this command.

## Usage

### Deploy

To package, build, and deploy to AWS, run:

``` bash
$ make deploy
```

Or, if you don't have make installed:

```
$ pip install -r lambda/requirements.txt -t lambda/vendor && terraform apply terraform/
```

Terraform will prompt you to provide a domain name of an existing Route53 Hosted Zone. The MX record for this domain name will be set to the SES SMTP receiver endpoints for your region, so choose a domain which you do not currently use to receive email. In the future, support will be added for subdomains and/or disabling the email receiver.

### Add a flight

New flights can be added by executing the AWS Step Function or by an SES (email) trigger.

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

Alternatively, check-ins can be submitted via e-mail using the AWS SES Lambda Receiver Action. To submit check-ins this way, just forward your reservation email to `checkin@$DOMAIN` where domain is the Route53 domain used when deploying the application. The reservation email is sent by Southwest at purchase time and should be in the form:

```
Flight reservation (ABC123) | 25DEC17 | ABC-XYZ | LASTNAME/FIRSTNAME
```

### Other

#### Notifications

An SNS topic `checkin-notifications` is created as part of the Terraform deploy, but you must manually create and attach a subscription to it through the SNS dashboard. See the Amazon documentation on how to [Subscribe to a Topic](https://docs.aws.amazon.com/sns/latest/dg/SubscribeTopic.html) for more information.

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
