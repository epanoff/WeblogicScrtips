from optparse import OptionParser
import os
import sys


# Print state of cluster
def print_cluster_state(cluster_name):
    try:
       state(cluster_name,"Cluster")
    except Exception, e:
       print 'Error while printing cluster state ',e
       dumpStack()


# check state of all cluster members if equal to RUNNING
def check_state_of_cluster_members(cluster_name, desired_state):
    try:
        domainConfig()
        cd('/')
        servers = cmo.getServers()
        domainRuntime()
        cd('/')
        collectedServers = []
        for server in servers:
            if server.getCluster() != None and server.getCluster().getName() == cluster_name:
                serverRuntimeMBean = getMBean('/ServerLifeCycleRuntimes/' + server.getName())
                serverState = serverRuntimeMBean.getState()
                if serverState != desired_state:
                    collectedServers.append(server.getName())
        if len(collectedServers) > 0:
           # oh oh not in desired state
           return 'false'
        else:
           # ok all servers in desired state
           return 'true'
    except Exception, e:
        print 'Error while checking member states ', e
        dumpStack()
        return 'false'


# check state of all cluster members if equal to RUNNING
def check_if_all_servers_of_cluster_are_running(cluster_name):
    return check_state_of_cluster_members(cluster_name, "RUNNING")


# check state of all cluster members if equal to desired mode
def check_if_all_servers_of_cluster_are_stopped(clustername):
    return check_state_of_cluster_members(clustername, "SHUTDOWN")


def start_cluster(cluster_name):
    try:
       start(cluster_name, "Cluster")
    except Exception, e:
       print 'Error while starting cluster ', e
       dumpStack()


def shutdown_cluster(cluster_name):
    try:
       shutdown(cluster_name, "Cluster", force="true")
    except Exception, e:
       print 'Error while shutting down cluster ', e
       dumpStack()


def startup_server(server_name):
    try:
       cd('domainRuntime:/ServerLifeCycleRuntimes/' + server_name)
       if server_status(server_name) in ['RUNNING', 'ADMIN']:
          print 'Server already running'
       else:
          start(server_name, 'Server', block='true')
       state = server_status(server_name)
       print state;
       while (state != 'RUNNING'):
          state = server_status(server_name)
          print state
          restart_delay(3000)
    except:
        print 'Error in getting current status of ' + server_name + '\n'
        print 'Please check logged in user has full access to complete the start operation on ' + server_name + '\n'
        sys.exit(8)


def shutdown_server(server_name):
    try:
      cd('domainRuntime:/ServerLifeCycleRuntimes/' + server_name)
      print 'Stoppping server ' + server_name
      if server_status(server_name) in ['SHUTDOWN', 'FAILED','FAILED_NOT_RESTARTABLE']:
        print 'Server already shutdowned'
      else:
        shutdown(server_name, 'Server', 'true', 1200, 'true', block='true')
        state = server_status(server_name)
        while ( state != 'SHUTDOWN' ):
            state=server_status(server_name)
            java.lang.Thread.sleep(5000)
    except:
        print 'Error in getting current status of ' + server_name + '\n'
        print 'Please check logged in user has full access to complete the stop operation on ' + server_name + '\n'
        sys.exit(9)


def shutdown_cluster_and_wait_for_shutdown(cluster_name):
    if check_if_all_servers_of_cluster_are_stopped(cluster_name) == 'true':
        print 'Cluster is already down'
        return
    # shutdown
    shutdown_cluster(cluster_name)

    currentcount = 0

    while ((check_if_all_servers_of_cluster_are_stopped(cluster_name) == 'false') and (currentcount < 30)):
        print 'Not yet all memebers of cluster in state SHUTDOWN - will wait for 10sec.'
        java.lang.Thread.sleep(10000)
        currentcount = currentcount + 1

    if (check_if_all_servers_of_cluster_are_stopped(cluster_name) == 'false'):
        print 'Sorry: Could not bring cluster to SHUTDOWN state !'


def server_status(server_name):
    try:
        cd('domainRuntime:/ServerLifeCycleRuntimes/' + server_name)
        server_state = cmo.getState()
        return server_state
    except:
        print 'Not able to get the' + server_state + 'server status. Please try again\n'
        print 'Please check logged in user has full access to complete the requested operation on ' + server_name + '\n'
        sys.exit(3)


def get_server_name_list_by_cluster(cluster):
    servName = []
    domainConfig()
    cd('/')
    servers = cmo.getServers()
    domainRuntime()
    cd('/')
    for server in servers:
        try:
            if server.getCluster().getName() == cluster:
                servName.append(server.getName())
        except AttributeError:
            print server.getName() + ' not in any cluster'
    return servName


def get_clusters():
    print "Installed Clusters:"
    cd('/Clusters')
    clusters = ls(returnMap="true")
    return clusters


def get_jndi_parameters_from_weblogic(string_initializer):
    try:
        array_par = []
        serverConfig()
        edit()
        cd('/StartupClasses/' + string_initializer)
        string_par = cmo.getArguments()
        for parameter in string_par.split(' '):
            array_par.append(parameter[:parameter.find('=')])
        return array_par
        save()
        stopEdit('y')
    except:
        print 'Not able to get the JNDI parameters from  /StartupClasses/ ' + StringInitializer + '.\n'
        sys.exit(4)


def get_jndi_parameters_from_file(file):
    try:
        arrayPar = []
        f = open(file, 'r')
        l = [line.strip() for line in f]
        for parameter in l:
            if not parameter.startswith('#'):
                if parameter[parameter.find('=') + 1:].startswith('java'):
                    arrayPar.append(parameter[parameter.rfind('=') + 1:])
        return arrayPar
    except:
        print 'Not able to get the JNDI parameters from ' + file + ' \n'
        sys.exit(5)


def check_jndi_parameters():
    jndi_parameters_from_file = get_jndi_parameters_from_file('./Beans/resources/ru/mvideo/bean/jndi.names.properties')
    jndi_parameters_from_weblogic = get_jndi_parameters_from_weblogic('StringInitializer')
    print jndi_parameters_from_file
    print jndi_parameters_from_weblogic
    for JNDI in jndi_parameters_from_file:
        if JNDI not in jndi_parameters_from_weblogic:
            print 'Error.  Add JNDI to Startup and Shutdown Classes ' + JNDI
            sys.exit(7)


def change_jndi_parameters(arguments):
    edit()
    startEdit()
    cd('/StartupClasses/StringInitializer')
    cmo.setArguments(arguments)
    save()
    print "JNDI added"


def add_jndi_parameters(arguments):
    edit()
    startEdit()
    cd('/StartupClasses/StringInitializer')
    arguments_now = cmo.getArguments()
    cmo.setArguments(arguments_now + " " + arguments)
    save()
    print "JNDI added"


def undeploy_app(app, ServersName):
    try:
        edit()
        startEdit()
        undeploy(appName=app, targets=ServersName)
        save()
        activate()
    except:
        print 'Error in undeploy application'


def deploy_app(app, path, servers_name):
    try:
        edit()
        startEdit()
        deploy(appName=app, path=path, targets = servers_name, remote='true', upload='true')
        save()
        activate()
    except:
        print 'Error in deploy application'
        sys.exit(2)


def get_application_status(app):
    cd('/')
    domainRuntime()
    cd('AppRuntimeStateRuntime/AppRuntimeStateRuntime')
    result = cmo.getIntendedState(app)
    return result


def restart_delay(dTime):
    java.lang.Thread.sleep(dTime)

def change_enforce_cred(domain):
    edit()
    startEdit()
    cd('SecurityConfiguration/' + domain)
    set('EnforceValidBasicAuthCredentials','false')
    save()
    activate()

def deploy_with_restart(file_path_ear, file_name_ear, weblogic_user_name, weblogic_password, weblogic_url):
    if os.path.isfile(file_path_ear + file_name_ear + '.ear'):
        connect(weblogic_user_name, weblogic_password,  weblogic_url)
        check_jndi_parameters()
        clusters = get_clusters()
        for cluster in clusters:
            servers = get_server_name_list_by_cluster(cluster)
            shutdown_cluster_and_wait_for_shutdown(cluster)
            restart_delay(3000)
            undeploy_app(file_name_ear + "_" + cluster , ",".join(servers))
            deploy_app(file_name_ear + "_" + cluster, file_path_ear + file_name_ear + '.ear', ",".join(servers))
            start_cluster(cluster)
            restart_delay(3000);
        state = get_application_status(file_name_ear + "_" + cluster)
        if state == 'STATE_ACTIVE':
            print file_name_ear + "_" + cluster + ' ' + state
        else:
            print file_name_ear + "_" + cluster + ' ' + str(state)
            sys.exit(1)
    else:
        print file_path_ear + file_name_ear + '.ear not exists'


def deploy_with_restart_server(file_path_ear, file_name_ear, weblogic_user_name, weblogic_password, weblogic_url, domain, server):
    if os.path.isfile(file_path_ear + file_name_ear + '.ear'):
        connect(weblogic_user_name, weblogic_password, weblogic_url)
        check_jndi_parameters()
        shutdown_server(server)
        undeploy_app(file_name_ear, server)
        restart_delay(3000)
        deploy_app(file_name_ear, file_path_ear + file_name_ear + '.ear', server)
        change_enforce_cred(domain)
        startup_server(server)
        restart_delay(3000)
        
        for x in range(0, 3):
           state = get_application_status(options.fileNameEAR)
           if state == 'STATE_ACTIVE':
               print options.fileNameEAR + ' ' + str(state)
               break
           else:
               print options.fileNameEAR + ' ' + str(state)
               restart_delay(3000)
               if x == 2:
                    sys.exit(1)         
    else:
        print options.filePathEAR + options.fileNameEAR + '.ear not exists'


parser = OptionParser()
parser.add_option('-a', '--action', dest='action',
                  help='deployWithRestart')
parser.add_option('-f', '--file',
                  dest='fileNameEAR', default='MVideo_Services_Platform',
                  help='Filename ear without file extension')
parser.add_option('-p', '--path',
                  dest='filePathEAR', default='./WebEar/target/',
                  help='Filename path ear')
parser.add_option('-u', '--weblogic-user-name',
                  dest='weblogicUserName', default='weblogic',
                  help='weblogic User Name')
parser.add_option('-w', '--weblogic-password',
                  dest='weblogicPassword', default='welcome0',
                  help='weblogic password')
parser.add_option('-r', '--weblogic-url',
                  dest='weblogicUrl', default='t3://localhost:7001',
                  help='weblogic url')
parser.add_option('-j', '--jndi',
                  dest='arguments', default='',
                  help='JNDI name arguments with format [jndiName=StringToAdd]*. Delimeter is space')
parser.add_option('-d', '--domain',
                  dest='domain', default='',
                  help='Weblogic Domain')
parser.add_option('-s', '--weblogic-server',
                  dest='weblogicServer', default='mvideo',
                  help='weblogic Server target ear')

(options, args) = parser.parse_args()

if options.action == 'deployWithRestartCluster':
    deploy_with_restart(options.filePathEAR, options.fileNameEAR, options.weblogicUserName, options.weblogicPassword, options.weblogicUrl)
    exit('y')

if options.action == 'deployWithRestart':
    deploy_with_restart_server(options.filePathEAR, options.fileNameEAR, options.weblogicUserName, options.weblogicPassword, options.weblogicUrl, options.domain, options.weblogicServer)
    exit('y')

if options.action == 'changeJNDI':
    connect(options.weblogicUserName, options.weblogicPassword, options.weblogicUrl)
    change_jndi_parameters(options.arguments)
    exit('y')

if options.action == 'addJNDI':
    connect(options.weblogicUserName, options.weblogicPassword, options.weblogicUrl)
    add_jndi_parameters(options.arguments)
    exit('y')
