#!/usr/bin/env bash
# Fail si une commande échoue
set -o errexit

# Installer Firefox et geckodriver
apt-get update
apt-get install -y firefox-esr wget

# Télécharger et installer geckodriver (dernière version stable)
GECKO_VERSION=$(wget -qO- https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep tag_name | cut -d '"' -f4)
wget -q https://github.com/mozilla/geckodriver/releases/download/$GECKO_VERSION/geckodriver-$GECKO_VERSION-linux64.tar.gz
tar -xzf geckodriver-$GECKO_VERSION-linux64.tar.gz -C /usr/local/bin
rm geckodriver-$GECKO_VERSION-linux64.tar.gz

echo "✅ Firefox + geckodriver installés"
