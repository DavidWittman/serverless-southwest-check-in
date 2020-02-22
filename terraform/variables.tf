variable "domains" {
  type        = list(string)
  description = "List of domains/subdomains to create the service under. WARNING: The MX records for this domain will be overwritten!"
}

variable "recipients" {
  type        = list(string)
  description = "List of email address patterns to deliver to, e.g. `checkin@example.com`, `example.com`, `subdomain.example.com`."
}

variable "admin_email" {
  description = "This email address will be used for alerts and BCCs on confirmations"
}

variable "feedback_email" {
  description = "An email address under one of the `domains` which receives user feedback. e.g. `feedback@example.com`."
  default     = ""
}

