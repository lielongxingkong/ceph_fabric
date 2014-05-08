#!/usr/bin/env python
# encoding: utf-8

from fabric.api import *
import os

HOSTNAME_CONF = "/etc/sysconfig/network"
DEPLOY_CONF_DIR = "/home/ceph/my_cluster"
HOSTS_CONF = "/etc/hosts"
OSD_PATH = "/var/local/"
AUTH_KEYS = "./authorized_keys"

cmd = "if [ -f ~/.ssh/id_rsa.pub ];then cat ~/.ssh/id_rsa.pub > %s; \
                    else echo > %s; fi" % (AUTH_KEYS, AUTH_KEYS)

os.system(cmd)

host_ip_map =  {
	'node1' : "192.168.1.21",
	'node2' : "192.168.1.22",
	'node3' : "192.168.1.23",
	'deploy' : '192.168.1.11',
}

all_nodes = host_ip_map.keys()
storage_nodes = [ i for i in host_ip_map.keys() if i != 'deploy']
monitors = ['node1', 'node2', 'node3']
osds = {
	'node1' : 'osd0',
	'node2' : 'osd1',
	'node3' : 'osd2',
}
osd_names = osds.values()
osd_nodes = osds.keys()
deploy = ['deploy']
debug = ['node1']

all_list = " " . join(all_nodes)
storage_list = " " . join(storage_nodes)
monitor_list = " " . join(monitors)
osd_name_list = " " . join(osd_names)
osd_list = " " . join(osd_nodes)

# set(all) = set(storage) + set(deploy)
# set(osd) in set(storage)
# set(monitor) in set(storage)
env.roledefs = {
	'all' : all_nodes,
	'storage' : storage_nodes,
	'deploy' : deploy,
	'monitor' : monitors,
	'osd' : osd_nodes,
	'debug' : debug,
}

passwd_dict = {
	'root' : '123456aA',
	'ceph' : 'ceph',
}
env.user = "root"
env.password = passwd_dict['root']

osd_map = " " . join("%s:%s%s" % (k, OSD_PATH, v) for k, v in osds.items())

#functions
@roles('debug')
def _debug():
	run("test " + OSD_PATH + osds[env.host])

@roles('storage')
def set_hosts():
	hosts = "\n" . join(["%s\t%s" % (v, k) for (k, v) in host_ip_map.items()]) + "\n"
	run('printf %s >> /etc/hosts' % repr(hosts))

@roles('deploy')
def set_deploy_hosts():
	set_hosts()

@roles('all')
def hostname():
	run('hostname %s' % env.host)

@roles('all')
def add_user():
	run('useradd -d /home/ceph -m ceph')
	run("echo 'ceph' | passwd ceph --stdin")
	run("echo 'ceph ALL = (root) NOPASSWD:ALL' | tee /etc/sudoers.d/ceph")
	run("chmod 0440 /etc/sudoers.d/ceph")
	run("sed -i 's/^Defaults.*requiretty/#[comment by ceph]&/' /etc/sudoers")

@roles('storage')
def ssh_keygen():
	run("ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa")
	key = run("cat ~/.ssh/id_rsa.pub")
	f = open(AUTH_KEYS, 'a')
	f.write(key + "\n")
	f.close()

@roles('storage')
def dispatch_auth_key():
	put(AUTH_KEYS, '~/.ssh/authorized_keys')
	run('chmod 600 ~/.ssh/authorized_keys')

@roles('storage')
def clean_auth_key():
	run('rm -f /home/ceph/.ssh/*')

@roles('deploy')
def install_deploy():
	put('./ceph.repo', '/etc/yum.repos.d/ceph.repo')
	run('yum makecache && yum install ceph-deploy')

@roles('deploy')
def create_config_dir():
	run('mkdir -p %s' % DEPLOY_CONF_DIR)

@roles('deploy')
def create_cluster():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy new %s' % monitor_list)

@roles('deploy')
def install_ceph():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy install %s' % storage_list)

@roles('deploy')
def initial_monitors():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy mon create-initial')

@roles('osd')
def create_osd_dir():
	sudo('mkdir -p %s%s' % (OSD_PATH, osds[env.host]))
	run('ls %s' % OSD_PATH)

@roles('osd')
def remove_osd_dir():
	run('rm -fr %s%s' % (OSD_PATH, osds[env.host]))
	run('ls %s' % OSD_PATH)

@roles('deploy')
def prepare_osd():
	with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy osd prepare %s' % osd_map)

@roles('deploy')
def activate_osd():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy osd activate %s' % osd_map)

@roles('deploy')
def dispatch_conf():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy admin %s' % storage_list)

@roles('deploy')
def purgedata():
	run('ceph-deploy purgedata %s' % storage_list)

@roles('deploy')
def forgetkeys():
	run('ceph-deploy forgetkeys')

@roles('deploy')
def purge():
	run('ceph-deploy purge %s' % storage_list)

#tasks
def set_hostname():
	execute(hostname)

def init_local():
	execute(set_local_hosts)

def init():
	execute(set_hosts)
	execute(hostname)
	execute(add_user)
	execute(install_deploy)

def make_auth():
	execute(ssh_keygen)
	execute(dispatch_auth_key)

def make_ceph_auth():
	with settings(user='ceph', password='ceph'):
		make_auth()

def deploy_ceph():
	with settings(user='ceph', password='ceph'):
		execute(create_config_dir)
		execute(create_cluster)
		execute(install_ceph)
		execute(initial_monitors)
		execute(create_osd_dir)
		execute(prepare_osd)
		execute(activate_osd)
		execute(dispatch_conf)

def purge_ceph_data():
	execute(purgedata)

def purge_ceph_keys():
	execute(forgetkeys)

def purge_ceph_all():
	execute(purge)

def debug():
	execute(create_osd_dir)
	execute(remove_osd_dir)
	#execute(_debug)
