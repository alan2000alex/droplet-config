provider "digitalocean" {
  token = var.do_token
}

# resource "digitalocean_ssh_key" "workload" {
#   name       = "${var.droplet_name}-key"
#   public_key = var.ssh_public_key
# }

data "digitalocean_ssh_key" "default" {
  name = "alan-lunix"
}
resource "digitalocean_droplet" "workload" {
  image             = "ubuntu-24-04-x64"
  name              = var.droplet_name
  region            = var.region
  size              = var.droplet_size
  ssh_keys          = [data.digitalocean_ssh_key.default.id]
  graceful_shutdown = true

  # ssh_keys          = [digitalocean_ssh_key.workload.fingerprint]
}

resource "digitalocean_firewall" "workload" {
  name        = "${var.droplet_name}-fw"
  droplet_ids = [digitalocean_droplet.workload.id]

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}
