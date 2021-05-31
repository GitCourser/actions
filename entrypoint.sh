mkdir -p /root/.ssh
echo "$KEY0" > /root/.ssh/id_rsa
echo "$KEY1" > /root/.ssh/id1_rsa
chmod 600 /root/.ssh/*_rsa

cd /root
git clone "git@$1.git" repo
cd /root/.ssh
mv id_rsa id0_rsa
mv id1_rsa id_rsa
cd /root/repo
git remote add gitee "git@gitee.com:$2.git"
git remote add github "git@github.com:$3.git"
# git push gitee master
# git push github master
git push --all gitee
git push --all github
