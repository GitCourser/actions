FROM ccr.ccs.tencentyun.com/scf-repo/runtime-python3:latest

ADD *.sh /

ENTRYPOINT ["sh", "/entrypoint.sh"]
