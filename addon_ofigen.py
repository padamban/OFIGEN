bl_info = {
    "name": "Optical Flow Image Generator",
    "author": "padamban",
    "version": (1, 0),
    "blender": (2, 77, 0),
    "location": "View3D > Tool Shelf > OFIGEN",
    "description": "Generate realistic images with spacial data.",
    "warning": "",
    "wiki_url": "",
    "category": "User",
    }

###################################
## Imports


import bpy
import bmesh
import sys
import os
import random
import math
import re


import mathutils
from math import radians, tan

from bpy.props import (StringProperty, BoolProperty, IntProperty, FloatProperty, FloatVectorProperty, EnumProperty, PointerProperty )

os.system("cls")




###################################
## Default config
class ConfigPaths():
    output = "D:\\ofigen\\_Data\\"
    models = "D:\\ofigen\\MultiModels\\"
    bounds = "D:\\ofigen\\Bounding\\"
    background = "D:\\ofigen\\Background\\"


###################################
## Constants

TARGET_NAME = "x_TRGT"
BBOX_NAME = "y_BND"
CAM_NAME = "a_CAM"
LAMP_NAME = "b_LAMP"
SUN_NAME = "b_SUN"
IMG_NAME = "c_IMG"


BBOX = 'BOX'
BSPHERE = 'SPH'


###################################
## Globals

TARGET_OBJECTS = []
IDS = [10000000]
FILES = None


###################################
## Gui/app variables

class AddonData(bpy.types.PropertyGroup):

    paths = ConfigPaths()
    data_path_out = bpy.props.StringProperty( name = "Folder", default = paths.output, description = "Path of the output. The genereted data will be dumped here.", subtype = 'DIR_PATH')
    
    data_path_objs = bpy.props.StringProperty( name = "Folder", default = paths.models, description = "Directory of the model database. Put your model files here and make sure to use the correct name and file format.", subtype = 'DIR_PATH')
    is_format_obj = bpy.props.BoolProperty( name = '.obj',  default=True,  description='Use .OBJ models.')
    is_format_stl = bpy.props.BoolProperty( name = '.stl',  default=False,  description='Use .STL models.')
    is_format_ply = bpy.props.BoolProperty( name = '.ply',  default=False,  description='Use .PLY models.')
    is_format_3ds = bpy.props.BoolProperty( name = '.3ds',  default=False,  description='Use .3DS models.')

    data_path_bounds = bpy.props.StringProperty( name = "Folder", default = paths.bounds, description = "Directory of the bounds. Contains the models that are used for bounding shapes. (Currently only BOX an SPH is supported by the fiters. However you can create new ones, just make sure to give them a tree letter capitalized name, which can be used as a tag in the model file nemes. ). ", subtype = 'DIR_PATH')
    is_shape_box = bpy.props.BoolProperty( name = 'Box',  default=True,  description="Use models with bounding 'box'. (The model name must contain _BOX)")
    is_shape_sphere = bpy.props.BoolProperty( name = 'Shpere',  default=True,  description="Use models with bounding 'sphere'. (The model name must contain _SPH)")
    filename_model_tag  = bpy.props.StringProperty( name = "Filter", default = "", description = "The model name contains this substring. By leaving it empty you are not filtering by file name.")
    
    data_path_imgs = bpy.props.StringProperty( name = "Folder", default = paths.background, description = "Directory of the backround image database.", subtype = 'DIR_PATH')
    filename_background_tag  = bpy.props.StringProperty( name = "Filter", default = "", description = "The backround image name contains this substring. By leaving it empty you are not filtering by file name.")
    
    max_number_of_models  = bpy.props.IntProperty( name = "(Max) number of models", default = 5, min=1, max=15, description = "Number of objects in the pictures. Maximum, because the addon does not garantee the deployment of the fullnumber of objects if the constraints doesn't leave enough space. Furthermor, if the number of object is random than this only signals the maximum number of object that we want to see deployed. ")
    min_distance_from_camera  = bpy.props.IntProperty( name = "Min distance", default = 10, min=5, max=12, description = "Minimum distance from the camera.")
    max_distance_from_camera  = bpy.props.IntProperty( name = "Max distance", default = 26, min=12, max=26, description = "Maximum distance from the camera.")
    field_of_view_coef  = bpy.props.FloatProperty( name = "Field of view Coef", default = 0.2, min=-0.2, max=0.5, description = "Modifies deployment in the field of view. In short you can set that the models can be placed on the edge of the image or not. (c=0 : no modification; c<0 : expands; c>0 narrows")
    proximity_coef  = bpy.props.FloatProperty( name = "Proximity Coef", default = 1, min=0, max=3, description = "Sets, how much the opjects can overlap. Imagine like each is in its bounding sphere and we want to limit the over lap of these overlaps. (c>1 : no overlap; c=0 : possible full overlap;)")
    is_random_number_of_models = bpy.props.BoolProperty( name = 'Is Random Number of Models',  default=True,  description='Random number of models.')
    is_randomize_the_use_of_models = bpy.props.BoolProperty( name = 'Random use of models',  default=True,  description='Random use of models, otherwise use it iteratively. ')
    is_randomize_the_use_of_images = bpy.props.BoolProperty( name = 'Random use of backgrounds',  default=True,  description='Random use of backgrounds, otherwise use it iteratively.')
    

    is_init_target_moving = bpy.props.BoolProperty( name = 'Are the targets rotating at init? ',  default=True,  description='If enabled the targets are rotated randomly after init.')
    init_target_rotation_coef  = bpy.props.IntProperty( name = "Max Rot°", default = 120, min=0, max=270, description = "0 = no rotation; The given valeu will serve as the maximun rotation on each axes. The actual value is selected randomly.")
    init_target_rot_constrain_x  = bpy.props.FloatProperty( name = "x", default = 0.2, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    init_target_rot_constrain_y  = bpy.props.FloatProperty( name = "y", default = 0.2, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    init_target_rot_constrain_z  = bpy.props.FloatProperty( name = "z", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")

    is_target_moving = bpy.props.BoolProperty( name = 'Are the targets moving? ',  default=True,  description='If enabled the targets are moved and rotated randomly between the to snapshots.')
    target_rotation_coef  = bpy.props.FloatProperty( name = "Rot coef", default = 9.0, min=0.0, max=10.0, description = "0 = no rotation; The given valeu will serve as the maximun rotation on each axes. The actual value is selected randomly.")
    target_move_coef  = bpy.props.FloatProperty( name = "Trans coef", default = 0.5, min=0.0, max=3.0, description = "0 = no movement; The given valeu will serve as the maximun movement on each axes. The actual value is selected randomly.")
    target_move_constrain_x  = bpy.props.FloatProperty( name = "x", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    target_move_constrain_y  = bpy.props.FloatProperty( name = "y", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    target_move_constrain_z  = bpy.props.FloatProperty( name = "z", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")

    is_background_moving = bpy.props.BoolProperty( name = 'Is the background moving? ',  default=False,  description='If enabled the background is moved and rotated randomly between the to snapshots.')
    background_rotation_coef  = bpy.props.FloatProperty( name = "Rot coef", default = 4.0, min=0.0, max=10.0, description = "0 = no rotation; The given valeu will serve as the maximun rotation on each axes. The actual value is selected randomly.")
    background_move_coef  = bpy.props.FloatProperty( name = "Trans coef", default = 2.0, min=0.0, max=4.0, description = "0 = no movement; The given valeu will serve as the maximun movement on each axes. The actual value is selected randomly.")
    background_move_constrain_x  = bpy.props.FloatProperty( name = "x", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    background_move_constrain_y  = bpy.props.FloatProperty( name = "y", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    background_move_constrain_z  = bpy.props.FloatProperty( name = "z", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")

    is_camera_moving = bpy.props.BoolProperty( name = 'Is the camera moving? ',  default=False,  description='If enabled the camera is moved and rotated randomly between the to snapshots.')
    camera_rotation_coef  = bpy.props.FloatProperty( name = "Rot coef", default = 0.5, min=0.0, max=10.0, description = "0 = no rotation; The given valeu will serve as the maximun rotation on each axes. The actual value is selected randomly.")
    camera_move_coef  = bpy.props.FloatProperty( name = "Trans", default = 1.0, min=0.0, max=2.0, description = "0 = no movement; The given valeu will serve as the maximun movement on each axes. The actual value is selected randomly.")
    camera_move_constrain_x  = bpy.props.FloatProperty( name = "x", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    camera_move_constrain_y  = bpy.props.FloatProperty( name = "y", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")
    camera_move_constrain_z  = bpy.props.FloatProperty( name = "z", default = 1.0, min=0.0, max=1.0, description = "0 = no movement in this directon; 1 = no limitation in this direction")



    run_iterations  = bpy.props.IntProperty( name = "Iterations", default = 1, min=1, max=100, description = "Number of times the program creates data. (one takes aprx. 4s)")


    # private vars
    numOfModels  = bpy.props.IntProperty( default = 0, min=0, max=1000)
    background_file  = bpy.props.StringProperty( default = "")


    def getModelFileNames(self):        
        models = []

        for root, dirs, files in os.walk(self.data_path_objs):
            for name in files:

                ok_format = False
                if self.is_format_stl and ('.stl' in name):
                    ok_format = True
                elif self.is_format_obj and ('.obj' in name):
                    ok_format = True
                elif self.is_format_ply and ('.ply' in name):
                    ok_format = True
                elif self.is_format_3ds and ('.3ds' in name):
                    ok_format = True
                
                ok_shape = False
                if self.is_shape_box and (BBOX in name):
                    ok_shape = True
                elif self.is_shape_sphere and (BSPHERE in name):
                    ok_shape = True
                
                has_substr = False
                if self.filename_model_tag in name:
                    has_substr = True

                if ok_format and ok_shape and has_substr:
                    models.append(os.path.join(root, name))

        return models

    def getBackgroundFileNames(self):
        images = []

        for root, dirs, files in os.walk(self.data_path_imgs):
            for name in files:                
                has_substr = False
                if self.filename_background_tag in name:
                    has_substr = True

                if has_substr:
                    images.append(os.path.join(root, name))

        return images


    def getBoundFileNames(self, boundingtag):
        bounds = []

        for root, dirs, files in os.walk(self.data_path_bounds):  
            for name in files:                             
                ok_format = False
                if ('.obj' in name):
                    ok_format = True

                ok_shape = False
                if boundingtag == BBOX and self.is_shape_box and (BBOX in name):
                    ok_shape = True
                elif boundingtag == BSPHERE and self.is_shape_sphere and (BSPHERE in name):
                    ok_shape = True

                if ok_shape and ok_format:
                    bounds.append(os.path.join(root, name))

        return bounds




###################################
## Local types

class BBoxData:
   def __init__(self, trgt):
        trgt.rotation_mode = 'XYZ'
        self.location = trgt.location
        self.dimensions = trgt.dimensions
        self.rotation_euler = trgt.rotation_euler
        self.delta_location = trgt.delta_location
        self.delta_rotation_euler = trgt.delta_rotation_euler
        self.radius = math.sqrt(math.pow(trgt.dimensions[0], 2) + math.pow(trgt.dimensions[1], 2) + math.pow(trgt.dimensions[2], 2))*0.5
        trgt.rotation_mode = 'QUATERNION'


class DeployedObjData:
   def __init__(self, name, location, radius):
        self.name = name
        self.location = location
        self.radius = radius



#############################
# BBOX data + display

def getBBoxDataInvisible(trgtName):
    trgt = bpy.data.objects[trgtName]
    bbox = BBoxData(trgt)
    return bbox

def addBoundingBox(context, trgtName, boxName, type):
    bboxData = getBBoxDataInvisible(trgtName)

    if type == BSPHERE:
        filePath = context.scene.addon_data.getBoundFileNames(BSPHERE)[0]   
    else: # BBOX
        filePath = context.scene.addon_data.getBoundFileNames(BBOX)[0]   

    bpy.ops.import_scene.obj(filepath=filePath, filter_glob="*.obj;*.mtl")
    for obj in bpy.context.selected_objects:
        obj.name = boxName 
        bbox = bpy.context.scene.objects[boxName]

    bbox.location = bboxData.location 
    bbox.dimensions = bboxData.dimensions*1.01 
    bbox.rotation_euler = bboxData.rotation_euler 
    bbox.delta_location = bboxData.delta_location 
    bbox.delta_rotation_euler = bboxData.delta_rotation_euler 

def removeBoundingBox(context, boxName):
    bpy.context.scene.objects[boxName].select = True
    bpy.ops.object.delete() 

def addBoundingBoxForAll(context, trgtName, boxName):
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(trgtName):
            objID = obj.name.split('.')[2]
            objBound = obj.name.split('.')[1]
            addBoundingBox(context, obj.name, boxName + '.' + objBound + '.' + objID, objBound)

def removeBoundingBoxForAll(context,boxName):
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(boxName):
            removeBoundingBox(context, obj.name)




#############################
# WRITE FILE + TEXT FORMATING

def writeOutput(context, textArray, filename):
    dir_out = context.scene.addon_data.data_path_out;
    with open(os.path.join(dir_out, filename), 'w') as fh:  
        for text in textArray:
            fh.write(text)
        pass

def floatFormat(num):
    return "{:.2f}".format(num)

def intFormat(num):
    return "{:.0f}".format(num)

def boolFormat(b):
    return "true" if b else "false"
    

def floatParamIntoJSON(name, data, indent=2, comma=True):
    return ' ' * indent + '"' + name + '": ' + floatFormat(data) + (',\n' if comma else '\n')

def intParamIntoJSON(name, data, indent=2, comma=True):
    return ' ' * indent + '"' + name + '": ' + intFormat(data) + (',\n' if comma else '\n')

def boolParamIntoJSON(name, data, indent=2, comma=True):
    return ' ' * indent + '"' + name + '": ' + boolFormat(data) + (',\n' if comma else '\n')

def stringParamIntoJSON(name, data, indent=2, comma=True):
    return ' ' * indent + '"' + name + '": "' + data + '"' + (',\n' if comma else '\n')


def vectorToJSON(name, vec, indent=6, comma=True):
    return ' ' * indent + '"' + name + '": [' + floatFormat(vec[0]) + ', ' + floatFormat(vec[1]) + ', ' + floatFormat(vec[2]) + ']' + (',\n' if comma else '\n')

def eulerToJSON(name, euler, indent=6, comma=True, compensate=True):
    return ' ' * indent + '"' + name + '": {"value":[' + floatFormat(euler.x - (radians(90) if compensate else radians(0))) + ', ' + floatFormat(euler.y) + ', ' + floatFormat(euler.z) + '], "order":"' + euler.order + '"}' + (',\n' if comma else '\n')

def matrixToJSON(name, matrix):
    rows = [""] * 4
    for x in range(0, 4):
        rows[x] = '[' + floatFormat(matrix[x][0])  + ', ' + floatFormat(matrix[x][1]) + ', ' + floatFormat(matrix[x][2]) + ', ' + floatFormat(matrix[x][3]) +  ']'
    return '"' + name + '": [' + rows[0] + ', ' + rows[1] + ', ' + rows[2] + ', ' + rows[3] + ']'

def bboxDataToJSON(cam, trgtName, indent):
    bboxData = getBBoxDataInvisible(trgtName)
    
    alltext = []
    alltext.append(' ' * indent + '{"' + trgtName + '":[\n')

    alltext.append(vectorToJSON('location', bboxData.location, indent+2))
    alltext.append(eulerToJSON('rotation_euler', bboxData.rotation_euler, indent+2))
    alltext.append(vectorToJSON('location_from_cam', (bboxData.location) - cam.location , indent+2))

    alltext.append(vectorToJSON('location_delta', bboxData.delta_location, indent+2))
    alltext.append(eulerToJSON('rotation_euler_delta', bboxData.delta_rotation_euler, indent+2, compensate=False))
    alltext.append(vectorToJSON('location_from_cam_delta', (bboxData.location + bboxData.delta_location) - cam.location , indent+2, comma=False))

    alltext.append(' ' * indent + ']}') 

    return alltext


def extractAllBBoxData(addonData, trgtName, camName):
    alltext = []

    cam = bpy.data.objects[camName]


    trgtLineStart = '{"' + "targets" + '":[\n'
    alltext.append(trgtLineStart)

    for obj in bpy.context.scene.objects:
        if obj.name.startswith(trgtName):
            text = bboxDataToJSON(cam, obj.name, 4)
            alltext = alltext + text
            alltext.append(',\n')


    trgtLineEnd = ']}'
    alltext.append(trgtLineEnd)
    return alltext


def extractBackgroundData(addonData,imgName):
    alltext = []
    
    img = bpy.data.objects[imgName]

    alltext.append('{"' + 'background' + '":[\n')
    
    alltext.append(vectorToJSON('location', img.location, 2))
    alltext.append(vectorToJSON('location_delta', img.delta_location, 2))
    alltext.append(eulerToJSON('rotation_euler', img.rotation_euler,  2, compensate=False))
    alltext.append(eulerToJSON('rotation_euler_delta', img.delta_rotation_euler,  2, compensate=False))

    alltext.append(stringParamIntoJSON("background_file", addonData.background_file, comma=False))
    alltext.append(']},\n')
    return alltext


def extractCameraData(name):
    cam = bpy.data.objects[name]
    alltext = []
    alltext.append('{"' + 'camera' + '":[\n')
    alltext.append(vectorToJSON('location', cam.location, 2))
    alltext.append(vectorToJSON('location_delta', cam.delta_location, 2))
    alltext.append(eulerToJSON('rotation_euler', cam.rotation_euler, 2, False))
    alltext.append(eulerToJSON('rotation_euler_delta', cam.delta_rotation_euler, 2, False, compensate=False))
    alltext.append(']},\n')
    return alltext

def extractPictureData(context, trgtName, camName, imgName, filename = "file"):
    addonData = context.scene.addon_data

    alltext = []
    alltext = alltext + extractBackgroundData(addonData, imgName)
    alltext = alltext + extractCameraData(camName)
    alltext = alltext + extractAllBBoxData(addonData, trgtName, camName)

    writeOutput(context, alltext, filename + '.txt')


def extractSceneConfigData(context, trgtName, camName, filename = "file"):
    addonData = context.scene.addon_data

    alltext = []

    alltext.append('{\n')
    alltext.append(stringParamIntoJSON("data_path_out", addonData.data_path_out))
    alltext.append(stringParamIntoJSON("data_path_objs", addonData.data_path_objs))
    alltext.append(stringParamIntoJSON("data_path_bounds", addonData.data_path_bounds))
    alltext.append(stringParamIntoJSON("data_path_imgs", addonData.data_path_imgs))
    alltext.append(stringParamIntoJSON("filename_model_tag", addonData.filename_model_tag))
    alltext.append(stringParamIntoJSON("filename_background_tag", addonData.filename_background_tag))

    alltext.append(boolParamIntoJSON("is_format_obj", addonData.is_format_obj))
    alltext.append(boolParamIntoJSON("is_format_stl", addonData.is_format_stl))
    alltext.append(boolParamIntoJSON("is_format_ply", addonData.is_format_ply))
    alltext.append(boolParamIntoJSON("is_format_3ds", addonData.is_format_3ds))

    alltext.append(boolParamIntoJSON("is_shape_box", addonData.is_shape_box))
    alltext.append(boolParamIntoJSON("is_shape_sphere", addonData.is_shape_sphere))

    alltext.append(boolParamIntoJSON("is_random_number_of_models", addonData.is_random_number_of_models))
    alltext.append(boolParamIntoJSON("is_randomize_the_use_of_models", addonData.is_randomize_the_use_of_models))
    alltext.append(boolParamIntoJSON("is_randomize_the_use_of_images", addonData.is_randomize_the_use_of_images))

    alltext.append(intParamIntoJSON("numOfModels", addonData.numOfModels))
    alltext.append(intParamIntoJSON("max_number_of_models", addonData.max_number_of_models))

    alltext.append(intParamIntoJSON("min_distance_from_camera", addonData.min_distance_from_camera))
    alltext.append(intParamIntoJSON("max_distance_from_camera", addonData.max_distance_from_camera))
    alltext.append(floatParamIntoJSON("field_of_view_coef", addonData.field_of_view_coef))
    alltext.append(floatParamIntoJSON("proximity_coef", addonData.proximity_coef))

    alltext.append(boolParamIntoJSON("is_init_target_moving", addonData.is_init_target_moving))
    alltext.append(floatParamIntoJSON("init_target_rotation_coef", addonData.init_target_rotation_coef))
    alltext.append(floatParamIntoJSON("init_target_rot_constrain_x", addonData.init_target_rot_constrain_x))
    alltext.append(floatParamIntoJSON("init_target_rot_constrain_y", addonData.init_target_rot_constrain_y))
    alltext.append(floatParamIntoJSON("init_target_rot_constrain_z", addonData.init_target_rot_constrain_z))

    alltext.append(boolParamIntoJSON("is_target_moving", addonData.is_target_moving))
    alltext.append(floatParamIntoJSON("target_move_coef", addonData.target_move_coef))
    alltext.append(floatParamIntoJSON("target_rotation_coef", addonData.target_rotation_coef))
    alltext.append(floatParamIntoJSON("target_move_constrain_x", addonData.target_move_constrain_x))
    alltext.append(floatParamIntoJSON("target_move_constrain_y", addonData.target_move_constrain_y))
    alltext.append(floatParamIntoJSON("target_move_constrain_z", addonData.target_move_constrain_z))

    alltext.append(boolParamIntoJSON("is_background_moving", addonData.is_background_moving))
    alltext.append(floatParamIntoJSON("background_move_coef", addonData.background_move_coef))
    alltext.append(floatParamIntoJSON("background_rotation_coef", addonData.background_rotation_coef))
    alltext.append(floatParamIntoJSON("background_move_constrain_x", addonData.background_move_constrain_x))
    alltext.append(floatParamIntoJSON("background_move_constrain_y", addonData.background_move_constrain_y))
    alltext.append(floatParamIntoJSON("background_move_constrain_z", addonData.background_move_constrain_z))

    alltext.append(boolParamIntoJSON("is_camera_moving", addonData.is_camera_moving))
    alltext.append(floatParamIntoJSON("camera_move_coef", addonData.camera_move_coef))
    alltext.append(floatParamIntoJSON("camera_rotation_coef", addonData.camera_rotation_coef))
    alltext.append(floatParamIntoJSON("camera_move_constrain_x", addonData.camera_move_constrain_x))
    alltext.append(floatParamIntoJSON("camera_move_constrain_y", addonData.camera_move_constrain_y))
    alltext.append(floatParamIntoJSON("camera_move_constrain_z", addonData.camera_move_constrain_z, comma=False))

    alltext.append('}\n')

    writeOutput(context, alltext, filename + '.txt')





 
 




#############################
# MOVE OBJECTS RANDOMLY

def randomNum(coef):
    return (random.randint(1,100000)-50000)*0.00001*coef

def moveRandomly(trgtName, linerCoef, rotationalCoef, xC=1, yC=1, zC=1 ):  
    trgt = bpy.context.scene.objects[trgtName]
    trgt.rotation_mode = 'XYZ'
    dLoc = (randomNum(linerCoef)*xC, randomNum(linerCoef)*yC, randomNum(linerCoef)*zC)    
    trgt.delta_location = dLoc
    dRotEuler = (radians(randomNum(rotationalCoef)), radians(randomNum(rotationalCoef)), radians(randomNum(rotationalCoef)))    
    trgt.delta_rotation_euler = dRotEuler
    print("     ->    ", dRotEuler)


def moveAllTargetsRandomly(context, trgtName):  
    addonData = context.scene.addon_data 
    if addonData.is_target_moving == True: 
        for obj in bpy.context.scene.objects:
            if obj.name.startswith(trgtName):
                moveRandomly(obj.name, addonData.target_move_coef, addonData.target_rotation_coef, addonData.target_move_constrain_x,addonData.target_move_constrain_y,addonData.target_move_constrain_z )


def randomRotateObject(name, coef, xR=1, yR=1, zR=1): 
    trgt = bpy.context.scene.objects[name]
    trgt.rotation_mode = 'XYZ'
    trgt.rotation_euler = (radians(90) + radians(randomNum(coef))*xR, radians(randomNum(coef))*yR, radians(randomNum(coef))*zR)


def moveBackgroundRandomly(context, name):
    addonData = context.scene.addon_data
    if addonData.is_background_moving == True:
        moveRandomly(name, addonData.background_move_coef, addonData.background_rotation_coef, addonData.background_move_constrain_x,addonData.background_move_constrain_y,addonData.background_move_constrain_z)

def moveCameraRandomly(context, name):
    addonData = context.scene.addon_data
    if addonData.is_camera_moving == True:
        moveRandomly(name, addonData.camera_move_coef, addonData.camera_rotation_coef, addonData.camera_move_constrain_x,addonData.camera_move_constrain_y,addonData.camera_move_constrain_z )

def resetRandomMove( name):
    moveRandomly(name, 0, 0)

def moveAllAsConfigSays(context):
    moveAllTargetsRandomly(context, TARGET_NAME)
    moveCameraRandomly(context, CAM_NAME)
    moveBackgroundRandomly(context, IMG_NAME)



#############################
# CAMERA FUNCTIONS

# TODO: Redo cameraData -it should return an object 
# TODO: Camera data to text function 

def cameraData(context, cam, distance):    
    vx = mathutils.Vector((1,0,0))
    vy = mathutils.Vector((0,1,0))
    vz = mathutils.Vector((0,0,1))
    loc, rot_quat, scl = cam.matrix_basis.decompose()
    vx.rotate(rot_quat)
    vy.rotate(rot_quat)
    vz.rotate(rot_quat)

    fowC = 1 - context.scene.addon_data.field_of_view_coef

    z_distance = vz*distance
    x_max = vx*distance*tan(cam.data.angle_x*fowC/2)
    y_max = vy*distance*tan(cam.data.angle_y*fowC/2)    
    # TODO: Create object like for bbox
    return vx, vy, vz, z_distance, y_max, x_max, loc, rot_quat


def addCamera(context, camName, location, rotationEuler):    
    cam_data = bpy.data.cameras.new(camName)
    cam_obj = bpy.data.objects.new(camName, cam_data)
    cam_obj.location = location
    cam_obj.rotation_euler = rotationEuler
    bpy.context.scene.objects.link(cam_obj)
    bpy.context.scene.update()
    TARGET_OBJECTS.append(DeployedObjData(camName, cam_obj.location, 2))
    bpy.data.scenes["Scene"].camera = cam_obj




#############################
# MOVE OBJECTS 


def createRandomSeedPosition(context, camName, distance, twitchMax = 1):
    cam = bpy.context.scene.objects[camName]

    vx, vy, vz, z_distance, y_max, x_max, loc, rot_quat = cameraData(context, cam, distance)
    
    rx = random.random()*twitchMax*2-twitchMax
    ry = random.random()*twitchMax*2-twitchMax

    location = loc - z_distance - x_max*rx - y_max*ry
    rotation_q = rot_quat

    return location, rotation_q


def getSeedPosition(context, camName, addonData, bboxData, positionList, proximityC): 

    seedPos = None  
    seedRot = None

    i_findPos = 100
    minDist = addonData.min_distance_from_camera
    maxDist = addonData.max_distance_from_camera
    overlap = -1

    while i_findPos > 0 :

        isOverlaped = False
        overlap = -1
        dist = ((maxDist - minDist) * random.random()) + minDist
        seedPos, seedRot = createRandomSeedPosition(context, camName, dist, 1)
        i_findPos = i_findPos-1  

        for pos in positionList:
            delta = seedPos - pos.location
            overlap = delta.length - bboxData.radius*proximityC - pos.radius*proximityC

            if 0 > overlap :
                isOverlaped = True
                break

        if isOverlaped==False :
            break
        else:
            seedPos = None  
            seedRot = None


    return seedPos, seedRot


def getBackgroundPosition():
    return 1


def changeObjectLocation(name, loc, rot_q):
    trgt = bpy.context.scene.objects[name]
    trgt.location = loc
    trgt.rotation_mode = 'QUATERNION'
    trgt.rotation_quaternion = rot_q

        
def resizeImage(imgname, distFromCam):
    img = bpy.data.objects[imgname]
    img.dimensions = img.dimensions*distFromCam*0.9
    





#############################
# Add/remove objects 

def getUniqueID():
    id = 0
    while True:
        # newID = random.randint(10000000, 99999999)   
        newID = IDS[-1] + 1
        if ~(newID in IDS):
            id = newID
            IDS.append(newID)
            break
    return id

def addImage(imgname, imgfile):
    removeObject(imgname)

    bpy.ops.import_image.to_plane(
        use_shadeless=True,
        files=[{'name': os.path.basename(imgfile)}],
        directory=os.path.dirname(imgfile)
    )
    for obj in bpy.context.selected_objects:
        obj.name = imgname


def removeObject(name):
    deleteModel(name)



def addModel(filePath, fileNameBase):    
    file_name = os.path.basename(filePath)
    bounding = BBOX

    if BSPHERE in file_name:
        bounding = BSPHERE

    if '.stl' in file_name:
        bpy.ops.import_mesh.stl(filepath=filePath)
    elif '.ply' in file_name:
        bpy.ops.import_mesh.ply(filepath=filePath)
    elif '.obj' in file_name:
        bpy.ops.import_scene.obj(filepath=filePath)
    elif '.3ds' in file_name:
        bpy.ops.import_scene.autodesk_3ds(filepath=filePath)
    else:
        return 'ERROR_NO_MODEL_CREATED';    

    createdObjRef = None


    bpy.context.scene.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()

    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

    for obj in bpy.context.selected_objects:
        ID = getUniqueID()
        obj.name = fileNameBase + '.' + bounding + '.' + str(ID)
        createdObjRef = obj
        bpy.context.scene.objects.active = obj



    return createdObjRef.name


def deleteModel(name):
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj = bpy.data.objects[name]
        if obj != None:
            obj.select = True
            bpy.ops.object.delete() 
    except:
        print("\nCouldn't find an object with this name. ", name)


def deleteAllRelated(name):
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(name):
            deleteModel(obj.name)



def generateTarget(context, camName, trgtName, index):
    addonData = context.scene.addon_data

    isRandNumOfModels = addonData.is_random_number_of_models
    isRandUseOfModels = addonData.is_randomize_the_use_of_models

    proxC = addonData.proximity_coef

    modelList = addonData.getModelFileNames()

    numOfModels = len(modelList)

    modelIdxRand = random.randint(1, numOfModels) - 1
    modelIdxOrd =  index % numOfModels - 1 

    chosenFile = modelList[modelIdxRand if isRandUseOfModels else modelIdxOrd]

    nameBapt = addModel(chosenFile, trgtName)

    bboxData = getBBoxDataInvisible(nameBapt)
    print("Start----------------")

    seedPos, seedRot = getSeedPosition(context, camName, addonData, bboxData, TARGET_OBJECTS, proxC)

    if seedPos == None :
        deleteModel(nameBapt)
        return
    
    addonData.numOfModels = addonData.numOfModels + 1
    changeObjectLocation(nameBapt, seedPos, seedRot)

    if addonData.is_init_target_moving == True:
        randomRotateObject(nameBapt, addonData.init_target_rotation_coef, addonData.init_target_rot_constrain_x, addonData.init_target_rot_constrain_y,addonData.init_target_rot_constrain_z )
    TARGET_OBJECTS.append(DeployedObjData(nameBapt, seedPos, bboxData.radius))
    print("End----------------", addonData.numOfModels)


def generateBackground(context, camname, imgname, idx=1):
    addonData = context.scene.addon_data
    backgrounds = addonData.getBackgroundFileNames()
    isRandUseOfImgs = addonData.is_randomize_the_use_of_images

    i = 1;
    if isRandUseOfImgs == True :
        i = random.randint(1, len(backgrounds)-1)        
    else:
        i = (idx % (len(backgrounds)-1))

    addonData.background_file = backgrounds[i]

    addImage(imgname, backgrounds[i])    

    dist = 30
    resizeImage(imgname, dist)
    pos, rotQ = createRandomSeedPosition(context, camname, dist, 0.05)

    changeObjectLocation(imgname, pos, rotQ)



#############################
# Lamps 


def addLight(context, location, rotationEuler, lightType, lightName):
    light_data = bpy.data.lamps.new(name=lightName, type=lightType)
    light_obj = bpy.data.objects.new(name=lightName, object_data=light_data)
    bpy.context.scene.objects.link(light_obj)
    light_obj.location = location
    light_obj.rotation_euler = rotationEuler



def setupLight(context, camName):
    cam = bpy.context.scene.objects[camName]

    removeObject(LAMP_NAME)
    removeObject(SUN_NAME)

    cl = cam.location
    addLight(context,  (3+cl.x, -6+cl.y, 7+cl.z), (radians(90), radians(0), radians(0)), 'POINT', LAMP_NAME)
    addLight(context, (-3+cl.x, -6+cl.y, 7+cl.z), (radians(60), radians(0), radians(0)), 'SUN', SUN_NAME)



#############################
# Render

def render(context, name):
    bpy.context.scene.render.filepath = context.scene.addon_data.data_path_out + name + ".png"
    bpy.ops.render.render(write_still=True, use_viewport=True)





#############################
# Manager functions

def clearScene(context):   
    bpy.ops.view3D.snap_cursor_to_center()
    for obj in bpy.context.scene.objects:
        obj.select = True
    bpy.ops.object.delete() 
    context.scene.addon_data.numOfModels = 0
    TARGET_OBJECTS = []
    IDS = []

def setupEnvironment(context):
    addCamera(context, CAM_NAME, (0, 0, 0), (radians(90), radians(0), radians(0)) )
    setupLight(context, CAM_NAME)


def RunOnce(context, name="test", subfolder="", idx=1):
    addonData = context.scene.addon_data

    if addonData.is_random_number_of_models == True:
        objcount = random.randint(1,addonData.max_number_of_models)
    else:
        objcount = addonData.max_number_of_models

    clearScene(context)
    setupEnvironment(context)
    generateBackground(context, CAM_NAME, IMG_NAME, idx)

    for x in range(objcount):
        generateTarget(context, CAM_NAME, TARGET_NAME, x)

    render(context, subfolder + name + ".1")
    addBoundingBoxForAll(context, TARGET_NAME, BBOX_NAME)    
    render(context, subfolder + name + ".1b")
    extractPictureData(context, TARGET_NAME, CAM_NAME, IMG_NAME, subfolder + name + ".1b")
    removeBoundingBoxForAll(context, BBOX_NAME)

    moveAllAsConfigSays(context)

    render(context, subfolder + name + ".2")
    addBoundingBoxForAll(context, TARGET_NAME, BBOX_NAME)    
    render(context, subfolder + name + ".2b")
    extractPictureData(context, TARGET_NAME, CAM_NAME, IMG_NAME, subfolder + name + ".2b")
    removeBoundingBoxForAll(context, BBOX_NAME)

    extractSceneConfigData(context, TARGET_NAME, CAM_NAME, subfolder + name + ".c")

    clearScene(context)


def RunNTimes(context, basename="test", folder=""):
    addonData = context.scene.addon_data

    for n in range(addonData.run_iterations):
        RunOnce(context, basename +'_'+ str(n), folder, n)



def DeleteFiles(context, folder):
    try:
        foldr = context.scene.addon_data.data_path_out + folder
        filelist = [ f for f in os.listdir(foldr) ]
        for f in filelist:
            os.remove(os.path.join(foldr, f))
    except:
        print("\nDeleteFiles: Couldn't find path. ")



###################################
## Just For Test 





###################################
###################################
###################################
## Actions

class Run(bpy.types.Operator):
    """Execute 'iteration' many times. See output location."""
    bl_idname = "myops.run"
    bl_label = "Run"


    def execute(self, context):

        DeleteFiles(context, "data\\")
        RunNTimes(context, "img", "data\\");
        
        return {'FINISHED'}






## Unit tests
class TestButton1(bpy.types.Operator):
    """Remove everything."""
    bl_idname = "myops.test1"
    bl_label = "DONE - Clear Scene"

    def execute(self, context):
        clearScene(context)
        print("Clear + Model List")
        print("Files: \n\n", context.scene.addon_data.getModelFileNames())

        return {'FINISHED'}

class TestButton2a(bpy.types.Operator):
    """Create camera and lamp."""
    bl_idname = "myops.test2a"
    bl_label = "DONE - Camera Crew Generation"

    def execute(self, context):
        setupEnvironment(context)
        return {'FINISHED'}


class TestButton2b(bpy.types.Operator):
    """."""
    bl_idname = "myops.test2b"
    bl_label = "DONE - Setup the ligthing."

    def execute(self, context):            
        setupLight(context, CAM_NAME)
        return {'FINISHED'}



class TestButton3a(bpy.types.Operator):
    """List available files in the console. Menu: Window -> C"""
    bl_idname = "myops.test3a"
    bl_label = "DONE - Get models and images from directory (console)"

    def execute(self, context):
        # getModelFileNames(context)
        os.system("cls")
        modelList = context.scene.addon_data.getModelFileNames()
        backgrounds = context.scene.addon_data.getBackgroundFileNames()
        boundsBox = context.scene.addon_data.getBoundFileNames(BBOX)
        boundsSpheres = context.scene.addon_data.getBoundFileNames(BSPHERE)
        print('modelList')
        print(modelList)
        print('backgrounds')
        print(backgrounds)
        print('boundsBox')
        print(boundsBox)
        print('boundsSpheres')
        print(boundsSpheres)
        return {'FINISHED'}



class TestButton3b(bpy.types.Operator):
    """Create a single target object."""
    bl_idname = "myops.test3b"
    bl_label = "DONE  - Model Generation"

    def execute(self, context):
        os.system("cls")

        generateTarget(context, CAM_NAME, TARGET_NAME, 7)
        return {'FINISHED'}

class TestButton3c(bpy.types.Operator):
    """Place an img in the view."""
    bl_idname = "myops.test3c"
    bl_label = "DONE - Background generation"

    def execute(self, context):            
        generateBackground(context, CAM_NAME, IMG_NAME)
        return {'FINISHED'}

class TestButton3d(bpy.types.Operator):
    """Remove all target objects."""
    bl_idname = "myops.test3d"
    bl_label = "DONE - Remove targets"

    def execute(self, context):        
        TARGET_OBJECTS = []    
        IDS = []
        context.scene.addon_data.numOfModels = 0
        deleteAllRelated(TARGET_NAME)        
        return {'FINISHED'}


class TestButton4(bpy.types.Operator):
    """Add a bounding box/sphere/ellipsoid to each target objects."""
    bl_idname = "myops.test4"
    bl_label = "DONE - Add BBox"
    
    def execute(self, context):    

        addBoundingBoxForAll(context, TARGET_NAME, BBOX_NAME)
        return {'FINISHED'}

class TestButton5(bpy.types.Operator):
    """Remove all bounding boxes."""
    bl_idname = "myops.test5"
    bl_label = "DONE - Remove BBox"
    
    def execute(self, context):
        removeBoundingBoxForAll(context, BBOX_NAME)
        return {'FINISHED'}

class TestButton6(bpy.types.Operator):
    """Get bbox data. (not necessary to add the bbox objects)"""
    bl_idname = "myops.test6"
    bl_label = "WIP  - Extract BBox Data (get correct data)"
    
    def execute(self, context):
        # extractBBoxData(context, BBOX_NAME)
        extractPictureData(context, TARGET_NAME, CAM_NAME, IMG_NAME)

        return {'FINISHED'}

class TestButton7(bpy.types.Operator):
    """Move target objects a bit."""
    bl_idname = "myops.test7"
    bl_label = "DONE - Move target."
    
    def execute(self, context):
        moveAllTargetsRandomly(context, TARGET_NAME)
        return {'FINISHED'}

class TestButton7b(bpy.types.Operator):
    """Move background imgage."""
    bl_idname = "myops.test7b"
    bl_label = "DONE - Move background imgage."
    
    def execute(self, context):
        moveBackgroundRandomly(context, IMG_NAME)
        return {'FINISHED'}


class TestButton7c(bpy.types.Operator):
    """Move camera."""
    bl_idname = "myops.test7c"
    bl_label = "DONE - Move camera."
    
    def execute(self, context):
        moveCameraRandomly(context, CAM_NAME)
        return {'FINISHED'}
        
class TestButton7d(bpy.types.Operator):
    """Move camera."""
    bl_idname = "myops.test7d"
    bl_label = "DONE - Reset random move (used only for camera)."
    
    def execute(self, context):
        resetRandomMove(CAM_NAME)
        return {'FINISHED'}

class TestButton7e(bpy.types.Operator):
    """Move everythyng as the setup data says (in the properties panel)."""
    bl_idname = "myops.test7e"
    bl_label = "DONE - Move all as config says."
    
    def execute(self, context):
        moveAllAsConfigSays(context)
        return {'FINISHED'}




class TestButton8(bpy.types.Operator):
    """Render - see the result in the output folder -> o.f./test/render.png"""
    bl_idname = "myops.test8"
    bl_label = "DONE  - Render"
    
    def execute(self, context):
        render(context, "test\\render")
        return {'FINISHED'}

class TestButton9(bpy.types.Operator):
    """Run Once - see output in ./_Data/test/test..."""
    bl_idname = "myops.test9"
    bl_label = "DONE - Run Once (using all config data)"
    
    def execute(self, context):

        DeleteFiles(context, "test\\once\\")
        RunOnce(context, "tst", "test\\once\\")
        
        return {'FINISHED'}

class TestButton10(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "myops.test10"
    bl_label = "WIP - Switch pivot mode"
    
    def execute(self, context):

        return {'FINISHED'}


###################################
###################################
###################################
## GUI

OFIGEN_TAB = 'OFIGen'

class View3DPanel():
    bl_space_type =  'VIEW_3D'
    bl_region_type = 'TOOLS'


class OfigenConfigPanel( View3DPanel, bpy.types.Panel):
    bl_label = "Config"
    bl_idname = "OFIGEN_config_panel"
    bl_category = OFIGEN_TAB

    def draw(self, context):
        addonData = context.scene.addon_data
        layout = self.layout

        layout.label(text="Data output folder")
        layout.prop(addonData, 'data_path_out')
        layout.separator()

        layout.label(text="Background directory")
        layout.prop(addonData, 'data_path_imgs')
        layout.prop(addonData, "filename_background_tag")
        layout.separator()

        layout.label(text="Model directory")
        layout.prop(addonData, 'data_path_objs')
        layout.prop(addonData, "filename_model_tag")

        col = layout.column()
        sub = col.row() 
        sub.prop(addonData, "is_format_obj")
        sub.prop(addonData, "is_format_stl")
        sub.prop(addonData, "is_format_ply")
        sub.prop(addonData, "is_format_3ds")
        col = layout.column()


        layout.separator()
        layout.label(text="Bounding objects")
        layout.prop(addonData, "data_path_bounds")
        sub = col.row() 
        sub.prop(addonData, "is_shape_box")
        sub.prop(addonData, "is_shape_sphere")
        layout.separator()
        
class OfigenPropertiesPanel( View3DPanel, bpy.types.Panel):
    bl_label = "Properties"
    bl_idname = "OFIGEN_property_panel"
    bl_category = OFIGEN_TAB

    def draw(self, context):
        addonData = context.scene.addon_data
        layout = self.layout
        layout.prop(addonData, "max_number_of_models", slider=True)

        col = layout.column()
        sub = col.row() 
        sub.prop(addonData, "min_distance_from_camera", slider=True)
        sub.prop(addonData, "max_distance_from_camera", slider=True)

        col = layout.column()
        sub = col.row() 
        sub.prop(addonData, "field_of_view_coef", slider=True)
        sub.prop(addonData, "proximity_coef", slider=True)

        layout.prop(addonData, "is_random_number_of_models")
        layout.prop(addonData, "is_randomize_the_use_of_models")
        layout.prop(addonData, "is_randomize_the_use_of_images")

        layout.separator()
        layout.prop(addonData, "is_init_target_moving")
        col = layout.column()
        sub = col.row() 
        sub.enabled = addonData.is_init_target_moving
        sub.prop(addonData, "init_target_rotation_coef")
        sub = col.row() 
        sub.enabled = addonData.is_target_moving
        sub.label(text="Rotation limiter")

        sub.prop(addonData, "init_target_rot_constrain_x")
        sub.prop(addonData, "init_target_rot_constrain_y")
        sub.prop(addonData, "init_target_rot_constrain_z")


        layout.separator()
        layout.prop(addonData, "is_target_moving")
        col = layout.column()
        sub = col.row() 
        sub.enabled = addonData.is_target_moving
        sub.prop(addonData, "target_rotation_coef")
        sub.prop(addonData, "target_move_coef")
        sub = col.row() 
        sub.enabled = addonData.is_target_moving
        sub.label(text="Move limiter")
        sub.prop(addonData, "target_move_constrain_x")
        sub.prop(addonData, "target_move_constrain_y")
        sub.prop(addonData, "target_move_constrain_z")

        layout.separator()
        layout.prop(addonData, "is_background_moving")
        col = layout.column()
        sub = col.row() 
        sub.enabled = addonData.is_background_moving
        sub.prop(addonData, "background_rotation_coef")
        sub.prop(addonData, "background_move_coef")
        sub = col.row() 
        sub.enabled = addonData.is_background_moving
        sub.label(text="Move limiter")
        sub.prop(addonData, "background_move_constrain_x")
        sub.prop(addonData, "background_move_constrain_y")
        sub.prop(addonData, "background_move_constrain_z")

        layout.separator()
        layout.prop(addonData, "is_camera_moving")
        col = layout.column()
        sub = col.row() 
        sub.enabled = addonData.is_camera_moving
        sub.prop(addonData, "camera_rotation_coef")
        sub.prop(addonData, "camera_move_coef")
        sub = col.row() 
        sub.enabled = addonData.is_camera_moving
        sub.label(text="Move limiter")
        sub.prop(addonData, "camera_move_constrain_x")
        sub.prop(addonData, "camera_move_constrain_y")
        sub.prop(addonData, "camera_move_constrain_z")




class OfigenRunPanel( View3DPanel, bpy.types.Panel):
    bl_label = "Run Program"
    bl_idname = "OFIGEN_run_panel"
    bl_category = OFIGEN_TAB

    def draw(self, context):
        addonData = context.scene.addon_data
        layout = self.layout
        layout.prop(addonData, "run_iterations", slider=True)
        layout.operator("myops.run")


class OfigenTestPanel( View3DPanel, bpy.types.Panel):
    bl_label = "Unit tests"
    bl_idname = "OFIGEN_test_panel"
    bl_category = OFIGEN_TAB

    def draw(self, context):
        addonData = context.scene.addon_data

        layout = self.layout

        layout.label(text="Scene manager")
        layout.operator("myops.test1")
        layout.operator("myops.test2a")
        layout.operator("myops.test2b")
        layout.separator()

        layout.label(text="Generator")
        layout.operator("myops.test3a")
        layout.operator("myops.test3b")   
        layout.operator("myops.test3c")   
        layout.operator("myops.test3d")   
        layout.separator()

        layout.label(text="Bounding object")
        layout.operator("myops.test4")        
        layout.operator("myops.test5")
        layout.operator("myops.test6")
        layout.separator()


        layout.label(text="Move")
        layout.operator("myops.test7")
        layout.operator("myops.test7b")
        layout.operator("myops.test7c")
        layout.operator("myops.test7d")
        layout.operator("myops.test7e")
        layout.separator()

        layout.label(text="Render")
        layout.operator("myops.test8")
        layout.separator()

        layout.label(text="Run")
        layout.operator("myops.test9")
        layout.separator()
        
        layout.operator("myops.test10")







###################################
###################################
###################################
## Register Addon 


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.addon_data = PointerProperty(type=AddonData)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.addon_data



if __name__ == "__main__":
    register()


