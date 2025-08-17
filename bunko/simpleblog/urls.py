from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
path('', views.inicio, name='inicio'),
path('admin-categorias/', views.adminCategorias, name='adminCategorias'),
path('add-categoria/', views.addCategoria, name='addCategoria'),
path('admin-paginas/', views.adminPaginas, name='adminPaginas'),
path('add-pagina/', views.addPagina, name='addPagina'),
path('view-pagina/<pid>', views.viewPagina, name='viewPagina'),
path('add-book-attr/<pid>', views.addAtributosBook, name='addBookAttr'),
path('save-book-attr/', views.saveBookAttr, name='saveBookAttr'),
path('add-attrs/', views.addAttrs, name='addAttrs'),
path('admin-colecciones/', views.adminColecciones, name='adminColecciones'),
path('add-coleccionsb/', views.addColeccionSB, name='addColeccionSB'),
path('view-coleccion/<colid>', views.viewColeccion, name='viewColeccion'),
path('add-relacion-ic/<c>/<p>', views.addRelacionIC, name='addRelacionIC'),
path('blog/<p>', views.blog, name='blog'),
path('sbcoleccion/<c>', views.sbcoleccion, name='sbcoleccion'),
path('categoria/<c>', views.categoria, name='categoria'),
path('rhistory/', views.readingHist, name='readingHist'),
path('epubgen/<c>', views.epubGen, name='epubGen'),



]