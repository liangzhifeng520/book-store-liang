from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'admin/', admin.site.urls),   #django2.0只支持path的写法
    url(r'^tinymce/', include('tinymce.urls')), # 富文本编辑器
    url(r'^search', include('haystack.urls')), # 全文检索框架

    url(r'^user/', include(('apps.user.urls', 'urls'), namespace='user')), # 用户模块
    # #2.0后，
    # 要用到namespace反向解释都要这样的格式
    url(r'^cart/', include(('apps.cart.urls', 'urls'), namespace='cart')), # 购物车模块
    url(r'^order/', include(('apps.order.urls','urls' ), namespace='order')), # 订单模块
    url(r'^', include(('apps.goods.urls', 'urls'), namespace='goods')), # 商品模块
]
