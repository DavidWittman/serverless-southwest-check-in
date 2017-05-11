resource "aws_sfn_state_machine" "check_in" {
  name     = "check-in"
  role_arn = "${aws_iam_role.state_machine.arn}"

  definition = <<EOF
{
  "Comment": "Checks in a Southwest reservation",
  "StartAt": "ScheduleCheckIn",
  "States": {
    "ScheduleCheckIn": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.sw_schedule_check_in.arn}",
      "Next": "WaitUntilCheckIn"
    },
    "WaitUntilCheckIn": {
      "Type": "Wait",
      "TimestampPath": "$.check_in_times.next",
      "Next": "CheckIn"
    },
    "CheckIn": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.sw_check_in.arn}",
      "Retry": [
        {
          "ErrorEquals": ["SouthwestAPIError"],
          "IntervalSeconds": 5,
          "MaxAttempts": 3
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["NotLastCheckIn"],
          "ResultPath": "$.not_last_check_in",
          "Next": "ScheduleCheckIn"
        }
      ],
      "End": true
    }
  }
}
EOF
}
