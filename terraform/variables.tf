variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "droplet_size" {
  description = "Droplet size slug (see: doctl compute size list)"
  type        = string
  default     = "s-1vcpu-1gb"
}

variable "region" {
  description = "DigitalOcean region slug"
  type        = string
  default     = "blr1"
}

variable "droplet_name" {
  description = "Name assigned to the droplet"
  type        = string
  default     = "workload-vm"
}

# variable "ssh_public_key" {
#   description = "SSH public key content to register with DigitalOcean (passed via TF_VAR_ssh_public_key)"
#   type        = string
#   sensitive   = true
# }
