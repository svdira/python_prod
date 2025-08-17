from django.shortcuts import render, redirect
from django import template
from .models import *
from django.db.models import Avg, Count, Min, Sum
from django.db.models import Q, Max
from django.db.models import FloatField
from django.db.models import F
from django.db.models.functions import Round
from django.db.models.functions import Cast
from datetime import datetime
import math
import random
import re



class getPageAttrs:

	def __init__(self,pagina):
		self.pagina = pagina

	def attrDict(self):

		atributos = {}

		this_pagina = PaginaSB.objects.get(pk=int(self.pagina))
		if attrPagina.objects.filter(pagina=this_pagina).count() > 0:
			paginas = attrPagina.objects.filter(pagina=this_pagina)

			for p in paginas:
				atributos[p.attNombre] = p.attValor.titulo

		if attrTexto.objects.filter(pagina=this_pagina).count() > 0:
			textos = attrTexto.objects.filter(pagina=this_pagina)

			for p in textos:
				atributos[p.attNombre] = p.attValor

		if attrEntero.objects.filter(pagina=this_pagina).count() > 0:
			enteros = attrEntero.objects.filter(pagina=this_pagina)

			for p in enteros:
				atributos[p.attNombre] = p.attValor


		if attrFecha.objects.filter(pagina=this_pagina).count() > 0:
			fechas = attrFecha.objects.filter(pagina=this_pagina)

			for p in fechas:
				atributos[p.attNombre] = p.attValor


		if attrDecimal.objects.filter(pagina=this_pagina).count() > 0:
			decimales = attrDecimal.objects.filter(pagina=this_pagina)

			for p in decimales:
				atributos[p.attNombre] = p.attValor

		return atributos



def adminCategorias(request):
	ptitulo = "Admin Categorias"
	categorias = CategoriaSB.objects.all()
	return render(request,'admin_categorias.html',{'ptitulo':ptitulo,'categorias':categorias})


def addCategoria(request):
	new_cat = request.POST.get("nombre_categoria")
	if len(new_cat)>=4:
		newC = CategoriaSB.objects.create(nombre_categoria=new_cat.lower())
		newC.save()

	return redirect('/simpleblog/admin-categorias')



def adminPaginas(request):
	ptitulo = "Admin Paginas"
	categorias = CategoriaSB.objects.all()
	paginas = PaginaSB.objects.all().order_by('-id')[0:50]

	if request.method == 'POST':
		keyword = request.POST.get("key_words")
		paginas = PaginaSB.objects.filter(titulo__contains=keyword).order_by('-id')[0:50]

	return render(request,'admin_paginas.html',{'ptitulo':ptitulo,'categorias':categorias,'paginas':paginas})


def addPagina(request):
	cat_id = int(request.POST.get("cat_id"))
	this_titulo = request.POST.get("titulo")
	this_contenido = request.POST.get("info")
	fecha_hoy = request.POST.get("fecha_hoy")
	this_categoria = CategoriaSB.objects.get(pk=cat_id)

	newP = PaginaSB.objects.create(titulo = this_titulo, contenido = this_contenido, categoria = this_categoria, fecha_inicio = fecha_hoy)
	newP.save()

	if newP.categoria.nombre_categoria == 'book':
		return redirect('/simpleblog/add-book-attr/{}'.format(newP.id))
	else:
		return redirect('/simpleblog/view-pagina/{}'.format(newP.id))


def viewPagina(request,pid):
	this_pagina = PaginaSB.objects.get(pk=int(pid))
	categorias = CategoriaSB.objects.all()
	atributos = getPageAttrs(this_pagina.id).attrDict()
	cant_att = len(atributos)

	if request.method == 'POST':
		cat_id = int(request.POST.get("cat_id"))
		this_titulo = request.POST.get("titulo")
		this_contenido = request.POST.get("info")
		this_categoria = CategoriaSB.objects.get(pk=cat_id)

		this_pagina.titulo = this_titulo
		this_pagina.contenido = this_contenido
		this_pagina.categoria = this_categoria
		this_pagina.save()

	return render(request,'view_pagina.html',{'ptitulo':this_pagina.titulo,'categorias':categorias,'this_pagina':this_pagina,'cant_att':cant_att, 'atributos':atributos})

def addAtributosBook(request,pid):
	this_pagina = PaginaSB.objects.get(pk=int(pid))
	list_autores = PaginaSB.objects.filter(categoria__nombre_categoria='author').order_by('titulo')

	return render(request,'add-book-attr.html',{'ptitulo':this_pagina.titulo,'this_pagina':this_pagina,'list_autores':list_autores})

def saveBookAttr(request):
	this_pagina = PaginaSB.objects.get(pk=int(request.POST.get("pagina_id")))
	this_author = PaginaSB.objects.get(pk=int(request.POST.get("author_id")))
	pub_year = int(request.POST.get("pub_year"))
	orig_lan = request.POST.get("orig_lan")

	cant_1 = attrPagina.objects.filter(pagina = this_pagina).count()
	cant_2 = attrFecha.objects.filter(pagina = this_pagina).count()
	cant_3 = attrTexto.objects.filter(pagina = this_pagina).count()
	cant_4 = attrEntero.objects.filter(pagina = this_pagina).count()
	cant_5 = attrDecimal.objects.filter(pagina = this_pagina).count()

	orden = cant_1 + cant_2 + cant_3 + cant_4 + cant_5 + 1

	newBA = attrPagina.objects.create(pagina = this_pagina, attNombre='Author', attValor=this_author, attOrden = orden)
	newBA.save()

	orden = orden + 1

	newBA = attrEntero.objects.create(pagina = this_pagina, attNombre='Pub Year', attValor=pub_year, attOrden = orden)
	newBA.save()

	orden = orden + 1

	newBA = attrTexto.objects.create(pagina = this_pagina, attNombre='Language', attValor=orig_lan, attOrden = orden)
	newBA.save()

	return redirect('/simpleblog/view-pagina/{}'.format(this_pagina.id))


def addAttrs(request):
	this_pagina = PaginaSB.objects.get(pk=int(request.POST.get("pageid")))

	tipo = request.POST.get("tipo")
	valor = request.POST.get("valor")
	nombre = request.POST.get("nombre")

	if tipo == "pagina":
		rel_pagina = PaginaSB.objects.get(pk=int(valor))
		newBA = attrPagina.objects.create(pagina = this_pagina, attNombre=nombre, attValor=rel_pagina, attOrden = 1)
		newBA.save()

	if tipo == "entero":
		newBA = attrEntero.objects.create(pagina = this_pagina, attNombre=nombre, attValor=valor, attOrden = 1)
		newBA.save()

	if tipo == "texto":
		newBA = attrTexto.objects.create(pagina = this_pagina, attNombre=nombre, attValor=valor, attOrden = 1)
		newBA.save()

	if tipo == "fecha":
		newBA = attrFecha.objects.create(pagina = this_pagina, attNombre=nombre, attValor=valor, attOrden = 1)
		newBA.save()

	if tipo == "decimal":
		newBA = attrDecimal.objects.create(pagina = this_pagina, attNombre=nombre, attValor=valor, attOrden = 1)
		newBA.save()


	return redirect('/simpleblog/view-pagina/{}'.format(this_pagina.id))


def adminColecciones(request):
	ptitulo = 'Admin Colecciones'
	colecciones = ItemColeccion.objects.all().order_by('-id')[0:40]

	if request.method == 'POST':
		colecciones = ItemColeccion.objects.filter(nombre__contains=request.POST.get("key_words"))
	return render(request,'admin_colecciones.html',{'ptitulo':ptitulo,'colecciones':colecciones})

def addColeccionSB(request):
	nombre = request.POST.get("nombre")
	info = request.POST.get("info")

	newC = ItemColeccion.objects.create(nombre=nombre,info=info)

	return redirect('/simpleblog/admin-colecciones')


def viewColeccion(request,colid):
	this_coleccion = ItemColeccion.objects.get(pk=int(colid))
	colitems = RelacionIC.objects.filter(coleccion=this_coleccion)

	searchItems = None

	if request.method == 'POST':
		keyword = request.POST.get("key_words")
		searchItems = PaginaSB.objects.filter(titulo__contains=keyword).order_by('-id')[0:50]

	return render(request,'view-coleccion.html',{'ptitulo':this_coleccion.nombre,'this_coleccion':this_coleccion,'colitems':colitems,'searchItems':searchItems})


def addRelacionIC(request,c,p):
	col = int(c)
	pag = int(p)

	coleccion = ItemColeccion.objects.get(pk=col)
	pagina = PaginaSB.objects.get(pk=pag)

	newRIC = RelacionIC.objects.create(coleccion=coleccion,pagina=pagina)
	newRIC.save()

	return redirect('/simpleblog/view-coleccion/{}'.format(col))


def inicio(request):
	items = PaginaSB.objects.all().order_by('-fecha_inicio')[0:25]
	ptitulo = 'Home - Simple Blog'
	colecciones = ItemColeccion.objects.all().order_by('id')[0:30]
	if request.method == 'POST':
		items = PaginaSB.objects.filter(titulo__contains=request.POST.get("kw")).order_by('-id')

	return render(request,'simple-blog.html',{'ptitulo':ptitulo,'items':items,'colecciones':colecciones})


def categoria(request,c):
	items = PaginaSB.objects.filter(categoria__id=int(c)).order_by('-fecha_creacion')

	this_categoria = CategoriaSB.objects.get(pk=int(c))
	ptitulo = 'Home - Simple Blog'
	colecciones = ItemColeccion.objects.all().order_by('id')[0:30]
	if request.method == 'POST':
		items = PaginaSB.objects.filter(titulo__contains=request.POST.get("kw"), categoria__id=int(c)).order_by('-id')

	return render(request,'categoria.html',{'ptitulo':ptitulo,'items':items,'colecciones':colecciones,'this_categoria':this_categoria})


def sbcoleccion(request,c):
	this_coleccion = ItemColeccion.objects.get(pk=int(c))
	items = RelacionIC.objects.filter(coleccion=this_coleccion).order_by('id')

	ptitulo = 'Home - Simple Blog'
	colecciones = ItemColeccion.objects.all().order_by('id')[0:30]
	if request.method == 'POST':
		items = RelacionIC.objects.filter(pagina__titulo__contains=request.POST.get("kw")).order_by('-id')

	return render(request,'sbcoleccion.html',{'ptitulo':ptitulo,'items':items,'colecciones':colecciones,'this_coleccion':this_coleccion})


def epubGen(request,c):
	this_coleccion = ItemColeccion.objects.get(pk=int(c))
	items = RelacionIC.objects.filter(coleccion=this_coleccion).order_by('id')

	ptitulo = this_coleccion.nombre
	colecciones = ItemColeccion.objects.all().order_by('id')[0:30]
	if request.method == 'POST':
		items = RelacionIC.objects.filter(pagina__titulo__contains=request.POST.get("kw")).order_by('-id')

	return render(request,'epubgen.html',{'ptitulo':ptitulo,'items':items,'colecciones':colecciones,'this_coleccion':this_coleccion})


def blog(request,p):
	this_pagina = PaginaSB.objects.get(pk=int(p))
	colecciones = ItemColeccion.objects.all().order_by('id')[0:30]
	atributos = getPageAttrs(this_pagina.id).attrDict()
	cant_att = len(atributos)
	return render(request,'blog.html',{'ptitulo':this_pagina.titulo,'this_pagina':this_pagina,'colecciones':colecciones,'atributos':atributos,'cant_att':cant_att})


def readingHist(request):
	ptitulo = 'Literature Reading History'
	lecturas = attrFecha.objects.filter(attNombre='Read',pagina__categoria__nombre_categoria='book').order_by('-attValor')

	return render(request,'read-history.html',{'ptitulo':ptitulo,'lecturas':lecturas})
