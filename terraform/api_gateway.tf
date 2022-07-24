resource "aws_api_gateway_rest_api" "josiah" {
  name        = "JosiahWeb"
  description = "Josiah's Button Mashing Game"
}

output "base_url" {
  value = "${aws_api_gateway_deployment.josiah.invoke_url}"
}