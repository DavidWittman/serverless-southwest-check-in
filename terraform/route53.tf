data "aws_route53_zone" "selected" {
  name = "${var.domain}"
}

resource "aws_route53_record" "ses_inbound_mx" {
  zone_id = "${data.aws_route53_zone.selected.zone_id}"
  name    = "${var.domain}"
  type    = "MX"
  ttl     = "300"
  records = ["10 inbound-smtp.us-east-1.amazonaws.com"]
}

resource "aws_route53_record" "ses_verification_txt" {
  zone_id = "${data.aws_route53_zone.selected.zone_id}"
  name    = "_amazonses.${var.domain}"
  type    = "TXT"
  ttl     = "300"
  records = ["${aws_ses_domain_identity.sw.verification_token}"]
}
