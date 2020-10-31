from mongoDocuments import Setup

import mongoengine as me


class Checkpoint(me.Document):
	"""
	Checkpoint document containing .vtk file for an associated .yaml setup
	"""

	name = me.StringField()  # Name
	setup = me.ReferenceField(Setup)  # associated yaml setup
	vtk = me.FileField()  # .vtk file
	vtk_hash = me.StringField(unique=True)  # vtk hash
	active = me.BooleanField()  # active toggle
	uploadDate = me.DateTimeField()  # Upload Date

	def __str__(self):
		return self.name
