resource "aws_sfn_state_machine" "check_in" {
  name     = "check-in"
  role_arn = aws_iam_role.state_machine.arn

  definition = <<EOF
{
  "Comment": "Checks in a Southwest reservation",
  "StartAt": "ScheduleCheckIns",
  "States": {
    "ScheduleCheckIns": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.sw_schedule_check_in.arn}",
      "Next": "MapCheckIns"
    },
    "MapCheckIns": {
      "Type": "Map",
      "ItemsPath": "$.check_in_times",
      "MaxConcurrency": 0,
      "Parameters": {
        "time.$": "$$.Map.Item.Value",
        "data.$": "$"
      },
      "Iterator": {
        "StartAt": "WaitUntilCheckIn",
        "States": {
          "WaitUntilCheckIn": {
            "Type": "Wait",
            "TimestampPath": "$.time",
            "Next": "CheckIn"
          },
          "CheckIn": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.sw_check_in.arn}",
            "InputPath": "$.data",
            "Retry": [
              {
                "ErrorEquals": ["SouthwestAPIError"],
                "IntervalSeconds": 3,
                "MaxAttempts": 3
              }
            ],
            "Catch": [{
              "ErrorEquals": ["ReservationNotFoundError"],
              "Next": "Fail"
             }, {
              "ErrorEquals": ["States.ALL"],
              "Next": "SendFailureNotification",
              "ResultPath": "$.error"
            }],
            "End": true
          },
          "SendFailureNotification": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.sw_check_in_failure.arn}",
            "InputPath": "$.data",
            "End": true
          },
          "Fail": {
            "Type": "Fail"
          }
        }
      },
      "End": true
    }
  }
}
EOF

}

