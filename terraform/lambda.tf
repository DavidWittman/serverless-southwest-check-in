data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/"
  output_path = "${path.module}/build/lambda.zip"
}

resource "aws_lambda_function" "sw_receive_email" {
  filename         = "${data.archive_file.lambda.output_path}"
  function_name    = "sw-receive-email"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handler.receive_email"
  runtime          = "python2.7"
  timeout          = 10
  source_code_hash = "${data.archive_file.lambda.output_base64sha256}"

  environment {
    variables = {
      S3_BUCKET_NAME    = "${aws_s3_bucket.email.id}"
      STATE_MACHINE_ARN = "${aws_sfn_state_machine.check_in.id}"
    }
  }
}

resource "aws_lambda_function" "sw_schedule_check_in" {
  filename         = "${data.archive_file.lambda.output_path}"
  function_name    = "sw-schedule-check-in"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handler.schedule_check_in"
  runtime          = "python2.7"
  timeout          = 10
  source_code_hash = "${data.archive_file.lambda.output_base64sha256}"
}

resource "aws_lambda_function" "sw_check_in" {
  filename         = "${data.archive_file.lambda.output_path}"
  function_name    = "sw-check-in"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handler.check_in"
  runtime          = "python2.7"
  timeout          = 15
  source_code_hash = "${data.archive_file.lambda.output_base64sha256}"
}

resource "aws_lambda_permission" "allow_ses" {
  statement_id   = "AllowExecutionFromSNS"
  action         = "lambda:InvokeFunction"
  function_name  = "${aws_lambda_function.sw_receive_email.function_name}"
  source_account = "${data.aws_caller_identity.current.account_id}"
  principal      = "ses.amazonaws.com"
}
