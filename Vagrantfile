# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  config.vm.box_url = "https://download.fedoraproject.org/pub/fedora/linux/releases/23/Cloud/x86_64/Images/Fedora-Cloud-Base-Vagrant-23-20151030.x86_64.vagrant-libvirt.box"
  config.vm.box = "f23-cloud-libvirt"
  config.vm.network "forwarded_port", guest: 5000, host: 5001
  config.vm.synced_folder ".", "/vagrant", type: "sshfs"

  # Ansible needs the guest to have these
  config.vm.provision "shell", inline: "sudo dnf install -y libselinux-python python2-dnf"

  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "devel/ansible/playbook.yml"
  end
  
  config.vm.post_up_message = "Provisioning Complete. Connect to your new vagrant box with\nvagrant ssh\nThen start the pkdb2 server with\npushd /vagrant/; ./runserver.py -c pkgdb2/vagrant_default_config.py --host \"0.0.0.0\";\nYour fresh pkgdb2 instance will now be accessible at\nhttp://localhost:5001/"

end
