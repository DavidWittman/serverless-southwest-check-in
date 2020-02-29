resource "aws_sfn_state_machine" "check_in" {
  name     = "check-in"
  role_arn = aws_iam_role.state_machine.arn

  definition = <<EOF
{
  "Comment": "Checks in a Southwest reservation",
  "StartAt": "ScheduleCheckIn",
  "States": {
    "ScheduleCheckIn": {
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
            "Next": "RecordCheckIn",
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
              "Next": "CheckInFailure"
            }]
          },
          "CheckInFailure": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.sw_check_in_failure.arn}",
            "End": true
          },
          "RecordCheckIn": {
            "Type": "Task",
            "Resource": "${aws_lambda_function.sw_record_check_in.arn}",
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

