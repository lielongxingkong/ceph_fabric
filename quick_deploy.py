#!/usr/bin/env python
# encoding: utf-8

from fabric.api import *

host_ip_map =  {
	'node1' : "192.168.1.21",	
	'node2' : "192.168.1.22",	
	'node3' : "192.168.1.23",	
	'deploy' : '192.168.1.11',	
}

all = host_ip_map.keys()
nodes = [ i for i in host_ip_map.keys() if i != 'deploy']
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

all_list = " " . join(all)
node_list = " " . join(nodes)
monitor_list = " " . join(monitors)
osd_name_list = " " . join(osd_names)
osd_node_list = " " . join(osd_nodes)

env.roledefs = {
	'all' : all, 
	'node' : nodes, 
	'deploy' : deploy, 
	'monitor' : monitors,
	'osd' : osd_nodes,
	'debug' : debug,
	'local' : ['localhost'],
}

passwd_dict = {
	'root' : '123456aA',
	'ceph' : 'ceph',
}
env.user = "root"
env.password = passwd_dict['root']

HOSTNAME_CONF = "/etc/sysconfig/network"
DEPLOY_CONF_DIR = "/home/ceph/my_cluster"
HOSTS_CONF = "/etc/hosts"
OSD_PATH = "/var/local/"

osd_map = " " . join("%s:%s%s" % (k, OSD_PATH, v) for k, v in osds.items())

'''
print "node_list: ", node_list
print "monitor_list: ", monitor_list
print "osd_name_list: ", osd_name_list
print "osd_node_list: ", osd_node_list
for k,v in env.roledefs.items():
	print str(k) + " => " + str(v)
'''

#functions 

#sub-tasks

@roles('debug')
def _debug():
	run("test " + OSD_PATH + osds[env.host])

@roles('node')
def set_hosts():
	hosts = "\n" . join(["%s\t%s" % (v, k) for (k, v) in host_ip_map.items()]) + "\n"
	run('printf %s >> /etc/hosts' % repr(hosts))

@roles('local')
def set_local_hosts():
	set_hosts() 

@roles('node', 'deploy')
def hostname():
	run('hostname %s' % env.host)

@roles('node', 'deploy')
def add_user():
	run('useradd -d /home/ceph -m ceph')
	run("echo 'ceph' | passwd ceph --stdin")
	run("echo 'ceph ALL = (root) NOPASSWD:ALL' | tee /etc/sudoers.d/ceph")
	run("chmod 0440 /etc/sudoers.d/ceph")
	run("sed -i 's/^Defaults.*requiretty/#[comment by ceph]&/' /etc/sudoers")

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
		run('ls')

@roles('deploy')
def install_ceph():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy install %s' % node_list)

@roles('deploy')
def initial_monitors():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy mon create-initial')

@roles('osd')
def create_osd_dir():
	run('mkdir -p %s%s' % (OSD_PATH, osds[env.host])) 
	run('ls %s' % OSD_PATH)

@roles('osd')
def remove_osd_dir():
	run('rm -fr %s%s' % (OSD_PATH, osds[env.host]))
	run('ls %s' % OSD_PATH)

@roles('osd')
def prepare_osd():
	run('ceph-deploy osd prepare %s' % osd_map)

@roles('osd')
def activate_osd():
	run('ceph-deploy osd activate %s' % osd_map)

@roles('deploy')
def dispatch_conf():
    with cd(DEPLOY_CONF_DIR):
		run('ceph-deploy admin %s' % node_list)

@roles('deploy')
def purgedata():
	run('ceph-deploy purgedata %s' % node_list)

@roles('deploy')
def forgetkeys():
	run('ceph-deploy forgetkeys')

@roles('deploy')
def purge():
	run('ceph-deploy purge %s' % node_list)

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

def deploy_ceph():
	with settings(user='ceph', password='ceph'):
		execute(create_config_dir)
		execute(create_cluster)
		execute(install_ceph)
		execute(initial_monitors)
		#create_osd_dir)
		#prepare_osd)
		#activate_osd)
		#dispatch_conf)

def purge_ceph_data():
	execute(purge_data)

def purge_ceph_package():
	execute(forgetkeys)

def purge_ceph_all():
	execute(purge)

def debug():
	execute(create_osd_dir)
	execute(remove_osd_dir)
	#execute(_debug)

