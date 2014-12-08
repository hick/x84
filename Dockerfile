FROM 192.157.212.96:5000/ubuntu1404
MAINTAINER  hick <hickwu@qq.com>

# add file
ADD run.sh  /
RUN chmod 755 /*.sh

# 暴露端口
EXPOSE 6023 6513
CMD ["/run.sh"]