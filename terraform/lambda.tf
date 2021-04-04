data "aws_s3_bucket_object" "artifacts_build_hash" {
  bucket = var.settings["s3_bucket"]
  key    = "artifacts/build.zip.base64sha256"
}

data "aws_s3_bucket_object" "artifacts_layer_hash" {
  bucket = var.settings["s3_bucket"]
  key    = "artifacts/layer.zip.base64sha256"
}

data "aws_caller_identity" "current" {
  # Retrieves information about the AWS account corresponding to the
  # access key being used to run Terraform, which we need to populate
  # the "source_account" on the permission resource.
}

resource "aws_lambda_layer_version" "flexepos_layer" {
  layer_name          = "flexepos_layer_${terraform.workspace}"
  s3_bucket           = var.settings["s3_bucket"]
  s3_key              = "artifacts/layer.zip"
  source_code_hash    = chomp(data.aws_s3_bucket_object.artifacts_layer_hash.body)
  compatible_runtimes = ["python3.7", "python3.6"]
}

resource "aws_lambda_function" "invoice_sync" {
  function_name = "invoice-sync-${terraform.workspace}"
  description   = "[${terraform.workspace}] Syncs the last 30 days of invoices from CrunchTime into Quickbooks"

  s3_bucket        = var.settings["s3_bucket"]
  s3_key           = "artifacts/build.zip"
  source_code_hash = chomp(data.aws_s3_bucket_object.artifacts_build_hash.body)
  role             = aws_iam_role.flexepos_lambda_role.arn
  handler          = "src.lambda_function.invoice_sync_handler"
  runtime          = "python3.7"
  timeout          = 480
  memory_size      = 960
  layers = [aws_lambda_layer_version.flexepos_layer.arn]

  environment {
    variables = local.lambda_env_invoice_sync
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_journal" {
  function_name = "daily-journal-${terraform.workspace}"
  description   = "[${terraform.workspace}] Sends an email report on store operations."

  s3_bucket        = var.settings["s3_bucket"]
  s3_key           = "artifacts/build.zip"
  source_code_hash = chomp(data.aws_s3_bucket_object.artifacts_build_hash.body)
  role             = aws_iam_role.flexepos_lambda_role.arn
  handler          = "src.lambda_function.daily_journal_handler"
  runtime          = "python3.7"
  timeout          = 480
  memory_size      = 960
  layers = [aws_lambda_layer_version.flexepos_layer.arn]

  environment {
    variables = local.lambda_env_daily_journal
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "daily_sales" {
  function_name = "daily-sales-${terraform.workspace}"
  description   = "[${terraform.workspace}] Enters daily sales for yesterday."

  s3_bucket        = var.settings["s3_bucket"]
  s3_key           = "artifacts/build.zip"
  source_code_hash = chomp(data.aws_s3_bucket_object.artifacts_build_hash.body)
  role             = aws_iam_role.flexepos_lambda_role.arn
  handler          = "src.lambda_function.daily_sales_handler"
  runtime          = "python3.7"
  timeout          = 480
  memory_size      = 960
  layers = [aws_lambda_layer_version.flexepos_layer.arn]

  environment {
    variables = local.lambda_env_daily_sales
  }

  tags = local.common_tags
}
