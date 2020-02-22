data "aws_route53_zone" "selected" {
  count = length(var.domains)
  name  = element(var.domains, count.index)
}

resource "aws_route53_record" "ses_inbound_mx" {
  count   = length(var.domains)
  zone_id = element(data.aws_route53_zone.selected.*.zone_id, count.index)
  name    = element(var.domains, count.index)
  type    = "MX"
  ttl     = "300"
  records = ["10 inbound-smtp.${data.aws_region.current.name}.amazonaws.com"]
}

resource "aws_route53_record" "ses_verification_txt" {
  count   = length(var.domains)
  zone_id = element(data.aws_route53_zone.selected.*.zone_id, count.index)
  name    = "_amazonses.${element(var.domains, count.index)}"
  type    = "TXT"
  ttl     = "300"
  records = [element(aws_ses_domain_identity.sw.*.verification_token, count.index)]
}

