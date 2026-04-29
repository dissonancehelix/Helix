#!/bin/bash
# Trails Database — MediaWiki setup script
# Run this inside WSL Ubuntu: bash /mnt/c/Users/dissonance/Desktop/Trails/scripts/setup_mediawiki.sh

set -e

MW_VERSION="1.41.5"
MW_DIR="/var/www/html/wiki"
DB_NAME="trails_wiki"
DB_USER="wiki_user"
DB_PASS="trailsdb2026"

echo "=== [1/5] Starting MariaDB ==="
sudo service mariadb start

echo "=== [2/5] Creating database and user ==="
sudo mariadb -e "
  CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
  GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
  FLUSH PRIVILEGES;
"
echo "Database ready: ${DB_NAME}"

echo "=== [3/5] Downloading MediaWiki ${MW_VERSION} ==="
cd /tmp
if [ ! -f "mediawiki-${MW_VERSION}.tar.gz" ]; then
  wget -q --show-progress "https://releases.wikimedia.org/mediawiki/1.41/mediawiki-${MW_VERSION}.tar.gz"
fi
tar -xzf "mediawiki-${MW_VERSION}.tar.gz"
sudo rm -rf "${MW_DIR}"
sudo mv "mediawiki-${MW_VERSION}" "${MW_DIR}"
sudo chown -R www-data:www-data "${MW_DIR}"

# NOTE: Extensions (Cargo, Page Forms, Page Schemas, Scribunto, Approved Revs,
# AbuseFilter, TemplateData) will be installed separately.
# Download them from: https://www.mediawiki.org/wiki/Special:ExtensionDistributor
# and extract each into ${MW_DIR}/extensions/
echo "=== Extensions: skipped — install manually via Special:ExtensionDistributor ==="

echo "=== [4/5] Composer dependencies ==="
command -v composer &>/dev/null || {
  wget -q https://getcomposer.org/installer -O /tmp/composer-setup.php
  sudo php /tmp/composer-setup.php --install-dir=/usr/local/bin --filename=composer
}
cd "${MW_DIR}"
sudo -u www-data composer install --no-dev --quiet 2>&1 | tail -5

echo "=== [5/5] Apache config ==="
sudo bash -c "cat > /etc/apache2/sites-available/trails-db.conf << 'EOF'
<VirtualHost *:8080>
    ServerName localhost
    DocumentRoot /var/www/html/wiki
    <Directory /var/www/html/wiki>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog \${APACHE_LOG_DIR}/wiki_error.log
    CustomLog \${APACHE_LOG_DIR}/wiki_access.log combined
</VirtualHost>
EOF"

grep -q "Listen 8080" /etc/apache2/ports.conf || sudo sed -i '/Listen 80$/a Listen 8080' /etc/apache2/ports.conf

sudo a2ensite trails-db.conf
sudo a2enmod rewrite
sudo service apache2 restart

echo ""
echo "=== Setup complete ==="
echo "MediaWiki: ${MW_DIR}"
echo "DB: ${DB_NAME} / ${DB_USER} / ${DB_PASS}"
echo ""
echo "Next: run the CLI installer:"
echo "  sudo -u www-data php ${MW_DIR}/maintenance/install.php \\"
echo "    --dbtype mysql --dbserver localhost --dbname ${DB_NAME} \\"
echo "    --dbuser ${DB_USER} --dbpass '${DB_PASS}' \\"
echo "    --server 'http://localhost:8080' --scriptpath '' \\"
echo "    --lang en --pass 'WikiAdmin2026!' \\"
echo "    'Trails Database' 'WikiAdmin'"
