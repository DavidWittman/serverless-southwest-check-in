variable "domains" {
  type        = "list"
  description = "List of domains/subdomains to create the service under. WARNING: The MX records for this domain will be overwritten!"
}

variable "recipients" {
  type        = "list"
  description = "List of email address patterns to deliver to, e.g. `checkin@example.com`, `example.com`, `subdomain.example.com`."
}

variable "admin_email" {
  description = "This email address will be used for alerts and BCCs on confirmations"
}
