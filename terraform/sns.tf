# We're only creating the topic here. A subscription needs to be
# manually created because it requires verification of the email.
resource "aws_sns_topic" "admin_notifications" {
  name = "checkin-notifications"
}

