FROM hivestack/python-392
# FROM centos/python-36-centos7
# FROM agileware/python-3.6.1-node-6.11

ADD *.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]
