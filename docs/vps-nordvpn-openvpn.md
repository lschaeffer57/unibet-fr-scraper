# VPS : tout le trafic via NordVPN (OpenVPN)

Une fois le tunnel **actif sur le système**, Python et le scraper sortent automatiquement par NordVPN : **pas besoin** de `NORDVPN_SOCKS_HOST` ni d’`UNIBET_SOCKS_PROXY`.

## 1. Sur le site Nord (my.nordaccount.com)

1. **NordVPN** → **Configuration**.
2. Onglet **Identifiants de service** : note le **nom d’utilisateur** et le **mot de passe** (ce ne sont **pas** l’email et le mot de passe du compte web).
3. Onglet **Fichiers de configuration OpenVPN** : télécharge un **.ovpn** TCP ou UDP pour le pays voulu (ex. France / Pays-Bas).

## 2. Sur le VPS (Debian / Ubuntu)

### Paquet OpenVPN

```bash
sudo apt-get update
sudo apt-get install -y openvpn
```

### Fichiers côté serveur

1. Copie le `.ovpn` sur le VPS, puis installe-le comme config client :

   ```bash
   sudo cp chemin/vers/ton-fichier.ovpn /etc/openvpn/client/nordvpn.conf
   sudo chmod 600 /etc/openvpn/client/nordvpn.conf
   ```

2. Crée un fichier d’authentification (**ligne 1 = user service**, **ligne 2 = mot de passe service**) :

   ```bash
   sudo nano /etc/openvpn/client/nordvpn.auth
   ```

   Contenu :

   ```text
   TON_UTILISATEUR_SERVICE
   TON_MOT_DE_PASSE_SERVICE
   ```

   Puis :

   ```bash
   sudo chmod 600 /etc/openvpn/client/nordvpn.auth
   ```

3. Édite `/etc/openvpn/client/nordvpn.conf` et remplace la ligne :

   ```text
   auth-user-pass
   ```

   par :

   ```text
   auth-user-pass /etc/openvpn/client/nordvpn.auth
   ```

   (S’il y a déjà un chemin vers un autre fichier, garde un seul `auth-user-pass` cohérent avec `nordvpn.auth`.)

### Démarrage au boot (systemd)

Le paquet fournit en général l’instance `openvpn-client@`.

```bash
sudo systemctl enable openvpn-client@nordvpn
sudo systemctl start openvpn-client@nordvpn
sudo systemctl status openvpn-client@nordvpn
```

Le nom après `@` doit être le **basename** du fichier sans `.conf` : ici `nordvpn` pour `nordvpn.conf`.

### Vérifier que le trafic sort par le VPN

```bash
curl -s https://api.ipify.org ; echo
# compare avec curl depuis ta machine sans VPN — l’IP doit être différente (Datacenter NordVPN)
```

Ou :

```bash
ip route
# une route par défaut ou une table liée à tun0 peut apparaître selon le .ovpn
```

## 3. Lancer le scraper

Sur **le même VPS**, sans variables proxy :

```bash
cd /chemin/vers/unibet-fr-scraper
source .venv/bin/activate   # si venv
python unibet_all_json.py
```

## 4. Pièges fréquents

| Problème | Piste |
|----------|--------|
| Le scraper est dans **Docker** | Le conteneur a souvent **son propre réseau** : il ne passe pas par le VPN de l’hôte. Solutions : `network_mode: host`, ou lancer Python **sur l’hôte**, ou utiliser le SOCKS applicatif (`UNIBET_SOCKS_PROXY`) depuis le conteneur. |
| **DNS** qui fuit ou ne résout pas | Voir les directives `dhcp-option DNS` dans le `.ovpn` Nord ; tester `dig www.unibet.fr`. |
| Tunnel **down** après reboot | Vérifier `systemctl is-enabled openvpn-client@nordvpn` et les journaux : `journalctl -u openvpn-client@nordvpn -e`. |

## 5. Sécurité

- Ne commite **jamais** `nordvpn.auth` ni un `.ovpn` contenant des clés privées dans un dépôt public.
- Révoque / régénère les **identifiants de service** sur Nord si tu penses qu’ils ont fuité.
