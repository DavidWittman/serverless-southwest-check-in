variable "domain" {
  description = "Domain name to create the service under. The MX records for this domain will be overwritten, so you may want to use a subdomain."
}

variable "admin_email" {
  description = "This email address will be used for alerts and BCCs on confirmations"
}
