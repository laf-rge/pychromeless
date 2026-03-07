data "aws_s3_bucket" "main" {
  bucket = var.settings.s3_bucket
}

resource "aws_s3_bucket_lifecycle_configuration" "tmp_cleanup" {
  bucket = data.aws_s3_bucket.main.id

  rule {
    id     = "cleanup-tmp-prefix"
    status = "Enabled"

    filter {
      prefix = "tmp/"
    }

    expiration {
      days = 1
    }
  }
}
