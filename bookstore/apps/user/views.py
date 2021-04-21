from django.shortcuts import render, redirect
from user.models import User, Address
from django.http import HttpResponse,JsonResponse
from django.core.mail import send_mail
from django.urls import reverse   #django2.0后的反向解释函数
from django.views.generic import View #类视图需要继承的类
from django.conf import settings    #导入jdango的密钥
from itsdangerous import TimedJSONWebSignatureSerializer as  Serializer #对信息加密的类，还可以设置激活时间
from itsdangerous import SignatureExpired #异常
import re
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login, logout  #django内在的认证账户密码系统
from django.core.paginator import Paginator  #分页
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from order.models import OrderInfo,OrderGoods

#user/register
#类视图（方便代码阅读，逻辑清晰，而且可以实现更多的功能）
class RegisterView(View):
    '''注册类'''
    def get(self, request):
        '''显示注册首页'''
        return render(request, 'register.html')

    def post(self, request):
        '''注册处理'''
        # 1、有发过来数据，就先接收数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        # keyi进行重复密码判断
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2、然后进行数据校验
        if not all([username, password, email]):  # 判断是否三个都接收到了
            # 数据不完整
            return render(request, 'register.html', {'errmsg': '数据不完整'})
            # 邮箱格式校验
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
            # 判断是否点击了同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
            # 判断用户名是否重复
        try:
            user = User.objects.get(username=username)  # 在User里面查询有没有username
        except User.DoesNotExist:
            # 用户名不存在，报DoesNotExist错误
            user = None
        if user:
            # 用户存在
            return render(request, 'register.html', {'errmsg': '此用户名已经存在'})

        # 3、进行业务处理：进行用户注册  （创建User模型一个用户信息，保存到数据库）
        user = User.objects.create_user(username, email, password)  #django自带的create_user()创建用户
        user.is_active = 0
        user.save()

        #发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/active/id
        #激活链接要包含身份信息，并且要把它加密
        serializer = Serializer(settings.SECRET_KEY, 3600)  #创建类 (1, 2)1参数为密钥，2参数为链接的有效时间
        info = {'confirm':user.id}
        token = serializer.dumps(info)  #加密（是byte格式）
        token = token.decode() #转化为utf8

        #发邮件（运用celery）
        send_register_active_email.delay(email, username, token)

        # 4、返回应答，跳转到首页
        return redirect(reverse('goods:index'))


#user/active
class ActiveView(View):
    '''用户激活类'''
    def get(self, request, token):
        '''进行用户激活'''
        serializer = Serializer(settings.SECRET_KEY, 3600)  #加密，解密时，都要创建
        try:
            info = serializer.loads(token)
            #获取待激活用户的id
            user_id = info['confirm']

            #根据id获取用户信息
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            #跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            #激活链接已过期
            return HttpResponse('激活链接已过期！您可以更换用户名再次进行注册激活！')


#user/login
class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        #判断是否记住了用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked =  ''
        return render(request, 'login.html', {'username':username, 'checked':checked})

    def post(self, request):
        '''登录校验'''
        #接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        #校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg':'数据不完整，请重新输入登录'})

        #业务处理:登录校验
        user = authenticate(username=username, password=password)
        if user is not None:
            #用户账号，密码正确
            if user.is_active:
                #用户已激活
                login(request, user)  #记录用户登录，记录在session

                #获取登录后所要跳转的地址（在as_view()那里判断了是否登录了 ）
                #默认跳转到首页。返回为None就跳到默认的url
                next_url = request.GET.get('next', reverse('goods:index'))

                #创建返回应答的对象
                response = redirect(next_url)  #本身就是一个HTTPResponseRedirect对象

                #判断是否要记录用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    #记录用户名
                    response.set_cookie('username', username, max_age=7*24*3600) #用cookie记录用户名，并设定时间为1周
                else:
                    response.delete_cookie('username')
                return response

            else:
                #用户还没激活

                return  render(request, 'login.html', {'errmsg':'账户未激活,请前往邮箱激活！'})
        else:
            #用户账户，密码错误
            return render(request, 'login.html', {'errmsg':'用户名或密码错误'})


#user/logout
class LogoutView(View):
    '''退出登录'''
    def get(self, request):
        '''退出登录'''
        #清除用户的session的信息
        logout(request)

        #跳转到首页
        return redirect(reverse('goods:index'))   #重对向


#/user
class UserInfoView(LoginRequiredMixin, View):
    '''用户中心-信息页'''
    def get(self, request):
        '''显示'''
        #page:'user' 传参数过去让它点击的标题变色

        #如果用户未登录->AnonymousUser类的一个实例
        # 如果用户登录->User类的一个实例
        #request.user.is_authenticated()  登录为ture

        #获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        #获取用户的历史浏览记录
        con = get_redis_connection('default')  #default是setting里配置好的

        history_key = 'history_%d'%user.id    #找到缓存的redis用户对应的id

        #获取用户最新浏览的5个商品id
        sku_ids = con.lrange(history_key, 0, 4) #返回列表[5,1,4,3,2]

        # #从数据库中查询用户浏览的商品的具体信息
        # goods_li = GoodsSKU.objects.filter(id_in=sku_ids) #顺序会乱
        #
        # #排好浏览记录的先后顺序
        # goods_res = []
        # for a_id in sku_ids:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)

        #遍历获取用户历史浏览的商品信息
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        #组织上下文
        context = {'page':'user',
                   'address':address,
                   'goods_li':goods_li}

        #除了你给模板文件传递的模板变量之外，django框架会把request.user也传给模板文件
        return render(request, 'user_center_info.html', context)   #返回模板


#/user/order
class UserOrderView(LoginRequiredMixin, View):
    '''用户中心-订单页'''
    def get(self, request, page):
        '''显示'''
        #获取用户订单信息
        user = request.user
        orders = OrderInfo.objects.filter(user=user).order_by('-create_time')  #按浏览时间排

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order_id查询订单商品信息
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)

            # 遍历order_skus计算商品的小计
            for order_sku in order_skus:
                # 计算小计
                amount = order_sku.count * order_sku.price
                # 动态给order_sku增加属性amount,保存订单商品的小计
                order_sku.amount = amount

            # 动态给order增加属性，保存订单状态标题
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_skus = order_skus

        # 分页
        paginator = Paginator(orders, 1)

        # 获取第page页的内容
        try:
            page = int(page)
        except Exception as e:
            page = 1

        if page > paginator.num_pages:
            page = 1

        # 获取第page页的Page实例对象
        order_page = paginator.page(page)

        # todo: 进行页码的控制，页面上最多显示5个页码
        # 1.总页数小于5页，页面上显示所有页码
        # 2.如果当前页是前3页，显示1-5页
        # 3.如果当前页是后3页，显示后5页
        # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {'order_page': order_page,
                   'pages': pages,
                   'page': 'order'}

        # 使用模板
        return render(request, 'user_center_order.html', context)


#/user/address
class AddressView(LoginRequiredMixin, View):
    '''用户中心-地址页'''
    def get(self, request):
        '''显示'''
        #获取用户的默认地址
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_site.html', {'page':'address', 'address':address})

    def post(self, request):
        '''添加地址'''
        #接收数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        #检验数据的完整性
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})
        #校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'电话格式不正确'})

        #业务处理：地址添加
        #如果用户已存在默认收货地址，添加的地址不作为默认收货地址，否则作为默认收货地址
        user = request.user

        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     #不存在默认收货地址
        #     address = None

        address = Address.objects.get_default_address(user)

        if address:
            is_default = False
        else:
            is_default = True

        #添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        #返回应答，刷新页面
        return redirect(reverse('user:address'))  #get请求方式





