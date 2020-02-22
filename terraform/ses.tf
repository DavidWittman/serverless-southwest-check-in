resource "aws_ses_domain_identity" "sw" {
  count  = length(var.domains)
  domain = element(var.domains, count.index)
}

resource "aws_ses_receipt_rule_set" "sw_check_in" {
  rule_set_name = "sw-check-in"
}

resource "aws_ses_active_receipt_rule_set" "sw_check_in" {
  rule_set_name = "sw-check-in"
}

resource "aws_ses_receipt_rule" "feedback" {
  count = var.feedback_email == "" ? 0 : 1

  name          = "sw-feedback"
  rule_set_name = aws_ses_receipt_rule_set.sw_check_in.rule_set_name
  recipients    = [var.feedback_email]

  enabled      = true
  scan_enabled = true

  sns_action {
    topic_arn = aws_sns_topic.admin_notifications.arn
    position  = 1
  }

  stop_action {
    scope    = "RuleSet"
    position = 2
  }
}

resource "aws_ses_receipt_rule" "store" {
  name          = "sw-check-in"
  rule_set_name = aws_ses_receipt_rule_set.sw_check_in.rule_set_name
  recipients    = var.recipients

  # position this rule after the feedback email rule if the email is set
  after        = var.feedback_email == "" ? "" : "sw-feedback"
  enabled      = true
  scan_enabled = true

  s3_action {
    bucket_name = aws_s3_bucket.email.id
    position    = 1
  }

  lambda_action {
    function_arn    = aws_lambda_function.sw_receive_email.arn
    invocation_type = "Event"
    position        = 2
  }
}

