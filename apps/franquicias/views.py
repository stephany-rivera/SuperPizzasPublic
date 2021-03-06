import datetime
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.http import HttpResponse
from apps.usuarios.forms import UsuarioForm, UserForm
from apps.pizzas.forms import FacturaForm
from django_tenants.utils import schema_context
from django.contrib.auth.models import User
from apps.usuarios.models import Usuario
from apps.pizzas.models import Pizza,Factura,Detalle,IngredientesA
from apps.ingredientes.models import Ingrediente
from tenant_schemas.utils import *
from django.http import HttpRequest
from rolepermissions.roles import assign_role
from apps.franquicias.models import Franquicia
import json
import os
from datetime import date
from django.core import serializers
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from apps.usuarios.forms import UserAuthenticationForm
from django.contrib.auth import authenticate
from reportlab.pdfgen import canvas
from django.views.generic import View
from io import BytesIO
from django.core.mail import send_mail




def home(request):
    if(request.tenant.working==True):
        #Si usario es anonimo? 
        if request.user.is_anonymous:
            return redirect('/')
        #Validacion del Formulario a traves del metodo POST
        else:
            id_usuario = request.user.id

            perfil = Usuario.objects.get(user=id_usuario)

            if perfil.rol != 'c':
                return render(request, 'base.html', {})
            else:
                return redirect('/login')
    else:
        return render(request,"404.html",{})
    

def home_admin(request):
    #Si usario es anonimo? 
    if request.user.is_anonymous:
        return redirect('/')
    #Validacion si es superusuario
    elif request.user.is_superuser:
        return render(request, 'base.html', {})
    else:
        return redirect('/')

def enviarcorreo(subject,message,recipient_list):
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient_list)

def inicio_franquicia(request):
    dominios = Dominio.objects.exclude(tenant__schema_name='public').select_related('tenant')
    tipos = TipoFranquicia.objects.all()
    return render(request, 'landingpage/index.html', {'tenants':dominios,'tipos':tipos})

def compra_franquicia(request,tipo):    
    dominios = Dominio.objects.exclude(tenant__schema_name='public').select_related('tenant')

    tipoir=TipoFranquicia.objects.get(nombre=tipo)

    if request.method == 'POST':

        form = FranquiciaForm(request.POST,prefix="form1",initial={'tipo': tipoir})
        formUsuario = UsuarioForm(request.POST,prefix="form2",initial={'rol': 'a'})
        formUserDjango = UserForm(request.POST,prefix="form3")
        if form.is_valid() and formUserDjango.is_valid():
            
            try:

                with transaction.atomic():
                    franquicia = form.save()
                   
                    Dominio.objects.create(domain='%s%s' % (franquicia.schema_name, settings.DOMAIN), is_primary=True, tenant=franquicia)

                    with schema_context(franquicia.schema_name):

                        #CREACIÓN DEL USUARIO DJANGO
                        
                        usuario = formUserDjango.save(commit=False)
                        
                        usuario = User(username=request.POST['form3-email'], email=request.POST['form3-email'], first_name=request.POST['form3-first_name'], last_name=request.POST['form3-last_name'])
                        
                        usuario.set_password(request.POST['form3-password1'])
                        
                        usuario.save()

                        assign_role(usuario,'administrador')
                       
                        #CREACION DEL USUARIO - INFORMACIÓN ADICIONAL

                        perfil = Usuario(user=usuario,cc=request.POST['form2-cc'],telefono=request.POST['form2-telefono'],pais=request.POST['form2-pais'],nombre_banco=request.POST['form2-nombre_banco'],fecha_vencimiento=request.POST['form2-fecha_vencimiento'],tipo_tarjeta=request.POST['form2-tipo_tarjeta'],numero_tarjeta=request.POST['form2-numero_tarjeta'],cvv=request.POST['form2-cvv'],rol='a')

                        perfil.save()
                        
                          # Cliente anonimo 

                        user_anonimo = User(username='anonimo@superpizzas.com',password="V7IyWywC9JZyno", email='anonimo@superpizzas.com', first_name='anonimo', last_name='anonimo')
                                                                        
                        user_anonimo.save()

                        assign_role(user_anonimo,'cliente')

                        cliente_anonimo = Usuario(user=user_anonimo,cc=0000000000,telefono=0000000000,pais='CO',nombre_banco='bancolombia',fecha_vencimiento='2019-11-21',tipo_tarjeta='visa',numero_tarjeta=000000000000000,cvv=000,rol='c')

                        cliente_anonimo.save()
                      

            except Exception as e: 
                print(e,"error")
            context={
                'nombre': form.data.get('form1-nombre'),
                'schema': form.data.get('form1-schema_name'),
            }
            enviarcorreo("Compra de Franquicia {t}".format(t=tipoir),"Gracias por adquirir nuestra franquicia para ingresara al portal utiliza tu correo: {u}  y la contraseña que digitaste".format(u=usuario.username),[usuario.username])
            return render(request,'landingpage/comprado.html',context)
        else:
            messages.error(request, "Por favor verificar los campos en rojo")
    else:
        form = FranquiciaForm(prefix="form1",initial={'tipo': tipoir})
        formUsuario = UsuarioForm(prefix="form2",initial={'rol': 'a'})
        formUserDjango = UserForm(prefix="form3")
    context = {
        'form1': form,
        'form2': formUsuario,
        'form3': formUserDjango,
        'dominios': dominios,
        'tipo': tipoir}
    return render(request, 'landingpage/compra.html', context)

def reg_franquicia(request):
    if(request.user.is_superuser):
        dominios = Dominio.objects.exclude(tenant__schema_name='public').select_related('tenant')
        if request.method == 'POST':
            form = FranquiciaForm(request.POST,prefix="form1")
            formUsuario = UsuarioForm(request.POST,prefix="form2",initial={'rol': 'a'})
            formUserDjango = UserForm(request.POST,prefix="form3")
            if form.is_valid() and formUserDjango.is_valid():
                try:
                    with transaction.atomic():
                        franquicia = form.save()
                        Dominio.objects.create(domain='%s%s' % (franquicia.schema_name, settings.DOMAIN), is_primary=True, tenant=franquicia)
                        with schema_context(franquicia.schema_name):
                            usuario = formUserDjango.save(commit=False)
                            usuario = User(username=request.POST['form3-email'], email=request.POST['form3-email'], first_name=request.POST['form3-first_name'], last_name=request.POST['form3-last_name'])
                            usuario.set_password(request.POST['form3-password1'])
                            usuario.save()
                            assign_role(usuario,'administrador')
                            perfil = Usuario(user=usuario,cc=request.POST['form2-cc'],telefono=request.POST['form2-telefono'],pais=request.POST['form2-pais'],nombre_banco=request.POST['form2-nombre_banco'],fecha_vencimiento=request.POST['form2-fecha_vencimiento'],tipo_tarjeta=request.POST['form2-tipo_tarjeta'],numero_tarjeta=request.POST['form2-numero_tarjeta'],cvv=request.POST['form2-cvv'],rol='a')
                            perfil.save()
                            
                except Exception as e: 
                    print(e,"error")
                messages.success(request, "Franquicia registrada")
                return redirect('franquicias:registrar')
            else:
                messages.error(request, "Por favor verificar los campos en rojo")
        else:
            form = FranquiciaForm(prefix="form1")
            formUsuario = UsuarioForm(prefix="form2",initial={'rol': 'a'})
            formUserDjango = UserForm(prefix="form3")
        context = {
            'form1': form,
            'form2': formUsuario,
            'form3': formUserDjango,
            'dominios': dominios,
            'regis':True
            }
        return render(request, 'franquicias/registrar.html', context)
    else:
        return redirect('/')

def inicio_tenants(request):
    if(request.tenant.working==True):
        franquicia = Franquicia.objects.get(schema_name=request.tenant.schema_name)
        context = {
            'pizzas':Pizza.objects.all(),
            'especiales': Pizza.objects.filter(especial=True,enventa=True),
            'enventas': Pizza.objects.filter(enventa=True),
            'franquicia':request,
            'colorprimario': json.loads(franquicia.configuracion)['colorprimario'],
            'colorsecundario': json.loads(franquicia.configuracion)['colorsecundario'],
            'tamanioletra': json.loads(franquicia.configuracion)['tamanioletra'],
            'tamanioletraX2': int(json.loads(franquicia.configuracion)['tamanioletra'])*2,
            'tamanioletraXpix': int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3,
            'logo':  franquicia.media,
        }
        return render(request, 'tenant/index.html', context)
    else:
        return render(request,"404.html",{})

def modificar_franquicia(request, id_franquicia):
    if(request.user.is_superuser):
        franquicia = get_object_or_404(Franquicia, id=id_franquicia)
        dominios = Dominio.objects.exclude(tenant__schema_name='public').select_related('tenant')
        form = ModificarFranquiciaForm(instance=franquicia)
        if request.method == 'POST':
            form = ModificarFranquiciaForm(request.POST, instance=franquicia)
            if form.is_valid():
                form.save()
                messages.success(request, "Se ha modificado correctamente la franquicia")
                return redirect('franquicias:registrar')
            else:
                messages.error(request, "Por favor verificar los campos en rojo")
        return render(request, 'franquicias/registrar.html', {'form': form, 'dominios': dominios,'regis':False})
    else:
        return redirect('/')


def check_schema(request):
    if HttpRequest.is_ajax and request.method == 'GET':        
        schema_name = request.GET.get('form1-schema_name','')       
        if schema_exists(schema_name):
            return HttpResponse('false')
        else:
            return HttpResponse('true')
    else:
        return HttpResponse("Zero")


def ordenar(request):
    if(request.tenant.working==True):
        franquicia = Franquicia.objects.get(schema_name=request.tenant.schema_name)
        context = {
            'pizzas':Pizza.objects.all(),        
            'enventas': Pizza.objects.filter(enventa=True),
            'franquicia':request,
            'colorprimario': json.loads(franquicia.configuracion)['colorprimario'],
            'colorsecundario': json.loads(franquicia.configuracion)['colorsecundario'],
            'tamanioletra': json.loads(franquicia.configuracion)['tamanioletra'],
            'tamanioletraX2': int(json.loads(franquicia.configuracion)['tamanioletra'])*2,
            'tamanioletraXpix': int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3,
            'logo':  franquicia.media,
        }
        return render(request, 'tenant/ordenar.html', context)
    else:
        return render(request,"404.html",{})
    
def configuraciones(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='a' and request.tenant.working==True and request.tenant.tipo.nombre=='premium'):
            if(request.tenant.tipo.nombre=="premium"):
                datosfran = Franquicia.objects.get(schema_name=request.tenant.schema_name)
                contexto = {'franquicia': datosfran, 
                'colorprimario': json.loads(datosfran.configuracion)['colorprimario'],
                'colorsecundario': json.loads(datosfran.configuracion)['colorsecundario'],
                'logo':  datosfran.media,
                'tamanioletra': json.loads(datosfran.configuracion)['tamanioletra']
                }

                if request.method == 'POST':
                    datosfran.configuracion = '{\"colorprimario\":\"#'+ request.POST.get("colorpimario") +'\",\"colorsecundario\":\"#'+ request.POST.get("colorsecundario") +'\", \"tamanioletra\":'+ request.POST.get("tamanioLetra") +'}'
                    
                    if request.FILES.get('inputFileLogoConfig') != None:
                        pathLogoAnterior = datosfran.media
                        if pathLogoAnterior != 'media/logos-franquicias/1_logo_default.png':
                            try:
                                os.remove(datosfran.media.path)
                            except:
                                print('***No se pudo Eliminar imagen anterior***')
                        datosfran.media = request.FILES.get('inputFileLogoConfig')
                    try:    
                        datosfran.save()
                        messages.success(request, 'Configuraciones guardadas correctamente')
                    except:
                        messages.error(request, 'Error al intentar guardar configuraciones')

                    datosfran = Franquicia.objects.get(schema_name=request.tenant.schema_name)
                    contexto = {'franquicia': datosfran, 
                    'colorprimario': json.loads(datosfran.configuracion)['colorprimario'],
                    'colorsecundario': json.loads(datosfran.configuracion)['colorsecundario'],
                    'logo':  datosfran.media,
                    'tamanioletra': json.loads(datosfran.configuracion)['tamanioletra']
                    }
                return render(request,'franquicias/configuraciones.html', contexto)
            else:
                return redirect('/admin')
        else:
            return render(request,"404.html",{})

def informacion(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='a' and request.tenant.working==True):
            inicio=request.tenant.fecha_corte
            dias=date.today()-inicio
            if request.method == 'POST':
                formulario = UserAuthenticationForm(request.POST)
                if formulario.is_valid:
                    username = request.POST['username']
                    password = request.POST['password']
                    acceso_user = authenticate(username = username, password = password)
                    user = User.objects.get(username=acceso_user)
                    perfil = Usuario.objects.get(user=user)
                    if acceso_user is not None and perfil.rol== 'a':
                        if acceso_user.is_active:
                            return renuncia(request)
                        else:
                            messages.add_message(request, messages.INFO, 'Error en usuario y contraseña')
                    else:
                        messages.add_message(request, messages.INFO, 'Error en usuario y contraseña')
                else:
                    messages.add_message(request, messages.INFO, 'Error en usuario y contraseña')
            else:
                formulario = UserAuthenticationForm()

            context={'dias':dias.days,'formulario':formulario}
            return render(request,'franquicias/info.html',context)
        else:
            return render(request,"404.html",{})

def renuncia(request):
    enviarcorreo("Retiro de franquicia {r}".format(r=request.tenant.nombre),"Gracias por haber adquirirdo nuestra franquicia te esperamos pronto de vuelta",[request.user.username])
    if(request.tenant.working==True):
        franquiciafields={"nombre":request.tenant.nombre,"dominio":request.tenant.schema_name,"tipo":request.tenant.tipo.nombre}
        franquicia={"model":"franquicias.franquicia","pk":request.tenant.id,"fields":franquiciafields}
        usuarios = serializers.serialize("json", Usuario.objects.all())
        ingredientes = serializers.serialize("json", Ingrediente.objects.all())
        pizzas = serializers.serialize("json", Pizza.objects.all())
        facturas = serializers.serialize("json", Factura.objects.all())
        detalles = serializers.serialize("json", Detalle.objects.all())
        context={'f':json.dumps(franquicia),'u':usuarios,'i':ingredientes,'p':pizzas,'fc':facturas,'dt':detalles}
        Franquicia.objects.filter(pk=request.tenant.id).update(working=False)
        Franquicia.objects.filter(pk=request.tenant.id).update(fecha_cancelada=datetime.datetime.now())
        return render(request,'tenant/renuncia.html',context)
    else:
        return render(request,"404.html",{})

class CartAgregar(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):
            id_producto = request.POST.get("id_producto", "")
            producto_item = Pizza.objects.filter(id=id_producto).values()[0]       
            respuesta = {}        
            if producto_item is not None:
                respuesta['estado'] = True
                cart = request.session.get('cart', {})
                if id_producto in cart:
                    respuesta['estado'] = False
                    respuesta['mensaje'] = "La pizza ya está añadida en el carrito de compras "                            
                    return JsonResponse(respuesta)
                else:
                    cart[''+id_producto] = producto_item
                    request.session['cart'] = cart
                    respuesta['cantidad'] = len(cart)
                    respuesta['mensaje'] = "Has añadido la pizza al carrito de compras"                              
                    return JsonResponse(respuesta)
            else:
                respuesta['estado'] = False
                respuesta['mensaje'] = "El producto no existe"
                return JsonResponse(respuesta)
        else:
            return render(request,"404.html",{})

class CartListar(TemplateView):
    template_name = "tenant/carrito_lista.html"    
    
    def get_context_data(self, **kwargs):
        if(self.request.tenant.working==True):
            context = super(CartListar, self).get_context_data(**kwargs)
            franquicia = Franquicia.objects.get(schema_name=self.request.tenant.schema_name)
            adicionales = self.request.session.get('ingredientes_add', "")                
            diccionario=""
            adicionales_dic="" 
            if(adicionales != ""):
                for key,adiciones in adicionales.items():                
                    diccionario+=adiciones[1 : -1]+","                                                             
                adicionales_dic="{"+diccionario[:-1]+"}"                 
                adicionales_dict = json.loads(adicionales_dic)  
                context['adicionales']=adicionales_dict    
            cantidades = self.request.session.get('cantidades',"")
            if(cantidades != ""):
                context['cantidades'] = cantidades 
            context['ingredientes']= Ingrediente.objects.all() 
            context['franquicia']=self.request
            context['pizzas']=Pizza.objects.filter(enventa=True)
            context['colorprimario'] = json.loads(franquicia.configuracion)['colorprimario']
            context['colorsecundario'] = json.loads(franquicia.configuracion)['colorsecundario']
            context['tamanioletra']=json.loads(franquicia.configuracion)['tamanioletra']
            context['tamanioletraX2'] = int(json.loads(franquicia.configuracion)['tamanioletra'])*2
            context['tamanioletraXpix'] = int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3
            context['logo'] = franquicia.media
            cart = self.request.session.get('cart', {})
            context['productos'] = cart            
            return context
        else:
            return render(self.request,"404.html",{})

class CartDelete(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):
            id_producto = request.POST.get("id_producto", "")
            cart = request.session.get('cart', {})
            ingredientes_add= request.session.get("ingredientes_add",{})             
            del cart[id_producto]  
            if id_producto in ingredientes_add:
                del ingredientes_add[id_producto]      
            request.session['ingredientes_add']=ingredientes_add            
            request.session['cart'] = cart
            respuesta = {'estado': True, 'mensaje': len(cart)}
            return JsonResponse(respuesta)
        else:
            return render(request,"404.html",{})

    def get_success_url(self):
        return reverse_lazy('cart_listar')

class AgregarCantidadCarrito(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):
            cantidades = request.POST.get("cantidades", "")
            detalles = []
            self.request.session['cantidades'] = cantidades
            respuesta = {'estado': True, }
            return JsonResponse(respuesta)
        else:
            return render(request,"404.html",{})

class CartComprar(TemplateView):
    template_name = "tenant/carrito_comprar.html"
    
    def get_context_data(self, **kwargs):
        if(self.request.tenant.working==True):
            context = super(CartComprar, self).get_context_data(**kwargs)
            franquicia = Franquicia.objects.get(schema_name=self.request.tenant.schema_name)
            form_factura= FacturaForm(self.request.POST or None)
            admin_franquicia = Usuario.objects.get(user_id=1)
            cliente=None
            customer = self.request.user 
            adicionales = self.request.session.get('ingredientes_add', "")                
            diccionario=""
            adicionales_dic="" 
            adicionales_dict={}
            if(adicionales != ""):
                for key,adiciones in adicionales.items():                
                    diccionario+=adiciones[1 : -1]+","                                                             
                adicionales_dic="{"+diccionario[:-1]+"}" 
                adicionales_dict = json.loads(adicionales_dic)  
                context['adicionales']=adicionales_dict         
            if customer.is_authenticated:
                if not customer.social_auth.exists():
                    form = UsuarioForm(self.request.POST or None,prefix="form2",initial={'pais': customer.usuario.pais,'direccion':customer.usuario.direccion})
                    cliente = Usuario.objects.get(user_id=customer.id)
                else:
                    form = UsuarioForm(self.request.POST or None,prefix="form2")    
            else:
                form = UsuarioForm(self.request.POST or None,prefix="form2")
            context["form"] = form_factura
            context['franquicia']=self.request
            context['colorprimario'] = json.loads(franquicia.configuracion)['colorprimario']
            context['colorsecundario'] = json.loads(franquicia.configuracion)['colorsecundario']
            context['tamanioletra']=json.loads(franquicia.configuracion)['tamanioletra']
            context['tamanioletraX2'] = int(json.loads(franquicia.configuracion)['tamanioletra'])*2
            context['tamanioletraXpix'] = int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3
            context['logo'] = franquicia.media
            cart = self.request.session.get('cart', {})
            cantidades = self.request.session.get('cantidades', {})       
            context['productos'] = cart
            context['cantidades'] = json.loads(cantidades) 
            context['cliente']=cliente 
            context["form2"] = form
            context['admin_franquicia']=admin_franquicia
            context['ingredientes']= Ingrediente.objects.all() 

            return context
        else:
            return render(self.request,"404.html",{})

    def post(self, request):
        if(request.tenant.working==True):
            direccion = request.POST['form2-direccion']
            ciudad= request.POST['ciudad']            
            customer = request.user  
            adicionales = self.request.session.get('ingredientes_add', "")                
            diccionario=""
            adicionales_dic="" 
            adicionales_dict={}
            if(adicionales != ""):
                for key,adiciones in adicionales.items():                
                    diccionario+=adiciones[1 : -1]+","                                                             
                adicionales_dic="{"+diccionario[:-1]+"}" 
                adicionales_dict = json.loads(adicionales_dic)      
            if customer.is_authenticated:
                if not customer.social_auth.exists():                   
                    cliente = Usuario.objects.get(user_id=customer.id)
                    factura = Factura(direccion=direccion, ciudad=ciudad, cliente=cliente)
                    factura.save()    
                else:
                    if not Usuario.objects.filter(user_id=customer.id).exists():   
                        usuario_gmail=User.objects.get(id=customer.id)                     
                        cliente_gmail = Usuario(user=usuario_gmail,cc=0000000000,telefono=0000000000,pais='CO',nombre_banco='bancolombia',fecha_vencimiento='2019-11-21',tipo_tarjeta='visa',numero_tarjeta=000000000000000,cvv=000,rol='c')
                        cliente_gmail.save()  
                    cliente_login = Usuario.objects.get(user_id=customer.id)
                    factura = Factura(direccion=direccion, ciudad=ciudad, cliente=cliente_login)
                    factura.save()
            else:
                if not User.objects.filter(email="anonimo@superpizzas.com").exists():
                    user_anonimo = User(username='anonimo@superpizzas.com',password="V7IyWywC9JZyno", email='anonimo@superpizzas.com', first_name='anonimo', last_name='anonimo')
                    user_anonimo.save()
                    assign_role(user_anonimo,'cliente')
                    cliente_anonimo = Usuario(user=user_anonimo,cc=0000000000,telefono=0000000000,pais='CO',nombre_banco='bancolombia',fecha_vencimiento='2019-11-21',tipo_tarjeta='visa',numero_tarjeta=000000000000000,cvv=000,rol='c')
                    cliente_anonimo.save()

                usuario_anonimo = User.objects.get(email="anonimo@superpizzas.com")
                cliente_anonimo = Usuario.objects.get(user_id=usuario_anonimo.id)
                factura = Factura(direccion=direccion, ciudad=ciudad, cliente=cliente_anonimo)
                factura.save()
            cantidades = self.request.session.get('cantidades', {})
            cantidades_dict = json.loads(cantidades)
            for k, v in cantidades_dict.items():
                producto_item = Pizza.objects.filter(id=v['id']).values()[0]
                detalle_item = Detalle(cantidad=v['cantidad'], precio=producto_item['valor'], factura=factura,
                                    producto_id=v['id'])
                detalle_item.save()            
            for k, v in adicionales_dict.items():
                adicionales_item=Ingrediente.objects.filter(id=v['id']).values()[0]  
                adicion_item=IngredientesA(cantidad=v['cantidad'],precio=adicionales_item['valor'],factura=factura,
                ingredientes_id=v['id'], producto_id=v['id_pizza'])
                adicion_item.save()
            
            self.request.session['cart'] = {}
            self.request.session['ingredientes_add']={}
            self.request.session['cantidades']={}
            #return HttpResponseRedirect(self.get_success_url())
            return HttpResponseRedirect('/compra_exitosa?id='+str(factura.id))
        else:
            return render(request,"404.html",{})



class CartSuccess(TemplateView):
    template_name = "tenant/carrito_success.html"

    def get_context_data(self, **kwargs):
        if(self.request.tenant.working==True):
            context = super(CartSuccess, self).get_context_data(**kwargs)
            franquicia = Franquicia.objects.get(schema_name=self.request.tenant.schema_name)
            context['franquicia']=self.request
            context['colorprimario'] = json.loads(franquicia.configuracion)['colorprimario']
            context['colorsecundario'] = json.loads(franquicia.configuracion)['colorsecundario']
            context['tamanioletra']=json.loads(franquicia.configuracion)['tamanioletra']
            context['tamanioletraX2'] = int(json.loads(franquicia.configuracion)['tamanioletra'])*2
            context['tamanioletraXpix'] = int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3
            context['logo'] = franquicia.media
            context['id_factura'] = self.request.GET['id']

            return context
        else:
            return render(self.request,"404.html",{})

def factura_PDF(request, id_factura=None):
    
    #Indicamos el tipo de contenido a devolver, en este caso un pdf
    response = HttpResponse(content_type='application/pdf')
    #La clase io.BytesIO permite tratar un array de bytes como un fichero binario, se utiliza como almacenamiento temporal
    buffer = BytesIO()
    #Canvas nos permite hacer el reporte con coordenadas X y Y
    pdf = canvas.Canvas(buffer)
    pdf.setTitle("Factura de Venta")
    pdf.setPageSize((200, 300))
    #Llamo al método cabecera donde están definidos los datos que aparecen en la cabecera del reporte.

    archivo_imagen = settings.MEDIA_ROOT+'/images/favicon.png'
    pdf.drawImage(archivo_imagen, 25, 240, 50, 50,preserveAspectRatio=True)
    
    pdf.setFont("Helvetica", 7)
    
    pdf.drawString(80, 280, request.tenant.nombre)
    pdf.drawString(80, 270, u"FACTURA DE VENTA")
    pdf.setFont("Helvetica", 6)
    pdf.drawString(80, 260, id_factura)
    pdf.drawString(80, 250, str(datetime.datetime.now().strftime("%Y-%m-%d")))

    factura = Factura.objects.get(id=id_factura)
    detalles = Detalle.objects.filter(factura=factura)
    ingredientes_adi=IngredientesA.objects.filter(factura=factura)

    pdf.setFont("Helvetica", 4)
    pdf.drawString(25, 230, "----------------------------------------------------------------------------------------------------------------------")
    pdf.drawString(25, 225, "Nombre:")
    if factura.cliente.user.first_name == "anonimo":
        pdf.drawString(70, 225, "No disponible")
    else:
        pdf.drawString(70, 225, factura.cliente.user.first_name+" "+factura.cliente.user.last_name)

    pdf.drawString(25, 220, "Email:")
    if factura.cliente.user.first_name == "anonimo":
        pdf.drawString(70, 220, "No disponible")
    else:
        pdf.drawString(70, 220, factura.cliente.user.username)
    pdf.drawString(25, 215, "Ciudad:")
    pdf.drawString(70, 215, factura.ciudad)
    pdf.drawString(25, 210, "Dirección:")
    pdf.drawString(70, 210, factura.direccion)
    pdf.setFont("Helvetica", 4)
    pdf.drawString(25, 205, "--------------------------------------------------------------------------------------------------------------------")
    pdf.setFont("Helvetica", 5)
    pdf.drawString(25, 200, "Resumen de Venta:")
    pdf.setFont("Helvetica", 4)
    pdf.drawString(25, 192, "Cant")
    pdf.drawString(50, 192, "Descripción")    
    pdf.drawString(150, 192, "Valor")
    total = 0
    total1=0
    total_pago=0
    line = 184
    pdf.setFont("Helvetica", 4)
    for detalle in detalles:

        pdf.drawString(25, line, str(detalle.cantidad))
        pdf.drawString(50, line, detalle.producto.nombre)
        valor = int(detalle.cantidad)*int(detalle.precio)
        pdf.drawString(150, line, "$ "+str(valor))
        line -= 5
        total += valor

    line=line-5
    pdf.setFont("Helvetica", 5)
    pdf.drawString(120, line, "Subtotal")
    pdf.drawString(150, line, "$ "+str(total))

    line=line-4
    pdf.setFont("Helvetica",5)
    pdf.drawString(25, line, "Ingredientes adicionales:")
    line=line-8
    pdf.setFont("Helvetica",4)
    pdf.drawString(25, line, "Cant")
    pdf.drawString(50, line, "Descripción")  
    pdf.drawString(85, line, "Pizza")
    pdf.drawString(150, line, "Valor")

    line=line-7
    for ingrediente in ingredientes_adi:        

        pdf.drawString(25, line, str(ingrediente.cantidad))
        pdf.drawString(50, line, ingrediente.ingredientes.nombre)
        pdf.drawString(80,line,ingrediente.producto.nombre)
        for detalle in detalles:
            if (detalle.producto.id == ingrediente.producto.id):
                valor1 = int(ingrediente.cantidad)*int(ingrediente.precio)*int(detalle.cantidad)
        pdf.drawString(150, line, "$ "+str(valor1))
        line -= 5
        total1 += valor1
    
    total_pago=total+total1
    pdf.setFont("Helvetica", 5)
    pdf.drawString(120, line-5, "Subtotal")
    pdf.drawString(150, line-5, "$ "+str(total1))

    pdf.setFont("Helvetica", 4)
    pdf.drawString(25, line-20, "-------------------------------------------------------")
    pdf.setFont("Helvetica", 5)
    pdf.drawString(120, line-20, "Total")    
    pdf.drawString(150, line-20, "$ "+str(total_pago))

    pdf.setFont("Helvetica", 3)
    pdf.drawString(25, 25, "Fecha de orden: ")
    pdf.drawString(70, 25, str(factura.fecha_creacion))

    pdf.showPage()
    pdf.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

def vender(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='v' and request.tenant.working==True):
            franquicia = Franquicia.objects.get(schema_name=request.tenant.schema_name)
            adicionales = request.session.get('ingredientes_add_venta', "")                
            diccionario=""
            adicionales_dic="" 
            adicionales_dict={}
            if(adicionales != ""):
                for key,adiciones in adicionales.items():                
                    diccionario+=adiciones[1 : -1]+","                                                             
                adicionales_dic="{"+diccionario[:-1]+"}" 
                adicionales_dict = json.loads(adicionales_dic)                       
            context = {
                'pizzas':Pizza.objects.all(),        
                'enventas': Pizza.objects.filter(enventa=True),
                'ingredientes': Ingrediente.objects.all(), 
                'adicionales':adicionales_dict,
                'franquicia':request,
                'colorprimario': json.loads(franquicia.configuracion)['colorprimario'],
                'colorsecundario': json.loads(franquicia.configuracion)['colorsecundario'],
                'tamanioletra': json.loads(franquicia.configuracion)['tamanioletra'],
                'tamanioletraX2': int(json.loads(franquicia.configuracion)['tamanioletra'])*2,
                'tamanioletraXpix': int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3,
                'logo':  franquicia.media,                
            }
            return render(request, 'tenant/vender.html', context)
        else:
            return render(request,"404.html",{})

class VentaCantidades(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):
            cantidades = request.POST.get("cantidades_venta", "")
            detalles = []
            self.request.session['cantidades_venta'] = cantidades
            respuesta = {'estado': True, }
            return JsonResponse(respuesta)
        else:
            return render(request,"404.html",{})

class IngredientesAd(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):   
            ingredientes = request.POST.get("ingredientes_add", "") 
            id_pizza = request.POST.get("id_producto", "")
            ingredientes_add = request.session.get('ingredientes_add', {})
            ingredientes_add[id_pizza] = ingredientes
            self.request.session['ingredientes_add'] = ingredientes_add              
            respuesta = {'estado': True, }
            return JsonResponse(respuesta)                            
            
        else:
            return render(request,"404.html",{})

class IngredientesAd_venta(TemplateView):

    def post(self, request):
        if(request.tenant.working==True):   
            ingredientes = request.POST.get("ingredientes_add_venta", "") 
            id_pizza = request.POST.get("id_producto_venta", "")
            ingredientes_add_venta = request.session.get('ingredientes_add_venta', {})
            ingredientes_add_venta[id_pizza] = ingredientes
            self.request.session['ingredientes_add_venta'] = ingredientes_add_venta            
            respuesta = {'estado': True, }
            return JsonResponse(respuesta)                            
            
        else:
            return render(request,"404.html",{})


def cancelar(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='v' and request.tenant.working==True):
            request.session['ingredientes_add_venta']={}  
            return redirect('vender')
        else:
            return render(request,"404.html",{})

def VenderPago(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='v' and request.tenant.working==True):
            franquicia = Franquicia.objects.get(schema_name=request.tenant.schema_name)
            adicionales = request.session.get('ingredientes_add_venta', "")                
            diccionario=""
            adicionales_dic="" 
            adicionales_dict={}
            if(adicionales != ""):
                for key,adiciones in adicionales.items():                
                    diccionario+=adiciones[1 : -1]+","                                                             
                adicionales_dic="{"+diccionario[:-1]+"}" 
                adicionales_dict = json.loads(adicionales_dic)
            cantidades = request.session.get('cantidades_venta', {})
            cantidades_dict = json.loads(cantidades)  
            cliente=None
            customer = request.user    
            id=[]     
            if customer.is_authenticated: 
                cliente = Usuario.objects.get(user_id=customer.id)                
            for k, v in cantidades_dict.items():
                id.append(v['id']) 
            pizza_item = Pizza.objects.filter(id__in=id)           
            if request.method == 'POST': 
                customer = request.user        
                if customer.is_authenticated:
                    cliente = Usuario.objects.get(user_id=customer.id)
                    factura = Factura(direccion='local', ciudad='local', cliente=cliente)
                    factura.save()                               
                for k, v in cantidades_dict.items():
                    producto_item = Pizza.objects.filter(id=v['id']).values()[0] 
                    detalle_item = Detalle(cantidad=v['cantidad'], precio=producto_item['valor'], factura=factura,
                                        producto_id=v['id'])
                    detalle_item.save()

                for k, v in adicionales_dict.items():
                    adicionales_item=Ingrediente.objects.filter(id=v['id']).values()[0]  
                    adicion_item=IngredientesA(cantidad=v['cantidad'],precio=adicionales_item['valor'],factura=factura,
                    ingredientes_id=v['id'], producto_id=v['id_pizza'])
                    adicion_item.save()

                request.session['cantidades_venta'] = {}
                request.session['ingredientes_add_venta']={}
                messages.success(request, 'Venta realizada')
                return redirect('vender')
            else:
                context = {
                    'productos': pizza_item ,
                    'cantidades':cantidades_dict,
                    'adicionales':adicionales_dict,
                    'ingredientes': Ingrediente.objects.all(),
                    'franquicia':request,
                    'colorprimario': json.loads(franquicia.configuracion)['colorprimario'],
                    'colorsecundario': json.loads(franquicia.configuracion)['colorsecundario'],
                    'tamanioletra': json.loads(franquicia.configuracion)['tamanioletra'],
                    'tamanioletraX2': int(json.loads(franquicia.configuracion)['tamanioletra'])*2,
                    'tamanioletraXpix': int(json.loads(franquicia.configuracion)['tamanioletra'])/10 +3,
                    'logo':  franquicia.media,               
                }
                return render(request, 'tenant/vender_pago.html', context)
        else:
            return render(request,"404.html",{})



def reportes(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='a' and request.tenant.working==True and request.tenant.tipo.nombre=='premium'):
            vmeses=[0,0,0,0,0,0,0,0,0,0,0,0]
            npizzas=[]
            vendedores=[]
            ventasVendedores=[]
            diasSemana=[0,0,0,0,0,0,0]
            contador1=0
            relacioncompras=[0,0,0]
            for cliente in Usuario.objects.all():
                if(cliente.rol=='v'):
                    vendedores.append(cliente.user.username)
                    ventasVendedores.append(0)
                    for factura in Factura.objects.all():
                        if(factura.cliente.id==cliente.id):
                            ventasVendedores[contador1]+=1
                    contador1+=1
                if(cliente.rol=='c'):
                    contadorcliente=0
                    for factura in Factura.objects.all():
                        if(cliente.id==factura.cliente.id):
                            contadorcliente+=1
                    if(contadorcliente==0):
                        relacioncompras[0]+=1
                    elif(contadorcliente==1):
                        relacioncompras[1]+=1
                    else:
                        relacioncompras[2]+=1
            sonespeciales=[0,0]
            total=0
            for pizza in Pizza.objects.all():
                npizzas.append(0)
            
            for detalle in Detalle.objects.all():
                npizzas[detalle.producto.id-1] += detalle.cantidad
                total += detalle.cantidad
                if(detalle.producto.especial==True):
                    sonespeciales[0]+=detalle.cantidad
                else:
                    sonespeciales[1]+=detalle.cantidad
            if(total!=0):
                porcentajeEspecial=(sonespeciales[0]*100)/total
                porcentajeNoEspecial=(sonespeciales[1]*100)/total
            else:
                porcentajeEspecial=0
                porcentajeNoEspecial=0
            laspizzas=list(Pizza.objects.values_list('id', flat=True))

            for factura in Factura.objects.all():
                diasSemana[factura.fecha_creacion.weekday()]+=1
                vmeses[factura.fecha_creacion.month-1]+=1

            contexto={'vene':vmeses[0],'vfeb':vmeses[1],'vmar':vmeses[2],'vabr':vmeses[3],'vmay':vmeses[4],'vjun':vmeses[5],'vjul':vmeses[6],'vago':vmeses[7],'vsep':vmeses[8],'voct':vmeses[9],'vnov':vmeses[10],'vdic':vmeses[11],'npizzas':npizzas,'pizzas':laspizzas,'especial':porcentajeEspecial,'noespecial':porcentajeNoEspecial, 'vendedores':vendedores, 'ventasvendedores':ventasVendedores,'ventasdias':diasSemana,'relacioncompras':relacioncompras}
            return render(request,'franquicias/graficos.html', contexto)
        else:
            return render(request,"404.html",{})

def ventas(request):
    if request.user.is_anonymous:
        return render(request,"404.html",{})
    else:
        if(request.user.usuario.rol=='a' and request.tenant.working==True):
            facturas=Factura.objects.all()
            detalles=Detalle.objects.all()
            ingredientesa=IngredientesA.objects.all()
            total1=0
            valor2=0
            valor2=0
            total2=0
            #totales={}
            totales=[]
            cantidadp=1
            vez=0
            for factura in facturas:
                for detalle in detalles:
                    if(detalle.factura.id == factura.id):
                        valor1 = int(detalle.cantidad)*int(detalle.precio)
                        total1 += valor1
                for ingrediente in ingredientesa:
                    if(ingrediente.factura.id == factura.id):
                        for detalle in detalles:
                            if (detalle.producto.id == ingrediente.producto.id and detalle.factura.id == ingrediente.factura.id):
                                valor2 = int(ingrediente.cantidad)*int(ingrediente.precio)*int(detalle.cantidad)
                        total1 += valor2
                totales.append(total1+total2)
                total1=0
                total2=0  
            context={'facturas':facturas,'detalles':detalles,'ingredientesa':ingredientesa,'totales':totales}
            return render(request,'franquicias/ventas.html',context)
        else:
            return render(request,"404.html",{})

def encontrarChurnRate(periodoActual,periodoAnterior):
    totalCustomers=0
    totalclientesAnterior=0
    totalclientesActual=0
    nuevosClientesActual=0
    customersLost=0
    for franquicia in Franquicia.objects.all():
        if(franquicia.schema_name!='public'):
            totalCustomers+=1
            if(franquicia.working==True):
                if(franquicia.fecha_corte.month==periodoActual):
                    nuevosClientesActual+=1
            if(franquicia.fecha_corte.month==periodoAnterior):
                    totalclientesAnterior+=1
            if(franquicia.fecha_corte.month==periodoActual):
                    totalclientesActual+=1
    
    customersLost=totalclientesAnterior+nuevosClientesActual-totalclientesActual
    churnRate=(customersLost/totalCustomers)*-100
    if(churnRate<0):
        return 0
    else:
        return churnRate

def metricas(request):
    if(request.user.is_superuser):
        periodoActual=date.today().month
        if(periodoActual!=1):
            periodoAnterior=periodoActual-1
        else:
            periodoAnterior=12
        totalCustomers=0
        totalclientesAnterior=0
        totalclientesActual=0
        nuevosClientesActual=0
        customersLost=0
        cuentasCanceladasActual=0
        for franquicia in Franquicia.objects.all():
            if(franquicia.schema_name!='public'):
                if(franquicia.fecha_corte.year==datetime.datetime.now().year):
                    totalCustomers+=1
                    if(franquicia.working==True):
                        if(franquicia.fecha_corte.month==periodoActual):
                            nuevosClientesActual+=1
                    else:
                        if(franquicia.fecha_corte.month==periodoActual):
                            cuentasCanceladasActual+=1
                    if(franquicia.fecha_corte.month<=periodoAnterior and franquicia.fecha_cancelada.month>=periodoActual):
                            totalclientesAnterior+=1
                    if(franquicia.fecha_corte.month==periodoActual):
                            totalclientesActual+=1
        if(totalCustomers>0):
            customersLost=totalclientesAnterior+nuevosClientesActual-totalclientesActual
            churnRate=(customersLost/totalCustomers)*-100
            arpu=cuentasCanceladasActual/totalCustomers
            
            if(churnRate!=0):
                acl=str(1/(churnRate/100))+" Meses"
                ltv=arpu*(1/(churnRate/100))
            else:
                acl="No calculable dado que su churnRate es 0"
                ltv="No calculable dado que su churnRate es 0"

            contexto={'periodoactual':periodoActual,'customerlost':customersLost,'totalcustomers':totalCustomers,'churnrate':churnRate,'acl':acl,'crr':(1-churnRate/100)*100,'cohort':[encontrarChurnRate(1,12),encontrarChurnRate(2,1),encontrarChurnRate(3,2),encontrarChurnRate(4,3),encontrarChurnRate(5,4),encontrarChurnRate(6,5),encontrarChurnRate(7,6),encontrarChurnRate(8,7),encontrarChurnRate(9,8),encontrarChurnRate(10,9),encontrarChurnRate(11,10),encontrarChurnRate(12,11)],'arpu':arpu,'ltv':ltv,'nuevosclientes':nuevosClientesActual}
            return render(request,'franquicias/metricas.html',contexto)
        else:
            messages.error(request, 'Aún no hay franquicias como para mostrat métricas')
            return redirect('/')
    else:
        return redirect('/')

