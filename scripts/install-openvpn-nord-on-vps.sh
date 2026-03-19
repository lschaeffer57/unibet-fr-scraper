#!/bin/sh
# Exécuter sur le VPS en root : installe openvpn-client (Debian/Ubuntu).
# Ensuite : copier nordvpn.conf + nordvpn.auth comme dans docs/vps-nordvpn-openvpn.md

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Lancer avec : sudo $0"
  exit 1
fi

apt-get update
apt-get install -y openvpn

install -d -m 755 /etc/openvpn/client
echo "OpenVPN installé."
echo "1) sudo cp ton-fichier.ovpn /etc/openvpn/client/nordvpn.conf && sudo chmod 600 /etc/openvpn/client/nordvpn.conf"
echo "2) Créer /etc/openvpn/client/nordvpn.auth (2 lignes : user service, pass service) chmod 600"
echo "3) Dans nordvpn.conf : auth-user-pass /etc/openvpn/client/nordvpn.auth"
echo "4) sudo systemctl enable --now openvpn-client@nordvpn"
echo "Doc : docs/vps-nordvpn-openvpn.md"
