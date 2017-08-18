from django.shortcuts import render, redirect
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail
from django.contrib.auth import authenticate
import simplejson
from .models import Room, User, RoomStudent

import random
import cloudconvert
import zipfile
import os
import types
import shutil
# Create your views here.


@csrf_exempt
def fileFormat(file):
    oldFormat = "ppt"
    if file.name[-1] == 'x':
        oldFormat = "pptx"
    elif file.name[-1] == 'y':
        oldFormat = "key"
    elif file.name[-1] == 'f':
        oldFormat = "pdf"
    else:
        oldFormat = "ppt"
    return oldFormat


@csrf_exempt
def convertFile(user, file):
    filedir = './'+str(user.user_file)
    oldFormat = fileFormat(file)
    api = cloudconvert.Api('L1LSv8pwJ7Qdd43Qs55ZJSUimEFuI1T1I4cExjNfDCZyb-V0rfxc-6B09KFuFHcl0aooGZ_CR7GiWdrgJ9A5_Q')
    process = api.convert({
        "inputformat": oldFormat,
        "outputformat": "png",
        "input": "upload",
        "filename": "user."+oldFormat,
        "file": open(filedir, 'rb')})
    process.wait()
    process.download('./frontend/static/pptzip/'+str(user.id)+'and'+str(user.file_num)+'.zip')
    os.remove(filedir)
    return


@csrf_exempt
def getTeacherFileInfo(request):
    req = simplejson.load(request)
    user = User.objects.get(name=req['name'])
    pageNum = sum([len(x) for _,_,x in os.walk('./frontend/static/ppt/'+str(user.id)+'and'+str(user.file_num))])
    response = JsonResponse({
        'teacherId': user.id,
        'fileNum': user.file_num,
        'maxPage': pageNum
    })
    return response


# need teacherName and roomId
# change the ppt name to teachername+roomid
@csrf_exempt
def closeRoomForFile(request):
    req = simplejson.load(request)
    oldDir = './frentend/static/ppt/'+req['teacherName']
    newDir = './frentend/static/ppt/'+req['teacherName']+req['roomId']
    response = JsonResponse({})
    return response


# need teachername and roomid
# will delete the ppt when kill the videoRoom
@csrf_exempt
def removeFile(request):
    req = simplejson.load(request)
    dir = './frontend/static/ppt/'+req['teacherName']+req['roomId']
    shutil.rmtree(dir)
    response = JsonResponse({})
    return response


@csrf_exempt
def getImg(request):
    req = simplejson.load(request)
    user = User.objects.get(username = req['account'])
    response = JsonResponse({'route': str(user.user_img)[8:]})
    return response


@csrf_exempt
def uploadFile(request):
    file = request.FILES.get('file')
    account = request.COOKIES.get('userAccount')
    user = User.objects.get(username = account)
    user.user_file = file
    user.file_num += 1
    user.save()
    convertFile(user, file)
    zip_file = zipfile.ZipFile('./frontend/static/pptzip/'+str(user.id)+'and'+str(user.file_num)+'.zip')  
    if os.path.isdir('./frontend/static/ppt/'+str(user.id)+'and'+str(user.file_num)):  
        pass  
    else:  
        os.mkdir('./frontend/static/ppt/'+str(user.id)+'and'+str(user.file_num))  
    for names in zip_file.namelist():  
        zip_file.extract(names,'./frontend/static/ppt/'+str(user.id)+'and'+str(user.file_num))  
    zip_file.close()
    response = JsonResponse({})
    return response


@csrf_exempt
def changeNum(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomId'])
    room.student_num = req['studentNum']
    room.save()
    response = JsonResponse({})
    return response


@csrf_exempt
def upload(request):
    uploadFile = request.FILES.get('myfile')
    account = request.COOKIES.get('userAccount')
    uploadUser = User.objects.get(username = account)
    oldImg = uploadUser.user_img
    uploadUser.user_img = uploadFile
    uploadUser.save()
    if oldImg != '':
        os.remove('./'+str(oldImg))
    response = JsonResponse({})
    return response


@csrf_exempt
def kickOut(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    student = User.objects.get(name=req['name'])
    roomStudent = RoomStudent.objects.get(room=room, student=student)
    roomStudent.can_watch = False
    roomStudent.save()
    response = JsonResponse({})
    return response


@csrf_exempt
def allowAllSpeak(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    roomStudents = RoomStudent.objects.filter(room=room)
    for roomStudent in roomStudents:
        roomStudent.can_speak = True
        roomStudent.save()
    response = JsonResponse({})
    return response


@csrf_exempt
def allowSpeak(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    for name in req['student']:
        student = User.objects.get(name=name)
        roomStudent = RoomStudent.objects.get(room=room, student=student)
        roomStudent.can_speak = True
        roomStudent.save()
    response = JsonResponse({})
    return response


@csrf_exempt
def gagAll(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    roomStudents = RoomStudent.objects.filter(room=room)
    stu = []
    for roomStudent in roomStudents:
        roomStudent.can_speak = False
        stu.append(roomStudent.student.name)
        roomStudent.save()
    response = JsonResponse({'gagList': stu})
    return response


@csrf_exempt
def checkGag(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    student = User.objects.get(name=req['name'])
    roomStudent = RoomStudent.objects.get(room=room, student=student)
    response = JsonResponse({'result': roomStudent.can_speak})
    return response


@csrf_exempt
def gag(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    student = User.objects.get(name=req['name'])
    roomStudent = RoomStudent.objects.get(room=room, student=student)
    roomStudent.can_speak = False
    roomStudent.save()
    response = JsonResponse({})
    return response


@csrf_exempt
def getRoomInfo(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    response = JsonResponse({
        'teacherName': room.teacher.name,
        'stuNum': room.student_num,
        'roomName': room.room_name
    })
    return response


@csrf_exempt
def joinRoom(request):
    req = simplejson.load(request)
    room = Room.objects.get(id=req['roomID'])
    student = User.objects.get(username=req['stuAccount'])
    roomStudent = RoomStudent.objects.filter(room=room, student=student)
    if len(roomStudent) == 0:
        RoomStudent.objects.create(room=room, student=student)
        response = JsonResponse({'result': room.id})
        return response
    elif roomStudent[0].can_watch == False:
        response = JsonResponse({'result': 'cannot'})
        return response
    else:
        response = JsonResponse({'result': room.id})
        return response


@csrf_exempt
def getName(request):
    req = simplejson.load(request)
    user = User.objects.get(username=req['account'])
    response = JsonResponse({
        'name': user.name,
        'isTeacher': user.is_teacher
    })
    return response


@csrf_exempt
def createRoom(request):
    req = simplejson.load(request)
    roomName = req['roomName']
    authId = req['account']
    teacher = User.objects.get(username=authId)
    Room.objects.create(teacher=teacher, room_name=roomName)
    response = JsonResponse({})
    return response


@csrf_exempt
def getRooms(request):
    req = simplejson.load(request)
    if req['type'] == 1:
        rooms = Room.objects.order_by('-create_time')[:8]
    else:
        rooms = Room.objects.order_by('-create_time')
    myroom = []
    for room in rooms:
        userImg = str(room.teacher.user_img)
        myroom.append({'roomName': room.room_name,
                       'teacherName': room.teacher.name,
                       'id': room.id,
                       'studentNum': room.student_num,
                       'userImg': userImg[8:]})
    response = JsonResponse(
        {'rooms': myroom})
    return response


@csrf_exempt
def getVerification(request):
    req = simplejson.load(request)
    user = User.objects.filter(username=req['mail'])
    if len(user) != 0:
        response = JsonResponse({'verification': 'exist'})
        return response
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    verification = []
    for i in range(6):
        verification.append(random.choice(seed))
    salt = ''.join(verification)
    send_mail('Ur verification code!', salt,
              'a1137901181@163.com', [req['mail']], fail_silently=False)
    response = JsonResponse({'verification': salt})
    return response


@csrf_exempt
def signUp(request):
    req = simplejson.load(request)
    userFilterWithName = User.objects.filter(name=req['username'])
    if len(userFilterWithName) != 0:
        response = JsonResponse({'result': False})
        return response
    user = User.objects.create_user(
        username=req['mail'], password=req['password'], name=req['username'])
    user.save()
    response = JsonResponse({'result': True})
    return response


@csrf_exempt
def login(request):
    req = simplejson.load(request)
    user = authenticate(username=req['account'], password=req['password'])
    if user is None:
        response = JsonResponse({'result': False})
    else:
        response = JsonResponse({'result': True, 'name': user.name})
    return response


@csrf_exempt
def getRand(request):
    req = simplejson.load(request)
    user = User.objects.filter(username=req['mail'])
    if len(user) == 0:
        response = JsonResponse({'verification': 'none'})
        return response
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    verification = []
    for i in range(6):
        verification.append(random.choice(seed))
    salt = ''.join(verification)
    send_mail('Ur verification code!', salt,
              'a1137901181@163.com', [req['mail']], fail_silently=False)
    response = JsonResponse({'verification': salt})
    return response


@csrf_exempt
def changePasswd(request):
    req = simplejson.load(request)
    user = User.objects.get(username=req['username'])
    user.set_password(req['password'])
    user.save()
    response = JsonResponse({'result': True})
    return response


@csrf_exempt
def changeName(request):
    req = simplejson.load(request)
    userFilterWithName = User.objects.filter(name=req['newname'])
    if len(userFilterWithName) != 0:
        response = JsonResponse({'result': False})
        return response
    user = User.objects.get(username=req['account'])
    user.name = req['newname']
    user.save()
    response = JsonResponse({'result': True})
    return response
# Create your views here.
