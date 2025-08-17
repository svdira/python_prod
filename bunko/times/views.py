from django.shortcuts import render, redirect
from django.core.paginator import Paginator
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
import locale


def plantilla(request):
	return render(request,'base_forms.html',{})

def busqueda(request):
	keyword = request.POST.get("kw")

	if len(keyword)>2:
		wiki_matches = Wiki.objects.filter(Q(title__contains=keyword) | Q(info__contains=keyword)).order_by('updated_at')
		book_matches = Book.objects.filter(Q(title__contains=keyword) | Q(info__contains=keyword))
		movie_matches = Movie.objects.filter(Q(title__contains=keyword) | Q(info__contains=keyword))

	return render(request,'results.html',{'wikies':wiki_matches,'books':book_matches,'movies':movie_matches,'keyword':keyword})


def addwiki(request,col):
	wtypes = WikiType.objects.filter(category__in=['blog','character','event','journal','news','review','profile']).order_by('category')
	colecciones = Pagina.objects.all().order_by('titulo')
	coleccion = None
	if int(col) > 0:
	    coleccion = Pagina.objects.get(pk=int(col))

	if request.method == 'POST':
		this_cat = WikiType.objects.get(pk=int(request.POST.get("cat_id")))
		this_titulo = request.POST.get("title")
		this_info = request.POST.get("info")

		newW = Wiki.objects.create(wtype=this_cat,title=this_titulo,info=this_info,updated_at=datetime.now())
		newW.save()

		if int(request.POST.get("col_id")) > 0:
			coleccion = Pagina.objects.get(pk=int(request.POST.get("col_id")))
			newREL = PageRels.objects.create(page=coleccion,child=newW)
			return redirect('/itemcol/{}/{}'.format(newW.id,coleccion.id))
		else:
			return redirect('/wiki/{}'.format(newW.id))
	else:
		return render(request,'add-wiki.html',{'wtypes':wtypes,'colecciones':colecciones,'coleccion':coleccion})

def addpersona(request):
	wtypes = WikiType.objects.all().order_by('category')

	if request.method == 'POST':
		this_cat = WikiType.objects.get(pk=int(request.POST.get("cat_id")))
		this_titulo = request.POST.get("title")
		this_info = request.POST.get("info")

		newW = Wiki.objects.create(wtype=this_cat,title=this_titulo,info=this_info,updated_at=datetime.now())
		newW.save()

		return redirect('/wiki/{}'.format(newW.id))
	else:
		return render(request,'add-persona.html',{'wtypes':wtypes})

def editwiki(request,wikiid):
	this_wiki = Wiki.objects.get(pk=int(wikiid))
	wtypes = WikiType.objects.all()
	relbook = MediaWiki.objects.filter(mwiki = this_wiki).latest('id')

	if request.method == 'POST':
		this_cat = WikiType.objects.get(pk=int(request.POST.get("cat_id")))
		this_titulo = request.POST.get("title")
		this_info = request.POST.get("info")
		Wiki.objects.filter(id=int(wikiid)).update(wtype=this_cat,title=this_titulo,info=this_info)

		if relbook:
		    return redirect('/book/{}'.format(relbook.media_id))
		else:
		    return redirect('/wiki/{}'.format(this_wiki.id))
	else:
		return render(request,'edit-wiki.html',{'this_wiki':this_wiki,'wtypes':wtypes})

def fastedit(request):
	this_cat = WikiType.objects.get(pk=int(request.POST.get("cat_id")))
	this_titulo = request.POST.get("title")
	this_info = request.POST.get("info")
	Wiki.objects.filter(id=int(request.POST.get("wikiid"))).update(wtype=this_cat,title=this_titulo,info=this_info,updated_at=datetime.now())
	if request.POST.get("origen")=='wiki_1':
		return redirect('/wiki/{}'.format(request.POST.get("wikiid")))
	else:
		return redirect('/itemcol/{}/{}'.format(request.POST.get("wikiid"),request.POST.get("colid")))



def wiki(request,wid):
	this_wiki = Wiki.objects.get(pk=int(wid))
	collection = Pagina.objects.all().order_by('titulo')
	wtypes = WikiType.objects.all()

	rel_books = Book.objects.raw("""
		select
		    a.*
		from
		    times_book a
		    inner join times_credito b
		    on a.id = b.media_id
		    inner join times_wiki c
		    on b.persona_id = c.id
		where
		    c.id = {}
		   order by a.pub_year
		    """.format(this_wiki.id))

	return render(request,'view-wiki.html',{'this_wiki':this_wiki,'paginas':collection,'wtypes':wtypes,'creditos':rel_books})

def homepage(request):
    page = request.GET.get('page', 1)
    nlist = 16
    npics = Wiki.objects.all().count()
    npages = math.ceil(npics/nlist)
    articles = Wiki.objects.all().exclude(wtype__id__in=[1,2,3,4,5,8,20]).exclude(id=180).order_by('-updated_at')
    paginator = Paginator(articles, 12)
    resultados = paginator.get_page(page)
    pinned_posts = Wiki.objects.filter(id=180)
    on_reading = DiraConsumo.objects.filter(fec_fin__isnull=True)


    if int(page) > 1:
        on_reading = None
      

    authors = Credito.objects.filter(ctype__id=1,media_type=1).exclude(persona__id__in = [36,40]).values('persona__title','persona__id').annotate(qbooks=Count('media_id')).order_by('-qbooks')
    autores = sorted(DiraOcupation.objects.filter(ocupation='author').all().order_by('persona__nombre'),key=lambda t: t.persona.nbooks, reverse=True)
    dpaginas = PageRels.objects.values('page__titulo','page__id').annotate(qitems = Count('page__id'), lastup=Max('child__updated_at')).order_by('-lastup')[0:50]

    return render(request,'homepage.html',{'articles':resultados,'pinned_posts':pinned_posts,'dpaginas':dpaginas,'npages':range(npages),'on_reading':on_reading,'authors':autores,'npage':int(page)})

def addbook(request):
	personas = Wiki.objects.filter(wtype__category='author').order_by('title')
	booktypes = WikiType.objects.filter(id__in=[9,10,11,12]).order_by('id')
	listas = BookList.objects.all().order_by('listname')

	if request.method == 'POST':
		autor = Wiki.objects.get(pk=int(request.POST.get("autor")))
		btype = WikiType.objects.get(pk=int(request.POST.get("btype")))
		btitle = request.POST.get("title")
		pubyear = int(request.POST.get("pub_year"))

		if request.POST.get("info","") == "":
		    binfo = f"No review or synopsis has been written for this title. Please feel free to write one."
		else:
		    binfo = request.POST.get("info","")

		origlan = request.POST.get("orig_lan")

		newB = Book.objects.create(title = btitle,orig_lan = origlan,info=binfo, pub_year=pubyear, wtype=btype)
		newB.save()
		if btype.id == 9:
		    credtype = CreditType.objects.get(pk=1)
		elif btype.id == 10:
		    credtype = CreditType.objects.get(pk=7)
		elif btype.id == 11:
		    credtype = CreditType.objects.get(pk=5)
		elif btype.id == 12:
		    credtype = CreditType.objects.get(pk=6)

		newC = Credito.objects.create(ctype=credtype, persona = autor, media_type=1, media_id=newB.id)



		if len(request.POST.get("tags",""))>0:
			tags = request.POST.get("tags","").split(",")
			for t in tags:
				bt = BookTag.objects.create(libro=newB,tag=t)
				bt.save()

		if request.FILES.get("imagen","")!='':
			ix = request.FILES.get("imagen")
			newM = BookMedia.objects.create(libro=newB,imgtype=1,imagen=ix)
			newM.save()

		if int(request.POST.get("lista_id"))>0:
			this_lista = BookList.objects.get(pk=int(request.POST.get("lista_id")))
			newBL =  RelBookList.objects.create(blist=this_lista,bbook=newB)
			newBL.save()



		return redirect('/book/{}'.format(newB.id))
	else:
		return render(request,'add-book.html',{'personas':personas,'booktypes':booktypes,'listas':listas})

def book(request,bookid):
	this_book = Book.objects.get(pk=int(bookid))
	wtypes = WikiType.objects.all()
	related_wikis = MediaWiki.objects.filter(media_type=1, media_id=this_book.id).order_by('id')
	listas = BookList.objects.all().order_by('listname')

	this_book_series = RelBookList.objects.filter(bbook=this_book,blist__tipo__in=[1,2,3])

	get_books = None

	series_libros = [this_book.id]

	tb_series = []
	if this_book_series:
		for bs in this_book_series:
			tb_series.append(bs.blist.id)
		if len(tb_series)>0:
			get_books =  RelBookList.objects.filter(blist__id__in=tb_series).exclude(bbook__id=this_book.id).values_list('bbook__id').distinct()
			for i in get_books:
				series_libros.append(i[0])

	conteo_be = BookEntity.objects.filter(libro__id__in=series_libros).count()

	citas = BookQuote.objects.filter(libro=this_book).order_by('id')

	barras = ProgressBar.objects.filter(libro=this_book,avance__lt=F('cantidad'))

	btags = BookTag.objects.filter(libro__id=this_book.id)

	entidades = BookEntity.objects.filter(libro__id__in=series_libros).order_by('-importancia','id')

	if conteo_be > 0 and conteo_be <= 15:
		return render(request,'view-book-entity.html',{'this_book':this_book,'entidades':entidades,'btags':btags,'wtypes':wtypes,'relw':related_wikis,'blistas':listas,'barras':barras,'citas':citas,'tb_series':series_libros})
	else:
		return render(request,'view-book.html',{'this_book':this_book,'entidades':entidades,'btags':btags,'wtypes':wtypes,'relw':related_wikis,'blistas':listas,'barras':barras,'citas':citas,'tb_series':series_libros})

def books(request,y):
	conteo_y = DiraConsumo.objects.filter(fec_fin__isnull=False).count()
	legacy_count = DiraBook.objects.filter(legacy=True).count()
	if conteo_y > 0:
		max_year = DiraConsumo.objects.filter(fec_fin__isnull=False).order_by('-fec_fin').first()
	else:
		max_year = 0

	if int(y)==1 and conteo_y > 0:
		y = max_year.fec_fin.strftime('%Y')
		conteo = DiraBook.objects.filter(Q(legacy=True) | Q(read=True)).count()
		anhos = DiraConsumo.objects.filter(volume__tipo='book',fec_fin__isnull=False).values('fec_fin__year').annotate(qbooks=Count('id')).order_by('-fec_fin__year')
		rqueue = DiraBook.objects.filter(diraconsumo__volume__isnull=True, tipo='book').order_by('pubyear')
		rhist = DiraConsumo.objects.filter(volume__tipo='book',fec_fin__year=int(y)).order_by('-fec_fin','-id')
	else:
		y = 0
		conteo = DiraBook.objects.filter(Q(legacy=True) | Q(read=True)).count()
		anhos = None
		rqueue = None
		rhist = None
	

	return render(request,'view-history.html',{'rhist':rhist,'rqueue':rqueue,'anhos':anhos,'anho':y,'conteo':conteo,'legacy_count':legacy_count})

def bqueue(request):

	rqueue = DiraBook.objects.filter(read=False,legacy=False, tipo='book').order_by('pubyear')
	qconteo = DiraBook.objects.filter(read=False,legacy=False, tipo='book').count()
	rhist = Consumo.objects.all().order_by('-finish_d')

	return render(request,'bqueue.html',{'rhist':rhist,'rqueue':rqueue,'qconteo':qconteo})

def bunko(request,y):

	max_year = Consumo.objects.order_by('-finish_d').first()

	if int(y)==1:
		y = max_year.finish_d.strftime('%Y')

	conteo = Consumo.objects.filter(volume__wtype__id__in=[10,11,12]).count()
	anhos = Consumo.objects.filter(volume__wtype__id__in=[10,11,12]).values('finish_d__year').annotate(qbooks=Count('id')).order_by('-finish_d__year')
	rqueue = Book.objects.filter(consumo__volume__isnull=True, wtype__id__in=[10,11,12]).order_by('pub_year')
	rhist = Consumo.objects.filter(volume__wtype__id__in=[10,11,12],finish_d__year=int(y)).order_by('-finish_d','-id')

	return render(request,'bunko.html',{'rhist':rhist,'rqueue':rqueue,'anhos':anhos,'anho':y,'conteo':conteo})


def bkqueue(request):

	rqueue = Book.objects.filter(consumo__volume__isnull=True, wtype__id__in=[10,11,12]).order_by('pub_year')
	rhist = Consumo.objects.all().order_by('-finish_d')

	return render(request,'bkqueue.html',{'rhist':rhist,'rqueue':rqueue})

def readbook(request):
	rbook = Book.objects.get(pk=int(request.POST.get("bookid")))

	fecha_i = request.POST.get("start_d")
	fecha_f = request.POST.get("finish_d")
	bpages = request.POST.get("pages")

	newR = Consumo.objects.create(volume = rbook, pages=bpages,start_d=fecha_i,finish_d=fecha_f)
	newR.save()

	return redirect('/book/{}'.format(rbook.id))

def appendwiki(request):
	this_wiki = Wiki.objects.get(pk=int(request.POST.get("wikiid")))
	this_page = Pagina.objects.get(pk=int(request.POST.get("pageid")))

	newR = PageRels.objects.create(page=this_page, child=this_wiki)
	newR.save()

	return redirect('/wiki/{}'.format(this_wiki.id))

def pagina(request,p):
	this_page = Pagina.objects.get(pk=int(p))
	children = PageRels.objects.filter(page=this_page).order_by('-child__updated_at')

	return render(request,'page.html',{'this_page':this_page,'children':children})

def htmlPublish(request,p):
	this_page = Pagina.objects.get(pk=int(p))
	children = PageRels.objects.filter(page=this_page).order_by('child__id')

	return render(request,'kindlePublish.html',{'this_page':this_page,'children':children})

def addmovie(request):
	if request.method == 'POST':
		mtitle = request.POST.get("title")
		mpremiere = request.POST.get("premiere")
		mruntime = request.POST.get("runtime")
		minfo = request.POST.get("info")

		newM = Movie.objects.create(title=mtitle,premiere=mpremiere,runtime=mruntime,info=minfo)
		newM.save()
		return redirect('/movie/{}'.format(newM.id))
	else:
		return render(request,'add-movie.html',{})

def movie(request,movieid):
	this_movie = Movie.objects.get(pk=int(movieid))
	wtypes = WikiType.objects.all()
	related_wikis = MediaWiki.objects.filter(media_type=2, media_id=this_movie.id).order_by('-id')
	director = MovieCredit.objects.filter(film__id=this_movie.id, credit = 'Director' )
	cast = MovieCredit.objects.filter(film__id=this_movie.id, credit = 'Main Cast')
	movielists = MovieList.objects.all().order_by('titulo')

	return render(request,'view-movie.html',{'movielists':movielists,'this_movie':this_movie,'wtypes':wtypes,'relw':related_wikis,'director':director,'cast':cast})

def watchmovie(request):
	wmovie = Movie.objects.get(pk=int(request.POST.get("movieid")))

	fecha_i = request.POST.get("start_d")

	newR = MovieWatch.objects.create(film=wmovie,wdate=fecha_i)
	newR.save()

	return redirect('/movie/{}'.format(wmovie.id))

def movies(request,y):

	max_year = MovieWatch.objects.order_by('-wdate').first()

	if int(y)==1:
		y = max_year.wdate.strftime('%Y')

	conteo = MovieWatch.objects.count()
	anhos = MovieWatch.objects.values('wdate__year').annotate(qbooks=Count('id')).order_by('-wdate__year')

	wmovies = MovieWatch.objects.filter(wdate__year=int(y)).order_by('-wdate')
	return render(request,'movie-history.html',{'wmovies':wmovies,'anho':int(y),'conteo':conteo,'anhos':anhos})

def mqueue(request):
	twmovies = Movie.objects.filter(moviewatch__film__isnull=True).order_by('premiere')
	return render(request,'mqueue.html',{'twmovies':twmovies})

def addshow(request):
	if request.method == 'POST':
		stitle = request.POST.get("title")
		stype = request.POST.get("cat_id")
		sinfo = request.POST.get("info")
		spremiere = request.POST.get("premiere")
		sfinale = request.POST.get("finale")
		sepisodes= request.POST.get("episodes")
		avgdur = request.POST.get("avgduration")

		newS = DiraTemporada.objects.create(show_title = stitle,
			single_season = True,
			show_premiere = spremiere,
			show_finale = sfinale,
			episodes = sepisodes,
			avg_duration = avgdur,
			tipo = stype,
			sinopsis =sinfo)
		newS.save()

		if request.POST.get("nowshow")=='ninguno':
			newSeries = ShowCollection.objects.create(cname=request.POST.get("newtitle"))
			newSeries.save()

			newR = RelShowCol.objects.create(coleccion=newSeries,temporada=newS)
			newR.save()
		else:
			series_id = int(request.POST.get("nowshow"))
			series_c = ShowCollection.objects.get(pk=series_id)
			newR = RelShowCol.objects.create(coleccion=series_c,temporada=newS)
			newR.save()

	
		return redirect('/show/{}'.format(newS.id))
	else:
		showtypes = ["show","anime"]
		show_series = ShowCollection.objects.all().order_by('cname')
		return render(request,'add-show.html',{'showtypes':showtypes,'show_series':show_series})

def show(request,show_id):
	this_show = DiraTemporada.objects.get(pk=int(show_id))
	series = RelShowCol.objects.filter(temporada=this_show).latest('id')

	return render(request,'dira-show.html',{'this_show':this_show,'series':series})

def watchshow(request):
	this_season = Season.objects.get(pk=int(request.POST.get("seasonid")))
	inicio = request.POST.get("start_d")
	fin = request.POST.get("finish_d")

	newW = SeasonProgressBar.objects.create(temporada=this_season,avance=1,fecha_inicio=inicio)
	newW.save()

	newPA = SeasonProgressLog.objects.create(barra=newW, fecha=inicio, progreso=1, delta_lec=1)
	newPA.save()

	return redirect('/show/{}'.format(this_season.show.id))

def addnewseason(request):
	this_show = Show.objects.get(pk=int(request.POST.get("show_id")))
	stitle = request.POST.get("stitle")
	sinfo = request.POST.get("info")
	spremiere = request.POST.get("premiere")
	sepisodes= request.POST.get("episodes")
	avgdur = request.POST.get("avgduration")

	newSE = Season.objects.create(show=this_show,season_t=stitle,info = sinfo, episodes=sepisodes, avg_runtime=avgdur,premiere=spremiere)
	newSE.save()

	return redirect('/show/{}'.format(this_show.id))

def shows(request):
	watchedshows = TempConsumo.objects.all().order_by('-fec_fin')
	return render(request,'shows.html',{'watchedshows':watchedshows})

def showqueue(request):
	twshows = ShowCollection.objects.all().order_by('cname')
	return render(request,'showqueue.html',{'twshows':twshows})

def addnewrelwiki(request):
	this_cat = WikiType.objects.get(pk=int(request.POST.get("cat_id")))
	this_titulo = request.POST.get("title")
	this_info = request.POST.get("info")
	this_book = Book.objects.get(pk=int(request.POST.get("media_id")))
	newW = Wiki.objects.create(wtype=this_cat,title=this_titulo,info=this_info,updated_at=datetime.now())
	newW.save()

	newRW = MediaWiki.objects.create(mwiki=newW,media_type=int(request.POST.get("media_type")), media_id=int(request.POST.get("media_id")))
	newRW.save()

	return redirect('/book/{}'.format(this_book.id))

def itemcol(request,itm,col):
	this_wiki = Wiki.objects.get(pk=int(itm))
	collection = Pagina.objects.get(pk=int(col))
	all_items = PageRels.objects.filter(page=collection).exclude(child=this_wiki).order_by('child__title')
	wtypes = WikiType.objects.all()
	collections = Pagina.objects.all()
	return render(request,'view-wiki-cols.html',{'this_wiki':this_wiki,'pagina':collection,'all_items':all_items,'paginas':collections,'wtypes':wtypes})

def addbooktolist(request):
	lista_id = request.POST.get("lista_id")
	book_id = request.POST.get("book_id")
	this_lista = BookList.objects.get(pk=int(lista_id))
	this_book  = Book.objects.get(pk=int(book_id))

	newR = RelBookList.objects.create(blist=this_lista,bbook=this_book)
	newR.save()

	return redirect('/booklist/{}'.format(lista_id))

def booklists(request):
	listas = BookList.objects.raw("""
                select
                a.*
                from
                times_booklist a
                left join (
                select
                    a.blist_id,
                    max(c.finish_d) max_f
                from
                    times_relbooklist a
                    inner join times_book b
                    on a.bbook_id = b.id
                    inner join times_consumo c
                    on b.id = volume_id
                group by
                    a.blist_id ) b
                on a.id = b.blist_id
                order by
                ifnull(b.max_f,'1999-12-31') desc, a.id desc
	""")
	return render(request,'booklists.html',{'listas':listas})


def booklist(request,lid):
	this_lista = BookList.objects.get(pk=int(lid))
	if this_lista.tipo == 0:
		this_books = RelBookList.objects.filter(blist=this_lista).order_by('id')
	else:
		this_books = RelBookList.objects.filter(blist=this_lista).order_by('bbook__pub_year','id')
	book_matches = None

	if request.method == 'POST':
		keyword = request.POST.get("keyword","")
		if len(keyword)>2:
			book_matches = Book.objects.filter(Q(title__contains=keyword) | Q(info__contains=keyword))

	return render(request,'lista.html',{'this_lista':this_lista,'this_books':this_books, 'book_s':book_matches})

def addprogressbar(request):
	import datetime
	this_book = Book.objects.get(pk=int(request.POST.get("book_id")))
	units = request.POST.get("units")
	cant = request.POST.get("cantidad")
	start_d = request.POST.get("start_date")

	conteo = Consumo.objects.filter(volume=this_book,start_d=datetime.datetime(1999, 12, 31)).count()


	if conteo > 0:
		Consumo.objects.filter(volume=this_book,start_d=datetime.datetime(1999, 12, 31)).delete()

	if request.POST.get("units") == 'AudioBook':
		tiempo = request.POST.get("cantidad").split(":")
		horas = int(tiempo[0])
		minutos = int(tiempo[1])

		paginas = 30*(float(1.0*horas) + float(minutos/60.0))

		cant = int(round(paginas,0))

	newPB = ProgressBar.objects.create(libro = this_book,units=units,cantidad=cant,fecha_inicio = start_d)
	newPB.save()

	return redirect('/book/{}'.format(this_book.id))

def saveprogress(request):
	barra = ProgressBar.objects.get(pk=int(request.POST.get("barraid")))
	libro = Book.objects.get(pk=int(request.POST.get("bookid")))
	progreso = request.POST.get("progress")
	fecha = request.POST.get("fecha")

	if barra.units == 'AudioBook':
		tiempo = request.POST.get("progress").split(":")
		horas = int(tiempo[0])
		minutos = int(tiempo[1])

		paginas = 30*(float(1.0*horas) + float(minutos/60.0))
		progreso = int(round(paginas,0))


	delta = int(progreso) - barra.avance

	if (int(progreso) <= barra.cantidad	and int(progreso) > barra.avance):
		newLog = ProgressLog.objects.create(barra=barra,fecha=fecha,progreso=progreso, delta_lec=delta)
		newLog.save()
		ProgressBar.objects.filter(id=barra.id).update(avance=progreso)

	if (int(progreso)==barra.cantidad):
		newC = Consumo.objects.create(volume=libro,pages=barra.cantidad,start_d=barra.fecha_inicio, finish_d=fecha)
		newC.save()

	return redirect('/book/{}'.format(libro.id))

def statistics(request):

	paginas = ProgressLog.objects.raw("""
			select
			    1 as id,
			     strftime('%Y',date(fecha,'weekday 0')) as anho,
			      1*strftime('%m',date(fecha,'weekday 0'))-1 as mes,
			       1*strftime('%d',date(fecha,'weekday 0')) as dia,
			    sum(delta_lec) as paginas
			from
			    times_progresslog a
			    left join times_progressbar b
			    on a.barra_id=b.id
			    left join times_book c
			    on b.libro_id=c.id
			where
			    c.wtype_id in (9,10) and a.fecha >= '2025-07-07' and units in ('Printed','Kindle')
			group by
			      strftime('%Y',date(fecha,'weekday 0')) ,
			      1*strftime('%m',date(fecha,'weekday 0')) -1,
			       1*strftime('%d',date(fecha,'weekday 0'))

						    """)
	data_points = "["
	for p in paginas:
		data_points=data_points+"{ x: new Date("+ str(p.anho) +","+ str(p.mes) +" , "+ str(p.dia) +"), y: "+str(p.paginas)+" },"
	data_points=data_points+"]"

	capitulos = ProgressLog.objects.raw("""
			select
			    1 as id,
			     strftime('%Y',date(fecha,'weekday 0')) as anho,
			      1*strftime('%m',date(fecha,'weekday 0'))-1 as mes,
			       1*strftime('%d',date(fecha,'weekday 0')) as dia,
			    sum(delta_lec) as paginas ,
			    date(fecha,'weekday 6') fecha
			from
			    times_progresslog a
			    left join times_progressbar b
			    on a.barra_id=b.id
			    left join times_book c
			    on b.libro_id=c.id
			where
			    c.wtype_id in (11) and a.fecha >= '2025-07-07'
			group by
			      strftime('%Y',date(fecha,'weekday 0')) ,
			      1*strftime('%m',date(fecha,'weekday 0')) -1,
			       1*strftime('%d',date(fecha,'weekday 0')),
			       date(fecha,'weekday 6') order by date(fecha,'weekday 6') desc
						    """)
	data_points2 = "["
	for p in capitulos:
		data_points2=data_points2+"{ x: new Date("+ str(p.anho) +","+ str(p.mes) +" , "+ str(p.dia) +"), y: "+str(p.paginas)+" },"
	data_points2=data_points2+"]"

	return render(request, 'stats.html', { "data_points" : data_points, "data_points2":data_points2, 'capitulos':capitulos })


def saveshowprogress(request):
	barra = SeasonProgressBar.objects.get(pk=int(request.POST.get("barraid")))
	show = Show.objects.get(pk=int(request.POST.get("showid")))
	progreso = request.POST.get("progress")
	fecha = request.POST.get("fecha")

	delta = int(progreso) - barra.avance

	if (int(progreso) <= barra.temporada.episodes and int(progreso) > barra.avance):
		newLog = SeasonProgressLog.objects.create(barra=barra,fecha=fecha,progreso=progreso, delta_lec=delta)
		newLog.save()
		SeasonProgressBar.objects.filter(id=barra.id).update(avance=progreso)

	if (int(progreso)== barra.temporada.episodes):
		newC = ShowWatch.objects.create(sseason=barra.temporada,start_d=barra.fecha_inicio, finish_d=fecha)
		newC.save()

	return redirect('/show/{}'.format(show.id))

def addbookmedia(request):
	bid = request.POST.get("media_id")
	this_book = Book.objects.get(pk=int(bid))
	ix = request.FILES.get("imagen")
	img_type = int(request.POST.get("img_type"))

	newM = BookMedia.objects.create(libro=this_book,imgtype=img_type,imagen=ix)
	newM.save()

	return redirect('/book/{}'.format(this_book.id))


def addfilmmedia(request):
	bid = request.POST.get("media_id")
	this_movie = Movie.objects.get(pk=int(bid))
	ix = request.FILES.get("imagen")
	img_type = int(request.POST.get("img_type"))

	newM = MovieMedia.objects.create(film=this_movie,imgtype=img_type,imagen=ix)
	newM.save()

	return redirect('/movie/{}'.format(this_movie.id))

def savepost(request):
	entry = request.POST.get("entrada")
	created_at = request.POST.get("fecha")


	newT = Tweet.objects.create(texto = entry, created_at=created_at)
	newT.save()

	pat = re.compile(r"#(\w+)")

	listado = pat.findall(entry)

	if len(listado)>0:
		for l in listado:
			newE = Etiqueta.objects.create(tweet=newT, etiqueta=l)

	return redirect('/journal/1')

def editTweet(request,tweet_id):
	this_tweet = Tweet.objects.get(pk=int(tweet_id))
	msg = 0

	if request.method == 'POST':
		this_tweet.texto = request.POST.get("info")
		this_tweet.save()
		msg=1
	return render(request,'edit-tweet.html',{'this_tweet':this_tweet,'codigo':msg})


def journal(request,y):
	max_year = Tweet.objects.order_by('-created_at').first()

	if int(y)==1:
		y = max_year.created_at.strftime('%Y')
		posts = Tweet.objects.filter(created_at__year=int(y)).order_by('-created_at','-id')
	else:
		y = int(y)
		posts = Tweet.objects.filter(created_at__year=int(y)).order_by('created_at','id')

	anhos = Tweet.objects.values('created_at__year').annotate(qitems=Count('id')).order_by('-created_at__year')

	return render(request,'journal.html',{'posts':posts,'anhos':anhos,'anho':int(y)})

def jtokindle(request, y):

	posts = Tweet.objects.filter(created_at__year=int(y)).order_by('created_at','id')

	return render(request,'printed_journal.html',{'this_year':int(y),'this_posts':posts})

def etiqueta(request,y,e):
	max_year = Etiqueta.objects.filter(etiqueta=e).order_by('-tweet__created_at').first()

	if int(y)==1:
		y = max_year.tweet.created_at.strftime('%Y')

	anhos = Etiqueta.objects.filter(etiqueta=e).values('tweet__created_at__year').annotate(qitems=Count('id')).order_by('-tweet__created_at__year')
	posts = Etiqueta.objects.filter(etiqueta=e,tweet__created_at__year=int(y)).order_by('-tweet__created_at','-id')
	return render(request,'etiqueta.html',{'posts':posts,'anhos':anhos,'anho':int(y), 'this_etiqueta':e})



def mediastats(request):

	paginas = SeasonProgressLog.objects.raw("""
			with todo as (select
			    1 as id,
			    'shows' type,
			    strftime('%Y',date(a.fecha,'weekday 6')) as anho,
			    1*strftime('%m',date(a.fecha,'weekday 6'))-1 as mes,
			    1*strftime('%d',date(a.fecha,'weekday 6')) as dia,
			    round(sum(a.delta_lec*c.avg_runtime/60.0),1) as horas ,
			    date(a.fecha,'weekday 6') fecha
			from
			    times_seasonprogresslog a
			    left join times_seasonprogressbar b
			    on a.barra_id = b.id
			    left join times_season c
			    on b.temporada_id = c.id
			where
			    a.fecha >= '2025-04-01'
			group by
			    strftime('%Y',date(a.fecha,'weekday 6')),
			    1*strftime('%m',date(a.fecha,'weekday 6'))-1,
			    1*strftime('%d',date(a.fecha,'weekday 6')),
			    date(a.fecha,'weekday 6')

			union all

			select
			    1 as id,
			    'movies' type,
			    strftime('%Y',date(a.wdate,'weekday 6')) as anho,
			    1*strftime('%m',date(a.wdate,'weekday 6'))-1 as mes,
			    1*strftime('%d',date(a.wdate,'weekday 6')) as dia,
			    round(sum(b.runtime/60.0),1) as horas ,
			    date(a.wdate,'weekday 6') fecha
			from
			    times_moviewatch a
			    left join times_movie b
			    on a.film_id = b.id
			where
			    a.wdate >= '2025-04-01'
			group by
			    strftime('%Y',date(a.wdate,'weekday 6')),
			    1*strftime('%m',date(a.wdate,'weekday 6'))-1,
			    1*strftime('%d',date(a.wdate,'weekday 6')),
			    date(a.wdate,'weekday 6') )

			select
				1 as id,
			    anho,
			    mes,
			    dia,
			    fecha,
			    sum(horas) as horas
			from
			    todo
			group by
			    anho,
			    mes,
			    dia,
			    fecha

									    """)
	data_points = "["
	for p in paginas:
		data_points=data_points+"{ x: new Date("+ str(p.anho) +","+ str(p.mes) +" , "+ str(p.dia) +"), y: "+str(p.horas)+" },"
	data_points=data_points+"]"


	return render(request, 'media-stats.html', { "data_points" : data_points })

def addmoviecredits(request):
	director = request.POST.get("director")
	cast = request.POST.get("cast")
	movie = Movie.objects.get(pk=int(request.POST.get("movie_id")))

	for strC in request.POST.get("director","").split(","):
		newMC = MovieCredit.objects.create(film=movie,credit='Director',persona=strC.strip())
		newMC.save()

	for strC in request.POST.get("cast","").split(","):
		newMC = MovieCredit.objects.create(film=movie,credit='Main Cast',persona=strC.strip())
		newMC.save()

	return redirect('/movie/{}'.format(movie.id))

def movieperson(request,strPersona):
	creditos = MovieCredit.objects.filter(persona=strPersona).order_by('-film__premiere')
	personas = MovieCredit.objects.values('persona').annotate(ncredits = Count('id')).order_by('-ncredits','persona')[0:30]
	this_persona = strPersona

	return render(request,'movie-person.html',{'creditos':creditos,'personas':personas,'this_persona':this_persona})

def bookduel(request):


	n_duelos  = BookDuel.objects.raw("""
	select
		1 as id,
	    count(1) as conteo
	 from
	    posibles_duelos a
	    left join times_bookduel b
	    on a.volume_izq = b.left_b_id and a.volume_der = b.right_b_id
	    left join times_bookduel c
	    on a.volume_izq = c.right_b_id and a.volume_der = c.left_b_id
	where
	    b.id is null and c.id is null""")

	for n in n_duelos:
		n_d = n.conteo

	if n_d > 0:
		elegido = random.randint(0, (n_d)-1)

		duelos = BookDuel.objects.raw("""
		select
		    a.id,
		    a.volume_der,
		    a.volume_izq
		from
		    posibles_duelos a
		    left join times_bookduel b
		    on a.volume_izq = b.left_b_id and a.volume_der = b.right_b_id
		    left join times_bookduel c
		    on a.volume_izq = c.right_b_id and a.volume_der = c.left_b_id
		where
		    b.id is null and c.id is null""")[elegido]



		random_obj = Book.objects.get(pk=duelos.volume_izq)
		random_obj2 = Book.objects.get(pk=duelos.volume_der)


		conteo_1 = BookDuel.objects.filter(left_b__id=int(random_obj.id),right_b__id=int(random_obj2.id)).count()
		conteo_2 = BookDuel.objects.filter(left_b__id=int(random_obj2.id),right_b__id=int(random_obj.id)).count()
		conteo_t = conteo_1 + conteo_2
	else:
		elegido = 0
		random_obj = None
		random_obj2 = None
		conteo_t = None

	topbooks = BookDuel.objects.raw("""
		select
		    1 as id,
		    conteos.*,
		    datos.title,
		    datos.pub_year,
		    case
		    	when conteos.duels <= 5 then 0
		    	when conteos.duels <= 10 then 1
		    	when conteos.duels <= 25 then 2
		    	else 3
		    end flag_votes,

		    round(100.000*conteos.wins/conteos.duels,1) as rank_p
		from
		    (select
		        book_id,
		        sum(c) as duels,
		        sum(wins) as wins
		    from
		        (select
		            left_b_id as book_id,
		            count(1) c,
		            sum(case when win_b_id=left_b_id then 1 else 0 end) wins
		        from
		            times_bookduel
		        group by
		            left_b_id

		        union all

		        select
		            right_b_id book_id,
		            count(1) c,
		            sum(case when win_b_id=right_b_id then 1 else 0 end) wins
		        from
		            times_bookduel
		        group by
		            right_b_id ) as x
		    group by
		        book_id) conteos
		    left join times_book datos
		    on conteos.book_id = datos.id
		order by
			case
		    	when conteos.duels <= 5 then 0
		    	when conteos.duels <= 10 then 1
		    	when conteos.duels <= 25 then 2
		    	else 3
		    end desc,
		    100.000*conteos.wins/conteos.duels desc,  conteos.duels desc """)

	return render(request,'book_duel.html',{'book1':random_obj,'book2':random_obj2,'topbooks':topbooks, 'conteo_t':conteo_t,'n_duelos':n_d})


def savebookduel(request,l,r,w):

	conteo_1 = BookDuel.objects.filter(left_b__id=int(l),right_b__id=int(r)).count()
	conteo_2 = BookDuel.objects.filter(left_b__id=int(r),right_b__id=int(l)).count()

	conteo_t = conteo_2 + conteo_1

	if conteo_t == 0:
		book1 = Book.objects.get(pk=int(l))
		book2 = Book.objects.get(pk=int(r))
		book3 = Book.objects.get(pk=int(w))
		newBD = BookDuel.objects.create(left_b=book1,right_b=book2,win_b=book3)

	return redirect('/bookduel')


def movieduel(request):

	n_duelos  = MovieDuel.objects.raw("""
	select
	    1 as id,
	    count(1) as conteo
	from
	    movie_duelosp a
	    left join times_movieduel b
	    on a.volume_izq = b.left_b_id and a.volume_der = b.right_b_id
	    left join times_movieduel c
	    on a.volume_izq = c.right_b_id and a.volume_der = c.left_b_id
	where
	    b.id is null and c.id is null""")

	for n in n_duelos:
		n_d = n.conteo


	if n_d > 0:
		elegido = random.randint(0, (n_d)-1)
		duelos = MovieDuel.objects.raw("""
		select
		    a.id,
		    a.volume_der,
		    a.volume_izq
		from
		    movie_duelosp a
		    left join times_movieduel b
		    on a.volume_izq = b.left_b_id and a.volume_der = b.right_b_id
		    left join times_movieduel c
		    on a.volume_izq = c.right_b_id and a.volume_der = c.left_b_id
		where
		    b.id is null and c.id is null""")[elegido]

		random_obj = Movie.objects.get(pk=duelos.volume_izq)
		random_obj2 = Movie.objects.get(pk=duelos.volume_der)
		conteo_1 = MovieDuel.objects.filter(left_b__id=int(random_obj.id),right_b__id=int(random_obj2.id)).count()
		conteo_2 = MovieDuel.objects.filter(left_b__id=int(random_obj2.id),right_b__id=int(random_obj.id)).count()
		conteo_t = conteo_1 + conteo_2
	else:
		elegido = 0
		random_obj = None
		random_obj2 = None
		conteo_t = None




	topbooks = MovieDuel.objects.raw("""
		select
		    1 as id,
		    conteos.*,
		    datos.title,
		    datos.premiere,
		    case
		    	when conteos.duels <= 5 then 0
		    	when conteos.duels <= 10 then 1
		    	when conteos.duels <= 25 then 2
		    	else 3
		    end flag_votes,
		    round(conteos.wins*100.00/conteos.duels,1) rank_p
		from
		    (select
		        book_id,
		        sum(c) as duels,
		        sum(wins) as wins
		    from
		        (select
		            left_b_id as book_id,
		            count(1) c,
		            sum(case when win_b_id=left_b_id then 1 else 0 end) wins
		        from
		            times_movieduel
		        group by
		            left_b_id

		        union all

		        select
		            right_b_id book_id,
		            count(1) c,
		            sum(case when win_b_id=right_b_id then 1 else 0 end) wins
		        from
		            times_movieduel
		        group by
		            right_b_id ) as x
		    group by
		        book_id) conteos
		    left join times_movie datos
		    on conteos.book_id = datos.id
		order by
			case
		    	when conteos.duels <= 5 then 0
		    	when conteos.duels <= 10 then 1
		    	when conteos.duels <= 25 then 2
		    	else 3
		    end desc,
		    conteos.wins*1.00/conteos.duels desc,  conteos.duels desc """)



	return render(request,'movie_duel.html',{'book1':random_obj,'book2':random_obj2,'topbooks':topbooks,'conteo_t':conteo_t})


def savemovieduel(request,l,r,w):

	conteo_1 = MovieDuel.objects.filter(left_b__id=int(l),right_b__id=int(r)).count()
	conteo_2 = MovieDuel.objects.filter(left_b__id=int(r),right_b__id=int(l)).count()

	conteo_t = conteo_2 + conteo_1

	if conteo_t == 0:
		book1 = Movie.objects.get(pk=int(l))
		book2 = Movie.objects.get(pk=int(r))
		book3 = Movie.objects.get(pk=int(w))
		newBD = MovieDuel.objects.create(left_b=book1,right_b=book2,win_b=book3)

	return redirect('/movieduel')

def quemarlibro(request,libro):

	libro = Book.objects.get(pk=int(libro))

	fecha_r = '1999-12-31'

	conteo_2 = Consumo.objects.create(volume = libro, pages=180,start_d=fecha_r,finish_d=fecha_r)
	conteo_2.save()



	return redirect('/booklists')


def moviedbImport(request):
    import requests
    import json

    movie_id = request.POST.get("title")

    url = "https://api.themoviedb.org/3/movie/{}?language=en-US".format(movie_id)
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NmM4MjVlMDFiY2RiMWQ1NWQ4YjRmYzNiNDQ0ODFhZiIsInN1YiI6IjYwMWM1NmFkNzMxNGExMDAzZGZjMzhiOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vnpzsejhhlKDqssAg1dHiMH64Ja4_bP2UPcJFgHrW3k"
    }

    response = requests.get(url, headers=headers)
    movie_dict = json.loads(response.text)
    movie_dict3 = json.loads(response.text)

    str_titulo = movie_dict['original_title']
    str_overview = movie_dict['overview']
    str_premiere = movie_dict['release_date']
    str_runtime= movie_dict['runtime']
    str_poster = "https://image.tmdb.org/t/p/w200{}".format(movie_dict['poster_path'])

    url = "https://api.themoviedb.org/3/movie/{}/credits?language=en-US".format(movie_id)

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0NmM4MjVlMDFiY2RiMWQ1NWQ4YjRmYzNiNDQ0ODFhZiIsInN1YiI6IjYwMWM1NmFkNzMxNGExMDAzZGZjMzhiOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.vnpzsejhhlKDqssAg1dHiMH64Ja4_bP2UPcJFgHrW3k"
    }

    response = requests.get(url, headers=headers)
    movie_dict = json.loads(response.text)

    int_c = 0
    str_director = ""
    for c in movie_dict['crew']:
        if c['job']=='Director':
            str_director = str_director+c['original_name']+","

    str_director = str_director[:-1]

    str_cast = ""
    for c in movie_dict['cast'][0:25]:
        str_cast = str_cast+c['original_name']+","

    str_cast = str_cast[:-1]

    str_tags = str_director+","+str_premiere[0:4]+","+str_cast

    return render(request,'add-moviedb.html',{'str_tags':str_tags,'str_titulo':str_titulo,'str_overview':str_overview,'str_premiere':str_premiere[0:4],'str_runtime':str_runtime,'str_poster':str_poster,'str_director':str_director,'str_cast':str_cast})

def savemovie(request):
	mtitle = request.POST.get("title")
	mpremiere = request.POST.get("premiere")
	mruntime = request.POST.get("runtime")
	minfo = request.POST.get("info")

	newM = Movie.objects.create(title=mtitle,premiere=mpremiere,runtime=mruntime,info=minfo)
	newM.save()

	director = request.POST.get("director")
	cast = request.POST.get("cast")
	movie = Movie.objects.get(pk=newM.id)

	for strC in request.POST.get("director","").split(","):
		newMC = MovieCredit.objects.create(film=movie,credit='Director',persona=strC.strip())
		newMC.save()

	for strC in request.POST.get("cast","").split(","):
		newMC = MovieCredit.objects.create(film=movie,credit='Main Cast',persona=strC.strip())
		newMC.save()

	if request.FILES.get("imagen","")!='':
		ix = request.FILES.get("imagen")
		newMM = MovieMedia.objects.create(film=newM,imgtype=1,imagen=ix)
		newMM.save()



	return redirect('/movie/{}'.format(newM.id))

def addtimesmedia(request):
	if request.method == 'POST':
		info = request.POST.get("descripcion")
		ix = request.FILES.get("imagen")
		newM = TimesMedia.objects.create(title=info,imgtype=1,imagen=ix)
		newM.save()
		return redirect('/mediapage/0')
	else:
		return render(request,'add-times-media.html',{})

def mediapage(request,p):

	conteo = TimesMedia.objects.all().count()

	ppp = 10

	paginas = math.ceil(conteo/ppp)

	if (int(p)+1) == paginas:
		next_p = 0
	else:
		next_p = (int(p)+1)

	pagina = int(p)



	medias = TimesMedia.objects.all().order_by('-id')[int(p)*ppp:(int(p)*ppp)+ppp]

	return render(request,'times-album.html',{'medias':medias,'next_p':next_p,'paginas':paginas,'next_p':next_p,'pagina':pagina})

def mphoto(request,photo,pagina):
	n_p = int(pagina)
	this_photo = TimesMedia.objects.get(pk=int(photo))

	str_embeding = "<img style='width:100%; border:1px solid grey; float:left; margin-bottom:1em;' src='{}'>".format(this_photo.imagen.url)

	str_embeding2 = "<img style='width:40%; margin-right:1em; margin-top:1em; margin-bottom:1em; border:1px solid grey; float:left' src='{}'>".format(this_photo.imagen.url)

	return render(request,'photo.html',{'this_photo':this_photo,'pagina':n_p,'strI':str_embeding, 'strI2':str_embeding2})

def addbooktags(request):
	this_libro = Book.objects.get(pk=int(request.POST.get("book")))
	tags = request.POST.get("tags","").split(",")

	for t in tags:
		bt = BookTag.objects.create(libro=this_libro,tag=t)
		bt.save()

	return redirect('/book/{}'.format(request.POST.get("book")))

def viewbooktag(request,this_tag):

	books = BookTag.objects.filter(tag=this_tag).order_by('libro__pub_year')

	now_tag = this_tag

	return render(request,'view-booktag.html',{'books':books,'now_tag':now_tag})

def addbookquote(request):
	this_libro = Book.objects.get(pk=int(request.POST.get("book_id")))
	this_quote = request.POST.get("cita")

	newBQ = BookQuote.objects.create(libro = this_libro, quote = this_quote)
	newBQ.save()

	return redirect('/book/{}'.format(this_libro.id))

def addmovielist(request):
	if request.method == 'POST':
		list_name = request.POST.get("title","")
		ml = MovieList.objects.create(titulo=list_name)
		return redirect('/movielist/{}'.format(ml.id))
	return render(request,'add-movie-list.html',{})


def addmovietolist(request,movie_id,movie_list):
	this_movie = Movie.objects.get(pk=int(movie_id))
	this_lista = MovieList.objects.get(pk=int(movie_list))

	newLine = MoveListItem.objects.create(lista = this_lista, film = this_movie)
	newLine.save()

	return redirect('/movielist/{}'.format(this_lista.id))

def movielists(request):
	listas = MovieList.objects.all().order_by('titulo')
	return render(request,'movielists.html',{'listas':listas})

def movielist(request,id_lista):
	this_lista = MovieList.objects.get(pk=int(id_lista))
	films = MoveListItem.objects.filter(lista=this_lista)
	movie_matches = None

	if request.method == 'POST':
		keyword = request.POST.get("keyword","")
		if len(keyword)>2:
			movie_matches = Movie.objects.filter(Q(title__contains=keyword) | Q(info__contains=keyword))

	return render(request,'movielist.html',{'films':films,'this_lista':this_lista,'movie_s':movie_matches})

def addwikiphoto(request):
	bid = request.POST.get("wiki_id")
	this_wiki = Wiki.objects.get(pk=int(bid))
	ix = request.FILES.get("imagen")
	img_type = int(request.POST.get("img_type"))

	newM = WikiPhoto.objects.create(wiki=this_wiki,imgtype=img_type,imagen=ix)
	newM.save()

	conteo_photos = PageRels.objects.filter(child=this_wiki).count()

	if conteo_photos == 0:
	    return redirect('/wiki/{}'.format(this_wiki.id))
	else:
	    pagina = PageRels.objects.filter(child=this_wiki).latest('id')
	    return redirect('/itemcol/{}/{}'.format(this_wiki.id,pagina.page.id))

def cuadernos(request):
	notebooks = Cuaderno.objects.all().order_by('titulo')
	return render(request,'cuadernos.html',{'notebooks':notebooks})

def addcuaderno(request):
	this_titulo = request.POST.get("titulo")
	newN = Cuaderno.objects.create(titulo = this_titulo)
	newN.save()


	return redirect('/cuadernos')

def cuaderno(request,c):
	this_notebook = Cuaderno.objects.get(pk=int(c))
	this_apuntes = Apunte.objects.filter(cuaderno = this_notebook).order_by('id')

	n_apuntes = Apunte.objects.filter(cuaderno = this_notebook).exclude(subtitulo__isnull=True).count()

	if n_apuntes <= 2:
		str_temp = 'base_forms.html'
	else:
		str_temp = 'base_listing.html'

	return render(request,'cuaderno.html',{'this_notebook':this_notebook,'this_apuntes':this_apuntes, 'n_apuntes':n_apuntes,  'str_temp':str_temp})


def addapunte(request):
	cuaderno = Cuaderno.objects.get(pk=int(request.POST.get("cid")))
	subtitulo = request.POST.get("subtitulo")
	contenido = request.POST.get("entrada")

	if len(subtitulo)>2:
		newApunte = Apunte.objects.create(cuaderno=cuaderno,contenido=contenido,subtitulo=subtitulo)
	else:
		newApunte = Apunte.objects.create(cuaderno=cuaderno,contenido=contenido)


	return redirect('/cuaderno/{}'.format(cuaderno.id))

def editapunte(request,aid):
	apunte = Apunte.objects.get(pk=int(aid))
	n_con = ApunteConsumo.objects.filter(apunte=apunte).count()

	this_consumo = None

	if n_con > 0:
		this_consumo = ApunteConsumo.objects.filter(apunte=apunte).order_by('id')
	list_mt = ['manga','episode','light-novel']
	list_units = ['paginas','minutos','capitulos']
	if request.method == 'POST':
		apunte = Apunte.objects.get(pk=int(request.POST.get("aid")))
		subtitulo = request.POST.get("subtitulo")
		contenido = request.POST.get("entrada")

		Apunte.objects.filter(id=apunte.id).update(contenido=contenido,subtitulo=subtitulo)
		return redirect('/cuaderno/{}'.format(apunte.cuaderno.id))
	else:
		return render(request,'edit-apunte.html',{'apunte':apunte,'list_mt':list_mt,'list_units':list_units, 'n_con':n_con,'this_consumo':this_consumo})

def nbtokindle(request, c):
	this_notebook = Cuaderno.objects.get(pk=int(c))
	this_apuntes = Apunte.objects.filter(cuaderno = this_notebook).order_by('id')

	return render(request,'printed_notebook.html',{'this_notebook':this_notebook,'this_apuntes':this_apuntes})

def addPartido(request,lid):
    liga = Liga.objects.get(pk=lid)
    equipos = LigaTeams.objects.filter(ligaRel__id=liga.id,flagActivo=True).order_by('equipoRel__nombre')
    last_matches = Partido.objects.filter(liga=liga).order_by('-id')[0:10]
    ligas = Liga.objects.all().order_by('-id')

    if request.method == 'POST':
        id_el = request.POST.get("local")
        id_ev = request.POST.get("visit")
        fecha = request.POST.get("fecha")
        fase = request.POST.get("fase")

        el = Equipo.objects.get(pk=int(id_el))
        ev = Equipo.objects.get(pk=int(id_ev))

        newM = Partido.objects.create(fecha=fecha,liga=liga,local=el,visita=ev,terminado=False,fase=fase)
        newM.save()
        last_mr = Partido.objects.latest('id')

        return render(request,'add-partido.html',{'liga':liga,'equipos':equipos,'last_m':last_mr,'lm':last_matches,'ligas':ligas})
    else:
        last_mr = Partido.objects.latest('id')
        return render(request,'add-partido.html',{'liga':liga,'equipos':equipos,'last_m':last_mr,'lm':last_matches,'ligas':ligas})

def addSoccerTeam(request):
    if request.method == 'POST':
        newT = Equipo.objects.create(nombre=request.POST.get("nombre"),pais=request.POST.get("pais"),logo=request.FILES.get("logo"))
        newT.save()

        return render(request,'add-soccer-team.html',{})
    else:
        return render(request,'add-soccer-team.html',{})


def sccteam(request,t):
    import datetime
    thisEquipo = Equipo.objects.get(pk=t)
    ligas = Liga.objects.all().order_by('-id')
    matches = Partido.objects.filter(Q(visita__id=int(t)) | Q(local__id=int(t))).exclude(terminado=False).order_by('-fecha')[0:10]
    contratos = Contrato.objects.filter(equ__id=int(t),active=True).order_by('number')
    fec_hoy = datetime.date.today()
    thisY = fec_hoy.strftime("%Y")
    antY = int(thisY)-1
    goal_table = Goles.objects.raw("select 1 as id, jugador,jugador_id, sum(case when anho='{}' then goles else 0 end) goles, sum(case when anho='{}' then goles else 0 end) goles_ant from futbol_scoreres where equipo_id={} group by jugador,jugador_id order by sum(case when anho='{}' then goles else 0 end) desc".format(int(thisY),antY,thisEquipo.id,int(thisY)))
    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]
    listado2 = []
    for l in listado:
        conteo = Contrato.objects.filter(equ__id=int(t),active=True,position=l).count()
        if conteo > 0:
            listado2.append(l)
    return render(request,'sccteam.html',{'matches':matches,'ligas':ligas,'thisEquipo':thisEquipo,'contratos':contratos,'listado':listado2,'posiciones':listado,'goal_table':goal_table,'thisY':thisY})


def viewMatch(request,pid):

    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]

    ligas = Liga.objects.all().order_by('-id')



    partido = Partido.objects.get(pk=pid)
    comentarios = PartidoComment.objects.filter(comm_partido__id=partido.id).order_by('minuto','id')
    lig = partido.liga.id
    matches = Partido.objects.filter(terminado=False,liga__id=lig,fecha__gte=partido.fecha).exclude(id=pid).order_by('fecha','id')[0:20]

    jugadores_local = Contrato.objects.filter(equ__id=partido.local.id,active=True).order_by('jug__nombre')
    jugadores_visit = Contrato.objects.filter(equ__id=partido.visita.id,active=True).order_by('jug__nombre')

    lgoles = Goles.objects.filter(partido__id=pid,asignado=1,penales=False).order_by('minuto','adicional')
    vgoles = Goles.objects.filter(partido__id=pid,asignado=2,penales=False).order_by('minuto','adicional')

    lpens = Penales.objects.filter(partido__id=pid,asignado=1).order_by('id')
    vpens = Penales.objects.filter(partido__id=pid,asignado=2).order_by('id')

    if request.method == 'POST':

        cid = request.POST.get("contrato")
        minuto = request.POST.get("minuto")
        adicional = request.POST.get("adicional")
        ct = Contrato.objects.get(pk=cid)
        asig = request.POST.get("asignado")

        if request.POST.get("penal","0")=="0":
            pn = False
        else:
            pn = True

        if request.POST.get("autogol","0")=="0":
            og = False
        else:
            if asig=="1":
                asig="2"
            else:
                asig="1"

            og = True

        newG = Goles.objects.create(partido=partido,asignado=asig,contrato=ct,minuto=minuto,adicional=adicional,penal=pn,penales=False,og=og)
        if og == False:
        	if pn == False:
        		texto = f"&#9917; ({newG.contrato.equ.nombre}) Gol de {newG.contrato.jug.nombre}"
        	else:
        		texto = f"&#9917; ({newG.contrato.equ.nombre}) Penal {newG.contrato.jug.nombre} "
        elif og ==True:
        	texto = f"&#9888;&#9917;  ({newG.contrato.equ.nombre}) Autogol {newG.contrato.jug.nombre}"

        newC = PartidoComment.objects.create(comm_partido=partido,comm=texto,minuto = newG.minuto,tipo=0)
        newC.save()
        newG.save()

        return render(request,'partido.html',{'matches':matches,'partido':partido,'jlocal':jugadores_local,'jvisit':jugadores_visit,'lgoles':lgoles,'vgoles':vgoles,'lpens':lpens,'vpens':vpens,'ligas':ligas,'listado':listado,'comentarios':comentarios})

    else:
        return render(request,'partido.html',{'matches':matches,'partido':partido,'jlocal':jugadores_local,'jvisit':jugadores_visit,'lgoles':lgoles,'vgoles':vgoles,'lpens':lpens,'vpens':vpens,'ligas':ligas,'listado':listado,'comentarios':comentarios})

def closeMatch(request,pid):
    partido = Partido.objects.get(pk=pid)
    partido.terminado = True
    partido.save()
    return redirect("/viewmatch/{}".format(pid))


def viewLiga(request,sta,lig):
    match_stat = sta

    ligas = Liga.objects.all().order_by('-id')
    liga = Liga.objects.get(pk=lig)

    if sta == "1":
        titulo = "Coming Fixtures"
        ot = "Finished"
        iot = "/viewliga/2/"+str(lig)
        matches = Partido.objects.filter(terminado=False,liga__id=int(lig)).order_by('fecha')[0:30]
        nmatches = Partido.objects.filter(terminado=False,liga__id=int(lig)).order_by('fecha').count()
    elif sta=="2":
        titulo = "Finished Fixtures"
        ot = "Coming"
        iot = "/viewliga/1/"+str(lig)
        matches = Partido.objects.filter(terminado=True,liga__id=int(lig)).order_by('-fecha')

    if sta=="1" and nmatches==0:
        return redirect("/viewliga/2/{}".format(liga.id))
    else:
        return render(request,'view-liga.html',{'matches':matches,'ligas':ligas,'ptitulo':titulo,'ot':ot,'iot':iot,'lig':liga})

def editPartido(request,pid):
    thisMatch = Partido.objects.get(pk=int(pid))
    equipos = LigaTeams.objects.filter(ligaRel__id=thisMatch.liga.id,flagActivo=True).order_by('equipoRel__nombre')
    thisliga = Liga.objects.get(pk=thisMatch.liga.id)

    if request.method == 'POST':
        id_el = request.POST.get("local")
        id_ev = request.POST.get("visit")
        fecha = request.POST.get("fecha")
        fase = request.POST.get("fase")

        el = Equipo.objects.get(pk=int(id_el))
        ev = Equipo.objects.get(pk=int(id_ev))

        Partido.objects.filter(id=thisMatch.id).update(fecha=fecha,liga=thisliga,local=el,visita=ev,terminado=False,fase=fase)
        return redirect('/viewmatch/{}'.format(thisMatch.id))
    else:
        return render(request,'edit-partido.html',{'thisMatch':thisMatch,'equipos':equipos})



def addNewPlayerGoal(request,t,m,a):
    equipo = Equipo.objects.get(pk=int(t))
    partido = Partido.objects.get(pk=int(m))
    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]
    asig = a
    if request.method=='POST':

        conteo_prev = Jugador.objects.filter(nombre=request.POST.get("nombre")).count()
        if conteo_prev == 0:

            nombre = request.POST.get("nombre")
            pais = request.POST.get("pais")
            position = request.POST.get("position")
            number = request.POST.get("number")

            newJugador = Jugador.objects.create(nombre=nombre,pais=pais, biographics="This section nees to be expanded.")
            newJugador.save()

            newC = Contrato.objects.create(jug=newJugador,equ=equipo,active=True, position=position,number = number)
            newC.save()

            minuto = request.POST.get("minuto")
            adicional = request.POST.get("adicional")

            if request.POST.get("penal","0")=="0":
                pn = False
            else:
                pn = True

            if request.POST.get("autogol","0")=="0":
                og = False
            else:
                if asig=="1":
                    asig="2"
                else:
                    asig="1"

                og = True

            newG = Goles.objects.create(partido=partido,asignado=asig,contrato=newC,minuto=minuto,adicional=adicional,penal=pn,penales=False,og=og)
            if og == False:
                if pn == False:
                    texto = f"&#9917; ({newG.contrato.equ.nombre}) Gol de {newG.contrato.jug.nombre}"
                else:
                        texto = f"&#9917; ({newG.contrato.equ.nombre}) Penal {newG.contrato.jug.nombre} "
            elif og ==True:
                texto = f"&#9888;&#9917; ({newG.contrato.equ.nombre}) Autogol {newG.contrato.jug.nombre} "
            newC = PartidoComment.objects.create(comm_partido=partido,comm=texto,minuto = newG.minuto,tipo=0)
            newC.save()
            newG.save()
            return(redirect('/viewmatch/{}/'.format(partido.id)))
        else:
            return redirect('/jugadores/')
    else:
        return render(request,'add-new-player-goal.html',{'equipo':equipo,'partido':partido,'listado':listado})

def regPenRound(request,pid):
    partido = Partido.objects.get(pk=pid)

    asignado = request.POST.get("asignado")
    contrato_id = request.POST.get("contrato")
    contrato = Contrato.objects.get(pk=contrato_id)

    if request.POST.get("anotado","0")=="0":
        anotado = False
    else:
        anotado = True

    newP = Penales.objects.create(partido=partido,asignado=asignado,contrato=contrato,anotado=anotado)
    newP.save()

    if anotado == True:
        newG = Goles.objects.create(partido=partido,asignado=asignado,contrato=contrato,minuto=121,adicional=0,penal=False,penales=True,og=False)
        newG.save()

    return redirect('/viewmatch/{}'.format(pid))


def addPlayerv2(request):
    pnombre = request.POST.get("nombre","")
    ppais = request.POST.get("pais","")
    partido = request.POST.get("partido","0")

    prev_conteo = Jugador.objects.filter(nombre=pnombre).count()

    if prev_conteo == 0 and int(partido) > 0:
        newJ = Jugador.objects.create(nombre=pnombre,pais=ppais)
        newJ.save()
        equ_id = request.POST.get("equipo","0")
        equipon = Equipo.objects.get(pk=int(equ_id))
        position = request.POST.get("position")
        number = request.POST.get("number")
        newC = Contrato.objects.create(jug=newJ,equ=equipon,position=position,number = number)
        newC.save()
        return redirect('/viewmatch/{}'.format(int(partido)))
    elif prev_conteo == 0 and int(partido) == 0:
        newJ = Jugador.objects.create(nombre=pnombre,pais=ppais)
        newJ.save()
        equ_id = request.POST.get("equipo","0")
        equipon = Equipo.objects.get(pk=int(equ_id))
        position = request.POST.get("position")
        number = request.POST.get("number")
        newC = Contrato.objects.create(jug=newJ,equ=equipon,position=position,number = number)
        newC.save()
        return redirect('/team/{}'.format(int(equ_id)))
    else:
        return redirect('/jugadores/')

def addpartidocomm(request):
    partido = request.POST.get("partido","0")
    comm = request.POST.get("comm","")
    minuto = request.POST.get("minuto","0")
    obj_partido = Partido.objects.get(pk=int(partido))

    newC = PartidoComment.objects.create(comm_partido=obj_partido,comm=comm,minuto=int(minuto),tipo=1)
    #1: Comentarios
    #2: Goal
    newC.save()

    return redirect('/viewmatch/{}'.format(partido))

def addsecleg(request):

    match = request.POST.get("partido","")
    fecha = request.POST.get("fecha","")

    old_match = Partido.objects.get(pk=int(match))

    newP = Partido.objects.create(fecha=fecha,liga=old_match.liga,local=old_match.visita,visita=old_match.local,terminado=False,fase=old_match.fase)
    newP.save()
    return redirect('/viewmatch/{}'.format(newP.id))

def viewsquad(request,par_id,equ_id):
    check_squad = matchSquad.objects.filter(equipo__id=int(equ_id),partido__id=int(par_id)).count()

    this_equipo = Equipo.objects.get(pk=int(equ_id))
    this_partido = Partido.objects.get(pk=int(par_id))

    if check_squad == 0:
        new_S = matchSquad.objects.create(equipo=this_equipo,partido=this_partido)
        new_S.save()
        sc_id = new_S.id
        plantilla = squadPlayers.objects.filter(squad__id=new_S.id)
    else:
        this_squad =  matchSquad.objects.filter(equipo__id=int(equ_id),partido__id=int(par_id)).latest('id')
        sc_id = this_squad.id
        plantilla = squadPlayers.objects.filter(squad__id=this_squad.id).order_by('tipo')

    contratos = Contrato.objects.filter(equ__id=int(equ_id)).order_by('jug__nombre')

    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]

    porteros = []
    defensas = []
    medicampos = []
    delanteros = []
    not_spec = []

    for p in plantilla:
        if p.jugador.position == "Goal Keeper":
            porteros.append(p)
        elif p.jugador.position == "Defender":
            defensas.append(p)
        elif p.jugador.position == "Midfielder":
            medicampos.append(p)
        elif p.jugador.position == "Forward":
            delanteros.append(p)
        elif p.jugador.position == "Not Specified":
            not_spec.append(p)


    return render(request,'squad.html',{'plantilla':plantilla,
                                        'contratos':contratos,
                                        'partido':this_partido,
                                        'equipo':this_equipo,
                                        'porteros':porteros,
                                        'defensas':defensas,
                                        'medicampos':medicampos,
                                        'delanteros':delanteros,
                                        'not_spec':not_spec,
                                        'sc_id':sc_id})

def viewMatches(request,sta):
    match_stat = sta

    ligas = Liga.objects.all().order_by('-id')
    equipos = Equipo.objects.all().order_by('nombre')

    if sta == "1":
        titulo = "Coming Fixtures"
        ot = "Finished"
        iot = "/viewmatches/2"
        matches = Partido.objects.filter(terminado=False,fecha__gte='2022-12-25').order_by('fecha')[0:50]
    elif sta=="2":
        titulo = "Finished Fixtures"
        ot = "Coming"
        iot = "/viewmatches/1"
        matches = Partido.objects.filter(terminado=True).order_by('-fecha')[0:50]

    return render(request,'view-matches.html',{'matches':matches,'ligas':ligas,'ptitulo':titulo,'ot':ot,'iot':iot,'equipos':equipos})

def jugadores(request):

    jugadores = Jugador.objects.all().order_by('-id')

    if request.method == 'POST':
        pnombre = request.POST.get("nombre","")
        ppais = request.POST.get("pais","")

        newJ = Jugador.objects.create(nombre=pnombre,pais=ppais, biographics = "This section needs to be expanded.")
        newJ.save()

        return redirect('/jugador/{}'.format(newJ.id))
    else:
        return render(request,'players.html',{'jugadores':jugadores})


def viewTable(request,liga):
    tp = Liga.objects.raw("select 1 as id, * from position_tables where ligaid={} order by ptos desc, dg desc".format(liga))
    tp2 = Liga.objects.raw("select 1 as id, * from fase_grups where ligaid={} order by fase, ptos desc, dg desc".format(liga))
    tg = Goles.objects.raw("select 1 as id, * from liga_goleadores where liga={} order by goles desc, penales desc".format(liga))

    matches = Partido.objects.filter(terminado=True,liga__id=int(liga)).exclude(fase__contains='Group').order_by('-fecha')

    liga = Liga.objects.get(pk=int(liga))
    ligas = Liga.objects.all().order_by('-id')
    if ('Champions' in liga.nombre) or ('UEFA Euro' in liga.nombre) or ('Copa America' in liga.nombre):
        tipo = 'grupos'
    else:
        tipo = 'liga'


    return render(request,'viewtable.html',{'tp':tp,'thisLiga':liga,'ligas':ligas,'tablagoles':tg, 'tp2':tp2,'tipo':tipo,'partidos':matches})

def unirligateams(request,liga):
    equipos = Equipo.objects.all().order_by('nombre')
    this_liga = Liga.objects.get(pk=int(liga))
    if request.method == 'POST':
        for e in equipos:
            if e.nombre in request.POST:
                equ = Equipo.objects.get(pk=e.id)
                nL = LigaTeams.objects.create(ligaRel=this_liga, equipoRel = equ, flagActivo = True)
        return redirect('/viewliga/1/{}'.format(this_liga.id))
    else:
        return render(request,'select_teams.html',{'equipos':equipos,'liga':this_liga})

def editComm(request,commid):
    comentario = PartidoComment.objects.get(pk=int(commid))
    if request.method == 'POST':
        PartidoComment.objects.filter(id=int(commid)).update(comm=request.POST.get("comm"))
        return redirect('/viewmatch/{}'.format(comentario.comm_partido.id))
    else:
        return render(request,'edit-comm.html',{'comentario':comentario})

def jugador(request,jid):
    jug = Jugador.objects.get(pk=int(jid))
    contratos = Contrato.objects.filter(jug__id=int(jid)).order_by('-id')
    equipos = Equipo.objects.all().order_by('nombre')
    goal_table = Goles.objects.raw("select 1 as id, liga,liga_id,equipo, sum(goles) goles, sum(cast(penales as int)) penales, sum(goles_contra) goles_contra from futbol_scoreres where jugador_id={} group by liga,liga_id,equipo order by liga_id desc".format(jug.id))
    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]

    if request.method == 'POST' and request.POST.get("team","0") != "0":
        equ_id = request.POST.get("team","0")

        equipon = Equipo.objects.get(pk=int(equ_id))

        position = request.POST.get("position")
        number = request.POST.get("number")


        newC = Contrato.objects.create(jug=jug,equ=equipon,position=position,number = number)
        newC.save()

        return render(request,'player.html',{'jug':jug,'contratos':contratos,'equipos':equipos})
    elif request.method == 'POST' and request.POST.get("team","0") == "0":
        pnombre = request.POST.get("nombre","")
        ppais = request.POST.get("pais","")

        newJ = Jugador.objects.create(nombre=pnombre,pais=ppais)
        newJ.save()

        equ_id = request.POST.get("team2","0")

        equipon = Equipo.objects.get(pk=int(equ_id))

        position = request.POST.get("position")
        number = request.POST.get("number")

        newC = Contrato.objects.create(jug=newJ,equ=equipon,position=position,number = number)
        newC.save()

        return redirect('/jugador/{}'.format(newJ.id))
    else:
        return render(request,'player.html',{'jug':jug,'contratos':contratos,'equipos':equipos,'listado':listado,'goal_table':goal_table})


def editContrato(request,c):
    thisC = Contrato.objects.get(pk=int(c))
    thisP = Jugador.objects.get(pk=thisC.jug.id)
    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]
    ngoles = Goles.objects.filter(contrato__id=thisC.id).count()

    og=0
    classGoles = None
    pn=0
    reg = 0

    if ngoles > 0:
        og = 0
        pn = 0
        reg = 0
        goles = Goles.objects.filter(contrato__id=thisC.id)
        classGoles = Goles.objects.filter(contrato__id=thisC.id,og=False).values('partido__liga__nombre').annotate(qgoles=Count('id'),maxfecha=Max('partido__fecha')).order_by('-maxfecha')
        for g in goles:
            if g.og == True:
                og = og + 1
            elif g.penal == True or g.penales == True:
                pn = pn + 1
            elif g.og == False and  g.penal== False and g.penales == False:
                reg = reg + 1



    if request.method == 'POST':
        Jugador.objects.filter(id=thisP.id).update(nombre=request.POST.get("nombre"),pais = request.POST.get("pais"))

        if request.POST.get("active"):
            checkb = True
        else:
            checkb = False


        Contrato.objects.filter(id=thisC.id).update(position= request.POST.get("position"),number= request.POST.get("number"),active=checkb)
        return redirect('/team/{}'.format(thisC.equ.id))
    else:
        return render(request,'edit-contrato.html',{'thisC':thisC,'listado':listado,'ngoles':(ngoles-og),'classGoles':classGoles,'pn':pn,'og':og,'reg':reg})

def updateSquad(request):

    plantilla = matchSquad.objects.get(pk=int(request.POST.get("squad_id")))
    contrato = Contrato.objects.get(pk=int(request.POST.get("contrato")))
    tipo = request.POST.get("tipo")

    newLP = squadPlayers.objects.create(squad=plantilla,jugador=contrato,tipo=tipo)


    return redirect('/squad/{}/{}'.format(plantilla.partido.id,plantilla.equipo.id))

def editBiographics(request,c):
    thisC = Contrato.objects.get(pk=int(c))
    thisP = Jugador.objects.get(pk=thisC.jug.id)
    listado = ["Goal Keeper","Defender","Midfielder","Forward","Not Specified"]

    if request.method == 'POST':
        Jugador.objects.filter(id=thisP.id).update(biographics=request.POST.get("biographics"))
        return redirect('/view-contrato/{}'.format(thisC.id))
    else:
        return render(request,'edit-pbio.html',{'thisC':thisC,'listado':listado})


def finance(request):
    cuentas = Cuenta.objects.all().order_by('tipo','id')
    tiposT = TrxTyp.objects.all().order_by('desc')

    transacciones = Trx.objects.all().order_by('-fecha','-id')
    saldos = Trx.objects.raw("select * from c_balance order by t_c, cid")

    cortes = Trx.objects.values('fecha__year','fecha__month').annotate(qitems = Count('id')).order_by('-fecha__year','-fecha__month')

    acc_saldo = 0
    for s in saldos:
        acc_saldo = acc_saldo + s.balance_final

    return render(request,'finance2.html',{'cuentas':cuentas,'tiposT':tiposT,'trxs':transacciones,'saldos':saldos,'fbal':acc_saldo,'cortes':cortes})


def saveTrx(request):

    if request.method == "POST":
        ttrx = request.POST.get("tipotrx")
        cuenta = request.POST.get("cuenta")
        monto = request.POST.get("monto")
        fecha = request.POST.get("fecha")
        desc = request.POST.get("detalle")

        c = Cuenta.objects.get(pk=cuenta)
        t = TrxTyp.objects.get(pk=ttrx)

        nt = Trx.objects.create(fecha = fecha, debito = c, credito=t, monto = monto,desc=desc)


        nt.save()

        return redirect('/finance/')
    else:
        return redirect('/finance/')

def savePmt(request):

    if request.method == "POST":
        origen = request.POST.get("origen")
        destino = request.POST.get("destino")
        monto = request.POST.get("monto")
        fecha = request.POST.get("fecha")
        desc = request.POST.get("detalle")

        o = Cuenta.objects.get(pk=origen)
        d = Cuenta.objects.get(pk=destino)

        i = TrxTyp.objects.get(pk=1)
        t = TrxTyp.objects.get(pk=2)

        nt = Trx.objects.create(fecha = fecha, debito = o, credito=t, monto = monto,desc=desc)
        nt.save()

        nt2 = Trx.objects.create(fecha = fecha, debito = d, credito=i, monto = monto,desc=desc)
        nt2.save()

        return redirect('/finance/')
    else:
        return redirect('/finance/')


def addBudgetReg(request):
    input_anho = int(request.POST.get('y'))
    input_mes = int(request.POST.get('m'))
    input_mbudget = float(request.POST.get('mbudget'))
    input_cuenta = TrxTyp.objects.get(pk=int(request.POST.get("cuenta")))
    Budget.objects.create(cuenta=input_cuenta,anho=input_anho,mes=input_mes,mbudget=input_mbudget)
    return redirect('/view-month/{}/{}'.format(input_anho,input_mes))

def finance2(request):
    cuentas = Cuenta.objects.all().order_by('tipo','id')
    tiposT = TrxTyp.objects.all().order_by('desc')

    transacciones = Trx.objects.all().order_by('-fecha','-id')
    saldos = Trx.objects.raw("select * from c_balance order by t_c, cid")

    cortes = Trx.objects.values('fecha__year','fecha__month').annotate(qitems = Count('id')).order_by('-fecha__year','-fecha__month')

    acc_saldo = 0
    for s in saldos:
        acc_saldo = acc_saldo + s.balance_final

    return render(request,'finance.html',{'cuentas':cuentas,'tiposT':tiposT,'trxs':transacciones,'saldos':saldos,'fbal':acc_saldo,'cortes':cortes})

def viewmonth(request,y,m):
    trx = Trx.objects.filter(fecha__year=y,fecha__month=m, credito__codigo=1).order_by('-fecha','-id')
    categories = TrxTyp.objects.all().order_by('desc')
    budexec = Trx.objects.raw("""select
                                    *,
                                    case when mbudget==0 then actual else actual-mbudget end bvar,
                                    case when mbudget==0 then 100 else 100*(actual-mbudget)/mbudget end pvar

                            from
                                fin_control
                            where
                                mes={} and anho={} and (mbudget>0 or actual>0)
                            order by mbudget desc""".format(m,y))
    tot_act = 0
    tot_bud = 0
    for t in budexec:
        tot_act = tot_act+t.actual
        tot_bud = tot_bud+t.mbudget

    if tot_bud == 0:
        perf = 0
    else:
        perf = 100.0*tot_act/tot_bud

    if perf <= 95.0:
        colp = "green"
    elif perf <= 101.5:
        colp = "orange"
    else:
        colp = "red"

    cortes = Trx.objects.values('fecha__year','fecha__month').annotate(qitems = Count('id')).order_by('-fecha__year','-fecha__month')

    return render(request,'view-month.html',{'trxs':trx,'be':budexec,'anho':y,'mes':m,'actual':tot_act, 'budget':tot_bud,'perf':perf,'colp':colp,'cortes':cortes,'categ':categories})

def addapucon(request):
	apunte = Apunte.objects.get(pk=request.POST.get("apu_id",""))

	media_type = request.POST.get("media_type","")
	unidades = request.POST.get("unidades","")
	cantidad = request.POST.get("cantidad","")
	fecha_inicio = request.POST.get("fecha_inicio","")
	fecha_fin = request.POST.get("fecha_fin","")

	newAC = ApunteConsumo.objects.create(apunte=apunte,
		fecha_inicio=fecha_inicio,
		fecha_fin=fecha_fin,
		media_type = media_type,
		unidades=unidades,
		cantidad=cantidad)

	newAC.save()

	return redirect('/cuaderno/{}#{}'.format(apunte.cuaderno.id,apunte.id))


def addcoleccion(request):
	if request.method == 'POST':
		this_titulo = request.POST.get("title")
		this_desc = request.POST.get("info")

		newC = Pagina.objects.create(titulo = this_titulo, info=this_desc)
		newC.save()

		return redirect('/page/{}'.format(newC.id))

	return render(request,'add-coleccion.html',{})

def addbooklist(request):
	if request.method == 'POST':
		this_titulo = request.POST.get("title")
		this_desc = request.POST.get("info")
		this_tipo = request.POST.get("tipo")

		newC = BookList.objects.create(listname = this_titulo, listinfo=this_desc,tipo = this_tipo)
		newC.save()

		return redirect('/booklist/{}'.format(newC.id))

	return render(request,'add-book-coleccion.html',{})


def addbooktolist2(request,book,lista):
	this_libro = DiraBook.objects.get(pk=int(book))
	this_lista = DiraSeries.objects.get(pk=int(lista))

	newR = DiraBookSeries.objects.create(volume=this_libro,series=this_lista)
	newR.save()

	return redirect('/dira-book-list/{}'.format(this_lista.id))

def addbookentity(request,book_id):
	this_book = Book.objects.get(pk=int(book_id))
	wtypes = ["character","place","event","object","battle"]

	if request.method == 'POST':
		newBE = BookEntity.objects.create(libro=this_book,etype=request.POST.get("etype"),nombre=request.POST.get("nombre"),info=request.POST.get("info"), importancia=int(request.POST.get("importancia")))
		newBE.save()
		return redirect('/book/{}'.format(this_book.id))

	return render(request,'add-book-entity.html',{'this_book':this_book,'wtypes':wtypes})

def viewentity(request,ent_id):
	this_entity = BookEntity.objects.get(pk=int(ent_id))

	this_book_series = RelBookList.objects.filter(bbook=this_entity.libro,blist__tipo__in=[1,2,3])

	get_books = None

	series_libros = [this_entity.libro.id]

	tb_series = []
	if this_book_series:
		for bs in this_book_series:
			tb_series.append(bs.blist.id)
		if len(tb_series)>0:
			get_books =  RelBookList.objects.filter(blist__id__in=tb_series).exclude(bbook__id=this_entity.libro.id).values_list('bbook__id').distinct()
			for i in get_books:
				series_libros.append(i[0])

	entidades = BookEntity.objects.filter(libro__id__in=series_libros).order_by('-importancia','id')

	otros_libros = Book.objects.filter(id__in=series_libros).order_by('id')

	ent_groups = BookEntityGroup.objects.all().order_by('groupname')

	if request.method == 'POST':
		this_entity.info = request.POST.get("info")
		this_entity.importancia = int(request.POST.get("importancia"))
		this_entity.save()

	return render(request,'view-single-entity.html',{'this_entity':this_entity,'entidades':entidades,'otros_libros':otros_libros,'ent_groups':ent_groups})


def addwikibook(request,book_id):
	this_book = Book.objects.get(pk=int(book_id))

	return render(request,'add-wiki-book.html',{'this_book':this_book})


def editbookinfo(request,book_id):
	this_book = Book.objects.get(pk=int(book_id))

	if request.method == 'POST':
		this_book.title = request.POST.get("title")
		this_book.info = request.POST.get("info")
		this_book.save()

		return redirect(f'/book/{this_book.id}')
	else:
		return render(request,'edit-book-info.html',{'this_book':this_book})

def createEntityGroup(request):
	nombre = request.POST.get("nombre")
	info = request.POST.get("info")

	newEBG = BookEntityGroup.objects.create(groupname=nombre, groupinfo=info)
	newEBG.save()

	return redirect('/viewentity/{}'.format(request.POST.get("entity_id")))

def addEntityToGroup(request):
	grupo = int(request.POST.get("cat_id"))
	entidad = (request.POST.get("entity_id"))

	this_group = BookEntityGroup.objects.get(pk=grupo)
	this_entidad = BookEntity.objects.get(pk=entidad)

	newGG = BookGroupEntity.objects.create(entity = this_entidad, grupo = this_group)
	newGG.save()


	return redirect('/viewentity/{}'.format(request.POST.get("entity_id")))


def viewEntityGroup(request,grupo_id):

	this_grupo = BookEntityGroup.objects.get(pk=int(grupo_id))
	this_entidades = BookGroupEntity.objects.filter(grupo=this_grupo).order_by('-entity__importancia','entity__id')
	all_groups = BookEntityGroup.objects.all().order_by('groupname')

	return render(request,'view-entity-group.html',{'this_grupo':this_grupo,'this_entidades':this_entidades,'all_grupos':all_groups})


def addConsumoNote(request,note_id):
	this_apunte = Apunte.objects.get(pk=int(note_id))
	list_mt = ['manga','episode','light-novel']
	list_units = ['paginas','minutos','capitulos']
	return render(request,'consumo-apunte.html',{'this_apunte':this_apunte,'list_mt':list_mt,'list_units':list_units})


def addbookshort(request,author):
	personas = Wiki.objects.filter(wtype__category='author').order_by('title')
	booktypes = WikiType.objects.filter(id__in=[9,10,11,12]).order_by('id')
	listas = BookList.objects.all().order_by('listname')
	author = Wiki.objects.get(pk=int(author))

	if request.method == 'POST':
		btype = WikiType.objects.get(pk=int(request.POST.get("btype")))
		btitle = request.POST.get("title")
		pubyear = int(request.POST.get("pub_year"))

		if request.POST.get("info","") == "":
		    binfo = f"No review or synopsis has been written for this title. Please feel free to write one."
		else:
		    binfo = request.POST.get("info","")

		origlan = request.POST.get("orig_lan")

		newB = Book.objects.create(title = btitle,orig_lan = origlan,info=binfo, pub_year=pubyear, wtype=btype)
		newB.save()
		if btype.id == 9:
		    credtype = CreditType.objects.get(pk=1)
		elif btype.id == 10:
		    credtype = CreditType.objects.get(pk=7)
		elif btype.id == 11:
		    credtype = CreditType.objects.get(pk=5)
		elif btype.id == 12:
		    credtype = CreditType.objects.get(pk=6)

		newC = Credito.objects.create(ctype=credtype, persona = author, media_type=1, media_id=newB.id)






		return redirect('/wiki/{}'.format(author.id))
	else:
		return render(request,'add-book-short.html',{'author':author,'booktypes':booktypes,'listas':listas})



def diraAddPersona(request):

	ocupaciones = ["author","light-novel author","illustrator","mangaka","translator","actor","director"]

	if request.method == 'POST':
		nombre = request.POST.get("nombre","")
		info = request.POST.get("info","")
		ocupacion = request.POST.get("ocupacion")

		newP = DiraPersona.objects.create(nombre=nombre,info=info)
		newP.save()

		if ocupacion != 'ninguna':
			newO = DiraOcupation.objects.create(persona=newP,ocupation=ocupacion)

		return redirect(f"/dira-persona/{newP.id}")
	return render(request,'dira-add-persona.html',{'ocupaciones':ocupaciones})


def diraAddBook(request):
	authors = DiraOcupation.objects.filter(ocupation='author').order_by('persona__nombre')
	booktypes = ["book","light-novel","manga","comic"]

	if request.method == 'POST':
		titulo = request.POST.get("titulo")
		getPubDate = request.POST.get("pubdate")

		if len(getPubDate)==4:
			pubyear = int(getPubDate)
			pubdate = None
		else:
			pubyear = int(getPubDate[:4])
			pubdate = getPubDate

		origlan = request.POST.get("orig_lan")
		tipo = request.POST.get("btype")
		author = DiraPersona.objects.get(pk=int(request.POST.get("autor")))

		if request.POST.get("info","") == "":
		    binfo = f"No review or synopsis has been written for this title. Please feel free to write one."
		else:
		    binfo = request.POST.get("info","")

		if request.FILES.get("imagen","")!='':
			ix = request.FILES.get("imagen")
		else:
			ix = None

		

		newB = DiraBook.objects.create(titulo = titulo,
			pubyear = pubyear,
			pubdate = pubdate,
			sinopsis=binfo, 
			idioma='TBA', 
			tipo='book',
			cover = ix,
			legacy=False,
			read = False)
		newB.save()

		newC = DiraBookCredit.objects.create(persona=author, 
			volume = newB, 
			credito = 'author')


		if len(request.POST.get("tags",""))>0:
			tags = request.POST.get("tags","").split(",")
			for t in tags:
				bt = DiraBookTag.objects.create(volume=newB,tag=t)
				bt.save()

		return redirect(f"/dira-book/{newB.id}")




	return render(request,'dira-add-book.html',{'authors':authors,'booktypes':booktypes})


def diraAddBookAuthor(request,author_id):
	author = DiraPersona.objects.get(pk=int(author_id))
	booktypes = ["book","light-novel","manga","comic"]

	if request.method == 'POST':
		titulo = request.POST.get("titulo")
		getPubDate = request.POST.get("pubdate")

		if len(getPubDate)==4:
			pubyear = int(getPubDate)
			pubdate = None
		else:
			pubyear = int(getPubDate[:4])
			pubdate = getPubDate

		origlan = request.POST.get("orig_lan")
		tipo = request.POST.get("btype")

		if request.POST.get("info","") == "":
		    binfo = f"No review or synopsis has been written for this title. Please feel free to write one."
		else:
		    binfo = request.POST.get("info","")

		if request.FILES.get("imagen","")!='':
			ix = request.FILES.get("imagen")
		else:
			ix = None

		

		newB = DiraBook.objects.create(titulo = titulo,
			pubyear = pubyear,
			pubdate = pubdate,
			sinopsis=binfo, 
			idioma='TBA', 
			tipo='book',
			cover = ix,
			legacy=True,
			read = False)
		newB.save()

		newC = DiraBookCredit.objects.create(persona=author, 
			volume = newB, 
			credito = 'author')


		if len(request.POST.get("tags",""))>0:
			tags = request.POST.get("tags","").split(",")
			for t in tags:
				bt = DiraBookTag.objects.create(volume=newB,tag=t)
				bt.save()

		return redirect(f"/dira-book/{newB.id}")




	return render(request,'dira-add-book-author.html',{'author':author,'booktypes':booktypes})


def diraBook(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))
	book_tags = DiraBookTag.objects.filter(volume = this_book)
	paginas = DiraBookPage.objects.filter(volume = this_book).order_by('-importancia')
	return render(request,'dira-book.html',{'this_book':this_book,'btags':book_tags,'paginas':paginas})

def diraEditBook(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))
	if request.method == 'POST':
		titulo = request.POST.get("titulo")
		sinopsis = request.POST.get("info")

		this_book.sinopsis = sinopsis
		this_book.titulo = titulo
		this_book.save()
		return redirect(f"/dira-book/{this_book.id}")
	return render(request,'dira-edit-book.html',{'this_book':this_book})

def diraStartRead(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))

	if request.method == 'POST':
		fecha_ini = request.POST.get("start_date")
		fecha_fin = request.POST.get("finish_date")
		formato = request.POST.get("formato")
		cantidad = request.POST.get("cantidad")
		idioma = request.POST.get("idioma")
		if request.POST.get("formato") == 'AudioBook':
			tiempo = request.POST.get("cantidad").split(":")
			horas = int(tiempo[0])
			minutos = int(tiempo[1])
			paginas = 30*(float(1.0*horas) + float(minutos/60.0))
			cantidad = int(round(paginas,0))

		if len(request.POST.get("finish_date",""))==0:
			fecha_fin = None
		else:
			this_book.read = True
			this_book.save()

		newC = DiraConsumo.objects.create(volume=this_book,
			fec_ini=fecha_ini,
			fec_fin=fecha_fin,
			formato = formato,
			paginas = cantidad,
			idioma = idioma)

		return redirect(f"/dira-book/{this_book.id}")


	return render(request,'dira-start-read.html',{'this_book':this_book})

def diraFinishRead(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))
	now_reading = DiraConsumo.objects.filter(volume=this_book,fec_fin__isnull=True).latest('id')

	if request.method == 'POST':
		fec_fin = request.POST.get("finish_date")
		now_reading.fec_fin = fec_fin
		now_reading.save()
		this_book.read = True
		this_book.save()
		return redirect(f"/dira-book/{this_book.id}")
	return render(request,'dira-finish-read.html',{'this_book':this_book})


def diraPersona(request,person_id):
	this_persona = DiraPersona.objects.get(pk=int(person_id))
	book_credits = DiraBookCredit.objects.filter(persona=this_persona).order_by('volume__pubyear')
	return render(request,'dira-persona.html',{'this_persona':this_persona,'book_credits':book_credits})

def diraAddBookPage(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))
	tipos = ["summary","review","character","place","event","object","quote"]
	if request.method == 'POST':
		titulo = request.POST.get("titulo","")
		contenido = request.POST.get("contenido","")
		tipo = request.POST.get("tipo","")
		importancia = request.POST.get("importancia","")

		newBP = DiraBookPage(volume=this_book,
			titulo = titulo,
			contenido = contenido,
			tipo = tipo,
			importancia = importancia,
			edited_at = datetime.now())
		newBP.save()

		return redirect(f"/dira-book/{this_book.id}")

	return render(request,'dira-add-book-page.html',{'this_book':this_book,'wtypes':tipos})


def diraEditBookPage(request,page_id):
	this_page = DiraBookPage.objects.get(pk=int(page_id))
	tipos = ["review","character","place","event","object","quote"]
	if request.method == 'POST':
		titulo = request.POST.get("titulo","")
		contenido = request.POST.get("contenido","")
		tipo = request.POST.get("tipo","")
		importancia = request.POST.get("importancia","")

		this_page.titulo = titulo
		this_page.contenido = contenido
		this_page.tipo = tipo 
		this_page.importancia = importancia
		this_page.edited_at = datetime.now()
		this_page.save()
		return redirect(f"/dira-book/{this_page.volume.id}")

	return render(request,'dira-edit-book-page.html',{'this_page':this_page,'wtypes':tipos})


def diraAddBookList(request):
	if request.method == 'POST':
		titulo = request.POST.get("title","")
		info = request.POST.get("info","")

		newL = DiraSeries.objects.create(titulo=titulo,info=info)
		newL.save()
		return redirect('/dira-book-lists')
	return render(request,'dira-add-book-list.html',{})

def diraBookLists(request):
	listas = sorted(DiraSeries.objects.all().order_by('-id'),key=lambda t: t.ultima_lectura, reverse=True)
	return render(request,'dira-book-lists.html',{'listas':listas})

def diraBookList(request,lista_id):
	books = DiraBookSeries.objects.filter(series__id=int(lista_id))
	this_lista = DiraSeries.objects.get(pk=int(lista_id))
	book_matches = None

	if request.method == 'POST':
		keyword = request.POST.get("keyword","")
		if len(keyword)>2:
			book_matches = DiraBook.objects.filter(Q(titulo__contains=keyword) | Q(sinopsis__contains=keyword))

	return render(request,'dira-book-list.html',{'books':books,'this_lista':this_lista,'book_s':book_matches})

def diraAddLegacyBook(request,book_id):
	this_book = DiraBook.objects.get(pk=int(book_id))
	this_book.legacy = True
	this_book.save()

	return redirect(f'/dira-book/{this_book.id}')

def diraLegacy(request):
	legacy_reads = DiraBook.objects.filter(legacy=True).order_by('pubyear')
	conteo = len(legacy_reads)
	return render(request,'dira-legacy.html',{'reads':legacy_reads,'conteo':conteo})

def diraAddBunkoSeries(request):
	authors = DiraOcupation.objects.filter(ocupation__in=["light-novel author","illustrator","mangaka"])
	tipos = ["light-novel","manga","comic"]

	if request.method == 'POST':
		this_author = DiraPersona.objects.get(pk=int(request.POST.get("autor")))
		tipo = request.POST.get("tipo")
		title = request.POST.get("title")
		info = request.POST.get("info")

		newS = DiraBunkoSeries.objects.create(series_title = title,
			series_author = this_author,
			series_info=info,
			series_type=tipo)

		newS.save()

		return redirect('/dira-bunko-all-series')

	return render(request,'dira-add-bunko-series.html',{'authors':authors,'tipos':tipos})


def diraBunkoSeriesList(request):
	this_series = DiraBunkoSeries.objects.all().order_by('series_title')
	return render(request,'dira-bunko-all-series.html',{'this_series':this_series})

def diraBunkoSeries(request,series_id):
	this_series = DiraBunkoSeries.objects.get(pk=int(series_id))
	this_volumes = DiraBunkoSeriesVolume.objects.filter(series=this_series).order_by('pubdate')
	return render(request,'dira-bunko-series.html',{'this_series':this_series,'this_volumes':this_volumes})

def diraAddBunkoVolume(request,series_id):
	this_series = DiraBunkoSeries.objects.get(pk=int(series_id))

	if request.method == 'POST':
		title = request.POST.get("title")
		pubdate = request.POST.get("pubdate")
		sinopsis = request.POST.get("sinopsis")

		newV = DiraBunkoSeriesVolume.objects.create(series=this_series,
			volume_title = title,
			pubdate = pubdate,
			sinopsis=sinopsis,
			read=False)
		newV.save()
		return redirect(f"/dira-bunko-series/{this_series.id}")

	return render(request,'dira-add-bunko-volume.html',{'this_series':this_series})


def diraBunkoVolume(request,volume_id):
	this_volume = DiraBunkoSeriesVolume.objects.get(pk=int(volume_id))
	paginas = DiraBunkoSeriesPage.objects.filter(volume = this_volume,tipo__in=['summary','review']).order_by('-importancia','id')
	wikipages = DiraBunkoSeriesPage.objects.filter(volume__series = this_volume.series).exclude(tipo__in=['summary','review']).order_by('-importancia','id')
	
	return render(request,'dira-bunko-volume.html',{'this_volume':this_volume,'paginas':paginas,'wikipages':wikipages})

def diraReadVolume(request,volume_id):
	this_volume = DiraBunkoSeriesVolume.objects.get(pk=int(volume_id))
	if request.method == 'POST':
		fecha_inicio = request.POST.get("start_date")
		fecha_fin = request.POST.get("finish_date")
		
		newCon = DiraBunkoSeriesConsumo.objects.create(volume=this_volume,
			fec_ini = fecha_inicio,
			fec_fin=fecha_fin,
			formato = 'kindle')
		newCon.save()
		this_volume.read = True
		this_volume.save()
		return redirect(f"/dira-bunko-volume/{this_volume.id}")
	return render(request,'dira-start-volume.html',{'this_volume':this_volume})

def diraAddBunkoPage(request,volume_id):
	this_volume = DiraBunkoSeriesVolume.objects.get(pk=int(volume_id))
	tipos = ["summary","review","character","place","event","object","quote"]
	if request.method == 'POST':
		titulo = request.POST.get("titulo","")
		contenido = request.POST.get("contenido","")
		tipo = request.POST.get("tipo","")
		importancia = request.POST.get("importancia","")

		newBP = DiraBunkoSeriesPage(volume=this_volume,
			page_title = titulo,
			page_content = contenido,
			tipo = tipo,
			importancia = importancia)
		newBP.save()

		return redirect(f"/dira-bunko-volume/{this_volume.id}")
	return render(request,'dira-add-bunko-page.html',{'this_volume':this_volume,'tipos':tipos})


def diraEditBunkoPage(request,page_id):
	this_page = DiraBunkoSeriesPage.objects.get(pk=int(page_id))
	tipos = ["summary","review","character","place","event","object","quote"]
	if request.method == 'POST':
		titulo = request.POST.get("titulo","")
		contenido = request.POST.get("contenido","")
		tipo = request.POST.get("tipo","")
		importancia = request.POST.get("importancia","")

		this_page.page_title = titulo
		this_page.page_content = contenido
		this_page.tipo = tipo 
		this_page.importancia = importancia
		this_page.save()

		return redirect(f"/dira-bunko-volume/{this_page.volume.id}")
	return render(request,'dira-edit-bunko-page.html',{'this_page':this_page,'tipos':tipos})

def diraWatchShow(request,show_id):
	this_show = DiraTemporada.objects.get(pk=int(show_id))
	if request.method == 'POST':
		fecha_inicio = request.POST.get("start_date")
		fecha_fin = request.POST.get("finish_date")
		
		newCon = TempConsumo.objects.create(show=this_show,
			fec_ini = fecha_inicio,
			fec_fin=fecha_fin)
		return redirect(f"/show/{this_show.id}")

	return render(request,'dira-watch-show.html',{'this_show':this_show})

def diraShowSeries(request,c_id):
	this_series = ShowCollection.objects.get(pk=int(c_id))
	this_seasons = RelShowCol.objects.filter(coleccion=this_series).order_by('temporada__show_premiere')
	return render(request,'dira-show-series.html',{'this_series':this_series,'this_seasons':this_seasons})






