#!/bin/sh 
case $1 in                                        
   start) cd /home/admin/django/dailyfresh && celery multi start w1 -A  celery_tasks.tasks -l info;;  # django项目根目录 : /opt/django-celery/
   stop) cd /home/admin/django/dailyfresh && celery multi stop w1 -A  celery_tasks.tasks -l info;; # django项目根目录 : /opt/django-celery/
   *) echo "require start|stop" ;;     
esac
