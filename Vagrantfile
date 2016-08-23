# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/23/Cloud/x86_64/Images/Fedora-Cloud-Base-Vagrant-23-20151030.x86_64.vagrant-libvirt.box"
  config.vm.box = "f23-cloud-libvirt"
  config.vm.network "forwarded_port", guest: 5000, host: 5001
  config.vm.synced_folder ".", "/vagrant", type: "sshfs"

  config.vm.provision "shell", inline: "sudo dnf -y install python redhat-rpm-config python-devel postgresql-devel postgresql-server rpl python-alembic python-psycopg2 gcc"

  config.vm.provision "shell", inline: "pip install kitchen paver urllib3"
  config.vm.provision "shell", inline: "pip install -r /vagrant/requirements.txt"

  config.vm.provision "shell", inline: "sudo postgresql-setup initdb"

  config.vm.provision "shell", inline: "sudo rpl 'host    all             all             127.0.0.1/32            ident' 'host    all             all             127.0.0.1/32            trust' /var/lib/pgsql/data/pg_hba.conf"
  config.vm.provision "shell", inline: "sudo rpl 'host    all             all             ::1/128                 ident' 'host    all             all             ::1/128                 trust' /var/lib/pgsql/data/pg_hba.conf"

  config.vm.provision "shell", inline: "sudo systemctl enable postgresql.service"
  config.vm.provision "shell", inline: "sudo systemctl start postgresql.service"

  config.vm.provision "shell", inline: "pushd /tmp/; curl -O https://infrastructure.fedoraproject.org/infra/db-dumps/pkgdb2.dump.xz; popd;"
  config.vm.provision "shell", inline: "sudo runuser -l postgres -c 'createdb pkgdb2'"

  config.vm.provision "shell", inline: "xzcat /tmp/pkgdb2.dump.xz | sudo runuser -l postgres -c 'psql pkgdb2'"

  # Set up development.ini
  config.vm.provision "shell", inline: "cp /vagrant/pkgdb2/default_config.py /vagrant/pkgdb2/vagrant_default_config.py", privileged: false
  config.vm.provision "shell", inline: "pushd /vagrant/; rpl 'sqlite:////var/tmp/pkgdb2_dev.sqlite' 'postgresql://postgres:whatever@localhost/pkgdb2' /vagrant/pkgdb2/vagrant_default_config.py; popd;"
  config.vm.provision "shell", inline: "echo 'Provisioning Complete. Connect to your new vagrant box with'"
  config.vm.provision "shell", inline: "echo 'vagrant ssh'"
  config.vm.provision "shell", inline: "echo 'Then start the pkdb2 server with'"
  config.vm.provision "shell", inline: "echo 'pushd /vagrant/; ./runserver.py -c pkgdb2/vagrant_default_config.py --host \"0.0.0.0\";'"
 

end

