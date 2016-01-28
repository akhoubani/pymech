#=============================================================================#
# neksuite                                                                    #
#                                                                             #
# A python module for reading and writing nek5000 files                       #
#                                                                             #
# Authors: Jacopo Canton, Nicolo' Fabbiane                                    #
# Contacts: jcanton(at)mech.kth.se, nicolo(at)mech.kth.se                     #
# Last edit: 2015-10-19                                                       #
#=============================================================================#
import struct
import numpy as np
import exadata as exdat


#==============================================================================
def readnek(fname):
	"""
	    readnek
	    A function for reading binary data from the nek5000 binary format

	    input variable:
	    fname : file name
	"""
	#
	try:
		infile = open(fname, 'rb')
	except IOError as e:
		print('I/O error ({0}): {1}'.format(e.errno, e.strerror))
		return -1
	#
	#---------------------------------------------------------------------------
	# READ HEADER
	#---------------------------------------------------------------------------
	#
	# read header
	header = infile.read(132).split()
	#
	# get word size
	wdsz = int(header[1])
	if (wdsz == 4):
		realtype = 'f'
	elif (wdsz == 8):
		realtype = 'd'
	else:
		print('ERROR: could not interpret real type (wdsz = %i)' %(wdsz))
		return -2
	#
	# get polynomial order
	lr1 = [int(header[2]), 
	       int(header[3]),
	       int(header[4])]
	#
	# compute total number of points per element
	npel = lr1[0] * lr1[1] * lr1[2]
	#
	# get number of pysical dimensions
	ndim = 2 + (lr1[2]>1)
	#
	# get number of elements
	nel = int(header[5])
	#
	# get number of elements in the file
	nelf = int(header[6])
	#
	# get current time
	time = float(header[7])
	#
	# get current time step
	istep = int(header[8])
	#
	# get file id
	fid = int(header[9])
	#
	# get tot number of files
	nf = int(header[10])
	#
	# get variables [XUPT]
	vars = header[-1]
	var = [0 for i in range(5)]
	for v in vars:
		if (v == 'X'):
			var[0] = ndim
		elif (v == 'U'):
			var[1] = ndim
		elif (v == 'P'):
			var[2] = 1
		elif (v == 'T'):
			var[3] = 1
		elif (v == 'S'):
			var[4] = 1 # TODO: need to know how this works
	#
	# compute number of scalar fields
	nfields = sum(var)
	#
	# identify endian encoding
	etagb = infile.read(4)
	etagL = struct.unpack('<f', etagb)[0]; etagL = int(etagL*1e5)/1e5
	etagB = struct.unpack('>f', etagb)[0]; etagB = int(etagB*1e5)/1e5
	if (etagL == 6.54321):
		# print('Reading little-endian file\n')
		emode = '<'
	elif (etagB == 6.54321):
		# print('Reading big-endian file\n')
		emode = '>'
	else:
		print('ERROR: could not interpret endianness')
		return -3
	#
	# read element map for the file
	elmap = infile.read(4*nelf)
	elmap = list(struct.unpack(emode+nelf*'i', elmap))
	#
	#---------------------------------------------------------------------------
	# READ DATA
	#---------------------------------------------------------------------------
	#
	# initialize data structure
	data = exdat.exadata(ndim, nel, lr1, var)
	data.time   = time
	data.istep  = istep
	data.wdsz   = wdsz
	if (emode == '<'):
		data.endian = 'little'
	elif (emode == '>'):
		data.endian = 'big'
	#
	# read geometry
	data.lims.pos[:,0] =  float('inf')
	data.lims.pos[:,1] = -float('inf')
	for iel in elmap:
		for idim in range(var[0]): # if var[0] == 0, geometry is not read
			fi = infile.read(npel*wdsz)
			fi = list(struct.unpack(emode+npel*realtype, fi))
			ip = 0
			for iz in range(lr1[2]):
				for iy in range(lr1[1]):
					data.elem[iel-1].pos[idim,iz,iy,:] = fi[ip:ip+lr1[0]]
					ip += lr1[0]
			data.lims.pos[idim,0] = min([data.lims.pos[idim,0]]+fi)
			data.lims.pos[idim,1] = max([data.lims.pos[idim,1]]+fi)
	#
	# read velocity
	data.lims.vel[:,0] =  float('inf')
	data.lims.vel[:,1] = -float('inf')
	for iel in elmap:
		for idim in range(var[1]): # if var[1] == 0, velocity is not read
			fi = infile.read(npel*wdsz)
			fi = list(struct.unpack(emode+npel*realtype, fi))
			ip = 0
			for iz in range(lr1[2]):
				for iy in range(lr1[1]):
					data.elem[iel-1].vel[idim,iz,iy,:] = fi[ip:ip+lr1[0]]
					ip += lr1[0]
			data.lims.vel[idim,0] = min([data.lims.vel[idim,0]]+fi)
			data.lims.vel[idim,1] = max([data.lims.vel[idim,1]]+fi)
	#
	# read pressure 
	data.lims.pres[:,0] =  float('inf')
	data.lims.pres[:,1] = -float('inf')
	for iel in elmap:
		for ivar in range(var[2]): # if var[2] == 0, pressure is not read
			fi = infile.read(npel*wdsz)
			fi = list(struct.unpack(emode+npel*realtype, fi))
			ip = 0
			for iz in range(lr1[2]):
				for iy in range(lr1[1]):
					data.elem[iel-1].pres[ivar,iz,iy,:] = fi[ip:ip+lr1[0]]
					ip += lr1[0]
			data.lims.pres[ivar,0] = min([data.lims.pres[ivar,0]]+fi)
			data.lims.pres[ivar,1] = max([data.lims.pres[ivar,1]]+fi)
	#
	# read temperature
	data.lims.temp[:,0] =  float('inf')
	data.lims.temp[:,1] = -float('inf')
	for iel in elmap:
		for ivar in range(var[3]): # if var[3] == 0, temperature is not read
			fi = infile.read(npel*wdsz)
			fi = list(struct.unpack(emode+npel*realtype, fi))
			ip = 0
			for iz in range(lr1[2]):
				for iy in range(lr1[1]):
					data.elem[iel-1].temp[ivar,iz,iy,:] = fi[ip:ip+lr1[0]]
					ip += lr1[0]
			data.lims.temp[ivar,0] = min([data.lims.temp[ivar,0]]+fi)
			data.lims.temp[ivar,1] = max([data.lims.temp[ivar,1]]+fi)
	#
	# read scalar fields
	data.lims.scal[:,0] =  float('inf')
	data.lims.scal[:,1] = -float('inf')
	for iel in elmap:
		for ivar in range(var[4]): # if var[4] == 0, scalars are not read
			fi = infile.read(npel*wdsz)
			fi = list(struct.unpack(emode+npel*realtype, fi))
			ip = 0
			for iz in range(lr1[2]):
				for iy in range(lr1[1]):
					data.elem[iel-1].scal[ivar,iz,iy,:] = fi[ip:ip+lr1[0]]
					ip += lr1[0]
			data.lims.scal[ivar,0] = min([data.lims.scal[ivar,0]]+fi)
			data.lims.scal[ivar,1] = max([data.lims.scal[ivar,1]]+fi)
	#
	#
	# close file
	infile.close()
	#
	# output
	return data