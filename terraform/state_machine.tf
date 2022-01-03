resource "aws_sfn_state_machine" "check_in" {
  name     = "check-in"
  role_arn = aws_iam_role.state_machine.arn
  definition = templatefile("${path.module}/state_machine.json.tftpl", {
    SCHEDULE_CHECK_IN_ARN = aws_lambda_function.sw_schedule_check_in.arn,
    CHECK_IN_ARN          = aws_lambda_function.sw_check_in.arn,
    UPDATE_HEADERS_ARN    = aws_lambda_function.sw_update_headers.arn,
    CHECK_IN_FAILURE_ARN  = aws_lambda_function.sw_check_in_failure.arn
  })
}
