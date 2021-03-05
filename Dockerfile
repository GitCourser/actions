FROM centos/python-36-centos7

ADD *.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]
