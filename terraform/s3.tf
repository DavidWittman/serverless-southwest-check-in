resource "aws_s3_bucket" "email" {
  bucket = "${var.domains[0]}-emails"
  acl    = "private"

  lifecycle_rule {
    id      = "expire-90-days"
    enabled = true
    prefix  = ""

    expiration {
      days = 90
    }
  }

  policy = <<POLICY
{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Sid": "ses-put-object",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "ses.amazonaws.com"
                ]
            },
            "Action": [
                "s3:PutObject"
            ],
            "Resource": "arn:aws:s3:::${var.domains[0]}-emails/*",
            "Condition": {
                "StringEquals": {
                    "aws:Referer": "${data.aws_caller_identity.current.account_id}"
                }
            }
        }
    ]
}
POLICY

}

