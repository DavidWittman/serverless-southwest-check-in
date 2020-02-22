resource "aws_cloudwatch_metric_alarm" "checkin_errors" {
  alarm_name          = "checkin-error"
  alarm_description   = "Monitor the ${aws_lambda_function.sw_check_in.function_name} Lambda for errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  treat_missing_data  = "notBreaching"

  # Set this threshold to 3 because we normally have _some_ retries due to races with Southwest's clock
  threshold = "3"

  dimensions = {
    FunctionName = aws_lambda_function.sw_check_in.function_name
  }

  alarm_actions = [aws_sns_topic.admin_notifications.arn]
}

resource "aws_cloudwatch_metric_alarm" "checkin_schedule_errors" {
  alarm_name          = "checkin-schedule-error"
  alarm_description   = "Monitor the ${aws_lambda_function.sw_schedule_check_in.function_name} Lambda for errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "1"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.sw_schedule_check_in.function_name
  }

  alarm_actions = [aws_sns_topic.admin_notifications.arn]
}

resource "aws_cloudwatch_metric_alarm" "checkin_receive_email_errors" {
  alarm_name          = "checkin-receive-email-error"
  alarm_description   = "Monitor the ${aws_lambda_function.sw_receive_email.function_name} Lambda for errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "1"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.sw_receive_email.function_name
  }

  alarm_actions = [aws_sns_topic.admin_notifications.arn]
}

