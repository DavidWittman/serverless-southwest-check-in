provider "aws" {
  region = "us-east-1"
  alias = "region"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {
  provider = "aws.region"
}
