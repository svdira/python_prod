class DiraTemporada(models.Model):
	show_title = models.CharField(max_length=300)
	single_season = models.BooleanField()
	show_premiere = models.DateField()
	show_finale = models.DateField()
	episodes = models.IntegerField()
	avg_duration = models.IntegerField()
	tipo = models.CharField(max_length=50)
	sinopsis = models.TextField()

	@property
	def ncons(self):
		n = DiraShowConsumo.objects.filter(show=self)
		return n

	def __str__(self):
		return self.show_title

class TempConsumo(models.Model):
	show = models.ForeignKey(DiraTemporada,on_delete=models.CASCADE)
	fec_ini = models.DateField()
	fec_fin = models.DateField(null=True,blank=True)

	def __str__(self):
		return self.show_title

