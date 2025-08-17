from django.db import models
from datetime import datetime
from django.db import models
from django.utils import timezone
import os
from uuid import uuid4
from django.db.models import Q, Avg, Count, Min, Sum
from random import choice
from django.utils.timezone import now
import re
import markdown


class CategoriaSB(models.Model):
	nombre_categoria = models.CharField(max_length=255)
	def __str__(self):
		return self.nombre_categoria

class PaginaSB(models.Model):
	titulo = models.CharField(max_length=255)
	contenido = models.TextField()
	fecha_creacion = models.DateTimeField(auto_now=True,editable=False)
	fecha_inicio = models.DateField(default='2025-04-29')
	categoria = models.ForeignKey(CategoriaSB, on_delete = models.CASCADE)

	@property
	def headtext(self):
		n_corte = self.contenido.find('==headtext==')
		if n_corte == -1:
			return self.contenido[0:350]
		else:
			return self.contenido[0:n_corte]

	@property
	def cleantext(self):
		n_corte = self.contenido.find('==headtext==')
		if n_corte == -1:
			return self.contenido
		else:
			return self.contenido.replace('==headtext==','')

	@property
	def mdOutput(self):
		n_corte = self.contenido.find('==headtext==')
		if n_corte == -1:
			this_texto = self.contenido
		else:
			this_texto = self.contenido.replace('==headtext==','')
		return(markdown.markdown(this_texto,extensions=['extra']))

	@property
	def authors(self):
		autores = ""
		if self.categoria.nombre_categoria == 'book':
			query_autores = attrPagina.objects.filter(attNombre='Author',pagina=self).order_by('id')

			for q in query_autores:
				autores = autores + q.attValor.titulo.strip() + ", "
		return autores[:-2]

	@property
	def pubyear(self):
		pub_year = 0
		if self.categoria.nombre_categoria == 'book':
			query_pubyear = attrEntero.objects.filter(attNombre='Pub Year',pagina=self).latest('id')
			pub_year=query_pubyear.attValor

		return pub_year

	def __str__(self):
		return self.titulo


class attrPagina(models.Model):
	pagina = models.ForeignKey(PaginaSB, on_delete=models.CASCADE, related_name="this_pagina")
	attNombre = models.CharField(max_length=255)
	attValor = models.ForeignKey(PaginaSB, on_delete=models.CASCADE, related_name="rel_pagina")
	attOrden = models.IntegerField()

	def __str__(self):
		return self.attNombre +' @ '+ self.pagina.titulo


class attrEntero(models.Model):
	pagina = models.ForeignKey(PaginaSB, on_delete=models.CASCADE)
	attNombre = models.CharField(max_length=255)
	attValor =  models.IntegerField()
	attOrden = models.IntegerField()

	def __str__(self):
		return self.attNombre +' @ '+ self.pagina.titulo

class attrFecha(models.Model):
	pagina = models.ForeignKey(PaginaSB, on_delete=models.CASCADE)
	attNombre = models.CharField(max_length=255)
	attValor = models.DateField()
	attOrden = models.IntegerField()

	def __str__(self):
		return self.attNombre +' @ '+ self.pagina.titulo

class attrTexto(models.Model):
	pagina = models.ForeignKey(PaginaSB, on_delete=models.CASCADE)
	attNombre = models.CharField(max_length=255)
	attValor = models.TextField()
	attOrden = models.IntegerField()

	def __str__(self):
		return self.attNombre +' @ '+ self.pagina.titulo


class attrDecimal(models.Model):
	pagina = models.ForeignKey(PaginaSB, on_delete=models.CASCADE)
	attNombre = models.CharField(max_length=255)
	attValor = models.DecimalField(max_digits=16, decimal_places=4)
	attOrden = models.IntegerField()

	def __str__(self):
		return self.attNombre +' @ '+ self.pagina.titulo

class ItemColeccion(models.Model):
	nombre = models.CharField(max_length=255)
	info = models.TextField()

	def __str__(self):
		return self.nombre

	@property
	def nitems(self):
		return RelacionIC.objects.filter(coleccion=self).count()

class RelacionIC(models.Model):
	pagina = models.ForeignKey(PaginaSB,on_delete=models.CASCADE)
	coleccion = models.ForeignKey(ItemColeccion,on_delete=models.CASCADE)

	def __str__(self):
		return self.pagina.titulo +' @ '+ self.coleccion.nombre




