#!/bin/bash

rm -rd site
rm -rd docs
rm -rd docs-test
rm mybank.db
rm -rd .playwright-mcp
rm mkdocs.yml

sudo apt-get install sqlite3 libxss1 libappindicator1 libindicator7 dbus-x11
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome*.deb
sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

google-chrome --headless=new --disable-dbus --screenshot=/tmp/cloud.png --dump-dom https://cloud.google.com
