# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 10:48:22 2021

@author: lakri
"""
import numpy as np
import vtk
from vtk.numpy_interface import dataset_adapter as dsa
from models.layers.mesh_prepare import *

filename = 'datasets/LAA_segmentation/0003.vtk'

reader = vtk.vtkPolyDataReader()
reader.SetFileName(filename)
reader.ReadAllScalarsOn()
reader.Update()
data = reader.GetOutput()

points = np.array( reader.GetOutput().GetPoints().GetData() )

print(data.GetCellData().GetScalars())

label = np.array( data.GetCellData().GetScalars() )

numpy_array_of_points = dsa.WrapDataObject(data).Points
poly = dsa.WrapDataObject(data).Polygons
poly_mat = np.reshape(poly,(-1,4))[:,1:4]

#%%
points_mat = []
label_mat = []
faces_mat = []

import os 
for f_name in os.listdir('datasets/LAA_segmentation/'):
    if f_name.endswith('.vtk'):
        filename = 'datasets/LAA_segmentation/' + f_name
        
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(filename)
        reader.ReadAllScalarsOn()
        reader.Update()
        data = reader.GetOutput()

        points = np.array( reader.GetOutput().GetPoints().GetData() )
        points_mat.append(points)
        
        label = np.array( data.GetCellData().GetScalars() )
        label_mat.append(label)

        numpy_array_of_points = dsa.WrapDataObject(data).Points
        poly = dsa.WrapDataObject(data).Polygons
        poly_mat = np.reshape(poly,(-1,4))[:,1:4]
        faces_mat.append(poly_mat)

        
        print(filename)
#%%
import matplotlib.pyplot as plt

no_points = np.zeros([106,1])
no_faces = np.zeros([106,1])
label_dist = np.zeros([106,1])
for i in range(len(points_mat)):
    no_points[i] = (len(points_mat[i]))
    no_faces[i] = (len(faces_mat[i]))
    label_dist[i] = label_mat[i].sum()/len(label_mat[i])
#%%
# An "interface" to matplotlib.axes.Axes.hist() method
n, bins, patches = plt.hist(x=no_points, bins='auto', color='#0504aa',
                            alpha=0.7, rwidth=0.85)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('No of points in meshes')
plt.ylabel('Frequency')
plt.title('Distributions of no points')
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
#%%
# An "interface" to matplotlib.axes.Axes.hist() method
n, bins, patches = plt.hist(x=no_faces, bins='auto', color='#0504aa',
                            alpha=0.7, rwidth=0.85)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('No of faces in meshes')
plt.ylabel('Frequency')
plt.title('Distributions of no faces')
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
#%%
n, bins, patches = plt.hist(x=label_dist, bins='auto', color='#0504aa',
                            alpha=0.7, rwidth=0.85)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('LAA labels as % of data')
plt.ylabel('Frequency')
plt.title('Distributions of LAA labels')
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)










 
        
        
        