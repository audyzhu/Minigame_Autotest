
# -*- coding: UTF-8 -*-
from websocket_server import WebsocketServer
import requests
import plotly.offline as pltoff
import plotly.graph_objs as go
import os
import datetime
import uuid
import copy

MAXCLINET =20

dataDict ={
	0:{
		'tipnum': 0,
		'tag_start_time': 0,
		'tag_end_time':1,
		'begin_tag': False,
		'testtime': 0,
		'FPSsum':0,
		'maxdrawCall': 0,
		'maxtrianglesFaces': 0,
		'maxmem': 0,
		'hasDraw': False,
		'version': "",
		'dataset': {
			'time':[],
			'FPS':[],
			'mem':[],
			'drawCall':[],
			'trianglesFaces':[]
		},
		'perform_data': {
			'avgFPS': [],
			'maxmem': [],
			'maxdrawCall': [],
			'maxtrianglesFaces': []
		},
		'orgin_perform_data':{
			'avgFPS': [0,0,0],
			'maxmem': [0,0,0],
			'maxdrawCall': [0,0,0],
			'maxtrianglesFaces': [0,0,0]
		},
		'tag_start_list':[0],
		'tag_end_list':[0],
	}
}
clientID_to_device = {}

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	server.send_message_to_all("Hey all, a new client has joined us")


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])
	if client['id'] in clientID_to_device:
		device = clientID_to_device[client['id']]
		if not dataDict[device]['hasDraw']:
			error_end_test(client['id'])
		del clientID_to_device[client['id']]
	else:
		print("client id isn't exist")

# Called when a client sends a message
def message_received(client, server, message):
	if len(message) > 200:
		message = message[:200]+'..'
	print("Client(%d) said:" % (client['id']))
	print(message)
	if len(clientID_to_device) > MAXCLINET:
		print("the num of conneted client is out of MAXCLINET")
		return -1
	dealdata(client['id'],message)

  
def dealdata(id,message):
	data = message.split(',')
	#结束测试并绘图
	if data[0]=="end":
		end_test(id)
	#开始测试begin,version,device
	elif data[0]=="begin":
		start_test(id,data)
	#标记开始
	elif data[0]=="tagStart":
		start_tag(id)
	# 标记结束
	elif data[0]=="tagEnd":
		end_tag(id)
	#接收数据fps.mem,drawCall,trianglesFaces
	else:
		save_test_data(id,data)

    
def start_tag(id):
	global dataDict
	device=clientID_to_device[id]
	dataDict[device]['FPSsum'] = 0
	dataDict[device]['maxmem'] = 0
	dataDict[device]['maxdrawCall'] = 0
	dataDict[device]['maxtrianglesFaces'] = 0
	dataDict[device]['tag_start_time'] = dataDict[device]['testtime']
	dataDict[device]['begin_tag'] = True


def end_tag(id):
	#global begin_tag,tipnum
	global dataDict
	device = clientID_to_device[id]
	if dataDict[device]['begin_tag']:
		dataDict[device]['begin_tag'] = False
		dataDict[device]['tipnum'] += 1
		dataDict[device]['tag_end_time'] = dataDict[device]['testtime']
		dataDict[device]['tag_start_list'].append(dataDict[device]['tag_start_time'])
		dataDict[device]['tag_end_list'].append(dataDict[device]['tag_end_time'])
		if dataDict[device]['tag_end_time'] <= dataDict[device]['tag_start_time']:
			print("test time is too short")
			return False
		avgFPS = dataDict[device]['FPSsum'] / (dataDict[device]['tag_end_time'] - dataDict[device]['tag_start_time'])
		dataDict[device]['perform_data']['avgFPS'].append(avgFPS);
		dataDict[device]['perform_data']['maxmem'].append(dataDict[device]['maxmem']);
		dataDict[device]['perform_data']['maxdrawCall'].append(dataDict[device]['maxdrawCall']);
		dataDict[device]['perform_data']['maxtrianglesFaces'].append(dataDict[device]['maxtrianglesFaces']);
	else:
		return -1


def start_test(id,data):
	global dataDict,clientID_to_device
	clientID_to_device[id] = data[2].encode("utf-8")
	device = data[2].encode("utf-8")

	try:
		dataDict[device]['hasDraw'] = False
	except:
		dataDict[device] = {}
		dataDict[device]['dataset']={}
		dataDict[device]['perform_data'] = {}
		dataDict[device]['orgin_perform_data'] = {}
		dataDict[device]['tag_start_list'] = []
		dataDict[device]['tag_end_list'] = []

	dataDict[device]['hasDraw'] = False
	dataDict[device]['testtime'] = 0
	dataDict[device]['FPSsum'] = 0
	dataDict[device]['maxdrawCall'] = 0
	dataDict[device]['maxtrianglesFaces'] = 0
	dataDict[device]['maxmem'] = 0
	dataDict[device]['tipnum'] = 0
	dataDict[device]['dataset'].clear()
	dataDict[device]['perform_data'].clear()
	dataDict[device]['dataset'] = {
		'time': [],
		'FPS': [],
		'mem': [],
		'drawCall': [],
		'trianglesFaces': []
	}
	dataDict[device]['perform_data'] = {
		'avgFPS': [],
		'maxmem': [],
		'maxdrawCall': [],
		'maxtrianglesFaces': []
	}
	version = filter(str.isdigit, data[1].encode("utf-8"))
	dataDict[device]['version'] = version[-3:]
  
  
def end_test(id):
	global hasDraw,orgin_perform_data
	global dataDict
	device = clientID_to_device[id]
	if dataDict[device]['hasDraw']:
		return -1
	else:
		dataDict[device]['hasDraw'] = True
	data_g = []
	photo_PFS = go.Scatter(
		x=dataDict[device]['dataset']['time'],
		y=dataDict[device]['dataset']['FPS'],
		name='FPS'
	)
	data_g.append(photo_PFS)
	photo_mem = go.Scatter(
		x=dataDict[device]['dataset']['time'],
		y=dataDict[device]['dataset']['mem'],
		name='mem',
		xaxis='x',
		yaxis='y2'
	)
	data_g.append(photo_mem)
	print(dataDict[device]['tag_start_list'])
	print(dataDict[device]['tag_end_list'])

	num = 0
	while num < dataDict[device]['tipnum']:
		photo_PFS_tag = go.Scatter(
			x=dataDict[device]['dataset']['time'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			y=dataDict[device]['dataset']['FPS'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			name='FPS_tag'+str(num),
			mode='lines',
			fill='tozeroy'
		)
		data_g.append(photo_PFS_tag)
		photo_mem_tag = go.Scatter(
			x=dataDict[device]['dataset']['time'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			y=dataDict[device]['dataset']['mem'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			name='mem_tag'+str(num),
			xaxis='x',
			yaxis='y2',
			mode='lines',
			fill='tozeroy'
		)
		data_g.append(photo_mem_tag)
		num += 1

	createTitle = html_tile(id)
	save_to_local(id,device+"_"+"perform.txt")
	myTitle = ""
	num = 1
	if not createTitle:
		while num <= dataDict[device]['tipnum']:
			print(dataDict[device]['tipnum'], num)
			myTitle += "第" + str(num) + "标记处" + "平均FPS = " + str(dataDict[device]['perform_data']['avgFPS'][num - 1]) + ", 峰值mem = " \
					   + str(dataDict[device]['perform_data']['maxmem'][num - 1]) + "MB, 峰值drawCall = " + str(dataDict[device]['perform_data']['maxdrawCall'][num - 1]) \
					   + ", 峰值三角面数 = " + str(dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1])
			myTitle += "<br>"
			num += 1
	else:
		myTitle = createTitle

	layout = go.Layout(title=myTitle,
					   xaxis={'title': 'time'}, yaxis={'title': 'frame'},
					   yaxis2=dict(anchor='x', overlaying='y', side='right', title='Mb'))
	fig = go.Figure(data=data_g, layout=layout)
	filename = "%s.html" % (uuid.uuid4())
	pltoff.plot(fig, filename=filename)
	dataDict[device]['orgin_perform_data'] = copy.deepcopy(dataDict[device]['perform_data'])
	print(dataDict[device]['orgin_perform_data'])


def error_end_test(id):
	global dataDict
	device = clientID_to_device[id]
	if dataDict[device]['hasDraw']:
		return -1
	else:
		dataDict[device]['hasDraw'] = True

	data_g = []
	photo_PFS = go.Scatter(
		x=dataDict[device]['dataset']['time'],
		y=dataDict[device]['dataset']['FPS'],
		name='FPS'
	)
	data_g.append(photo_PFS)
	photo_mem = go.Scatter(
		x=dataDict[device]['dataset']['time'],
		y=dataDict[device]['dataset']['mem'],
		name='mem',
		xaxis='x',
		yaxis='y2'
	)
	data_g.append(photo_mem)

	num = 0
	while num < dataDict[device]['tipnum']:
		photo_PFS_tag = go.Scatter(
			x=dataDict[device]['dataset']['time'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			y=dataDict[device]['dataset']['FPS'][dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			name='FPS_tag'+str(num),
			mode='lines',
			fill='tozeroy'
		)
		data_g.append(photo_PFS_tag)
		photo_mem_tag = go.Scatter(
			x=dataDict[device]['dataset']['time'][
			  dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			y=dataDict[device]['dataset']['mem'][
			  dataDict[device]['tag_start_list'][num]:dataDict[device]['tag_end_list'][num]],
			name='mem_tag'+str(num),
			xaxis='x',
			yaxis='y2',
			mode='lines',
			fill='tozeroy'
		)
		data_g.append(photo_mem_tag)
		num += 1

	myTitle = ""
	num = 1
	while num <= dataDict[device]['tipnum']:
		print(dataDict[device]['tipnum'], num)
		myTitle += "第" + str(num) + "标记处" + "平均FPS = " + str(dataDict[device]['perform_data']['avgFPS'][num - 1]) + ", 峰值mem = " \
				   + str(dataDict[device]['perform_data']['maxmem'][num - 1]) + "MB, 峰值drawCall = " + str(\
					dataDict[device]['perform_data']['maxdrawCall'][num - 1]) \
				   + ", 峰值三角面数 = " + str(dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1])
		num += 1

	layout = go.Layout(title=myTitle,
					   xaxis={'title': 'time'}, yaxis={'title': 'frame'},
					   yaxis2=dict(anchor='x', overlaying='y', side='right', title='Mb'))
	fig = go.Figure(data=data_g, layout=layout)
	filename = "%s.html" % (uuid.uuid4())
	pltoff.plot(fig, filename=filename)

  
def save_test_data(id,data):
	global dataDict
	device = clientID_to_device[id]
	try:
		dataDict[device]['dataset']['time'].append(dataDict[device]['testtime'])
		dataDict[device]['dataset']['FPS'].append(data[0])
		dataDict[device]['dataset']['mem'].append(data[1])
		dataDict[device]['testtime'] += 1
		intdata0 = filter(str.isdigit, data[0].encode("utf-8"))
		intdata1 = filter(str.isdigit, data[1].encode("utf-8"))
		intdata2 = filter(str.isdigit, data[2].encode("utf-8"))
		intdata3 = filter(str.isdigit, data[3].encode("utf-8"))
		dataDict[device]['FPSsum'] += int(intdata0)
		if int(intdata1) > dataDict[device]['maxmem']:
			dataDict[device]['maxmem'] = float(intdata1) / 100
		if int(intdata2) > dataDict[device]['maxdrawCall']:
			dataDict[device]['maxdrawCall'] = int(intdata2)
		if int(intdata3) > dataDict[device]['maxtrianglesFaces']:
			dataDict[device]['maxtrianglesFaces'] = int(intdata3)
	except:
		print("undefined data type")


def html_tile(id):
	device = clientID_to_device[id]
	myTitle = ""
	num = 1
	try:
		while num <= dataDict[device]['tipnum']:
			myTitle += "第" + str(num) + "标记处" + "平均FPS = " + str(dataDict[device]['perform_data']['avgFPS'][num - 1])
			if dataDict[device]['perform_data']['avgFPS'][num - 1] >= dataDict[device]['orgin_perform_data']['avgFPS'][num - 1]:
				myTitle += "(↑" + str(dataDict[device]['perform_data']['avgFPS'][num - 1] - dataDict[device]['orgin_perform_data']['avgFPS'][num - 1]) + ")"
			else:
				myTitle += "(↓" + str(dataDict[device]['orgin_perform_data']['avgFPS'][num - 1] - dataDict[device]['perform_data']['avgFPS'][num - 1]) + ")"
			myTitle += ", 峰值mem = " + str(dataDict[device]['perform_data']['maxmem'][num - 1])
			if dataDict[device]['perform_data']['maxmem'][num - 1] >= dataDict[device]['orgin_perform_data']['maxmem'][num - 1]:
				myTitle += "(↑" + str(dataDict[device]['perform_data']['maxmem'][num - 1] - dataDict[device]['orgin_perform_data']['maxmem'][num - 1]) + ")"
			else:
				myTitle += "(↓" + str(dataDict[device]['orgin_perform_data']['maxmem'][num - 1] - dataDict[device]['perform_data']['maxmem'][num - 1]) + ")"
			myTitle += "MB, 峰值drawCall = " + str(dataDict[device]['perform_data']['maxdrawCall'][num - 1])
			if dataDict[device]['perform_data']['maxdrawCall'][num - 1] >= dataDict[device]['orgin_perform_data']['maxdrawCall'][num - 1]:
				myTitle += "(↑" + str(dataDict[device]['perform_data']['maxdrawCall'][num - 1] - dataDict[device]['orgin_perform_data']['maxdrawCall'][num - 1]) + ")"
			else:
				myTitle += "(↓" + str(dataDict[device]['orgin_perform_data']['maxdrawCall'][num - 1] - dataDict[device]['perform_data']['maxdrawCall'][num - 1]) + ")"
			myTitle += ", 峰值三角面数 = " + str(dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1])
			if dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1] >= dataDict[device]['orgin_perform_data']['maxtrianglesFaces'][num - 1]:
				myTitle += "(↑" + str(dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1] - dataDict[device]['orgin_perform_data']['maxtrianglesFaces'][num - 1]) + ")"
			else:
				myTitle += "(↓" + str(dataDict[device]['orgin_perform_data']['maxtrianglesFaces'][num - 1] - dataDict[device]['perform_data']['maxtrianglesFaces'][num - 1]) + ")"
			myTitle += "<br>"
			num += 1
	except:
		return False
	return myTitle


PORT = 9001
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.run_forever()

