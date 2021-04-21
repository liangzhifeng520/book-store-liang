#使用celery
'''Celery - 分布式任务队列
Celery 是一个简单、灵活且可靠的，处理大量消息的分布式系统，并且提供维护这样一个系统的必需工具。
它是一个专注于实时处理的任务队列，同时也支持任务调度。'''
from celery import Celery
from django.conf import settings    #导入jdango的密钥
from django.core.mail import send_mail
from django.template import loader
import time

#在任务处理者一端加这几句
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookstore.settings') #设置环境变量
django.setup()   #设置django初始化

from goods.models import GoodsType,IndexGoodsBanner,IndexPromotionBanner,IndexTypeGoodsBanner
from django_redis import get_redis_connection

#创建一个Celery类的实例对象 指定执行的中间人
app = Celery('celery_tasks.tasks', broker='redis://47.103.204.150:6379/8') #(tasks文件夹，redis数据库的地址/端口/数据库名)

#定义任务函数
@app.task   #装饰函数有delay方法
def send_register_active_email(to_email, username, token):
    '''发送激活邮件'''
    #组织邮件信息
    subject = '良辰线上书城欢迎信息'  # 邮箱标题
    message = ''  # 邮箱正文
    sender = settings.EMAIL_FROM  #收件人看到的发件人邮箱
    receiver = [to_email]
    html_message = '<h1>%s, 欢迎您成为良辰线上书城注册会员<h1>请点击下面链接激活您的账号<br/>' \
                   '<a href="http://47.103.204.150/user/active/%s">http://47.103.204.150/user/active/%s</a>' % (
                   username, token, token)  # html格式邮箱正文
    send_mail(subject, message, sender, receiver, html_message=html_message)  # 发送
    time.sleep(5)


@app.task
def generate_static_index_html():
    '''产生首页静态页面'''
    # 获取商品的种类信息
    # 先睡两秒，以防数据库更新太慢，数据还没更新就已经生成页面
    time.sleep(2)

    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的图片展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
        type.image_banners = image_banners
        type.title_banners = title_banners

    # 获取购物车商品数目
    cart_count = 0

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners,
               'cart_count': cart_count,}

    # 使用模板
    # 使用模板
    #return render(request, 'index.html', context)  #返回的是HttpResponse对象
    # 1.加载模板文件,返回模板对象
    temp = loader.get_template('static_index.html')
    # 2.模板渲染
    static_index_html = temp.render(context)

    # 生成首页对应静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')  #设置保存的路径，settings.BASE_DIR代表bookstore的根目录
    with open(save_path, 'w') as f:
        f.write(static_index_html)













