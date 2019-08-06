data "archive_file" "vendor" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/vendor/"
  output_path = "${path.module}/build/vendor.zip"
}

data "archive_file" "src" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/src/"
  output_path = "${path.module}/build/src.zip"
}

resource "aws_lambda_layer_version" "deps" {
  description         = "Bundled dependencies for Checkin Bot"
  filename            = "${data.archive_file.vendor.output_path}"
  layer_name          = "check-in-deps"
  compatible_runtimes = ["python3.6", "python3.7"]
}

resource "aws_lambda_function" "sw_receive_email" {
  filename         = "${data.archive_file.src.output_path}"
  function_name    = "sw-receive-email"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handlers.receive_email"
  runtime          = "python3.6"
  timeout          = 10
  source_code_hash = "${data.archive_file.src.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.deps.arn}"]

  environment {
    variables = {
      S3_BUCKET_NAME    = "${aws_s3_bucket.email.id}"
      STATE_MACHINE_ARN = "${aws_sfn_state_machine.check_in.id}"
      EMAIL_SOURCE      = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC         = "${var.admin_email}"
    }
  }
}

resource "aws_lambda_function" "sw_schedule_check_in" {
  filename         = "${data.archive_file.src.output_path}"
  function_name    = "sw-schedule-check-in"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handlers.schedule_check_in"
  runtime          = "python3.6"
  timeout          = 10
  source_code_hash = "${data.archive_file.src.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.deps.arn}"]

  environment {
    variables = {
      EMAIL_SOURCE = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC    = "${var.admin_email}"
    }
  }
}

resource "aws_lambda_function" "sw_check_in" {
  filename         = "${data.archive_file.src.output_path}"
  function_name    = "sw-check-in"
  role             = "${aws_iam_role.lambda.arn}"
  handler          = "handlers.check_in"
  runtime          = "python3.6"
  timeout          = 30
  source_code_hash = "${data.archive_file.src.output_base64sha256}"
  layers           = ["${aws_lambda_layer_version.deps.arn}"]
}

resource "aws_lambda_permission" "allow_ses" {
  statement_id   = "AllowExecutionFromSES"
  action         = "lambda:InvokeFunction"
  function_name  = "${aws_lambda_function.sw_receive_email.function_name}"
  source_account = "${data.aws_caller_identity.current.account_id}"
  principal      = "ses.amazonaws.com"
}
