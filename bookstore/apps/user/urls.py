from django.conf.urls import url
from django.contrib.auth.decorators import login_required  #判断是否登录的装饰器（防止没登陆的去访问后台 ）
from user.views import RegisterView, ActiveView, LoginView, LogoutView, UserInfoView, UserOrderView, AddressView
urlpatterns = [
    #url(r'^register$', views.register, name='register'), #注册
    url(r'^register$',RegisterView.as_view(), name='register' ),
    #as_view()方法是一个View类里面的方法，用来分发访问方式，再调用相应的Register的视图
    url(r'^active/(?P<token>.*)', ActiveView.as_view(), name='active'), #用户激活
    url(r'^login$', LoginView.as_view(), name='login'), #登录页面
    url(r'^logout$', LogoutView.as_view(), name='logout'),  #注销登录

    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心-信息页
    # url(r'^order$',login_required(UserOrderView.as_view()), name='order'), #用户中心-订单页
    # url(r'^address$',login_required(AddressView.as_view()), name='address'), #用户中心-地址页
    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-信息页
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单页
    url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心-地址页

]

