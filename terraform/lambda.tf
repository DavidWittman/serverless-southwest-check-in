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

resource "aws_s3_bucket_object" "chromedriver" {
  bucket = aws_s3_bucket.layers.bucket
  key    = "chromedriver.zip"
  source = "${path.module}/build/chromedriver.zip"
  etag   = filemd5("${path.module}/build/chromedriver.zip")
}

resource "aws_lambda_layer_version" "chromedriver" {
  description      = "Chromedriver"
  s3_bucket        = aws_s3_bucket.layers.bucket
  s3_key           = aws_s3_bucket_object.chromedriver.id
  source_code_hash = filebase64sha256("${path.module}/build/chromedriver.zip")
  layer_name       = "chromedriver"
}

resource "aws_lambda_layer_version" "deps" {
  description         = "Bundled dependencies for Checkin Bot"
  filename            = data.archive_file.vendor.output_path
  layer_name          = "check-in-deps"
  source_code_hash    = data.archive_file.vendor.output_base64sha256
  compatible_runtimes = ["python3.6", "python3.7"]
}

resource "aws_lambda_function" "sw_update_headers" {
  filename         = data.archive_file.src.output_path
  function_name    = "sw-update-headers"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.update_headers"
  runtime          = "python3.6"
  timeout          = 60
  memory_size      = 768
  source_code_hash = data.archive_file.src.output_base64sha256
  layers           = [aws_lambda_layer_version.chromedriver.arn, aws_lambda_layer_version.deps.arn]
}

resource "aws_lambda_function" "sw_receive_email" {
  filename         = data.archive_file.src.output_path
  function_name    = "sw-receive-email"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.receive_email"
  runtime          = "python3.6"
  timeout          = 10
  source_code_hash = data.archive_file.src.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      S3_BUCKET_NAME    = aws_s3_bucket.email.id
      STATE_MACHINE_ARN = aws_sfn_state_machine.check_in.id
      EMAIL_SOURCE      = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC         = var.admin_email
      EMAIL_FEEDBACK    = var.feedback_email
    }
  }
}

resource "aws_lambda_function" "sw_schedule_check_in" {
  filename         = data.archive_file.src.output_path
  function_name    = "sw-schedule-check-in"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.schedule_check_in"
  runtime          = "python3.6"
  timeout          = 10
  source_code_hash = data.archive_file.src.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      EMAIL_SOURCE   = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC      = var.admin_email
      EMAIL_FEEDBACK = var.feedback_email
    }
  }
}

resource "aws_lambda_function" "sw_check_in" {
  filename         = data.archive_file.src.output_path
  function_name    = "sw-check-in"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.check_in"
  runtime          = "python3.6"
  timeout          = 30
  source_code_hash = data.archive_file.src.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      EMAIL_SOURCE   = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC      = var.admin_email
      EMAIL_FEEDBACK = var.feedback_email
    }
  }
}

resource "aws_lambda_function" "sw_check_in_failure" {
  filename         = data.archive_file.src.output_path
  function_name    = "sw-check-in-failure"
  role             = aws_iam_role.lambda.arn
  handler          = "handlers.check_in_failure"
  runtime          = "python3.6"
  timeout          = 10
  source_code_hash = data.archive_file.src.output_base64sha256
  layers           = [aws_lambda_layer_version.deps.arn]

  environment {
    variables = {
      EMAIL_SOURCE   = "\"Checkin Bot\" <no-reply@${var.domains[0]}>"
      EMAIL_BCC      = var.admin_email
      EMAIL_FEEDBACK = var.feedback_email
    }
  }
}

resource "aws_lambda_permission" "allow_ses" {
  statement_id   = "AllowExecutionFromSES"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.sw_receive_email.function_name
  source_account = data.aws_caller_identity.current.account_id
  principal      = "ses.amazonaws.com"
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id   = "AllowExecutionFromCloudwatch"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.sw_update_headers.function_name
  source_account = data.aws_caller_identity.current.account_id
  principal      = "events.amazonaws.com"
}
