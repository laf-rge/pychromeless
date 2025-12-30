# Frontend deployment to Namecheap server
# Note: References SSM parameters created in ssm.tf

# Build frontend
resource "null_resource" "frontend_build" {
  triggers = {
    # Trigger rebuild when package files change
    package_json = filebase64sha256("${path.module}/../frontend/package.json")
    # bun.lockb may not exist initially, so we use try() to handle that
    bun_lockb = try(filebase64sha256("${path.module}/../frontend/bun.lockb"), "initial")
    # Or trigger on source files if you want more granular control
    # source_hash = sha256(join("", [
    #   for f in fileset("${path.module}/../frontend/src", "**") :
    #   filesha256("${path.module}/../frontend/src/${f}")
    # ]))
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${path.module}/../frontend && \
      bun install --frozen-lockfile && \
      bun run build
    EOT
  }
}

# Depend on SSM parameters being created first
resource "null_resource" "frontend_build_wait" {
  depends_on = [
    aws_ssm_parameter.namecheap_server_host,
    aws_ssm_parameter.namecheap_server_user,
    aws_ssm_parameter.namecheap_server_path,
    aws_ssm_parameter.namecheap_server_port,
    aws_ssm_parameter.namecheap_ssh_key,
  ]
  triggers = {
    # This resource just ensures SSM parameters exist before deployment
    ssm_params = join(",", [
      aws_ssm_parameter.namecheap_server_host.id,
      aws_ssm_parameter.namecheap_server_user.id,
      aws_ssm_parameter.namecheap_server_path.id,
      aws_ssm_parameter.namecheap_server_port.id,
      aws_ssm_parameter.namecheap_ssh_key.id,
    ])
  }
}

# Deploy frontend to Namecheap server
resource "null_resource" "frontend_deploy" {
  triggers = {
    # Trigger deployment when build output changes
    frontend_hash = filebase64sha256("${path.module}/../frontend/dist/index.html")
    # Also trigger when build completes
    build_id = null_resource.frontend_build.id
    # Trigger when SSM parameters change
    ssm_params = null_resource.frontend_build_wait.id
  }

  depends_on = [
    null_resource.frontend_build,
    null_resource.frontend_build_wait,
  ]

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      echo "Starting frontend deployment..."
      echo "Deploying to: ${aws_ssm_parameter.namecheap_server_user.value}@${aws_ssm_parameter.namecheap_server_host.value}:${aws_ssm_parameter.namecheap_server_path.value}"

      # Write SSH key to temp file
      echo '${aws_ssm_parameter.namecheap_ssh_key.value}' > /tmp/namecheap_deploy_key_${terraform.workspace}
      chmod 600 /tmp/namecheap_deploy_key_${terraform.workspace}
      echo "SSH key written to temporary file"

      # Check if dist directory exists
      if [ ! -d "${path.module}/../frontend/dist" ]; then
        echo "ERROR: dist directory does not exist. Build may have failed."
        exit 1
      fi

      # Count files to be deployed
      FILE_COUNT=$(find ${path.module}/../frontend/dist -type f | wc -l)
      echo "Found $FILE_COUNT files to deploy in dist directory"
      echo "Sample files:"
      ls -lh ${path.module}/../frontend/dist/ | head -10

      echo "Syncing files from ${path.module}/../frontend/dist/ to server..."
      # Deploy using rsync
      rsync -avz --delete --progress \
        -e "ssh -i /tmp/namecheap_deploy_key_${terraform.workspace} -p ${aws_ssm_parameter.namecheap_server_port.value} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
        ${path.module}/../frontend/dist/ \
        ${aws_ssm_parameter.namecheap_server_user.value}@${aws_ssm_parameter.namecheap_server_host.value}:${aws_ssm_parameter.namecheap_server_path.value}/

      echo "Deployment completed successfully!"

      # Verify deployment by checking files on server
      echo "Verifying deployment..."
      SERVER_FILE_COUNT=$(ssh -i /tmp/namecheap_deploy_key_${terraform.workspace} -p ${aws_ssm_parameter.namecheap_server_port.value} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
        ${aws_ssm_parameter.namecheap_server_user.value}@${aws_ssm_parameter.namecheap_server_host.value} \
        "find ${aws_ssm_parameter.namecheap_server_path.value} -type f | wc -l" 2>/dev/null || echo "0")

      if [ -f "${path.module}/../frontend/dist/index.html" ]; then
        ssh -i /tmp/namecheap_deploy_key_${terraform.workspace} -p ${aws_ssm_parameter.namecheap_server_port.value} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
          ${aws_ssm_parameter.namecheap_server_user.value}@${aws_ssm_parameter.namecheap_server_host.value} \
          "test -f ${aws_ssm_parameter.namecheap_server_path.value}/index.html && echo '✓ index.html found on server' || echo '✗ ERROR: index.html not found on server'"
        echo "Server has $SERVER_FILE_COUNT files deployed"
      else
        echo "✗ ERROR: index.html not found locally, cannot verify"
      fi

      # Clean up SSH key
      rm /tmp/namecheap_deploy_key_${terraform.workspace}
      echo "Temporary SSH key cleaned up"
    EOT
  }
}

# Output deployment status
output "frontend_deployment_status" {
  value       = "Frontend deployed to ${aws_ssm_parameter.namecheap_server_host.value}${aws_ssm_parameter.namecheap_server_path.value}"
  sensitive   = true
  depends_on  = [null_resource.frontend_deploy]
}
