resource "aws_ses_domain_identity" "sw" {
  domain = "${var.domain}"
}

resource "aws_ses_receipt_rule_set" "sw_check_in" {
  rule_set_name = "sw-check-in"
}

resource "aws_ses_active_receipt_rule_set" "sw_check_in" {
  rule_set_name = "sw-check-in"
}

resource "aws_ses_receipt_rule" "store" {
  name          = "sw-check-in"
  rule_set_name = "sw-check-in"
  recipients    = ["${var.domain}"]
  enabled       = true
  scan_enabled  = true

  s3_action {
    bucket_name = "${aws_s3_bucket.email.id}"
    position    = 1
  }

  lambda_action {
    function_arn    = "${aws_lambda_function.sw_receive_email.arn}"
    invocation_type = "Event"
    position        = 2
  }
}
