import geometry
import time
import tkinter as tk
from tkinter import ttk
import grbl_gcodes as grbl

#geometry_types = [
#|
#|__geometry class instance 1 = Geometry(**kwargs,
#|		|type = 'Geom1'  		#this will be 'Hole', 'Rectangle', etc
#|		|instance_count = n 	#current count of the number of geometry objects in the geometry_dict 
#|		|etc.
#|		|___geometry_dict{
#|		|   |n:   geometry_module.Geom1(instance n)
#|		|   |n+1: geometry_module.Geom1(instance n+1)
#|		|   |n+2:...
#|		|   |}
#|		|)
#|	
#|__geometry class instance 2 = Geometry(**kwargs,
#|		|type = 'Geom2'  		#this will be 'Hole', 'Rectangle', etc
#|		|instance_count = n 	#current count of the number of geometry objects in the geometry_dict 
#|		|etc.
#|		|___geometry_dict{
#|		|   |n:   geometry_module.Geom2(instance n)
#|		|   |n+1: geometry_module.Geom2(instance n+1)
#|		|   |n+2:...
#|		|   |}
#|		|)
#|
#|__etc.
#]
geometry_types = []

def create_gcode():
	settings={}
	settings['units'] 			= units_var.get() #str 'G20' inches or 'G21' mm
	settings['tool_diameter'] 	= float(cutter_diam.get())
	settings['depth_of_cut'] 	= float(depth_of_cut.get())
	settings['speed'] 			= float(speed.get())
	settings['feed'] 			= float(feed.get())
	settings['retract_height'] 	= float(retract_height.get())
	settings['unit_precision'] 	= 5

	gcode = []
	gcode_header = [\
		f'{grbl.plane_xy} (xy plane select)',\
		f'{settings["units"]} (G20=inch G21=mm)',\
		'G90 (absolute distance)',\
		f'M3 S{settings["speed"]} (spindle clockwise)',\
		'G4 P20 (dwell 20 seconds)']
	gcode_footer = ['M5 (spindle stop)', 'M2 (program end)']

	for line in gcode_header:
		gcode.append(line)
		
	for type in geometry_types:
		if len(type.geometry_dict): 						#type.geometry_dict holds a number of geometry objects of type string kwarg 
			for instance in list(type.geometry_dict): 	#eg: hole 1, hole 2, etc
				geometry_gcode = type.geometry_dict[instance].create_gcode(settings)
				#print(geometry_gcode)
				[gcode.append(i) for i in geometry_gcode]
	
	for line in gcode_footer:
		gcode.append(line)
		
	#[print(i) for i in gcode]

	year_day = time.strftime('%y.%j')
	hours_minutes_seconds = time.strftime('%H.%M.%S')

	with open('{}_{}_{}.ngc'.format(year_day, hours_minutes_seconds, filename.get()), 'w') as f:
		for item in gcode:
			f.write(item + '\n')
		
def export_data():
	export_filename = '{}.geom'.format(filename.get())
	file_buffer = []
	file_buffer.append('Setup')
	file_buffer.append('units,{}'.format(units_var.get()))
	file_buffer.append('cutter_diameter,{}'.format(cutter_diam.get()))
	file_buffer.append('speed,{}'.format(speed.get()))
	file_buffer.append('feed,{}'.format(feed.get()))
	file_buffer.append('depth_of_cut,{}'.format(depth_of_cut.get()))
	file_buffer.append('retract_height,{}'.format(retract_height.get()))

	for geometry in geometry_types:
		if len(geometry.geometry_dict):

			if geometry.type == 'Hole':
				file_buffer.append('Hole,(x,y,diameter,depth,type,side)')
				for n in list(geometry.geometry_dict):
					data_str = geometry.geometry_dict[n].data_export()
					file_buffer.append('{}'.format(data_str))

			if geometry.type == 'Rectangle':
				file_buffer.append('Rectangle,(x1,y1,x2,y2,depth,type,side)')
				for n in list(geometry.geometry_dict):
					data_str = geometry.geometry_dict[n].data_export()
					file_buffer.append('{}'.format(data_str))

			if geometry.type == 'Conn':
				file_buffer.append('Conn,(x_center,y_center,a,b,rotation,depth,type)')
				for n in list(geometry.geometry_dict):
					data_str = geometry.geometry_dict[n].data_export()
					file_buffer.append('{}'.format(data_str))

	with open(export_filename, 'w') as f:
		n = len(file_buffer)
		for index,line in enumerate(file_buffer):
			f.write(line)
			if index+1 < n:
				f.write('\n')

def import_data():
	for type in geometry_types:
		while type.instance_counter > 0: type.del_item()

	input_csv = []
	import_filename = '{}.geom'.format(filename.get())
	with open(import_filename, 'r') as f: input_lines = f.read().splitlines()
	for line in input_lines: input_csv.append(line.split(','))

	for line in input_csv:
		#print(line)
		if line[0].startswith('Setup'):
			csv_section = 'Setup'
			continue
		if line[0].startswith('Hole'):
			csv_section = 'Hole'
			continue
		if line[0].startswith('Rectangle'):
			csv_section = 'Rectangle'
			continue
		if line[0].startswith('Conn'):
			csv_section = 'Conn'
			continue

		if csv_section == 'Setup':
			if line[0] == 'units' and line[1] == 'G20': rb_in.invoke() #g20 inches
			if line[0] == 'units' and line[1] == 'G21': rb_mm.invoke() #g21 mm
			if line[0] == 'cutter_diameter': 	cutter_diam.set(float(line[1]))
			if line[0] == 'speed': 				speed.set(float(line[1]))
			if line[0] == 'feed': 				feed.set(float(line[1]))
			if line[0] == 'depth_of_cut': 		depth_of_cut.set(float(line[1]))
			if line[0] == 'retract_height': 	retract_height.set(float(line[1]))
		
		if csv_section == 'Hole':
			hole_class = geometry_types[geometry_types.index(hole)]
			hole_class.add_item()
			last_instance = list(hole_class.geometry_dict)[-1]
			hole_class.geometry_dict[last_instance].x_center_var.set(line[0])
			hole_class.geometry_dict[last_instance].y_center_var.set(line[1])
			hole_class.geometry_dict[last_instance].diam_var.set(line[2])
			hole_class.geometry_dict[last_instance].depth_var.set(line[3])
			if line[4]  == 'perimeter': hole_class.geometry_dict[last_instance].type_spin_box_var.set('perimeter')
			if line[4]  == 'pocket': 	hole_class.geometry_dict[last_instance].type_spin_box_var.set('pocket')
			if line[5]  == 'inside':	hole_class.geometry_dict[last_instance].side_spin_box_var.set('inside')
			if line[5]  == 'outside':	hole_class.geometry_dict[last_instance].side_spin_box_var.set('outside')

		if csv_section == 'Rectangle':
			rect_class = geometry_types[geometry_types.index(rect)]
			rect_class.add_item()
			last_instance = list(rect_class.geometry_dict)[-1]
			rect_class.geometry_dict[last_instance].x1_var.set(line[0])
			rect_class.geometry_dict[last_instance].y1_var.set(line[1])
			rect_class.geometry_dict[last_instance].x2_var.set(line[2])
			rect_class.geometry_dict[last_instance].y2_var.set(line[3])
			rect_class.geometry_dict[last_instance].depth_var.set(line[4])
			if line[5]  == 'perimeter':	rect_class.geometry_dict[last_instance].type_spin_box_var.set('perimeter')
			if line[5]  == 'pocket':	rect_class.geometry_dict[last_instance].type_spin_box_var.set('pocket')
			if line[6]  == 'inside':	rect_class.geometry_dict[last_instance].side_spin_box_var.set('inside')
			if line[6]  == 'outside':	rect_class.geometry_dict[last_instance].side_spin_box_var.set('outside')

		if csv_section == 'Conn':
			conn_class = geometry_types[geometry_types.index(conn)]
			conn_class.add_item()
			last_instance = list(conn_class.geometry_dict)[-1]
			conn_class.geometry_dict[last_instance].x_center_var.set(line[0])
			conn_class.geometry_dict[last_instance].y_center_var.set(line[1])
			conn_class.geometry_dict[last_instance].a_dim_var.set(line[2])
			conn_class.geometry_dict[last_instance].b_dim_var.set(line[3])
			conn_class.geometry_dict[last_instance].rotation_var.set(line[4])
			conn_class.geometry_dict[last_instance].depth_var.set(line[5])
			if line[6]  == 'dogbone':	conn_class.geometry_dict[last_instance].type_spin_box_var.set('dogbone')
			if line[6]  == 'D':			conn_class.geometry_dict[last_instance].type_spin_box_var.set('D')
			if line[6]  == 'doubleD':	conn_class.geometry_dict[last_instance].type_spin_box_var.set('doubleD')
			if line[6]  == 'DE':		conn_class.geometry_dict[last_instance].type_spin_box_var.set('DE')

		
def get_profiles():
	file_name = 'cutting_profiles.txt'
	with open (file_name, 'r') as f:
		file_lines = f.readlines()

class Geometry: #each Geometry instance is container for a geometry type and holds n instances of that geometry type
	def __init__(self, **kwargs):
		self.type 				= kwargs['type']
		self.parent_frame 		= kwargs['parent_frame']
		self.instance_counter 	= 0 	#integer number of objects of this class type
		self.geometry_dict 		= {} 	#holds all the objects of this geometry type
		
		self.create_gui_items()
		
	def create_gui_items(self):
		self.header_frame 		= tk.Frame(self.parent_frame)
		self.data_frame 		= tk.Frame(self.parent_frame)
		self.canvas 			= tk.Canvas(self.data_frame, width=450)
		self.canvas_frame 		= tk.Frame(self.canvas)
		
		self.header_frame		.grid(row=0, column=0, sticky='w')
		self.data_frame			.grid(row=1, column=0, sticky='w')
		self.canvas				.grid(row=0, column=0, sticky="nsew")
		self.canvas				.create_window(0, 0, window=self.canvas_frame, anchor='nw',)

		self.vert_scrollbar 	= tk.Scrollbar(self.data_frame,orient=tk.VERTICAL)
		self.vert_scrollbar		.config(command=self.canvas.yview)
		self.canvas				.config(yscrollcommand=self.vert_scrollbar.set)
		self.vert_scrollbar		.grid(row=0, column=1, sticky="ns")

		self.canvas_frame		.bind("<Configure>", lambda x= None: (self.canvas.configure(scrollregion=self.canvas.bbox("all"))) )

		self.add_btn 			= tk.Button(self.header_frame,text='Add',command=self.add_item)
		self.del_btn 			= tk.Button(self.header_frame,text='Delete',command=self.del_item)
		self.add_btn			.grid(row=0,column=0)
		self.del_btn			.grid(row=0,column=1)
	
	def add_item(self):
		self.instance_counter += 1
		if self.type == 'Hole':
			self.geometry_dict[self.instance_counter] = geometry.Hole(self.canvas_frame,self.instance_counter)

		if self.type == 'Rectangle':
			self.geometry_dict[self.instance_counter] = geometry.CornerRectangle(self.canvas_frame,self.instance_counter)
			
		if self.type == 'Polygon':
			self.geometry_dict[self.instance_counter] = geometry.Polygon(self.canvas_frame,self.instance_counter)
			
		if self.type == 'Conn':
			self.geometry_dict[self.instance_counter] = geometry.Conn(self.canvas_frame,self.instance_counter)
			
		if self.type == 'Rect Hole Pattern':
			self.geometry_dict[self.instance_counter] = geometry.RectHolePattern(self.canvas_frame,self.instance_counter)
			
	def del_item(self):
		if self.instance_counter > 0:
			self.geometry_dict[self.instance_counter].destroy_entries()
			del self.geometry_dict[self.instance_counter]
			self.instance_counter-=1
			
	def test(self):
		self.geometry_dict[self.instance_counter].test()
	
root = tk.Tk()
root.resizable(False, False)
#root.title("title")

###main gui layout########################################
main_frame 			= tk.Frame(root)#, height=500, width=500)
top_frame 			= tk.Frame(main_frame)
options_frame 		= tk.Frame(top_frame)
bottom_frame 		= tk.Frame(main_frame)
nb 					= ttk.Notebook(bottom_frame)

main_frame			.grid(column=0, row=0)
top_frame			.grid(column=0, row=0)
options_frame		.grid(row=0,column=0, sticky='w')
bottom_frame		.grid(column=0, row=1)
nb					.grid(row = 1, column=0)

###options frame############################################
units_var 				= tk.StringVar()
cutter_diam 			= tk.StringVar()
speed 					= tk.StringVar()
feed 					= tk.StringVar()
depth_of_cut 			= tk.StringVar()
retract_height 			= tk.StringVar()
filename 				= tk.StringVar()

cutter_diam				.set('0.125')
speed					.set('10000')
feed					.set('5')
depth_of_cut			.set('0.005')
retract_height			.set('0.100')
filename				.set('job_out')

rb_in 					= tk.Radiobutton(options_frame, text = "inch\nG20", variable=units_var, value = "G20")
rb_mm 					= tk.Radiobutton(options_frame, text = "mm\nG21", variable=units_var, value = "G21")
rb_in					.invoke()

cutter_diam_label 		= tk.Label(options_frame,text='Tool Diameter')
speed_label 			= tk.Label(options_frame,text='Spindle RPM')
retract_height_label 	= tk.Label(options_frame,text='Retract Height')
depth_of_cut_label 		= tk.Label(options_frame,text='Depth of Cut')
feed_label 				= tk.Label(options_frame,text='Feed Rate')
filename_label 			= tk.Label(options_frame,text='File Name')

cutter_diam_entry 		= tk.Entry(options_frame, textvariable=cutter_diam)
speed_entry 			= tk.Entry(options_frame, textvariable=speed)
feed_entry 				= tk.Entry(options_frame, textvariable=feed)
depth_of_cut_entry 		= tk.Entry(options_frame, textvariable=depth_of_cut)
retract_height_entry 	= tk.Entry(options_frame, textvariable=retract_height)
filename_entry 			= tk.Entry(options_frame, textvariable=filename)

gcode_btn 				= tk.Button(options_frame, text='Create G-Code', command=create_gcode)
export_data_btn 		= tk.Button(options_frame, text='Export Data',command=export_data)
import_data_btn 		= tk.Button(options_frame, text='Import Data', command=import_data)

rb_in					.grid(row=0, column=0)
rb_mm					.grid(row=0, column=1)
cutter_diam_label		.grid(row=2, column=0)
cutter_diam_entry		.grid(row=2, column=1)
speed_label				.grid(row=3, column=0)
speed_entry				.grid(row=3, column=1)
feed_label				.grid(row=4, column=0)
feed_entry				.grid(row=4, column=1)
depth_of_cut_label		.grid(row=5, column=0)
depth_of_cut_entry		.grid(row=5, column=1)
retract_height_label	.grid(row=6, column=0)
retract_height_entry	.grid(row=6, column=1)
filename_label			.grid(row=7, column=0)
filename_entry			.grid(row=7, column=1)
gcode_btn				.grid(row=8, column=0)
export_data_btn			.grid(row=8, column=1)
import_data_btn			.grid(row=8, column=2)

###shapes notebook###############################################
page1 = ttk.Frame(nb)
page2 = ttk.Frame(nb)
page3 = ttk.Frame(nb)
page4 = ttk.Frame(nb)
page5 = ttk.Frame(nb)
nb.add(page1, text='Hole')
nb.add(page2, text='Rect')
nb.add(page3, text='Poly')
nb.add(page4, text='Conn') #dogbone, dsub, sma, etc.
nb.add(page5, text='RctHolPtrn')

##page1 hole setup###############################################
hole_header_frame = tk.Frame(page1)
hole_content_frame = tk.Frame(page1)
hole_header_frame.grid(row=0,column=0, sticky='w')
hole_content_frame.grid(row=1,column=0)
hole_labels	= tk.Label(hole_header_frame,text= '\t\t\tX Center    Y Center    Diameter    Depth')
hole_labels.grid(row=0, column=0)

hole = Geometry(type='Hole', parent_frame=hole_content_frame)
geometry_types.append(hole)

##page2 rect setup###############################################
rect_header_frame = tk.Frame(page2)
rect_content_frame = tk.Frame(page2)
rect_content_frame.grid(row=1, column=1)
rect_header_frame.grid(row=0, column=1, sticky='w')
rect_labels	= tk.Label(rect_header_frame,text= '\t\t\tX1\t   Y2\t      X2\t          Y2\t             Depth')
rect_labels.grid(row=0, column=0)

rect = Geometry(type='Rectangle', parent_frame=rect_content_frame)
geometry_types.append(rect)

##page3 poly setup###############################################
poly_header_frame = tk.Frame(page3)
poly_content_frame = tk.Frame(page3)
poly_header_frame.grid(row=0,column=0, sticky='w')
poly_content_frame.grid(row=1,column=0, sticky='w')
poly_label = tk.Label(poly_header_frame,text= 'Vertices: (x1,y1),(x2,y2), ... Depth')
poly_label.grid(row=0,column=0)

poly = Geometry(type='Polygon', parent_frame=poly_content_frame)
geometry_types.append(poly)

##page4 conn setup############################################
conn_header_frame = tk.Frame(page4)
conn_content_frame = tk.Frame(page4)
conn_header_frame.grid(row=0,column=0, sticky='w')
conn_content_frame.grid(row=1,column=0, sticky='w')
conn_label = tk.Label(conn_header_frame,text= "\t         X Center    Y Center            'A'            'B'          Rotation       Depth")
conn_label.grid(row=0,column=0)

conn = Geometry(type='Conn', parent_frame=conn_content_frame)
geometry_types.append(conn)

##page5 hole pattern setup#######################################
rect_hole_pattern_header_frame	= tk.Frame(page5)
rect_hole_pattern_content_frame	= tk.Frame(page5)
rect_hole_pattern_header_frame	.grid(row=0,column=0, sticky='w')
rect_hole_pattern_content_frame	.grid(row=1,column=0, sticky='w')
rect_hole_ptn_label	= tk.Label(rect_hole_pattern_header_frame,text= 'Xo Yo X Spc. Y Spc. X Qty Y Qty Diam Depth')
rect_hole_ptn_label.grid(row=0,column=0)

rect_hole_pattern = Geometry(type='Rect Hole Pattern', parent_frame=rect_hole_pattern_content_frame)
geometry_types.append(rect_hole_pattern)

if __name__ == "__main__":
	pass
	

root.mainloop()