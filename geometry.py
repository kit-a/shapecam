import math
import tkinter as tk
from tkinter import ttk

#generates all negative z layer height values for 2.5d milling
def z_height_passes(total_depth,depth_of_cut,unit_precision):
	depth = abs(total_depth)
	doc = abs(depth_of_cut)
	z_height_passes=[] 
	number_z_height_passes = int(depth/doc)

	for i in range(number_z_height_passes):
		zheight = (i+1)*doc*-1
		z_height_passes.append(round(zheight,unit_precision))

	if zheight > depth*-1:
		z_height_passes.append(round(depth*-1,unit_precision))

	return(z_height_passes)

class Hole:
	def __init__(self, frame, instance_count):
		self.frame 				= frame
		self.instance_count 	= instance_count
		self.types 				= ['perimeter','pocket']
		self.sides 				= ['inside','outside']
		self.side				= ''
		self.type 				= ''
		self.x_center 			= 0
		self.y_center 			= 0
		self.hole_diameter 		= 0
		self.depth 				= 0
		self.create_entries()
		
	def create_entries(self):
		self.x_center_var 		= tk.DoubleVar()
		self.y_center_var 		= tk.DoubleVar()
		self.diam_var 			= tk.DoubleVar()
		self.depth_var 			= tk.DoubleVar()
		self.side_spin_box_var 	= tk.StringVar()
		self.type_spin_box_var 	= tk.StringVar()
		
		self.side_spin_box		= tk.Spinbox(self.frame, values = self.sides,textvariable=self.side_spin_box_var, width=9)
		self.type_spin_box		= tk.Spinbox(self.frame, values = self.types,textvariable=self.type_spin_box_var, width=9)
		self.x_center_entry 	= tk.Entry(self.frame, textvariable=self.x_center_var, width=9)
		self.y_center_entry 	= tk.Entry(self.frame, textvariable=self.y_center_var, width=9)
		self.diam_entry 		= tk.Entry(self.frame, textvariable=self.diam_var, width=9)
		self.depth_entry 		= tk.Entry(self.frame, textvariable=self.depth_var, width=9)
		
		self.side_spin_box		.grid(row=self.instance_count, column=0)
		self.type_spin_box		.grid(row=self.instance_count, column=1)
		self.x_center_entry 	.grid(row=self.instance_count, column=2)
		self.y_center_entry 	.grid(row=self.instance_count, column=3)
		self.diam_entry 		.grid(row=self.instance_count, column=4)
		self.depth_entry 		.grid(row=self.instance_count, column=5)

	def destroy_entries(self):
		self.side_spin_box		.destroy()
		self.type_spin_box		.destroy()
		self.x_center_entry 	.destroy()
		self.y_center_entry 	.destroy()
		self.diam_entry 		.destroy()
		self.depth_entry 		.destroy()
		
	def update_variables(self):
		self.side 				= self.side_spin_box_var.get()
		self.type 				= self.type_spin_box_var.get()
		self.x_center 			= self.x_center_var.get()
		self.y_center 			= self.y_center_var.get()
		self.hole_diameter 		= self.diam_var.get()
		self.depth 				= self.depth_var.get()

	def data_export(self):
		self.update_variables()
		x = self.x_center
		y = self.y_center
		diam = self.hole_diameter
		depth = self.depth
		type = self.type
		side = self.side
		return(f'{x},{y},{diam},{depth},{type},{side}')
		
	def create_gcode(self, settings):
		gcode = []
		tool_diameter 			= settings['tool_diameter']
		depth_of_cut 			= settings['depth_of_cut']
		speed 					= settings['speed']
		feed 					= settings['feed']
		retract_height 			= settings['retract_height']
		unit_precision 			= settings['unit_precision']
		
		self.update_variables()
		x_center = round(self.x_center, unit_precision)
		y_center = round(self.y_center, unit_precision)
	
		if self.side == 'inside': #cutter on the inside of the profile
			toolpath_od = self.hole_diameter - tool_diameter
			toolpath_radius = toolpath_od/2
			
		elif self.side == 'outside': #cutter on the outside of the profile
			toolpath_od = self.hole_diameter + tool_diameter
			toolpath_radius = toolpath_od/2
			
		toolpath_radius = round(toolpath_radius,unit_precision)
		hole_max_y = round(self.x_center + toolpath_radius, unit_precision)
		
		#generate all of the layer z height values for 2.5d milling
		z_heights=z_height_passes(self.depth,depth_of_cut,unit_precision) 
		
		#Gcode time
		if self.type == 'perimeter':
			#positioning and setup
			gcode.append('F{}'.format(feed))#use same feed rate throughout
			gcode.append('S{}'.format(speed))
			gcode.append(f'G0 Z{retract_height}')#go to safe z height
			gcode.append(f'G0 X{x_center} Y{y_center}')    #go to hole center
			gcode.append(f'G1 X{hole_max_y} Y{y_center} Z0')#go to hole starting point
			
			#generate and append helical arcs
			for i in z_heights:
				gcode.append(f'G3 X{hole_max_y} Y{y_center} Z{i} I{-toolpath_radius}')#travel circumference, down z layer height
				gcode.append(f'G1 X{hole_max_y} Y{y_center} Z{i}')#no move but tell machine we are back at starting point

			gcode.append(f'G3 X{hole_max_y} Y{y_center} Z{i} I{-toolpath_radius}')#bottom of hole
			gcode.append(f'G0 Z{retract_height}')#retract height
			#gcode.append(f'G0 X{x_center} Y{y_center}')#hole center
		
		if self.type == 'pocket':
			#create annular rings for pocketed hole type
			tool_overlap = .1
			effective_tool_diameter = tool_diameter* (1-tool_overlap)
			annular_ring_quantity = int(toolpath_radius/effective_tool_diameter)
			if annular_ring_quantity == 0:
				annular_ring_quantity = 1 #dont use too big of a tool
			annular_rings=[]
			for i in range(1, annular_ring_quantity+1):
				annular_rings.append(effective_tool_diameter*(i-.5))
			if annular_rings[-1] < toolpath_radius:
				annular_rings.append(toolpath_radius)

			#positioning and setup
			gcode.append(f'F{feed}')#use same feed rate throughout
			gcode.append(f'S{speed}')
			gcode.append(f'G0 Z{retract_height}')#go to safe z height
			gcode.append(f'G0 X{x_center} Y{y_center}')#go to hole center
		
			for i in z_heights:
				for j in annular_rings:
					gcode.append(f'G1 X{x_center} Y{y_center+j} Z{i}')
					gcode.append(f'G3 X{x_center} Y{y_center+j} Z{i} J{j*-1}')#travel circumference, down z layer height
			
			gcode.append(f'G0 Z{retract_height}')#retract height
			#gcode.append(f'G0 X{x_center} Y{y_center}')#hole center

		return(gcode)

class RectHolePattern:
	def __init__(self, frame, instance_count):
		self.frame 			= frame
		self.instance_count 			= instance_count
		self.types 					= ['perimeter','pocket']
		self.type 			= ''
		self.x_center_start 	= 0
		self.y_center_start 	= 0
		self.xspacing 		= 0
		self.yspacing 		= 0
		self.xquant 		= 0
		self.yquant 		= 0
		self.hole_diameter 	= 0
		self.depth 			= 0
		self.create_entries()
		
	def create_entries(self):
		self.x_center_start_var 		= tk.StringVar()
		self.y_center_start_var 		= tk.StringVar()
		self.xspacing_var 			= tk.StringVar()
		self.yspacing_var 			= tk.StringVar()
		self.xquant_var 			= tk.StringVar()
		self.yquant_var 			= tk.StringVar()
		self.diam_var 				= tk.StringVar()
		self.depth_var 				= tk.StringVar()
		self.type_spin_box_var 		= tk.StringVar()
		

		self.type_spin_box			= tk.Spinbox(self.frame, values = self.types,textvariable=self.type_spin_box_var, width=10)
		self.x_center_start_entry 	= tk.Entry(self.frame, textvariable=self.x_center_start_var, width=7)
		self.y_center_start_entry 	= tk.Entry(self.frame, textvariable=self.y_center_start_var, width=7)
		self.xspacing_entry 		= tk.Entry(self.frame, textvariable=self.xspacing_var, width=7)
		self.yspacing_entry 		= tk.Entry(self.frame, textvariable=self.yspacing_var, width=7)
		self.xquant_entry 			= tk.Entry(self.frame, textvariable=self.xquant_var, width=7)
		self.yquant_entry 			= tk.Entry(self.frame, textvariable=self.yquant_var, width=7)
		self.diam_entry 			= tk.Entry(self.frame, textvariable=self.diam_var, width=7)
		self.depth_entry 			= tk.Entry(self.frame, textvariable=self.depth_var, width=7)
		
		self.type_spin_box			.grid(row=self.instance_count, column=0)
		self.x_center_start_entry 	.grid(row=self.instance_count, column=1)
		self.y_center_start_entry 	.grid(row=self.instance_count, column=2)
		self.xspacing_entry 		.grid(row=self.instance_count, column=3)
		self.yspacing_entry 		.grid(row=self.instance_count, column=4)
		self.xquant_entry 			.grid(row=self.instance_count, column=5)
		self.yquant_entry 			.grid(row=self.instance_count, column=6)
		self.diam_entry 			.grid(row=self.instance_count, column=7)
		self.depth_entry 			.grid(row=self.instance_count, column=8)
		
	def destroy_entries(self):
		self.type_spin_box			.destroy()
		self.x_center_start_entry 	.destroy()
		self.y_center_start_entry 	.destroy()
		self.xspacing_entry 		.destroy()
		self.yspacing_entry 		.destroy()
		self.xquant_entry 			.destroy()
		self.yquant_entry 			.destroy()
		self.diam_entry 			.destroy()
		self.depth_entry 			.destroy()
		
	def update_variables(self):
		self.type 			= self.type_spin_box_var.get()
		self.x_center_start 	= float(self.x_center_start_var.get())
		self.y_center_start 	= float(self.y_center_start_var.get())
		self.xspacing 		= float(self.xspacing_var.get())
		self.yspacing 		= float(self.yspacing_var.get())
		self.xquant 		= int(self.xquant_var.get())
		self.yquant 		= int(self.yquant_var.get())
		self.hole_diameter 	= float(self.diam_var.get())
		self.depth 			= float(self.depth_var.get())
		
	def create_gcode(self, settings):
		gcode = []
		tool_diameter 		= settings['tool_diameter']
		depth_of_cut 		= settings['depth_of_cut']
		speed 				= settings['speed']
		feed 				= settings['feed']
		retract_height 		= settings['retract_height']
		unit_precision 		= settings['unit_precision']
		
		self.update_variables()
		
		toolpath_od = self.hole_diameter - tool_diameter
		toolpath_radius = toolpath_od/2
		
		#generate all of the layer z height values for 2.5d milling
		z_height_passes=[] 
		number_z_height_passes = self.depth/depth_of_cut
		
		for i in range(int(number_z_height_passes)):
			zheight = (i+1) * depth_of_cut * -1
			z_height_passes.append(zheight)
		
		if zheight > self.depth * -1:
			z_height_passes.append(self.depth * -1)
			
		#create annular rings for pocketed hole type
		tool_overlap = .1
		effective_tool_diameter = tool_diameter* (1-tool_overlap)
		annular_ring_quantity = int(toolpath_radius/effective_tool_diameter)
		if annular_ring_quantity == 0: annular_ring_quantity = 1 #dont use too big of a tool
		
		annular_rings=[]
		for i in range(1, annular_ring_quantity+1):
			annular_rings.append(effective_tool_diameter*(i-.5))
		if annular_rings[-1] < toolpath_radius:
			annular_rings.append(toolpath_radius)
					
		#Gcode time
		if self.type == 'perimeter':
			#positioning and setup
			gcode.append('F{}'.format(feed))#use same feed rate throughout
			gcode.append('S{}'.format(speed))
			
			for i in range(self.xquant):
				x_center = self.x_center_start + (i*self.xspacing)
				
				for j in range(self.yquant):
					y_center = self.y_center_start + (j*self.yspacing)
				
					gcode.append('G0 Z{}'.format(round(retract_height, unit_precision)))#go to safe z height
					gcode.append('G0 X{} Y{}'.format(round(x_center, unit_precision), round(y_center, unit_precision)))    #go to hole center
					gcode.append('G1 X{} Y{} Z0'.format(round(x_center+toolpath_radius, unit_precision), round(y_center, unit_precision),round(i, unit_precision)))#go to hole starting point
					
					#generate and append helical arcs
					for i in z_height_passes:
						gcode.append('G3 X{} Y{} Z{} I{}'.format(round(x_center+toolpath_radius, unit_precision), round(y_center, unit_precision),round(i, unit_precision), round(-toolpath_radius, unit_precision)))#travel circumference, down z layer height
						gcode.append('G1 X{} Y{} Z{}'.format(round(x_center+toolpath_radius, unit_precision), round(y_center, unit_precision),round(i, unit_precision)))#no move but tell machine we are back at starting point

					gcode.append('G3 X{} Y{} Z{} I{}'.format(round(x_center+toolpath_radius, unit_precision), round(y_center, unit_precision),round(i, unit_precision), round(-toolpath_radius, unit_precision)))#bottom of hole
					gcode.append('G1 X{} Y{} Z{}'.format(round(x_center+toolpath_radius, unit_precision), round(y_center, unit_precision),round(i, unit_precision)))#no move but tell machine we are back at starting point
					gcode.append('G0 Z{}'.format(round(retract_height, unit_precision)))#retract height
					gcode.append('G0 X{} Y{}'.format(round(x_center, unit_precision), round(y_center, unit_precision)))#hole center
		
		if self.type == 'pocket':
			#positioning and setup
			gcode.append('F{}'.format(feed))#use same feed rate throughout
			gcode.append('S{}'.format(speed))
			
			for i in range(self.xquant):
				x_center = self.x_center_start + (i*self.xspacing)
				
				for j in range(self.yquant):
					y_center = self.y_center_start + (j*self.yspacing)
					
					gcode.append('G0 Z{}'.format(round(retract_height, unit_precision)))#go to safe z height
					gcode.append('G0 X{} Y{}'.format(round(x_center, unit_precision), round(y_center, unit_precision)))    #go to hole center
				
					for i in z_height_passes:
						for j in annular_rings:
							gcode.append('G1 X{} Y{} Z{}'.format(round(x_center, unit_precision), round(y_center+j, unit_precision),i))
							gcode.append('G3 X{} Y{} J{}'.format(round(x_center, unit_precision), round(y_center+j, unit_precision),round(j*-1, unit_precision)))#travel circumference, down z layer height
					
					gcode.append('G0 Z{}'.format(round(retract_height, unit_precision)))#retract height
					gcode.append('G0 X{} Y{}'.format(round(x_center, unit_precision), round(y_center, unit_precision)))#hole center


		return(gcode)
	
class CornerRectangle:
	def __init__(self,frame,instance_count):
		self.frame 				= frame
		self.instance_count 	= instance_count
		self.types 				= ['perimeter','pocket']
		self.sides 				= ['inside','outside']
		self.side 				= ''
		self.type 				= ''
		self.x1 				= 0
		self.y1 				= 0
		self.x2 				= 0
		self.y2 				= 0
		self.depth 				= 0
		self.create_entries()
		
	def create_entries(self):
		self.x1_var 			= tk.DoubleVar()
		self.y1_var 			= tk.DoubleVar()
		self.x2_var 			= tk.DoubleVar()
		self.y2_var 			= tk.DoubleVar()
		self.depth_var 			= tk.DoubleVar()
		self.side_spin_box_var 	= tk.StringVar()
		self.type_spin_box_var 	= tk.StringVar()
		
		self.side_spin_box 		= tk.Spinbox(self.frame, values=self.sides, textvariable=self.side_spin_box_var, width=9)
		self.type_spin_box 		= tk.Spinbox(self.frame, values=self.types, textvariable=self.type_spin_box_var, width=9)
		self.x1_entry 			= tk.Entry(self.frame, textvariable=self.x1_var, width=9)
		self.y1_entry 			= tk.Entry(self.frame, textvariable=self.y1_var, width=9)
		self.x2_entry 			= tk.Entry(self.frame, textvariable=self.x2_var, width=9)
		self.y2_entry 			= tk.Entry(self.frame, textvariable=self.y2_var, width=9)
		self.depth_entry 		= tk.Entry(self.frame, textvariable=self.depth_var, width=9)

		self.side_spin_box		.grid(row=self.instance_count, column=0)
		self.type_spin_box		.grid(row=self.instance_count, column=1)
		self.x1_entry			.grid(row=self.instance_count, column=2)
		self.y1_entry			.grid(row=self.instance_count, column=3)
		self.x2_entry			.grid(row=self.instance_count, column=4)
		self.y2_entry			.grid(row=self.instance_count, column=5)
		self.depth_entry		.grid(row=self.instance_count, column=6)
		
	def destroy_entries(self):
		self.side_spin_box.destroy()
		self.type_spin_box.destroy()
		self.x1_entry.destroy()
		self.y1_entry.destroy()
		self.x2_entry.destroy()
		self.y2_entry.destroy()
		self.depth_entry.destroy()
		
	def update_variables(self):
		self.side = self.side_spin_box.get()
		self.type = self.type_spin_box.get()
		self.x1 = self.x1_var.get()
		self.y1 = self.y1_var.get()
		self.x2 = self.x2_var.get()
		self.y2 = self.y2_var.get()
		self.depth = self.depth_var.get()
	
	def data_export(self):
		self.update_variables()
		x1 = self.x1 
		y1 = self.y1
		x2 = self.x2 
		y2 = self.y2
		depth = self.depth
		type = self.type
		side = self.side
		return('{},{},{},{},{},{},{}'.format(x1,y1,x2,y2,depth,type,side))

	
	def create_gcode(self, settings):
		gcode = []
		tool_diameter 	= settings['tool_diameter']
		depth_of_cut 	= settings['depth_of_cut']
		speed 			= settings['speed']
		feed 			= settings['feed']
		retract_height 	= settings['retract_height']
		unit_precision 	= settings['unit_precision']
		
		self.update_variables()
		
		x_center = (self.x2 - self.x1) / 2 + self.x1
		y_center = (self.y2 - self.y1) / 2 + self.y1

		if self.side =='outside': #cutter on inside of profile
			max_toolpath_x = x_center + abs((self.x2 - self.x1) / 2) + tool_diameter/2
			min_toolpath_x = x_center - abs((self.x2 - self.x1) / 2) - tool_diameter/2
			max_toolpath_y = y_center + abs((self.y2 - self.y1) / 2) + tool_diameter/2
			min_toolpath_y = y_center - abs((self.y2 - self.y1) / 2) - tool_diameter/2
		
		elif self.side =='inside': #cutter on outside of profile
			max_toolpath_x = x_center + abs((self.x2 - self.x1) / 2) - tool_diameter/2
			min_toolpath_x = x_center - abs((self.x2 - self.x1) / 2) + tool_diameter/2
			max_toolpath_y = y_center + abs((self.y2 - self.y1) / 2) - tool_diameter/2
			min_toolpath_y = y_center - abs((self.y2 - self.y1) / 2) + tool_diameter/2
		
		x_center = round(x_center, unit_precision)
		y_center = round(y_center, unit_precision)
		max_toolpath_x = round(max_toolpath_x, unit_precision)
		min_toolpath_x = round(min_toolpath_x, unit_precision)
		max_toolpath_y = round(max_toolpath_y, unit_precision)
		min_toolpath_y = round(min_toolpath_y, unit_precision)
		
		#generate all of the layer z height values for 2.5d milling
		z_heights=z_height_passes(self.depth,depth_of_cut,unit_precision)

		if self.type == 'perimeter':
			#positioning and setup
			gcode.append(f'F{feed}') #use same feed rate throughout
			gcode.append(f'S{speed}')
			gcode.append(f'G0 Z{retract_height}') #go to safe z height
			gcode.append(f'G1 X{min_toolpath_x} Y{min_toolpath_y}') #go to xmin ymin
			
			#generate and append perimeter pass at each z_height_pass
			for i in z_heights:
				gcode.append(f'G1 X{min_toolpath_x} Y{max_toolpath_y} Z{i}') #xmin ymax plunge here
				gcode.append(f'G1 X{max_toolpath_x} Y{max_toolpath_y}') #xmax ymax
				gcode.append(f'G1 X{max_toolpath_x} Y{min_toolpath_y}') #xmax ymin
				gcode.append(f'G1 X{min_toolpath_x} Y{min_toolpath_y}') #xmin ymin
				
			gcode.append(f'G1 X{min_toolpath_x} Y{max_toolpath_y}') #xmin ymax
			gcode.append(f'G0 Z{retract_height}')
			#gcode.append(f'G0 X{x_center} Y{y_center}') #go to center
			
		if self.type == 'pocket':
			tool_overlap_pct = .1
			eff_tool_D = tool_diameter * (1-tool_overlap_pct) #effective tool diameter
			y_stripes = []
			num_y_stripes = int((max_toolpath_x - min_toolpath_x)/eff_tool_D)
			y_stripes.append(min_toolpath_x)
			
			for i in range(num_y_stripes):
				y_stripes.append(round(min_toolpath_x + (i+1)*eff_tool_D,unit_precision))
			
			if (min_toolpath_x + (i+1)*eff_tool_D) < (max_toolpath_x - eff_tool_D):
				y_stripes.append(round(max_toolpath_x - eff_tool_D,unit_precision))
			
			y_stripes.append(max_toolpath_x)
			
			gcode.append(f'F{feed}') #use same feed rate throughout
			gcode.append(f'S{speed}')
			gcode.append(f'G0 Z{retract_height}') #go to safe z height
			gcode.append(f'G0 X{min_toolpath_x} Y{min_toolpath_y} F{feed}')
			
			first_pass = 1
			for i in z_heights:
				if first_pass:
					gcode.append(f'G1 X{y_stripes[0]} Y{min_toolpath_y} F{feed}')
					gcode.append(f'G1 X{y_stripes[0]} Y{max_toolpath_y} Z{i} F{feed}')
					first_pass = 0
				else: 
					gcode.append(f'G1 X{y_stripes[0]} Y{min_toolpath_y} Z{i} F{feed}')
					gcode.append(f'G1 X{y_stripes[0]} Y{max_toolpath_y} F{feed}')

				gcode.append(f'G1 X{y_stripes[-1]} Y{max_toolpath_y} F{feed}')
				gcode.append(f'G1 X{y_stripes[-1]} Y{min_toolpath_y} F{feed}')
				gcode.append(f'G1 X{y_stripes[0]} Y{min_toolpath_y} F{feed}')
				
				at_ymin = True
				
				for j in y_stripes:
					if (not at_ymin): 
						gcode.append(f'G1 X{j} Y{min_toolpath_y} F{feed}')
						at_ymin = True
					else:
						gcode.append(f'G1 X{j} Y{max_toolpath_y} F{feed}')
						at_ymin = False
		
					if (y_stripes.index(j) < len(y_stripes)-1): #are we not at the last element in the list?
						gcode.append(f'G1 X{y_stripes[y_stripes.index(j)+1]} F{feed}')
					 
				gcode.append(f'G1 Y{min_toolpath_y} F{feed}')
			gcode.append(f'G0 Z{retract_height}')
			
		return(gcode)

class Polygon:
	def __init__(self, frame, instance_count):
		self.frame = frame
		self.instance_count = instance_count
		self.types = ['outside','inside']
		self.create_entries()
		
	def create_entries(self):
		self.points_var 		= tk.StringVar()
		self.depth_var 			= tk.StringVar()
		self.type_spin_box_var 	= tk.StringVar()
		
		self.points_entry 		= tk.Entry(self.frame, textvariable=self.points_var, width=50)
		self.depth_entry		= tk.Entry(self.frame, textvariable=self.depth_var, width=10)
		self.type_spin_box		= tk.Spinbox(self.frame, values = self.types,textvariable=self.type_spin_box_var, width=10)
		
		self.type_spin_box		.grid(row=self.instance_count, column=0)
		self.points_entry 		.grid(row=self.instance_count, column=1)
		self.depth_entry 		.grid(row=self.instance_count, column=2)
		
	def destroy_entries(self):
		self.type_spin_box.destroy()
		self.points_entry.destroy()
		self.depth_entry.destroy()
		
	def pnpoly(self, nvert, vertx, verty, testx, testy):
		#test for point in polygon 
		#https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html
		#nvert 	Number of vertices in the polygon.
		#vertx, verty 	Arrays containing the x- and y-coordinates of the polygon's vertices. 
		#testx, testy	X- and y-coordinate of the test point. 
		c = False
		i = 0
		j = nvert-1
		
		for i in range(nvert):
			if ((verty[i]>testy) != (verty[j]>testy)) and (testx < (vertx[j]-vertx[i]) * (testy-verty[i]) / (verty[j]-verty[i]) + vertx[i]):
				c = not c
			j = i
			i=i+1
		return c
		
	def process_points(self, point_list): #takes a list of (X,Y) tuples, returns 'point_data'
		'''
		data is stored centric to each point:
		point_data=[[point, left unit vector, right unit vector, inside unit bisector vector, magnitude of inside angle], ...]
		point_data=[[(X,Y),(X_luv,Y_luv),(X_ruv,Y_ruv),(X_ins_bis,Y_ins_bis),inside_angle], ...]
		
		'left' and 'right' unit vectors at a vertex and two sides
		the inside unit vector always points to the inside of the polygon
		
	    Ins.Unit	^       	b			point 'b' is < Pi radians inside angle
		Bisector^   | R.U.V.	|\    /|
				 \  |			| \  / |
				  \ |			|  \/  |
			 <------o point		|  a   |	point 'a' is > Pi radians inside angle
			 L.U.V.				|______|
		'''

		point_data=[]
	
		for index,point in enumerate(point_list):
			x = point[0]
			y = point[1]
			
			#form unit vector pointing to previous ('left') point
			if index == 0: #first case is special becasue of wrap around
				prev_x = point_list[-1][0]
				prev_y = point_list[-1][1]
			else:
				prev_x = point_list[index-1][0]
				prev_y = point_list[index-1][1]
				
			left_vector = (prev_x - x, prev_y - y)
			mag_left_vector = math.sqrt(left_vector[0]**2 + left_vector[1]**2)
			unit_left_vector = (left_vector[0]/mag_left_vector, left_vector[1]/mag_left_vector)
			
			
			#form unit vector pointing to next ('right') point
			if index == len(point_list)-1: #last case is special becasue of wrap around
				next_x = point_list[0][0]
				next_y = point_list[0][1]
			else:
				next_x = point_list[index+1][0]
				next_y = point_list[index+1][1]
				
			right_vector = (next_x-x, next_y-y)
			mag_right_vector = math.sqrt(right_vector[0]**2 + right_vector[1]**2)
			unit_right_vector = (right_vector[0]/mag_right_vector, right_vector[1]/mag_right_vector)
			
			
			#find the unit bisector between left vector and right vector 
			bisector = ( unit_left_vector[0] + unit_right_vector[0], unit_left_vector[1] + unit_right_vector[1])
			mag_bisector = math.sqrt(bisector[0]**2 + bisector[1]**2)
			unit_bisector = (bisector[0]/mag_bisector, bisector[1]/mag_bisector)
			
			#if the unit bisector is not pointing inside the polygon, flip it around. 
			#Find the inside angle in radians.
			scale = .01 
			scaled_bisector = (unit_bisector[0]*scale, unit_bisector[1]*scale)
			testx = x + scaled_bisector[0]
			testy = y + scaled_bisector[1]
			vertx, verty = zip(*point_list)
			point_inside = self.pnpoly(len(vertx), vertx, verty, testx, testy)
			
			if point_inside:
				inside_unit_bisector = unit_bisector
				#angle between two vectors = acos(A dot B)
				inside_angle = math.acos(unit_left_vector[0]*unit_right_vector[0] + unit_left_vector[1]*unit_right_vector[1])
			else:
				inside_unit_bisector = (unit_bisector[0]*-1, unit_bisector[1]*-1)
				inside_angle = 2*math.pi - math.acos(unit_left_vector[0]*unit_right_vector[0] + unit_left_vector[1]*unit_right_vector[1])
			
			point_data.append([point, unit_left_vector, unit_right_vector, inside_unit_bisector, inside_angle])
			
		return point_data
		
	def polygon_is_clockwise(self, point_data):
		#https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
		sum=0
		#[(0, 0), (0, 1), (0.7, 0.7), (0.3, 0.9), 0.78],...]
		points= [i[0] for i in point_data] #x,y points extracted from point_data
		#print(points)
		for index, point in enumerate(points):
			if index == len(points)-1: #last point is special; wrap around to first point
				x_val_current = points[index][0]
				y_val_current = points[index][1]
				x_val_next = points[0][0]
				y_val_next = points[0][1]
			else:
				x_val_current = points[index][0]
				y_val_current = points[index][1]
				x_val_next = points[index+1][0]
				y_val_next = points[index+1][1]
			
			sum += (x_val_next-x_val_current)*(y_val_next+y_val_current)
		
		if sum >=0: return(True)
		else: return(False)
				
	def InsetPoints (self, point_data, inset):
		pass
		
	def outset_points (self, point_data, offset):
		#point_data=[[(X,Y),(X_luv,Y_luv),(X_ruv,Y_ruv),(X_ins_bis,Y_ins_bis),inside_angle], ...]
		#note that the inside bisector is unit length
		outset_points = []
		#print(point_data)
		clockwise_polygon = self.polygon_is_clockwise(point_data)
		
		for point in point_data:
			#is the inside angle less than pi radians or 180 deg? This is a 'convex' corner of the polygon.
			#an offset needs to arc around the sharp point.
			
			if point[4] < math.pi: 
				#if we are moving around the polygon clockwise, 
				#the left unit vector needs to be outset by a distance along a clockwise 90deg rotation of the L.U.V.
				arc_center = point[0]
				
				if clockwise_polygon:
					#clockwise rotation: (x,y)->(y,-x)
					#counter clockwise rotation: (x,y)->(-y,x)
					rv_90deg_ccw = (-1*point[2][1], point[2][0])
					lv_90deg_cw = (point[1][1] , -1*point[1][0])
					mag_rv_90deg_ccw = math.sqrt(rv_90deg_ccw[0]**2 + rv_90deg_ccw[1]**2)
					mag_lv_90deg_cw = math.sqrt(lv_90deg_cw[0]**2 + lv_90deg_cw[1]**2)
					unit_rv_90deg_ccw = (rv_90deg_ccw[0]/mag_rv_90deg_ccw, rv_90deg_ccw[1]/mag_rv_90deg_ccw)
					unit_lv_90deg_cw = (lv_90deg_cw[0]/mag_lv_90deg_cw, lv_90deg_cw[1]/mag_lv_90deg_cw)
					
					arc_start = (unit_rv_90deg_ccw[0]*offset+arc_center[0],unit_rv_90deg_ccw[1]*offset+arc_center[1]) 
					arc_end = (unit_lv_90deg_cw[0]*offset+arc_center[0],unit_lv_90deg_cw[1]*offset+arc_center[1]) 
					
					arc = ('cw', arc_start, arc_center, arc_end)
					# print(arc[1][0],',',arc[1][1])
					# print(arc[2][0],',',arc[2][1])
					# print(arc[3][0],',',arc[3][1])
					outset_points.append(arc)
					
				else:
					#clockwise rotation: (x,y)->(y,-x)
					#counter clockwise rotation: (x,y)->(-y,x)
					rv_90deg_ccw = (point[2][1], -1*point[2][0])
					lv_90deg_cw = (-1*point[1][1] , point[1][0])
					mag_rv_90deg_ccw = math.sqrt(rv_90deg_ccw[0]**2 + rv_90deg_ccw[1]**2)
					mag_lv_90deg_cw = math.sqrt(lv_90deg_cw[0]**2 + lv_90deg_cw[1]**2)
					unit_rv_90deg_ccw = (rv_90deg_ccw[0]/mag_rv_90deg_ccw, rv_90deg_ccw[1]/mag_rv_90deg_ccw)
					unit_lv_90deg_cw = (lv_90deg_cw[0]/mag_lv_90deg_cw, lv_90deg_cw[1]/mag_lv_90deg_cw)
					
					arc_start = (unit_rv_90deg_ccw[0]*offset+arc_center[0],unit_rv_90deg_ccw[1]*offset+arc_center[1]) 
					arc_end = (unit_lv_90deg_cw[0]*offset+arc_center[0],unit_lv_90deg_cw[1]*offset+arc_center[1]) 
					
					arc = ('ccw', arc_start, arc_center, arc_end)
					# print(arc[1][0],',',arc[1][1])
					# print(arc[2][0],',',arc[2][1])
					# print(arc[3][0],',',arc[3][1])
					outset_points.append(arc)
					
			else:
				x= point[0][0]
				y=point[0][1]
				unit_bis_inside = point[3]
				offset_point = (-1*unit_bis_inside[0]*offset + x, -1*unit_bis_inside[1]*offset+ y)
				# print(offset_point[0],',',offset_point[1])
				outset_points.append(('pt', offset_point))
		return(outset_points)
			
	def update_variables(self):
		self.type 			= self.type_spin_box.get()
		self.points 		= self.points_entry.get()
		self.depth 			= float(self.depth_entry.get())

	def create_gcode(self, settings):
		gcode = []
		tool_diameter 		= settings['tool_diameter']
		depth_of_cut 		= settings['depth_of_cut']
		speed 				= settings['speed']
		feed 				= settings['feed']
		retract_height 		= settings['retract_height']
		unit_precision 		= settings['unit_precision']
		
		self.update_variables()
		
		parsed_points = self.parse_points_input(self.points)
		if self.type == 'outside':
			points = self.outset_points(parsed_points,tool_diameter/2)
		elif self.type == 'inside':
			pass

		#generate all of the layer z height values for 2.5d milling
		z_height_passes=[] 
		number_z_height_passes = self.depth/depth_of_cut
		
		for i in range(int(number_z_height_passes)):
			zheight = (i+1) * depth_of_cut * -1
			z_height_passes.append(zheight)
		
		if zheight > self.depth * -1:
			z_height_passes.append(self.depth * -1)
		
		gcode.append('F{}'.format(feed))#use same feed rate throughout
		gcode.append('S{}'.format(speed))
		gcode.append('G0 Z{}'.format(round(retract_height, unit_precision)))#go to safe z height

		# points[i][0] #cw/ccw
		# points[i][1][0] #arc start x 
		# points[i][1][1] #arc start y
		# points[i][2][0] #vertex x 
		# points[i][2][1] #vertex y
		# points[i][3][0] #arc end x 
		# points[i][3][1] #arc end y

		if points[0][0] =='pt': #inside corner single point
			first_center_x = points[0][1][0]
			first_center_y = points[0][1][1]
		else: #these are outside corner arc moves (cw or ccw)
			first_center_x = points[0][2][0]
			first_center_y = points[0][2][1]

		gcode.append('G0 X{} Y{}'.format(round(first_center_x, unit_precision), round(first_center_y, unit_precision)  ) )    #go to first vertex
		
		for i in z_height_passes:
			for j, k in enumerate(points): #points is list of tuples
				if points[j][0] == 'cw':
					cw_ccw = 'G2'

					arc_start_x  	= round(points[j][3][0], unit_precision)
					arc_start_y  	= round(points[j][3][1], unit_precision)
					center_x 		= round(points[j][2][0], unit_precision)
					center_y 		= round(points[j][2][1], unit_precision)
					arc_end_x  		= round(points[j][1][0], unit_precision)
					arc_end_y  		= round(points[j][1][1], unit_precision)
					i_dist 			= round(center_x - arc_start_x, unit_precision)
					j_dist 			= round(center_y - arc_start_y, unit_precision)

					gcode.append('G1 X{} Y{} Z{}'.format(arc_start_x, arc_start_y,round(i, unit_precision))) #redundant move to start position
					gcode.append('{} X{} y{} I{} J{}'.format(cw_ccw, arc_end_x, arc_end_y, i_dist, j_dist))
					gcode.append('G1 X{} Y{} Z{}'.format(arc_end_x, arc_end_y,round(i, unit_precision))) #redundant move to end position
				
				elif points[j][0] == 'ccw':
					cw_ccw = 'G3'
					arc_start_x  	= round(points[j][3][0], unit_precision)
					arc_start_y  	= round(points[j][3][1], unit_precision)
					center_x 		= round(points[j][2][0], unit_precision)
					center_y 		= round(points[j][2][1], unit_precision)
					arc_end_x  		= round(points[j][1][0], unit_precision)
					arc_end_y  		= round(points[j][1][1], unit_precision)
					i_dist 			= round(center_x - arc_start_x, unit_precision)
					j_dist 			= round(center_y - arc_start_y, unit_precision)

					gcode.append('G1 X{} Y{} Z{}'.format(arc_start_x, arc_start_y,round(i, unit_precision))) #redundant move to start position
					gcode.append('{} X{} y{} I{} J{}'.format(cw_ccw, arc_end_x, arc_end_y, i_dist, j_dist))
					gcode.append('G1 X{} Y{} Z{}'.format(arc_end_x, arc_end_y,round(i, unit_precision))) #redundant move to end position

				elif points[j][0] == 'pt': #inside corner, no arc just a single point
					pt_x = round(points[j][1][0], unit_precision)
					pt_y = round(points[j][1][1], unit_precision)

					gcode.append('G1 X{} Y{} Z{}'.format(pt_x, pt_y,round(i, unit_precision))) #redundant move to start position
		return(gcode)
		
	
	def test(self):
		pass
		# parsed_points = self.parse_points_input()
		# self.outset_points(parsed_points)

	def parse_points_input(self, input_string):
		#takes '(0,0),(4,0),(3,3),...'
		try:
			points_string = input_string[1:-1].split('),(')
			points_split=[i.split(',') for i in points_string]
			input_points = [(float(i[0]), float(i[1])) for i in points_split]
			return(self.process_points(input_points))

		except Exception as e:
			print('error parsing string input')
			print(e)
			
class Conn: #cutouts for connectors, special shapes, etc.
	def __init__(self, frame, instance_count):
		self.frame					=frame
		self.instance_count 		= instance_count
		self.types 					= ['dogbone','D','doubleD','DE']
		self.type 					= ''
		self.x_center 				= 0 #variable usage depending on type selected
		self.y_center 				= 0 #dogbone: a=width, b=height; d|dd:a=diam,b=flat dist; dsubs: N/A
		self.a_dim					= 0
		self.b_dim					= 0
		self.rotation				= 0
		self.depth					= 0
		self.create_entries()
	
	def create_entries(self):
		self.x_center_var 		= tk.DoubleVar()
		self.y_center_var 		= tk.DoubleVar()
		self.a_dim_var 			= tk.DoubleVar() #variable usage depending on type selected
		self.b_dim_var 			= tk.DoubleVar() #dogbone: a=width, b=height; d|dd:a=diam,b=flat dist; dsubs: N/A
		self.depth_var 			= tk.DoubleVar()
		self.rotation_var 		= tk.DoubleVar()
		self.type_spin_box_var	= tk.StringVar()
		
		self.x_center_entry 	= tk.Entry(self.frame, textvariable=self.x_center_var, width=9)
		self.y_center_entry 	= tk.Entry(self.frame, textvariable=self.y_center_var, width=9)
		self.a_dim_entry 		= tk.Entry(self.frame, textvariable=self.a_dim_var, width=9)
		self.b_dim_entry 		= tk.Entry(self.frame, textvariable=self.b_dim_var, width=9)
		self.rotation_entry		= tk.Entry(self.frame, textvariable=self.rotation_var, width=9)
		self.depth_entry		= tk.Entry(self.frame, textvariable=self.depth_var, width=9)
		self.type_spin_box		= tk.Spinbox(self.frame, values=self.types,textvariable=self.type_spin_box_var, width=10)
		
		self.type_spin_box		.grid(row=self.instance_count, column=0)
		self.x_center_entry 	.grid(row=self.instance_count, column=1)
		self.y_center_entry 	.grid(row=self.instance_count, column=2)
		self.a_dim_entry 		.grid(row=self.instance_count, column=3)
		self.b_dim_entry 		.grid(row=self.instance_count, column=4)
		self.rotation_entry 	.grid(row=self.instance_count, column=5)
		self.depth_entry 		.grid(row=self.instance_count, column=6)
		
		
	def destroy_entries(self):
		self.x_center_entry.destroy()
		self.y_center_entry.destroy()
		self.a_dim_entry.destroy()
		self.b_dim_entry.destroy()
		self.rotation_entry.destroy()
		self.depth_entry.destroy()
		self.type_spin_box.destroy()

	def update_variables(self):
		self.x_center 			= self.x_center_var.get()
		self.y_center 			= self.y_center_var.get()
		self.a_dim 				= self.a_dim_var.get()
		self.b_dim 				= self.b_dim_var.get()
		self.rotation 			= self.rotation_var.get()
		self.depth 				= self.depth_var.get()
		self.type		 		= self.type_spin_box_var.get()

	def data_export(self):
		self.update_variables()
		x = self.x_center
		y = self.y_center
		a = self.a_dim
		b = self.b_dim
		rotation = self.rotation
		depth = self.depth
		type = self.type
		return(f'{x},{y},{a},{b},{rotation},{depth},{type}')

	def create_gcode(self, settings):
		gcode = []
		tool_diameter 		= settings['tool_diameter']
		depth_of_cut 		= settings['depth_of_cut']
		speed 				= settings['speed']
		feed 				= settings['feed']
		retract_height 		= settings['retract_height']
		unit_precision 		= settings['unit_precision']
		
		self.update_variables()

		retract_height = round(retract_height,unit_precision)
		x_center = round(self.x_center,unit_precision)
		y_center = round(self.y_center,unit_precision)
		a = self.a_dim
		b = self.b_dim
		tool_radius = tool_diameter/2
		rotation = self.rotation
		depth = self.depth
		type = self.type
		
		#generate all of the layer z height values for 2.5d milling
		z_heights=z_height_passes(depth,depth_of_cut,unit_precision) 

		#calc x,y points for 'D' and 'doubleD' shaped cutouts
		diameter = a
		flat_width = b
		x = flat_width/2 - tool_radius
		y = math.sqrt((diameter/2)**2 - x**2) - tool_radius #this is approximate FIXME

		x_max = round(x_center+x,unit_precision)
		x_min = round(x_center-x,unit_precision)
		y_max = round(y_center+y,unit_precision)
		y_min = round(y_center-y,unit_precision)
		
		#Gcode time
		if self.type == 'D':
			#positioning and setup
			gcode.append(f'F{feed}')#use same feed rate throughout
			gcode.append(f'S{speed}')
			gcode.append(f'G0 Z{retract_height}')#go to safe z height
			gcode.append(f'G0 X{x_center} Y{y_center}')    #go to center
			gcode.append(f'G1 X{x_min} Y{y_max} Z0') #go to lower right point
			
			#generate and append perimeter passes
			for i in z_heights:
				gcode.append(f'G1 X{x_min} Y{y_min} Z{i}')#go to upper right point
				gcode.append(f'G3 X{x_min} Y{y_max} I{round(x_center - x_min,unit_precision)} J{round(y_center - y_min,unit_precision)}')#go to upper left point
				gcode.append(f'G1 X{x_min} Y{y_max}')#go to lower left point
			
			gcode.append(f'G1 X{x_min} Y{y_min}')#go to upper right point
			gcode.append(f'G0 Z{retract_height}')#go to safe z height

		if self.type == 'doubleD':
			#positioning and setup
			gcode.append(f'F{feed}')#use same feed rate throughout
			gcode.append(f'S{speed}')
			gcode.append(f'G0 Z{retract_height}')#go to safe z height
			gcode.append(f'G0 X{x_center} Y{y_center}')    #go to center
			gcode.append(f'G1 X{x_max} Y{y_min} Z0') #go to lower right point
			
			#generate and append perimeter passes
			for i in z_heights:
				gcode.append(f'G1 X{x_max} Y{y_max} Z{i}')#go to upper right point
				gcode.append(f'G3 X{x_min} Y{y_max} I{round(x_center - x_max,unit_precision)} J{round(y_center - y_max,unit_precision)}')#go to upper left point
				gcode.append(f'G1 X{x_min} Y{y_min}')#go to lower left point
				gcode.append(f'G3 X{x_max} Y{y_min} I{round(x_center - x_min,unit_precision)} J{round(y_center - y_min,unit_precision)}')#go to lower right point
			
			gcode.append(f'G1 X{x_max} Y{y_max}')#go to upper right point
			gcode.append(f'G0 Z{retract_height}')#go to safe z height
		return(gcode)
