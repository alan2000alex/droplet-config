output "droplet_ip" {
  description = "Public IPv4 address of the workload droplet"
  value       = digitalocean_droplet.workload.ipv4_address
}
